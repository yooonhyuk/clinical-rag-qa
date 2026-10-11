"""DOCX extraction with the standard library (zip + XML), no python-docx.

- paragraphs whose style is a heading ("Heading N" / "제목 N", or an `outlineLvl`) build the
  section path ("1. 개요 > 1.1 목적"); every other paragraph is body text of the current section
- tables become "열이름: 값; ..." lines (`rows_to_lines`) inside the current section. A merged
  cell (`gridSpan`, `vMerge`) keeps its value once and leaves the other grid cells empty. The
  first row is the header only when every cell is non-empty (same rule as HTML tables)
- headers, footers, footnotes and tracked deletions (`w:del`, `w:moveFrom`) are left out;
  tracked insertions (`w:ins`) are kept

DOCX has no pages; the section path is the citation (`page_number=None`).

The OOXML container helpers (`open_ooxml`, `read_member`, `parse_xml`, `TextBudget`) are shared
with the XLSX extractor and enforce the safety limits: no DTD/entities (rejected inside the parser,
any encoding), a cap on zip entries and on the bytes really decompressed per archive (zip bombs;
each part is read once), a cap on the compression ratio of each large part, and a cap on the text
built from the archive (a small part referenced or repeated many times must not become gigabytes).
Malformed structure (nesting deeper than MAX_DEPTH, a table row wider than MAX_GRID_COLUMNS) is a
`CORRUPTED_FILE`.
"""

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from app.services.document_types import ExtractionError, Section
from app.services.pdf_extractor import normalize_text
from app.services.table_rows import rows_to_lines

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # password-protected OOXML is an OLE container
MAX_ENTRIES = 5_000
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
# A part above 1 MB that inflates more than 100x is refused before it is parsed: the XML tree costs
# ~13-27 B per XML byte, so a 130 KB zip of repeated tiny elements would otherwise cost >1 GB.
# Real documents measured 5-20x (a 7.4 MB / 82.5 MB workbook is 11x); the attacks were 480-500x.
MAX_PART_RATIO = 100
_RATIO_MIN_BYTES = 1024 * 1024
# Text built from one archive, in UTF-8 bytes: max(floor, ratio x bytes really decompressed).
# Healthy files build less text than their XML (0.4x for a 50,000-row workbook).
MIN_TEXT_BYTES = 8 * 1024 * 1024
TEXT_RATIO = 2
MAX_DEPTH = 100  # element nesting walked recursively (real documents stay far below)
MAX_GRID_COLUMNS = 1_000  # a Word table has at most 63 columns

_HEADING_NAME_RE = re.compile(r"^(?:heading|제목)\s*(\d)$", re.IGNORECASE)
_SKIP_TAGS = {
    f"{W}pPr",
    f"{W}rPr",
    f"{W}tblPr",
    f"{W}trPr",
    f"{W}tcPr",
    f"{W}del",
    f"{W}moveFrom",
    "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback",
}
_TITLE_DEPTH = 3


class OoxmlArchive(zipfile.ZipFile):
    """ZipFile that counts the bytes it really decompresses and reads each part only once."""

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.cache: dict[str, bytes] = {}
        self.bytes_read = 0


def open_ooxml(path: Path, kind: str) -> OoxmlArchive:
    """Open an OOXML zip, mapping the failure modes to typed `ExtractionError`s."""
    try:
        with path.open("rb") as fh:
            magic = fh.read(8)
    except OSError as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Cannot read {kind}: {exc}") from exc
    if magic == _OLE_MAGIC:
        raise ExtractionError("ENCRYPTED_FILE", f"{kind}: 암호화되었거나 구형(doc/xls) 파일입니다")
    try:
        archive = OoxmlArchive(path)
    except (zipfile.BadZipFile, OSError) as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Cannot open {kind}: {exc}") from exc
    infos = archive.infolist()
    if len(infos) > MAX_ENTRIES or sum(i.file_size for i in infos) > MAX_TOTAL_BYTES:
        archive.close()
        raise ExtractionError("CORRUPTED_FILE", f"{kind} archive is too large to read safely")
    return archive


def read_member(archive: OoxmlArchive, name: str, *, required: bool = True) -> bytes | None:
    """Bytes of a part. Repeated reads hit the cache; the bytes actually decompressed across the
    whole archive are capped at MAX_TOTAL_BYTES (the zip header sizes can lie)."""
    if name in archive.cache:
        return archive.cache[name]
    try:
        info = archive.getinfo(name)
    except KeyError:
        if required:
            raise ExtractionError("CORRUPTED_FILE", f"Missing part: {name}") from None
        return None
    if info.file_size > MAX_MEMBER_BYTES:
        raise ExtractionError("CORRUPTED_FILE", f"Part too large: {name}")
    limit = min(MAX_MEMBER_BYTES, MAX_TOTAL_BYTES - archive.bytes_read)
    try:
        with archive.open(info) as fh:
            data = fh.read(limit + 1)
    except (zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError) as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Cannot read part {name}: {exc}") from exc
    if len(data) > limit:
        raise ExtractionError("CORRUPTED_FILE", f"Part or archive too large: {name}")
    if len(data) > _RATIO_MIN_BYTES and len(data) > MAX_PART_RATIO * max(info.compress_size, 1):
        raise ExtractionError("CORRUPTED_FILE", f"Part is compressed suspiciously well: {name}")
    archive.bytes_read += len(data)
    archive.cache[name] = data
    return data


