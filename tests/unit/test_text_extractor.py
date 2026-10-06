from pathlib import Path

import pymupdf
import pytest

from app.services.chunker import chunk_sections
from app.services.text_extractor import ExtractionError, extract, extract_markdown


def _multiline_pdf(path: Path, pages: list[list[str]]) -> Path:
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page()
        for i, line in enumerate(lines):
            page.insert_text((72, 72 + 18 * i), line)
    doc.save(path)
    return path


def _pdf(path: Path, pages: list[str], **save_kwargs: object) -> Path:
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text, fontname="korea")
    doc.save(path, **save_kwargs)
    return path


def test_markdown_sections_use_headings_as_titles() -> None:
    md = "# Guide\nintro\n\n## Upload Validation\n1. 파일 형식\n2. 필수 태그\n\n## Empty\n"
    sections = extract_markdown(md)
    assert [s.section_title for s in sections] == ["Guide", "Upload Validation"]
    assert "필수 태그" in sections[1].text


def test_markdown_heading_inside_code_fence_is_not_a_section() -> None:
    md = "## Real\ntext\n```\n# not a heading\n```\n"
    sections = extract_markdown(md)
    assert len(sections) == 1
    assert "# not a heading" in sections[0].text


def test_txt_and_cp949(tmp_path: Path) -> None:
    utf8 = tmp_path / "a.txt"
    utf8.write_text("업로드 가이드", encoding="utf-8")
    cp949 = tmp_path / "b.txt"
    cp949.write_bytes("헬프데스크 운영 시간".encode("cp949"))
    assert extract(utf8, "txt")[0].text == "업로드 가이드"
    assert extract(cp949, "txt")[0].text == "헬프데스크 운영 시간"


def test_pdf_pages_keep_page_numbers(tmp_path: Path) -> None:
    path = _pdf(tmp_path / "p.pdf", ["첫 페이지", "", "셋째 페이지 SliceThickness"])
    sections = extract(path, "pdf")
    assert len(sections) == 1  # no headings: one section that spans pages 1 and 3
    section = sections[0]
    assert section.page_number == 1
    offset = section.text.index("셋째")
    assert section.page_at(0) == 1 and section.page_at(offset) == 3  # blank page skipped
    chunks = chunk_sections(sections, size=100, overlap=10)
    assert chunks[0].page_number == 1


def test_pdf_korean_cid_font_is_decoded(tmp_path: Path) -> None:
    """pymupdf's non-embedded "korea" font writes UniKS-UTF16-H; pypdf needs our CMap patch."""
    path = _pdf(tmp_path / "k.pdf", ["한국어 본문 텍스트"])
    assert "한국어 본문 텍스트" in extract(path, "pdf")[0].text


def test_pdf_headings_split_sections_and_chunks_cite_their_page(tmp_path: Path) -> None:
    path = _multiline_pdf(
        tmp_path / "h.pdf",
        [
            ["Guideline Header", "1 Background", "Intro text on page one."],
            ["Guideline Header", "4.2 Evaluation of activity", "ORR should be documented."],
            ["Guideline Header", "4.2.1 Sub point", "Detail text."],
        ],
    )
    sections = extract(path, "pdf")
    titles = [s.section_title for s in sections]
    assert titles == [
        "1 Background",
        "1 Background > 4.2 Evaluation of activity",
        "1 Background > 4.2 Evaluation of activity > 4.2.1 Sub point",
    ]
    assert [s.page_number for s in sections] == [1, 2, 3]
    # the running header repeats on every page and is removed
    assert all("Guideline Header" not in s.text for s in sections)


def test_pdf_without_text_layer_fails(tmp_path: Path) -> None:
    path = _pdf(tmp_path / "scan.pdf", [""])
    with pytest.raises(ExtractionError) as err:
        extract(path, "pdf")
    assert err.value.error_type == "NO_EXTRACTABLE_TEXT"


def test_encrypted_pdf_fails(tmp_path: Path) -> None:
    path = _pdf(
        tmp_path / "enc.pdf",
        ["secret"],
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw="pw",
        owner_pw="owner",
    )
    with pytest.raises(ExtractionError) as err:
        extract(path, "pdf")
    assert err.value.error_type == "ENCRYPTED_PDF"


def test_corrupted_pdf_fails(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a pdf at all")
    with pytest.raises(ExtractionError) as err:
        extract(path, "pdf")
    assert err.value.error_type == "CORRUPTED_FILE"


def test_empty_markdown_fails(tmp_path: Path) -> None:
    path = tmp_path / "empty.md"
    path.write_text("   \n", encoding="utf-8")
    with pytest.raises(ExtractionError) as err:
        extract(path, "md")
    assert err.value.error_type == "EMPTY_DOCUMENT"


def test_unsupported_type(tmp_path: Path) -> None:
    path = tmp_path / "x.docx"
    path.write_bytes(b"PK")
    with pytest.raises(ExtractionError) as err:
        extract(path, "docx")
    assert err.value.error_type == "UNSUPPORTED_FILE_TYPE"
