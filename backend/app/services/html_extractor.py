"""HTML extraction with the standard library (`html.parser`), tuned for DocBook-generated
standards pages such as DICOM PS3.15 Annex E (chtml) but generic otherwise.

- `<h1>`..`<h6>` build the section path ("E.1 Application Level ... > E.1.1 De-identifier");
  "Note" sub-headings stay part of their parent section
- navigation headers/footers, `<head>`, `<script>`, `<style>` are skipped
- every `<table>` becomes its own section titled by its caption ("Table E.1-1. ..."); each row
  is one line "Attribute Name: Patient's Name; Tag: (0010,0010); Basic Prof.: Z; ...", so a
  lookup question ("what does the Basic Profile do with tag X?") retrieves one row with both
  the tag and its action. Single-row layout tables (release banners) are dropped.

HTML has no pages; the section path / table caption is the citation.
"""

from html.parser import HTMLParser
from pathlib import Path

from app.services.document_types import ExtractionError, Section
from app.services.pdf_extractor import normalize_text
from app.services.table_rows import rows_to_lines

_BLOCK = {"p", "div", "li", "dt", "dd", "br", "pre", "blockquote", "tr", "section"}
_SKIP = {"head", "script", "style", "noscript"}
_NAV_CLASSES = {"navheader", "navfooter"}
_NOTE_TITLES = {"note", "notes"}


class _Table:
    def __init__(self, caption: str) -> None:
        self.caption = caption
        self.header: list[list[str]] = []
        self.body: list[list[str]] = []
        self.row: list[str] | None = None
        self.row_all_th = True
        self.cell: list[str] | None = None
        self.colspan = 1
        self.in_head = False


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: list[Section] = []
        self.path: list[tuple[int, str]] = []
        self.buffer: list[str] = []
        self.line: list[str] = []
        self.skip_depth = 0
        self.div_stack: list[bool] = []  # True for divs that start a skipped region
        self.heading: tuple[int, list[str]] | None = None
        self.tables: list[_Table] = []
        self.caption_capture: list[str] | None = None
        self.pending_caption = ""

    # --- helpers -------------------------------------------------------------------------
    def _title(self) -> str | None:
        return " > ".join(t for _, t in self.path[-3:]) if self.path else None

    def _end_line(self) -> None:
        text = " ".join("".join(self.line).split())
        if text:
            self.buffer.append(text)
        self.line.clear()

    def _flush(self) -> None:
        self._end_line()
        text = "\n".join(self.buffer).strip()
        if text:
            self.sections.append(Section(text=normalize_text(text), section_title=self._title()))
        self.buffer.clear()

    # --- parser callbacks ----------------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "div":
            nav = bool(set((attr.get("class") or "").split()) & _NAV_CLASSES)
            self.div_stack.append(nav)
            if nav:
                self.skip_depth += 1
        if tag in _SKIP:
            self.skip_depth += 1
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._end_line()
            self.heading = (int(tag[1]), [])
        elif tag == "p" and "title" in (attr.get("class") or "").split():
            self.caption_capture = []
        elif tag == "table":
            self._flush()
            self.tables.append(_Table(self.pending_caption))
            self.pending_caption = ""
        elif self.tables:
            table = self.tables[-1]
            if tag == "thead":
                table.in_head = True
            elif tag in {"tbody", "tfoot"}:
                table.in_head = False
            elif tag == "tr":
                table.row = []
                table.row_all_th = True
            elif tag in {"td", "th"} and table.row is not None:
                table.cell = []
                table.row_all_th = table.row_all_th and tag == "th"
                table.colspan = max(1, int(attr.get("colspan") or 1))
            elif tag in _BLOCK and table.cell is not None:
                table.cell.append(" ")
        elif tag in _BLOCK:
            self._end_line()

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.div_stack:
            if self.div_stack.pop():
                self.skip_depth -= 1
            return
        if tag in _SKIP:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if self.heading and tag == f"h{self.heading[0]}":
            level, parts = self.heading
            self.heading = None
            text = " ".join("".join(parts).split())
            if text and text.lower() not in _NOTE_TITLES:
                self._flush()
                while self.path and self.path[-1][0] >= level:
                    self.path.pop()
                self.path.append((level, normalize_text(text)))
            elif text:
                self.buffer.append(text)
            return
        if tag == "p" and self.caption_capture is not None:
            caption = " ".join("".join(self.caption_capture).split())
            self.caption_capture = None
            if caption.lower().startswith("table"):
                self.pending_caption = caption
            elif caption:
                self.line.append(caption)
                self._end_line()
            return
        if self.tables:
            table = self.tables[-1]
            if tag in {"td", "th"} and table.cell is not None and table.row is not None:
                table.row.extend([" ".join("".join(table.cell).split())] * table.colspan)
                table.cell = None
            elif tag == "tr" and table.row is not None:
                # <thead> rows, or leading rows made only of <th> cells, are the header
                leading_th = table.row_all_th and not table.body
                (table.header if table.in_head or leading_th else table.body).append(table.row)
                table.row = None
            elif tag == "table":
                self._end_table(self.tables.pop())
            return
        if tag in _BLOCK:
            self._end_line()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.heading is not None:
            self.heading[1].append(data)
        elif self.caption_capture is not None:
            self.caption_capture.append(data)
        elif self.tables and self.tables[-1].cell is not None:
            self.tables[-1].cell.append(data)
        elif not self.tables:
            self.line.append(data)

    def _end_table(self, table: _Table) -> None:
        if len(table.header) + len(table.body) < 2:
            return  # layout table (release banner, navigation)
        lines = rows_to_lines(table.header, table.body)
        if not lines:
            return
        caption = table.caption or "Table"
        parent = " > ".join(t for _, t in self.path[-2:])
        title = f"{parent} > {caption}" if parent else caption
        text = normalize_text("\n".join([caption, *lines]))
        self.sections.append(Section(text=text, section_title=title))

    def close(self) -> None:
        super().close()
        self._flush()


def extract_html(path: Path) -> list[Section]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Cannot read HTML: {exc}") from exc
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ExtractionError("CORRUPTED_FILE", "HTML is not UTF-8") from exc
    parser = _Parser()
    parser.feed(content)
    parser.close()
    return parser.sections
