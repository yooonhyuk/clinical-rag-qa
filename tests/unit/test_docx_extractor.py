import zipfile
from pathlib import Path

import pytest

from app.services.docx_extractor import MAX_MEMBER_BYTES
from app.services.text_extractor import ExtractionError, extract

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _docx(path: Path, body: str, styles: str = "", extra: dict[str, str] | None = None) -> Path:
    parts = {
        "word/document.xml": f"<w:document {W}><w:body>{body}</w:body></w:document>",
        "word/styles.xml": f"<w:styles {W}>{styles}</w:styles>",
        **(extra or {}),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in parts.items():
            z.writestr(name, content)
    return path


def _p(text: str, style: str | None = None, outline: int | None = None) -> str:
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if outline is not None:
        ppr += f'<w:outlineLvl w:val="{outline}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>"


def _style(sid: str, name: str) -> str:
    return f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/></w:style>'


def _tc(text: str, span: int = 1, vmerge: str | None = None) -> str:
    props = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
    if vmerge == "restart":
        props += '<w:vMerge w:val="restart"/>'
    elif vmerge == "continue":
        props += "<w:vMerge/>"
    return f"<w:tc><w:tcPr>{props}</w:tcPr><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"


def _tr(*cells: str) -> str:
    return f"<w:tr>{''.join(cells)}</w:tr>"


def test_heading_path_from_styles_english_korean_and_outline(tmp_path: Path) -> None:
    styles = _style("H1", "heading 1") + _style("KO2", "제목 2")
    body = (
        _p("개요", "H1")
        + _p("본문 하나")
        + _p("세부", "KO2")
        + _p("본문 둘")
        + _p("개요 외", outline=0)
        + _p("본문 셋")
    )
    sections = extract(_docx(tmp_path / "a.docx", body, styles), "docx")
    assert [(s.section_title, s.text, s.page_number) for s in sections] == [
        ("개요", "본문 하나", None),
        ("개요 > 세부", "본문 둘", None),
        ("개요 외", "본문 셋", None),
    ]


def test_table_rows_merged_cells_and_header_rule(tmp_path: Path) -> None:
    table = (
        "<w:tbl>"
        + _tr(_tc("단계"), _tc("판독자"), _tc("기한"))
        + _tr(_tc("1차", vmerge="restart"), _tc("A"), _tc("5"))
        + _tr(_tc("", vmerge="continue"), _tc("B"), _tc("5"))
        + _tr(_tc("확정", span=3))
        + "</w:tbl>"
    )
    text = extract(_docx(tmp_path / "t.docx", table), "docx")[0].text
    assert text.splitlines() == [
        "단계: 1차; 판독자: A; 기한: 5",
        "판독자: B; 기한: 5",
        "단계: 확정",
    ]
    # first row with an empty cell is not a header: plain "a | b" lines
    no_header = "<w:tbl>" + _tr(_tc("x"), _tc("")) + _tr(_tc("1"), _tc("2")) + "</w:tbl>"
    assert extract(_docx(tmp_path / "n.docx", no_header), "docx")[0].text == "x\n1 | 2"


def test_one_row_table_keeps_its_text(tmp_path: Path) -> None:
    # a boxed note or title block: the only row must not be consumed as a header of nothing
    boxed = "<w:tbl>" + _tr(_tc("주의"), _tc("판독 전 영상 품질 확인")) + "</w:tbl>"
    body = _p("앞 문단") + boxed + _p("뒤 문단")
    text = extract(_docx(tmp_path / "b.docx", body), "docx")[0].text
    assert text.splitlines() == ["앞 문단", "주의 | 판독 전 영상 품질 확인", "뒤 문단"]


def test_tracked_changes_keep_insertions_drop_deletions_and_skip_notes(tmp_path: Path) -> None:
    body = (
        "<w:p><w:r><w:t>결과는 </w:t></w:r>"
        '<w:del w:id="1"><w:r><w:delText>7일</w:delText></w:r></w:del>'
        '<w:ins w:id="2"><w:r><w:t>5일</w:t></w:r></w:ins>'
        "<w:r><w:t> 이내.</w:t></w:r></w:p>"
    )
    extra = {
        "word/header1.xml": f"<w:hdr {W}><w:p><w:r><w:t>HEADER</w:t></w:r></w:p></w:hdr>",
        "word/footnotes.xml": (
            f"<w:footnotes {W}><w:p><w:r><w:t>NOTE</w:t></w:r></w:p></w:footnotes>"
        ),
    }
    text = extract(_docx(tmp_path / "c.docx", body, extra=extra), "docx")[0].text
    assert text == "결과는 5일 이내."


def test_corrupted_docx_errors(tmp_path: Path) -> None:
    bad_zip = tmp_path / "z.docx"
    bad_zip.write_bytes(b"PK\x03\x04 not a zip")
    bad_xml = tmp_path / "x.docx"
    with zipfile.ZipFile(bad_xml, "w") as z:
        z.writestr("word/document.xml", "<w:document")
    no_part = tmp_path / "m.docx"
    with zipfile.ZipFile(no_part, "w") as z:
        z.writestr("other.xml", "<a/>")
    for path in (bad_zip, bad_xml, no_part):
        with pytest.raises(ExtractionError) as err:
            extract(path, "docx")
        assert err.value.error_type == "CORRUPTED_FILE"


def test_password_protected_docx_is_encrypted_file(tmp_path: Path) -> None:
    path = tmp_path / "enc.docx"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64)
    with pytest.raises(ExtractionError) as err:
        extract(path, "docx")
    assert err.value.error_type == "ENCRYPTED_FILE"


