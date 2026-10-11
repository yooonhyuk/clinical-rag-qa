"""XLSX extraction with the standard library (zip + XML), no openpyxl.

- one sheet = one section (`section_title` = sheet name); hidden sheets are indexed too and
  their state is reported in the diagnostics (`extract_xlsx_with_diagnostics`)
- cell values: shared strings, inline strings, formula cached values (`<v>`); numeric cells with
  a date number format (built-in 14-22, or a custom format containing y/m/d) become ISO dates
- the header row is the first of the top 15 rows with at least 4 non-empty cells. Rows above it
  are kept as "a | b" lines (titles, notices); rows below become "열이름: 값; ..." lines
  (only the columns that hold a value, so a far-away column costs nothing) prefixed with
  "[sheet name]" so one line still says where it came from

XLSX has no pages; the sheet name is the citation (`page_number=None`).
Container safety limits (no DTD, zip bomb and part ratio caps, the text budget) are shared with the
DOCX extractor.
"""

import logging
import posixpath
import re
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

from app.services.document_types import ExtractionError, Section
from app.services.docx_extractor import (
    OoxmlArchive,
    TextBudget,
    open_ooxml,
    parse_xml,
    read_member,
    utf8_size,
)
from app.services.pdf_extractor import normalize_text

logger = logging.getLogger(__name__)

S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

_HEADER_SCAN_ROWS = 15
_HEADER_MIN_CELLS = 4
_BUILTIN_DATE_IDS = set(range(14, 23))
_QUOTED_RE = re.compile(r'"[^"]*"|\[[^\]]*\]|\\.|_.|\*.')
_REF_RE = re.compile(r"^([A-Z]+)(\d+)$")
_MAX_COLUMNS = 16_384
_MAX_SHEETS = 256
_ELAPSED_RE = re.compile(r"\[(?:h+|m+|s+)\]", re.IGNORECASE)  # [h]:mm:ss = a duration, not a date


def _to_int(raw: str | None, default: int = 0) -> int:
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _column_index(ref: str) -> int | None:
    match = _REF_RE.match(ref)
    if not match:
        return None
    index = 0
    for ch in match.group(1):
        index = index * 26 + ord(ch) - 64
    return index - 1 if index <= _MAX_COLUMNS else None


def _inline_text(el: ET.Element) -> str:
    """Text of a shared/inline string item; phonetic guides (`rPh`) are not part of the value."""
    parts: list[str] = []
    for child in el:
        if child.tag == f"{S}t":
            parts.append(child.text or "")
        elif child.tag == f"{S}r":
            parts.extend(t.text or "" for t in child.findall(f"{S}t"))
    return "".join(parts)


def _shared_strings(archive: OoxmlArchive) -> list[str]:
    data = read_member(archive, "xl/sharedStrings.xml", required=False)
    if data is None:
        return []
    return [_inline_text(si) for si in parse_xml(data, "xl/sharedStrings.xml").findall(f"{S}si")]


def _is_date_format(code: str) -> bool:
    if _ELAPSED_RE.search(code):
        return False
    return bool(re.search(r"[ymd]", _QUOTED_RE.sub("", code).lower()))


def _date_styles(archive: OoxmlArchive) -> set[int]:
    """Indexes of cellXfs whose number format is a date."""
    data = read_member(archive, "xl/styles.xml", required=False)
    if data is None:
        return set()
    root = parse_xml(data, "xl/styles.xml")
    custom = {
        _to_int(n.get("numFmtId"), -1): n.get("formatCode", "")
        for n in root.iterfind(f"{S}numFmts/{S}numFmt")
    }
    styles: set[int] = set()
    for i, xf in enumerate(root.iterfind(f"{S}cellXfs/{S}xf")):
        fmt_id = _to_int(xf.get("numFmtId"))
        if fmt_id in _BUILTIN_DATE_IDS or (fmt_id in custom and _is_date_format(custom[fmt_id])):
            styles.add(i)
    return styles


def _serial_to_text(value: float, date1904: bool) -> str | None:
    epoch = datetime(1904, 1, 1) if date1904 else datetime(1899, 12, 30)
    try:
        moment = epoch + timedelta(days=value)
    except OverflowError:
        return None
    if value < 1:
        return moment.strftime("%H:%M")
    if moment.hour == 0 and moment.minute == 0:
        return moment.strftime("%Y-%m-%d")
    return moment.strftime("%Y-%m-%d %H:%M")


def _number_text(raw: str) -> str:
    try:
        number = float(raw)
    except ValueError:
        return raw
    return str(int(number)) if number.is_integer() and abs(number) < 1e15 else raw


def _cell_value(c: ET.Element, strings: list[str], date_styles: set[int], date1904: bool) -> str:
    kind = c.get("t", "n")
    if kind == "inlineStr":
        is_el = c.find(f"{S}is")
        return _inline_text(is_el) if is_el is not None else ""
    v = c.find(f"{S}v")
    raw = (v.text or "") if v is not None else ""
    if not raw:
        return ""
    if kind == "s":
        try:
            return strings[int(raw)]
        except (ValueError, IndexError):
            return ""
    if kind == "b":
        return "TRUE" if raw == "1" else "FALSE"
    if kind in {"str", "e"}:
        return raw
    if _to_int(c.get("s")) in date_styles:
        try:
            if (text := _serial_to_text(float(raw), date1904)) is not None:
                return text
        except ValueError:
            pass
    return _number_text(raw)