class TextBudget:
    """UTF-8 bytes of text built from an archive so far; `spend` stops the build once the cap
    (`MIN_TEXT_BYTES` or `TEXT_RATIO` x the bytes decompressed, whichever is larger) is passed."""

    def __init__(self, archive: OoxmlArchive, kind: str) -> None:
        self.archive = archive
        self.kind = kind
        self.used = 0

    @property
    def remaining(self) -> int:
        return max(MIN_TEXT_BYTES, TEXT_RATIO * self.archive.bytes_read) - self.used

    def check(self, size: int) -> None:
        if size > self.remaining:
            raise ExtractionError("CORRUPTED_FILE", f"{self.kind} text is too large to index")

    def spend(self, size: int) -> None:
        self.check(size)
        self.used += size


def utf8_size(text: str) -> int:
    return len(text.encode("utf-8"))


def check_depth(depth: int, kind: str) -> None:
    if depth > MAX_DEPTH:
        raise ExtractionError("CORRUPTED_FILE", f"{kind} nesting is deeper than {MAX_DEPTH}")


class _NoDoctypeBuilder(ET.TreeBuilder):
    """Tree builder that refuses any DOCTYPE (and so any entity declaration), whatever the
    encoding: the check runs inside the parser, not on the raw bytes."""

    def doctype(self, name, pubid, system) -> None:  # noqa: ANN001
        raise ValueError("DTD declarations are not allowed")


def parse_xml(data: bytes, name: str) -> ET.Element:
    parser = ET.XMLParser(target=_NoDoctypeBuilder())
    try:
        parser.feed(data)
        return parser.close()
    except ValueError as exc:
        raise ExtractionError(
            "CORRUPTED_FILE", f"DTD/entity declarations not allowed: {name}"
        ) from exc
    except ET.ParseError as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Invalid XML in {name}: {exc}") from exc


def _style_levels(archive: OoxmlArchive) -> dict[str, int]:
    """styleId -> heading level (1-based) for heading styles and styles with an outline level.

    A style inherits the level of the style it is `basedOn` (user style <- Heading 1)."""
    data = read_member(archive, "word/styles.xml", required=False)
    if data is None:
        return {}
    own: dict[str, int] = {}
    parent: dict[str, str] = {}
    for style in parse_xml(data, "word/styles.xml").iter(f"{W}style"):
        style_id = style.get(f"{W}styleId")
        if not style_id:
            continue
        based = style.find(f"{W}basedOn")
        if based is not None and based.get(f"{W}val"):
            parent[style_id] = based.get(f"{W}val", "")
        name_el = style.find(f"{W}name")
        match = (
            _HEADING_NAME_RE.match((name_el.get(f"{W}val") or "").strip())
            if name_el is not None
            else None
        )
        if match:
            own[style_id] = max(1, int(match.group(1)))
            continue
        outline = style.find(f"{W}pPr/{W}outlineLvl")
        if outline is not None and (lvl := _outline_level(outline)) is not None:
            own[style_id] = lvl
    # Each style is resolved once: a chain stops at the first style already resolved (O(N), a
    # long or circular basedOn chain cannot cost quadratic time).
    levels: dict[str, int] = dict(own)
    resolved = set(own)
    for style_id in parent:
        chain: list[str] = []
        on_chain: set[str] = set()
        current = style_id
        while current and current not in resolved and current not in on_chain:
            chain.append(current)
            on_chain.add(current)
            current = parent.get(current, "")
        level = levels.get(current) if current in resolved else None
        for sid in chain:
            resolved.add(sid)
            if level is not None:
                levels[sid] = level
    return levels


def _outline_level(el: ET.Element) -> int | None:
    try:
        value = int(el.get(f"{W}val", ""))
    except ValueError:
        return None
    return value + 1 if 0 <= value <= 8 else None  # 9 = body text


def _text(el: ET.Element, out: list[str], depth: int) -> None:
    check_depth(depth, "DOCX")
    for child in el:
        tag = child.tag
        if tag in _SKIP_TAGS:
            continue
        if tag == f"{W}t":
            out.append(child.text or "")
        elif tag == f"{W}tab":
            out.append(" ")
        elif tag in {f"{W}br", f"{W}cr"}:
            out.append(" ")
        else:
            _text(child, out, depth + 1)


def _paragraph_text(p: ET.Element, depth: int) -> str:
    parts: list[str] = []
    _text(p, parts, depth + 1)
    return " ".join("".join(parts).split())


def _heading_level(p: ET.Element, style_levels: dict[str, int]) -> int | None:
    ppr = p.find(f"{W}pPr")
    if ppr is None:
        return None
    outline = ppr.find(f"{W}outlineLvl")
    if outline is not None:
        return _outline_level(outline)
    style = ppr.find(f"{W}pStyle")
    return style_levels.get(style.get(f"{W}val", "")) if style is not None else None