def test_entities_and_oversized_parts_are_rejected(tmp_path: Path) -> None:
    bomb = (
        '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;">]>'
        f"<w:document {W}><w:body><w:p><w:r><w:t>&b;</w:t></w:r></w:p></w:body></w:document>"
    )
    path = tmp_path / "bomb.docx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", bomb)
    with pytest.raises(ExtractionError) as err:
        extract(path, "docx")
    assert err.value.error_type == "CORRUPTED_FILE"

    big = tmp_path / "big.docx"
    with zipfile.ZipFile(big, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", b"0" * (MAX_MEMBER_BYTES + 1))
    with pytest.raises(ExtractionError) as err:
        extract(big, "docx")
    assert err.value.error_type == "CORRUPTED_FILE"


def test_empty_docx_fails(tmp_path: Path) -> None:
    with pytest.raises(ExtractionError) as err:
        extract(_docx(tmp_path / "e.docx", ""), "docx")
    assert err.value.error_type == "EMPTY_DOCUMENT"


def test_utf16_doctype_entity_is_rejected(tmp_path: Path) -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE d [<!ENTITY a "PWN">]>'
        f"<w:document {W}><w:body><w:p><w:r><w:t>&a;</w:t></w:r></w:p></w:body></w:document>"
    )
    path = tmp_path / "u16.docx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml.encode("utf-16"))
    with pytest.raises(ExtractionError) as err:
        extract(path, "docx")
    assert err.value.error_type == "CORRUPTED_FILE"
    assert "DTD" in str(err.value)


def test_total_decompressed_bytes_are_capped(tmp_path: Path, monkeypatch) -> None:
    from app.services import docx_extractor
    from app.services.docx_extractor import open_ooxml, read_member

    path = _docx(tmp_path / "t.docx", _p("x" * 500), extra={"word/pad.xml": "<a>" + "y" * 500})
    with open_ooxml(path, "DOCX") as archive:
        read_member(archive, "word/document.xml")
        # the budget left is smaller than the next part really is
        monkeypatch.setattr(docx_extractor, "MAX_TOTAL_BYTES", archive.bytes_read + 100)
        with pytest.raises(ExtractionError) as err:
            read_member(archive, "word/pad.xml")
        assert err.value.error_type == "CORRUPTED_FILE"


def test_part_is_read_once_and_counted(tmp_path: Path) -> None:
    from app.services.docx_extractor import open_ooxml, read_member

    path = _docx(tmp_path / "o.docx", _p("x"))
    with open_ooxml(path, "DOCX") as archive:
        first = read_member(archive, "word/document.xml")
        counted = archive.bytes_read
        assert read_member(archive, "word/document.xml") is first
        assert archive.bytes_read == counted == len(first or b"")


def test_style_inheritance_and_grid_before_after(tmp_path: Path) -> None:
    styles = (
        _style("H1", "heading 1")
        + '<w:style w:type="paragraph" w:styleId="Mine"><w:name w:val="My Title"/>'
        '<w:basedOn w:val="Mid"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Mid"><w:name w:val="Mid"/>'
        '<w:basedOn w:val="H1"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Loop"><w:basedOn w:val="Loop"/></w:style>'
    )
    table = (
        "<w:tbl>"
        + _tr(_tc("단계"), _tc("판독자"), _tc("기한"))
        + '<w:tr><w:trPr><w:gridBefore w:val="1"/></w:trPr>'
        + _tc("A")
        + _tc("5")
        + "</w:tr>"
        + '<w:tr><w:trPr><w:gridAfter w:val="1"/></w:trPr>'
        + _tc("1차")
        + _tc("B")
        + "</w:tr>"
        + "</w:tbl>"
    )
    body = _p("사용자 제목", "Mine") + _p("본문", "Loop") + table
    sections = extract(_docx(tmp_path / "s.docx", body, styles), "docx")
    assert sections[0].section_title == "사용자 제목"
    assert sections[0].text.splitlines() == [
        "본문",
        "판독자: A; 기한: 5",
        "단계: 1차; 판독자: B",
    ]