Row = dict[int, str]  # column index -> value, only the columns that hold a value


def _sheet_rows(
    root: ET.Element,
    strings: list[str],
    date_styles: set[int],
    date1904: bool,
    budget: TextBudget,
) -> list[tuple[int, Row]]:
    """Cell values are paid for while they are read: a shared string referenced by many cells
    multiplies a tiny file into gigabytes."""
    rows: list[tuple[int, Row]] = []
    for seq, row in enumerate(root.iterfind(f"{S}sheetData/{S}row"), start=1):
        number = _to_int(row.get("r"), seq)
        cells: Row = {}
        next_col = 0
        for c in row.findall(f"{S}c"):
            col = _column_index(c.get("r", ""))
            col = next_col if col is None else col
            next_col = col + 1
            raw = _cell_value(c, strings, date_styles, date1904)
            budget.check(len(raw))  # before the normalized copy is made (chars <= UTF-8 bytes)
            value = " ".join(raw.split())
            if value:
                budget.spend(utf8_size(value))
                cells[col] = value
        if cells:
            rows.append((number, cells))
    return rows


def _plain(row: Row) -> str:
    return " | ".join(row[c] for c in sorted(row))


def _labelled(header: Row, row: Row) -> str:
    return "; ".join(f"{header[c]}: {row[c]}" if c in header else row[c] for c in sorted(row))


def _sheet_lines(name: str, rows: list[tuple[int, Row]], budget: TextBudget) -> list[str]:
    lines: list[str] = []
    for line in _render_lines(name, rows):
        budget.spend(utf8_size(line) + 1)  # the header text is repeated on every row below it
        lines.append(line)
    return lines


def _render_lines(name: str, rows: list[tuple[int, Row]]) -> Iterator[str]:
    header_at = next(
        (
            i
            for i, (n, r) in enumerate(rows)
            if n <= _HEADER_SCAN_ROWS and len(r) >= _HEADER_MIN_CELLS
        ),
        None,
    )
    if header_at is None:
        for _, r in rows:
            yield f"[{name}] {_plain(r)}"
        return
    header = rows[header_at][1]
    for _, r in rows[:header_at]:
        yield _plain(r)
    for _, r in rows[header_at + 1 :]:
        yield f"[{name}] {_labelled(header, r)}"


def _sheet_parts(archive: OoxmlArchive) -> list[tuple[str, str, str]]:
    """(sheet name, state, part path) in workbook order."""
    workbook = read_member(archive, "xl/workbook.xml")
    rels = read_member(archive, "xl/_rels/workbook.xml.rels")
    if workbook is None or rels is None:
        raise ExtractionError("CORRUPTED_FILE", "XLSX workbook parts are missing")
    targets = {
        r.get("Id", ""): r.get("Target", "")
        for r in parse_xml(rels, "xl/_rels/workbook.xml.rels").iter(f"{REL}Relationship")
    }
    parts: list[tuple[str, str, str]] = []
    for sheet in parse_xml(workbook, "xl/workbook.xml").iter(f"{S}sheet"):
        if len(parts) >= _MAX_SHEETS:
            raise ExtractionError("CORRUPTED_FILE", f"XLSX has more than {_MAX_SHEETS} sheets")
        target = targets.get(sheet.get(f"{R}id", ""))
        if not target:
            continue
        part = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        parts.append(
            (sheet.get("name", ""), sheet.get("state", "visible"), posixpath.normpath(part))
        )
    return parts


def extract_xlsx_with_diagnostics(path: Path) -> tuple[list[Section], list[str]]:
    """Sections (one per non-empty sheet) and diagnostics lines such as "sheet 'X': hidden".

    A sheet that points at an already-read part is skipped (and noted in the diagnostics)."""
    diagnostics: list[str] = []
    sections: list[Section] = []
    with open_ooxml(path, "XLSX") as archive:
        workbook = read_member(archive, "xl/workbook.xml")
        date1904 = False
        if workbook is not None:
            pr = parse_xml(workbook, "xl/workbook.xml").find(f"{S}workbookPr")
            date1904 = pr is not None and pr.get("date1904", "0") in {"1", "true"}
        strings = _shared_strings(archive)
        date_styles = _date_styles(archive)
        seen_parts: set[str] = set()
        cell_budget = TextBudget(archive, "XLSX")  # values, and separately the rendered lines,
        line_budget = TextBudget(archive, "XLSX")  # across all sheets
        for name, state, part in _sheet_parts(archive):
            if part in seen_parts:  # a healthy workbook never shares a part between sheets
                diagnostics.append(f"sheet '{name}': duplicate part {part}, skipped")
                continue
            seen_parts.add(part)
            if state != "visible":
                diagnostics.append(f"sheet '{name}': {state}")
            data = read_member(archive, part)
            if data is None:
                continue
            rows = _sheet_rows(parse_xml(data, part), strings, date_styles, date1904, cell_budget)
            lines = _sheet_lines(name, rows, line_budget)
            if lines:
                text = normalize_text("\n".join(lines))
                sections.append(Section(text=text, section_title=name))
    for line in diagnostics:
        logger.info("%s: %s", path.name, line)
    return sections, diagnostics


def extract_xlsx(path: Path) -> list[Section]:
    return extract_xlsx_with_diagnostics(path)[0]
