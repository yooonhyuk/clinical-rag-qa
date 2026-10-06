"""Heading detection, PDF cleanup, JATS XML and HTML table extraction (public corpus formats)."""

from pathlib import Path

import pytest

from app.services.chunker import chunk_sections
from app.services.document_loader import scan_documents
from app.services.headings import SectionPath, detect_heading
from app.services.pdf_extractor import normalize_text, sections_from_pages, strip_running_lines
from app.services.table_rows import rows_to_lines
from app.services.text_extractor import extract

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("line", "level"),
    [
        ("I. INTRODUCTION", 1),
        ("Ⅳ. 탐색임상시험", 1),
        ("APPENDIX A:  BEFORE IMAGING:  CHARTER CONSIDERATIONS", 1),
        ("제3장 임상시험의 실시", 1),
        ("A. Choice of Imaging Modality", 2),
        ("1 Background", 2),
        ("1. 세포독성 물질", 2),
        ("10.4 참조표준의 설정", 3),
        ("4.2.1 Evaluation of toxicity", 4),
        ("1.1.1. 주요 목적", 4),
        ("6.1.2.4 Evaluation of activity", 5),
        ("자. 기록 및 보고", 6),
    ],
)
def test_headings_are_detected_with_levels(line: str, level: int) -> None:
    heading = detect_heading(line, "Next line starts a paragraph.")
    assert heading is not None and heading.level == level


@pytest.mark.parametrize(
    ("line", "next_line"),
    [
        # numbered provision that wraps (ICH E6(R3) 1.5)
        ("1.5 A qualified physician or, when appropriate, a qualified dentist (or other", "qual"),
        ("2.4.2 Before initiating a trial, the investigator/institution should have", None),
        ("3 상 임상시험 이전에 음식-약물 간 상호작용 시험이 수행되어야 한다.", None),
        ("18 November 2023", None),
        ("1 B1-2006-2-001 2006.01 제정", None),
        ("I. INTRODUCTION.......................................... 1", None),
        ("Ⅰ. 서론 · · · · · · · · · · · · · · · · · · 1", None),
        ("차. 모든 임상시험 관련 정보는 정확한 보고, 해석 및 확인이 가능하도록", None),
        ("The purpose of this guidance is to assist sponsors", None),
    ],
)
def test_body_text_is_not_a_heading(line: str, next_line: str | None) -> None:
    assert detect_heading(line, next_line) is None


def test_section_path_pops_same_or_deeper_levels() -> None:
    path = SectionPath()
    for line in ("Ⅴ. 3상 치료적 확증임상시험", "1. 설계", "1.5. 평가변수", "1.6. 완치목적"):
        heading = detect_heading(line)
        assert heading is not None
        path.push(heading)
    assert path.title() == "Ⅴ. 3상 치료적 확증임상시험 > 1. 설계 > 1.6. 완치목적"


def test_running_headers_footers_and_page_numbers_are_removed() -> None:
    pages = [
        ["Contains Nonbinding Recommendations", f"{n}", f"body {'abcdefghi'[n - 1]}", f"Page {n}/9"]
        for n in range(1, 10)
    ]
    cleaned = strip_running_lines(pages)
    assert cleaned[0] == ["body a"]
    assert all(len(lines) == 1 for lines in cleaned)


def test_toc_pages_are_dropped_and_sections_track_pages() -> None:
    toc = "\n".join(
        [
            "목 차",
            "Ⅰ. 서론 · · · · · · · · · · 1",
            "Ⅱ. 약동학 · · · · · · · · 1",
            "Ⅲ. 바이오 · · · · · · · 2",
        ]
    )
    body1 = "Ⅰ. 서론\n서론 본문입니다.\nⅡ. 약동학\n약동학 본문"
    body2 = "약동학 계속되는 본문\nⅢ. 바이오마커\n바이오마커 본문"
    sections = sections_from_pages([toc, body1, body2])
    assert [s.section_title for s in sections] == ["Ⅰ. 서론", "Ⅱ. 약동학", "Ⅲ. 바이오마커"]
    pk = sections[1]
    assert pk.page_number == 2
    assert pk.page_at(pk.text.index("계속")) == 3


def test_korean_jamo_middle_dot_is_normalised() -> None:
    assert normalize_text("사용량ᆞ사용방법") == "사용량·사용방법"
    assert normalize_text("제ㆍ개정") == "제·개정"


def test_table_rows_carry_their_column_names() -> None:
    lines = rows_to_lines(
        [["Attribute Name", "Tag", "Basic Prof.", "Rtn. UIDs Opt."]],
        [
            ["Patient's Name", "(0010,0010)", "Z", ""],
            ["Study Instance UID", "(0020,000D)", "U", "K"],
        ],
    )
    assert lines == [
        "Attribute Name: Patient's Name; Tag: (0010,0010); Basic Prof.: Z",
        "Attribute Name: Study Instance UID; Tag: (0020,000D); Basic Prof.: U; Rtn. UIDs Opt.: K",
    ]