def test_ole_docx_message_mentions_legacy(tmp_path: Path) -> None:
    path = tmp_path / "old.docx"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64)
    with pytest.raises(ExtractionError) as err:
        extract(path, "docx")
    assert err.value.error_type == "ENCRYPTED_FILE"
    assert "구형(doc/xls)" in str(err.value)


def _cap_text(monkeypatch: pytest.MonkeyPatch, cap: int) -> None:
    """Fix the shared text budget at `cap` bytes (no share of the decompressed bytes)."""
    from app.services import docx_extractor

    monkeypatch.setattr(docx_extractor, "MIN_TEXT_BYTES", cap)
    monkeypatch.setattr(docx_extractor, "TEXT_RATIO", 0)


def _extract_traced(path: Path) -> tuple[list | ExtractionError, int]:
    import tracemalloc

    tracemalloc.start()
    try:
        try:
            result: list | ExtractionError = extract(path, "docx")
        except ExtractionError as exc:
            result = exc
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, peak


def _assert_corrupted(result: object, message: str) -> None:
    assert isinstance(result, ExtractionError), result
    assert result.error_type == "CORRUPTED_FILE"
    assert message in str(result)


def test_long_header_repeated_on_many_rows_is_cut(tmp_path: Path, monkeypatch) -> None:
    cap = 8 * 1024 * 1024
    _cap_text(monkeypatch, cap)
    big = "word " * 20_000  # 100 KB per header cell, repeated on every body line
    rows = _tr(*(_tc(big) for _ in range(4))) + _tr(*(_tc("v") for _ in range(4))) * 1_500
    path = _docx(tmp_path / "hdr.docx", f"<w:tbl>{rows}</w:tbl>")  # 600 MB if fully rendered
    result, peak = _extract_traced(path)
    _assert_corrupted(result, "text is too large")
    assert peak < cap * 4


def test_paragraph_text_is_capped(tmp_path: Path, monkeypatch) -> None:
    _cap_text(monkeypatch, 1_000)
    path = _docx(tmp_path / "p.docx", _p("x" * 400) * 3)
    _assert_corrupted(_extract_traced(path)[0], "text is too large")


def test_nested_paragraphs_in_a_cell_are_read_once(tmp_path: Path, monkeypatch) -> None:
    cap = 8 * 1024 * 1024
    _cap_text(monkeypatch, cap)
    big = "word " * 40_000  # 200 KB at the bottom of 90 nested paragraphs (was copied 90 times)
    nested = "<w:p>" * 90 + f"<w:r><w:t>{big}</w:t></w:r>" + "</w:p>" * 90
    cell = f"<w:tc>{nested}</w:tc>"
    table = "<w:tbl>" + _tr(_tc("a"), _tc("")) + _tr(cell, _tc("b")) + "</w:tbl>"
    result, peak = _extract_traced(_docx(tmp_path / "n.docx", table))
    assert isinstance(result, list), result
    assert result[0].text.count("word") == 40_000
    assert peak < cap * 4


def test_nested_table_and_text_box_text_is_not_duplicated(tmp_path: Path) -> None:
    box = (
        "<w:p><w:r><w:t>바깥</w:t></w:r><w:r><w:pict><w:txbxContent>"
        "<w:p><w:r><w:t>상자</w:t></w:r></w:p></w:txbxContent></w:pict></w:r></w:p>"
    )
    inner = "<w:tbl>" + _tr(_tc("x"), _tc("y")) + _tr(_tc("z"), _tc("")) + "</w:tbl>"
    outer_cell = f"<w:tc><w:p><w:r><w:t>앞</w:t></w:r></w:p>{inner}{box}</w:tc>"
    table = "<w:tbl>" + _tr(_tc("항목"), _tc("내용")) + _tr(_tc("1"), outer_cell) + "</w:tbl>"
    sections = extract(_docx(tmp_path / "nt.docx", box + table), "docx")
    assert sections[0].text.splitlines() == ["바깥상자", "항목: 1; 내용: 앞 x y z 바깥상자"]


