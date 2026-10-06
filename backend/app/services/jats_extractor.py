"""JATS XML (Europe PMC / PMC full text) extraction with the standard library.

- `<article-title>` and the abstract come first; the abstract's own `<sec>`s keep their titles
- `<body>` `<sec>/<title>` nesting becomes the section path ("Main body > Follow-up")
- paragraphs, list items, figure captions and boxed text are kept as text
- `<table-wrap>` becomes one section per table: label + caption, then one line per row in
  "header: value; header: value" form so a single row still carries its column names
- `<back>` (references, acknowledgements, funding, competing interests) is skipped

XML files have no pages, so `page_number` is always None; the section path is the citation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from app.services.document_types import ExtractionError, Section
from app.services.pdf_extractor import normalize_text
from app.services.table_rows import rows_to_lines

_SKIP_TAGS = {"ref-list", "fn-group", "ack", "glossary", "table-wrap-foot", "label", "object-id"}
_SKIP_SEC_TYPES = {"kwd-group", "history", "supplementary-material"}
# Back-matter style sections that some publishers put inside <body>.
_SKIP_SEC_TITLES = {
    "acknowledgements",
    "acknowledgments",
    "authors’ contributions",
    "authors' contributions",
    "author contributions",
    "funding",
    "availability of data and materials",
    "data availability statement",
    "ethics approval and consent to participate",
    "consent for publication",
    "competing interests",
    "conflicts of interest",
    "associated data",
    "footnotes",
    "references",
}
_BLOCK_TAGS = {"p", "list-item", "disp-quote", "def-item", "statement"}


def _text(el: ET.Element) -> str:
    return " ".join(normalize_text("".join(el.itertext())).split())


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _row(tr: ET.Element) -> list[str]:
    cells: list[str] = []
    for cell in tr:
        if _local(cell.tag) in {"td", "th"}:
            cells.extend([_text(cell)] * max(1, int(cell.get("colspan", "1") or 1)))
    return cells


def _table_lines(table: ET.Element) -> list[str]:
    header: list[list[str]] = []
    body: list[list[str]] = []
    for part in table.iter():
        if _local(part.tag) in {"thead", "tbody", "tfoot"}:
            target = header if _local(part.tag) == "thead" else body
            target += [_row(tr) for tr in part if _local(tr.tag) == "tr"]
    if not header and not body:  # rows directly under <table>
        body = [_row(tr) for tr in table if _local(tr.tag) == "tr"]
    return rows_to_lines(header, body)


class _Collector:
    def __init__(self) -> None:
        self.sections: list[Section] = []
        self.path: list[str] = []
        self.buffer: list[str] = []

    def title(self) -> str | None:
        return " > ".join(self.path[-3:]) if self.path else None

    def flush(self) -> None:
        text = "\n".join(self.buffer).strip()
        if text:
            self.sections.append(Section(text=text, section_title=self.title()))
        self.buffer.clear()

    def table(self, wrap: ET.Element) -> None:
        self.flush()
        label = next((_text(c) for c in wrap if _local(c.tag) == "label"), "")
        caption = next((_text(c) for c in wrap if _local(c.tag) == "caption"), "")
        name = " ".join(x for x in (label, caption) if x) or "Table"
        lines = [name]
        for table in (c for c in wrap.iter() if _local(c.tag) == "table"):
            lines += _table_lines(table)
        title = " > ".join([*self.path[-2:], label or "Table"])
        self.sections.append(Section(text="\n".join(lines), section_title=title))

    def walk(self, el: ET.Element) -> None:
        tag = _local(el.tag)
        if tag in _SKIP_TAGS or el.get("sec-type") in _SKIP_SEC_TYPES:
            return
        if tag == "table-wrap":
            self.table(el)
            return
        if tag in {"sec", "abstract", "boxed-text", "app"}:
            heading = next((c for c in el if _local(c.tag) == "title"), None)
            if heading is not None and _text(heading).lower() in _SKIP_SEC_TITLES:
                return
            self.flush()
            pushed = False
            if heading is not None and _text(heading):
                self.path.append(_text(heading))
                pushed = True
            elif tag == "abstract":
                self.path.append("Abstract")
                pushed = True
            for child in el:
                if child is not heading:
                    self.walk(child)
            self.flush()
            if pushed:
                self.path.pop()
            return
        if tag == "fig":
            caption = " ".join(_text(c) for c in el if _local(c.tag) in {"label", "caption"})
            if caption:
                self.buffer.append(caption)
            return
        if tag in _BLOCK_TAGS and not any(
            _local(c.tag) in _BLOCK_TAGS for c in el.iter() if c is not el
        ):
            if value := _text(el):
                self.buffer.append(value)
            return
        for child in el:
            self.walk(child)


def extract_jats(path: Path) -> list[Section]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Cannot parse XML: {exc}") from exc
    if _local(root.tag) != "article":
        raise ExtractionError("UNSUPPORTED_FILE_TYPE", "XML is not a JATS <article>")

    collector = _Collector()
    title = root.find(".//front//article-title")
    if title is not None and _text(title):
        collector.sections.append(Section(text=_text(title), section_title="Title"))
    for abstract in root.findall(".//front//abstract"):
        if abstract.get("abstract-type") in {"graphical", "teaser"}:
            continue
        collector.walk(abstract)
    body = root.find("body")
    if body is not None:
        collector.walk(body)
    collector.flush()
    return collector.sections
