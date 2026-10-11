"""Generate synthetic Office/encrypted-PDF samples into `samples/office/`.

- `demo-imaging-charter.docx`: fictional imaging review charter (heading hierarchy, a table with
  merged cells, tracked insertion + deletion, a header and a footnote that must not be indexed)
- `demo-imaging-schedule.xlsx`: fictional imaging schedule (notice rows above the header, dates,
  formula cached values, one hidden sheet)
- `demo-signed-protocol.pdf`: AES-128 PDF with an owner (permission) password only, like a
  signed copy: it opens without a password

DOCX/XLSX use only the standard library (zip + XML). The PDF needs pymupdf (dev dependency).
Kept out of `samples/documents` so the toy evaluation numbers do not change.

Usage: uv run --project backend python scripts/generate_sample_office.py
"""

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf

OUT = Path(__file__).resolve().parents[1] / "samples" / "office"
_STAMP = (2026, 10, 11, 0, 0, 0)  # fixed so the files are reproducible

_W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
_S_NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
_R_NS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def _zip(path: Path, parts: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in parts.items():
            info = zipfile.ZipInfo(name, date_time=_STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, _DECL + content)


# --- DOCX ----------------------------------------------------------------------------------
def _p(text: str, style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}<w:r><w:t>{escape(text)}</w:t></w:r></w:p>"


def _cell(text: str, span: int = 1, vmerge: str | None = None) -> str:
    props = ""
    if span > 1:
        props += f'<w:gridSpan w:val="{span}"/>'
    if vmerge == "restart":
        props += '<w:vMerge w:val="restart"/>'
    elif vmerge == "continue":
        props += "<w:vMerge/>"
    tcpr = f"<w:tcPr>{props}</w:tcPr>" if props else ""
    return f"<w:tc>{tcpr}{_p(text)}</w:tc>"


def _row(*cells: str) -> str:
    return f"<w:tr>{''.join(cells)}</w:tr>"


def _docx() -> None:
    table = (
        "<w:tbl><w:tblPr/>"
        + _row(_cell("판독 단계"), _cell("판독자"), _cell("기한(영업일)"))
        + _row(_cell("1차 판독", vmerge="restart"), _cell("판독의 A"), _cell("5"))
        + _row(_cell("", vmerge="continue"), _cell("판독의 B"), _cell("5"))
        + _row(_cell("불일치 중재", vmerge="restart"), _cell("중재 판독의 C"), _cell("3"))
        + _row(_cell("최종 확정 (가상 위원회 합의)", span=3))
        + "</w:tbl>"
    )
    changes = (
        "<w:p><w:r><w:t xml:space="
        '"preserve">판독 결과는 </w:t></w:r>'
        '<w:del w:id="1" w:author="demo"><w:r><w:delText>7일</w:delText></w:r></w:del>'
        '<w:ins w:id="2" w:author="demo"><w:r><w:t>5영업일</w:t></w:r></w:ins>'
        '<w:r><w:t xml:space="preserve"> 이내에 전달한다.</w:t></w:r></w:p>'
    )
    body = "".join(
        [
            _p("영상 판독 차터 (가상 샘플)", "Title"),
            _p("1. 목적", "Heading1"),
            _p("이 문서는 데모용 가상 임상시험 DEMO-ONC-01의 독립 영상 판독 절차를 정의한다."),
            _p("2. 판독 절차", "Heading1"),
            _p("2.1 판독자 구성", "Heading2"),
            _p("판독자는 영상의학 전문의 3명으로 구성하며 서로의 판독 결과를 보지 못한다."),
            table,
            _p("2.2 판독 기한", "Heading2"),
            changes,
            _p("3. 불일치 처리", "Heading1"),
            _p("두 판독자의 반응 평가가 다르면 중재 판독자가 최종 결과를 정한다."),
        ]
    )
    styles = "".join(
        f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/></w:style>'
        for sid, name in (
            ("Heading1", "heading 1"),
            ("Heading2", "heading 2"),
            ("Title", "Title"),
        )
    )
    _zip(
        OUT / "demo-imaging-charter.docx",
        {
            "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/></Types>',
            "word/document.xml": f"<w:document {_W_NS}><w:body>{body}</w:body></w:document>",
            "word/styles.xml": f"<w:styles {_W_NS}>{styles}</w:styles>",
            "word/header1.xml": f"<w:hdr {_W_NS}>{_p('HEADER-DO-NOT-INDEX')}</w:hdr>",
            "word/footnotes.xml": (
                f"<w:footnotes {_W_NS}>{_p('FOOTNOTE-DO-NOT-INDEX')}</w:footnotes>"
            ),
        },
    )


# --- XLSX ----------------------------------------------------------------------------------
def _xlsx() -> None:
    strings = [
        "영상 촬영 일정표 (가상 샘플)",
        "문서 작성: 가상 영상 운영팀 / 일정은 방문 기준일에 따른다",
        "방문",
        "기준일",
        "촬영일",
        "검사",
        "Screening",
        "Week 6",
        "Week 12",
        "흉부/복부/골반 CT",
        "구분",
        "비고",
        "보관용 메모",
        "내부 확인 필요",
    ]

    def s(i: int) -> str:
        return f'<c t="s"><v>{i}</v></c>'

    def ref(col: str, row: int, inner: str) -> str:
        return inner.replace("<c ", f'<c r="{col}{row}" ', 1)

    inline_header = '<c t="inlineStr"><is><t>일정 차이(일)</t></is></c>'
    rows = [
        f'<row r="1">{ref("A", 1, s(0))}</row>',
        f'<row r="2">{ref("A", 2, s(1))}</row>',
        '<row r="4">'
        + "".join(ref(c, 4, s(i)) for c, i in zip("ABCD", (2, 3, 4, 5), strict=True))
        + ref("E", 4, inline_header)
        + "</row>",
    ]
    for n, (visit_idx, base, taken) in enumerate(
        [(6, 46300, 46298), (7, 46342, 46344), (8, 46384, 46386)], start=5
    ):
        rows.append(
            f'<row r="{n}">'
            + ref("A", n, s(visit_idx))
            + ref("B", n, f'<c s="1"><v>{base}</v></c>')
            + ref("C", n, f'<c s="1"><v>{taken}</v></c>')
            + ref("D", n, s(9))
            + ref("E", n, f"<c><f>C{n}-B{n}</f><v>{taken - base}</v></c>")
            + "</row>"
        )
    sheet1 = f"<worksheet {_S_NS}><sheetData>{''.join(rows)}</sheetData></worksheet>"
    hidden_rows = (
        f'<row r="1">{ref("A", 1, s(10))}{ref("B", 1, s(11))}</row>'
        f'<row r="2">{ref("A", 2, s(12))}{ref("B", 2, s(13))}</row>'
    )
    sheet2 = f"<worksheet {_S_NS}><sheetData>{hidden_rows}</sheetData></worksheet>"
    sst = f"<sst {_S_NS}>" + "".join(f"<si><t>{escape(t)}</t></si>" for t in strings) + "</sst>"
    styles = (
        f"<styleSheet {_S_NS}>"
        '<cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>'
    )
    workbook = (
        f"<workbook {_S_NS} {_R_NS}><sheets>"
        '<sheet name="촬영 일정" sheetId="1" r:id="rId1"/>'
        '<sheet name="메모" sheetId="2" state="hidden" r:id="rId2"/>'
        "</sheets></workbook>"
    )
    rels = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="worksheet" Target="worksheets/sheet2.xml"/>'
        "</Relationships>"
    )
    _zip(
        OUT / "demo-imaging-schedule.xlsx",
        {
            "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/></Types>',
            "xl/workbook.xml": workbook,
            "xl/_rels/workbook.xml.rels": rels,
            "xl/sharedStrings.xml": sst,
            "xl/styles.xml": styles,
            "xl/worksheets/sheet1.xml": sheet1,
            "xl/worksheets/sheet2.xml": sheet2,
        },
    )


# --- encrypted PDF -------------------------------------------------------------------------
def _pdf() -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    lines = [
        "DEMO-ONC-01 Signed Protocol Copy (Fictional Sample)",
        "",
        "1. Signature",
        "This copy carries a permission password only; it opens without a password.",
        "Principal investigator signature: Demo Investigator (fictional).",
    ]
    for i, line in enumerate(lines):
        page.insert_text((72, 72 + 18 * i), line)
    doc.save(
        OUT / "demo-signed-protocol.pdf",
        encryption=pymupdf.PDF_ENCRYPT_AES_128,
        owner_pw="demo-owner",
        user_pw="",
        permissions=pymupdf.PDF_PERM_PRINT,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _docx()
    _xlsx()
    _pdf()
    for path in sorted(OUT.iterdir()):
        print(f"wrote {path.relative_to(OUT.parents[1])} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