def test_deep_nesting_is_corrupted_not_recursion_error(tmp_path: Path) -> None:
    deep_sdt = "<w:sdt><w:sdtContent>" * 2_000 + _p("x") + "</w:sdtContent></w:sdt>" * 2_000
    deep_run = "<w:p>" + "<w:r>" * 2_000 + "<w:t>x</w:t>" + "</w:r>" * 2_000 + "</w:p>"
    deep_cell = "<w:tbl><w:tr><w:tc>" * 300 + _p("x") + "</w:tc></w:tr></w:tbl>" * 300
    run_in_cell = "<w:tbl>" + _tr(f"<w:tc>{deep_run}</w:tc>") + "</w:tbl>"
    for i, body in enumerate((deep_sdt, deep_run, run_in_cell, deep_cell)):
        _assert_corrupted(_extract_traced(_docx(tmp_path / f"d{i}.docx", body))[0], "nesting")


def test_row_wider_than_grid_cap_is_corrupted(tmp_path: Path) -> None:
    wide = _tr(*(_tc("v", span=200) for _ in range(6)))  # 1,200 grid columns
    grid_before = '<w:tr><w:trPr><w:gridBefore w:val="200"/></w:trPr>'
    before = grid_before + _tc("v", span=200) * 5 + "</w:tr>"
    for i, row in enumerate((wide, before)):
        result, peak = _extract_traced(_docx(tmp_path / f"w{i}.docx", f"<w:tbl>{row * 50}</w:tbl>"))
        _assert_corrupted(result, "wider than")
        assert peak < 4 * 1024 * 1024
    ok = _tr(*(_tc("v", span=200) for _ in range(5)))  # 1,000 columns is still accepted
    sections = extract(_docx(tmp_path / "ok.docx", f"<w:tbl>{ok}</w:tbl>"), "docx")
    assert sections[0].text == "v | v | v | v | v"


def test_highly_compressed_document_part_is_refused_before_parsing(tmp_path: Path) -> None:
    cell = "<w:tc><w:tcPr><w:vMerge/></w:tcPr></w:tc>"
    body = "<w:tbl>" + _tr(*([cell] * 50_000)) + "</w:tbl>"  # 2 MB of XML, deflates ~500x
    result, peak = _extract_traced(_docx(tmp_path / "r.docx", body))
    _assert_corrupted(result, "compressed")
    assert peak < 4 * 2 * 1024 * 1024


def test_long_and_circular_based_on_chains_are_linear(tmp_path: Path) -> None:
    import time

    n = 20_000

    def based(sid: str, parent: str) -> str:
        return (
            f'<w:style w:type="paragraph" w:styleId="{sid}"><w:basedOn w:val="{parent}"/></w:style>'
        )

    chain = "".join(based(f"s{i}", f"s{i + 1}") for i in range(n)) + _style(f"s{n}", "heading 1")
    cycle = "".join(based(f"c{i}", f"c{(i + 1) % n}") for i in range(n))
    body = _p("제목", "s0") + _p("본문", f"c{n // 2}")
    started = time.monotonic()
    sections = extract(_docx(tmp_path / "chain.docx", body, chain + cycle), "docx")
    assert time.monotonic() - started < 1
    assert [(s.section_title, s.text) for s in sections] == [("제목", "본문")]


def test_realistic_300_page_document_passes_the_caps(tmp_path: Path) -> None:
    """300 page-like blocks (heading, 8 paragraphs, 5 x 21 table) with varied words, i.e. the
    compression real documents have, stay under the part ratio and text caps."""
    import random
    import time

    rng = random.Random(11)
    words = [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(2, 10)))
        for _ in range(3_000)
    ] + ["임상시험", "대상자", "투약", "방문", "이상반응", "평가", "기준", "판독"]

    def sentence(k: int) -> str:
        return " ".join(rng.choices(words, k=k))

    styles = _style("H1", "heading 1")
    blocks = []
    for page in range(300):
        rows = _tr(*(_tc(f"열{c}") for c in range(5)))
        for _ in range(20):
            rows += _tr(*(_tc(sentence(rng.randint(1, 4))) for _ in range(5)))
        blocks.append(
            _p(f"{page + 1}. {sentence(3)}", "H1")
            + "".join(_p(sentence(rng.randint(20, 60))) for _ in range(8))
            + f"<w:tbl>{rows}</w:tbl>"
        )
    path = _docx(tmp_path / "long.docx", "".join(blocks), styles)
    started = time.monotonic()
    sections = extract(path, "docx")
    assert time.monotonic() - started < 10
    assert len(sections) == 300
    assert all(len(s.text.splitlines()) == 28 for s in sections)
    assert sections[0].text.splitlines()[-1].startswith("열0: ")