JATS = """<?xml version="1.0"?>
<article><front><article-meta><title-group><article-title>iRECIST demo</article-title>
</title-group><abstract><sec><title>Background</title><p>Short abstract.</p></sec></abstract>
</article-meta></front><body>
<sec><title>Main</title><p>Intro paragraph.</p>
  <sec><title>Follow-up</title><p>iUPD must be confirmed.</p>
    <table-wrap><label>Table 1</label><caption><p>Response categories</p></caption>
      <table><thead><tr><th>Category</th><th>Definition</th></tr></thead>
      <tbody><tr><td>iCPD</td><td>confirmed progression</td></tr></tbody></table>
    </table-wrap></sec></sec>
<sec><title>Competing interests</title><p>None.</p></sec>
</body><back><ref-list><ref>Ref 1</ref></ref-list></back></article>"""


def test_jats_sections_tables_and_back_matter(tmp_path: Path) -> None:
    path = tmp_path / "a.xml"
    path.write_text(JATS, encoding="utf-8")
    sections = extract(path, "xml")
    by_title = {s.section_title: s.text for s in sections}
    assert by_title["Title"] == "iRECIST demo"
    assert by_title["Abstract > Background"] == "Short abstract."
    assert by_title["Main > Follow-up"] == "iUPD must be confirmed."
    table = by_title["Main > Follow-up > Table 1"]
    assert "Table 1 Response categories" in table
    assert "Category: iCPD; Definition: confirmed progression" in table
    assert "None." not in "".join(by_title.values())  # competing interests skipped
    assert all(s.page_number is None for s in sections)


HTML = """<html><head><title>x</title><style>p{}</style></head><body>
<div class="navheader"><table><tr><td>Prev</td><td>Next</td></tr></table></div>
<h1>E Attribute Confidentiality Profiles</h1><p>Annex intro.</p>
<h2>E.1 Application Level Confidentiality Profile</h2>
<h3>Note</h3><p>A note stays in E.1.</p>
<p class="title"><strong>Table E.1-1. Profile Attributes</strong></p>
<table><thead><tr><th>Attribute Name</th><th>Tag</th><th>Basic Prof.</th></tr></thead>
<tbody><tr><td><p>Patient's Name</p></td><td><p>(0010,0010)</p></td><td><p>Z</p></td></tr>
<tr><td>Burned In Annotation</td><td>(0028,0301)</td><td>C</td></tr></tbody></table>
</body></html>"""


def test_html_headings_and_table_rows(tmp_path: Path) -> None:
    path = tmp_path / "a.html"
    path.write_text(HTML, encoding="utf-8")
    sections = extract(path, "html")
    by_title = {s.section_title: s.text for s in sections}
    e1 = "E Attribute Confidentiality Profiles > E.1 Application Level Confidentiality Profile"
    assert "A note stays in E.1." in by_title[e1]
    table = by_title[f"{e1} > Table E.1-1. Profile Attributes"]
    assert "Attribute Name: Patient's Name; Tag: (0010,0010); Basic Prof.: Z" in table
    assert "Prev" not in "".join(by_title.values())  # navigation skipped


def test_scanner_knows_xml_and_html(tmp_path: Path) -> None:
    (tmp_path / "a.xml").write_text(JATS, encoding="utf-8")
    (tmp_path / "b.html").write_text(HTML, encoding="utf-8")
    types = {f.file_name: (f.file_type, f.supported) for f in scan_documents(tmp_path)}
    assert types == {"a.xml": ("xml", True), "b.html": ("html", True)}


@pytest.mark.parametrize(
    ("name", "expected_title", "needle"),
    [
        ("11_dicom_ps3.15_annexE_2026d.html", "Table E.1-1.", "Tag: (0010,0010)"),
        ("07_irecist_how_to_2020.xml", "Responses to therapy", "iCPD"),
        ("04_mfds_anticancer_guideline_ko.pdf", "1.1.1. 주요 목적", "최대내약용량"),
        ("01_fda_imaging_endpoint_2018.pdf", "C. Should Image Interpretation Be Blinded", "blind"),
    ],
)
def test_public_corpus_documents_extract_with_sections(
    name: str, expected_title: str, needle: str
) -> None:
    path = ROOT / "corpus" / "public" / name
    file_type = next(f.file_type for f in scan_documents(path.parent) if f.file_name == name)
    sections = extract(path, file_type)
    matching = [s for s in sections if expected_title in (s.section_title or "")]
    assert matching and any(needle in s.text for s in matching)
    chunks = chunk_sections(sections)
    assert all(c.text.strip() for c in chunks)
    if file_type == "pdf":
        assert all(c.page_number is not None for c in chunks)
        assert not any("Contains Nonbinding Recommendations" in c.text for c in chunks)