_CONTAINER_TAGS = {f"{W}sdt", f"{W}sdtContent", f"{W}ins"}


def _cell_text(container: ET.Element, depth: int) -> str:
    """Text of a cell from its direct children only, so text nested below a paragraph (a text
    box) or a nested table is collected exactly once. A nested table is flattened in order."""
    check_depth(depth, "DOCX")
    parts: list[str] = []
    for child in container:
        if child.tag == f"{W}p":
            text = _paragraph_text(child, depth + 1)
        elif child.tag == f"{W}tbl":
            text = " ".join(
                t
                for tr in child.findall(f"{W}tr")
                for tc in tr.findall(f"{W}tc")
                if (t := _cell_text(tc, depth + 2))
            )
        elif child.tag in _CONTAINER_TAGS:
            text = _cell_text(child, depth + 1)
        else:
            continue
        if text:
            parts.append(text)
    return " ".join(parts)


def _row_grid(tr: ET.Element, tag: str) -> int:
    """Empty grid columns before/after the cells of a row (`w:gridBefore` / `w:gridAfter`)."""
    el = tr.find(f"{W}trPr/{W}{tag}")
    try:
        return max(0, min(int(el.get(f"{W}val", "0")), 200)) if el is not None else 0
    except ValueError:
        return 0


def _widen(row: list[str], extra: int) -> None:
    if len(row) + extra > MAX_GRID_COLUMNS:
        raise ExtractionError("CORRUPTED_FILE", f"DOCX table row is wider than {MAX_GRID_COLUMNS}")
    row.extend([""] * extra)


def _row_cells(tr: ET.Element, depth: int) -> list[str]:
    row: list[str] = []
    _widen(row, _row_grid(tr, "gridBefore"))
    for tc in tr.findall(f"{W}tc"):
        props = tc.find(f"{W}tcPr")
        span = 1
        continued = False
        if props is not None:
            grid = props.find(f"{W}gridSpan")
            if grid is not None:
                try:
                    span = max(1, min(int(grid.get(f"{W}val", "1")), 200))
                except ValueError:
                    span = 1
            merge = props.find(f"{W}vMerge")
            continued = merge is not None and merge.get(f"{W}val", "continue") != "restart"
        _widen(row, span)
        row[-span] = "" if continued else _cell_text(tc, depth + 1)
    _widen(row, _row_grid(tr, "gridAfter"))
    return row


def _table_lines(tbl: ET.Element, budget: TextBudget, depth: int) -> list[str]:
    """Rendered one row at a time, each line paid for before it is built: the header text is
    repeated on every body line, so a few rows under a long header would otherwise be gigabytes."""
    check_depth(depth, "DOCX")
    lines: list[str] = []
    header: list[list[str]] = []
    header_size = 0
    for i, tr in enumerate(tbl.findall(f"{W}tr")):
        row = _row_cells(tr, depth + 1)
        if i == 0 and all(c.strip() for c in row):
            header = [row]
            header_size = sum(utf8_size(c) for c in row)
            budget.spend(header_size)
            continue
        if not any(c.strip() for c in row):
            continue
        # upper bound of the line: every header name, every value and a "h: v; " separator
        budget.spend(header_size + sum(utf8_size(c) + 4 for c in row))
        lines.extend(rows_to_lines(header, [row]))
    if header and not lines:
        # a one-row table (a boxed note, a title block) has no body for its "header": keep its text
        lines.append(" | ".join(c for c in header[0] if c))
    return lines


def extract_docx(path: Path) -> list[Section]:
    with open_ooxml(path, "DOCX") as archive:
        data = read_member(archive, "word/document.xml")
        if data is None:
            raise ExtractionError("CORRUPTED_FILE", "Missing part: word/document.xml")
        levels = _style_levels(archive)
    body = parse_xml(data, "word/document.xml").find(f"{W}body")
    if body is None:
        raise ExtractionError("CORRUPTED_FILE", "DOCX has no body")

    budget = TextBudget(archive, "DOCX")
    sections: list[Section] = []
    path_stack: list[tuple[int, str]] = []
    buffer: list[str] = []

    def title() -> str | None:
        return " > ".join(t for _, t in path_stack[-_TITLE_DEPTH:]) or None

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append(Section(text=normalize_text(text), section_title=title()))
        buffer.clear()

    def walk(container: ET.Element, depth: int) -> None:
        check_depth(depth, "DOCX")
        for el in container:
            if el.tag == f"{W}p":
                text = _paragraph_text(el, depth + 1)
                if not text:
                    continue
                budget.spend(utf8_size(text) + 1)
                level = _heading_level(el, levels)
                if level is not None:
                    flush()
                    while path_stack and path_stack[-1][0] >= level:
                        path_stack.pop()
                    path_stack.append((level, normalize_text(text)))
                else:
                    buffer.append(text)
            elif el.tag == f"{W}tbl":
                buffer.extend(_table_lines(el, budget, depth + 1))
            elif el.tag in _CONTAINER_TAGS:
                walk(el, depth + 1)

    walk(body, 0)
    flush()
    return sections
