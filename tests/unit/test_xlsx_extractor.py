import zipfile
from pathlib import Path

import pytest

from app.services.text_extractor import ExtractionError, extract
from app.services.xlsx_extractor import _is_date_format, extract_xlsx_with_diagnostics

NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
RNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def _xlsx(
    path: Path,
    sheets: list[tuple[str, str, str]],
    shared: list[str] | None = None,
    styles: str = '<cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs>',
) -> Path:
    """sheets: (name, state, sheetData xml)."""
    wb = "".join(
        f'<sheet name="{n}" sheetId="{i}" state="{st}" r:id="rId{i}"/>'
        for i, (n, st, _) in enumerate(sheets, start=1)
    )
    rels = "".join(
        f'<Relationship Id="rId{i}" Target="worksheets/s{i}.xml"/>'
        for i in range(1, len(sheets) + 1)
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", f"<workbook {NS} {RNS}><sheets>{wb}</sheets></workbook>")
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>',
        )
        z.writestr("xl/styles.xml", f"<styleSheet {NS}>{styles}</styleSheet>")
        z.writestr(
            "xl/sharedStrings.xml",
            f"<sst {NS}>" + "".join(f"<si><t>{t}</t></si>" for t in shared or []) + "</sst>",
        )
        for i, (_, _, data) in enumerate(sheets, start=1):
            z.writestr(
                f"xl/worksheets/s{i}.xml",
                f"<worksheet {NS}><sheetData>{data}</sheetData></worksheet>",
            )
    return path


def _row(n: int, *cells: str) -> str:
    return f'<row r="{n}">' + "".join(cells) + "</row>"


def _s(ref: str, idx: int) -> str:
    return f'<c r="{ref}" t="s"><v>{idx}</v></c>'


def test_sheet_sections_header_detection_and_dates(tmp_path: Path) -> None:
    shared = ["일정표", "안내문", "방문", "날짜", "검사", "비고", "V1", "CT", "RULE"]
    data = (
        _row(1, _s("A1", 0))
        + _row(2, _s("A2", 1), _s("B2", 1))  # < 4 cells: still above the header
        + _row(4, _s("A4", 2), _s("B4", 3), _s("C4", 4), _s("D4", 5))
        + _row(
            5,
            _s("A5", 6),
            '<c r="B5" s="1"><v>46300</v></c>',
            _s("C5", 7),
            '<c r="D5"><f>1+2</f><v>3</v></c>',
        )
    )
    other = _row(1, _s("A1", 8), _s("B1", 8))
    path = _xlsx(
        tmp_path / "a.xlsx", [("일정", "visible", data), ("규칙", "visible", other)], shared
    )
    sections = extract(path, "xlsx")
    assert [s.section_title for s in sections] == ["일정", "규칙"]
    lines = sections[0].text.splitlines()
    assert lines[0] == "일정표"
    assert lines[1] == "안내문 | 안내문"
    assert lines[2] == "[일정] 방문: V1; 날짜: 2026-10-05; 검사: CT; 비고: 3"
    assert sections[1].text == "[규칙] RULE | RULE"
    assert all(s.page_number is None for s in sections)


def test_date_format_detection() -> None:
    assert _is_date_format("yyyy-mm-dd")
    assert _is_date_format("[$-412]yyyy\\-mm\\-dd")
    assert not _is_date_format('0.00" days"')
    assert not _is_date_format("#,##0.00")
    assert not _is_date_format("[Red]0.0")


def test_custom_date_numfmt_and_datetime(tmp_path: Path) -> None:
    styles = (
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy/mm/dd hh:mm"/></numFmts>'
        '<cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="164"/></cellXfs>'
    )
    data = _row(
        1,
        '<c r="A1" t="inlineStr"><is><t>a</t></is></c>',
        '<c r="B1" t="inlineStr"><is><t>b</t></is></c>',
        '<c r="C1" t="inlineStr"><is><t>c</t></is></c>',
        '<c r="D1" t="inlineStr"><is><t>d</t></is></c>',
    ) + _row(2, '<c r="A2" s="1"><v>46300.5</v></c>', '<c r="D2"><v>2.5</v></c>')
    text = extract(_xlsx(tmp_path / "d.xlsx", [("S", "visible", data)], styles=styles), "xlsx")[
        0
    ].text
    assert text == "[S] a: 2026-10-05 12:00; d: 2.5"


def test_hidden_sheet_is_indexed_and_reported(tmp_path: Path) -> None:
    data = _row(1, '<c r="A1" t="inlineStr"><is><t>secret</t></is></c>')
    path = _xlsx(tmp_path / "h.xlsx", [("보임", "visible", data), ("숨김", "hidden", data)])
    sections, diagnostics = extract_xlsx_with_diagnostics(path)
    assert [s.section_title for s in sections] == ["보임", "숨김"]
    assert diagnostics == ["sheet '숨김': hidden"]


def test_corrupted_and_encrypted_xlsx_errors(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"PK\x03\x04 broken")
    with pytest.raises(ExtractionError) as err:
        extract(bad, "xlsx")
    assert err.value.error_type == "CORRUPTED_FILE"
    enc = tmp_path / "enc.xlsx"
    enc.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64)
    with pytest.raises(ExtractionError) as err:
        extract(enc, "xlsx")
    assert err.value.error_type == "ENCRYPTED_FILE"


def test_empty_workbook_fails(tmp_path: Path) -> None:
    with pytest.raises(ExtractionError) as err:
        extract(_xlsx(tmp_path / "e.xlsx", [("S", "visible", "")]), "xlsx")
    assert err.value.error_type == "EMPTY_DOCUMENT"


def test_far_column_cell_does_not_blow_up_memory(tmp_path: Path) -> None:
    import time
    import tracemalloc

    rows = [_row(1, *(f'<c r="{c}1" t="inlineStr"><is><t>h{c}</t></is></c>' for c in "ABCD"))]
    rows += [_row(n, f'<c r="A{n}" t="inlineStr"><is><t>v{n}</t></is></c>') for n in range(2, 3001)]
    rows.append(_row(3001, '<c r="XFD3001" t="inlineStr"><is><t>far</t></is></c>'))
    path = _xlsx(tmp_path / "far.xlsx", [("S", "visible", "".join(rows))])
    tracemalloc.start()
    started = time.monotonic()
    sections = extract(path, "xlsx")
    elapsed = time.monotonic() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 20 * 1024 * 1024  # was ~500 MB when every row was padded to 16,384 columns
    assert elapsed < 5
    lines = sections[0].text.splitlines()
    assert lines[0] == "[S] hA: v2"
    assert lines[-1] == "[S] far"  # no header name for that column: the bare value


def test_repeated_sheet_part_is_one_section_and_sheet_count_is_capped(tmp_path: Path) -> None:
    from app.services import xlsx_extractor
    from app.services.docx_extractor import open_ooxml

    data = _row(1, '<c r="A1" t="inlineStr"><is><t>x</t></is></c>')
    path = _xlsx(tmp_path / "rep.xlsx", [("S1", "visible", data)])
    # many <sheet> elements that all point at the same worksheet part
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    sheets = "".join(f'<sheet name="N{i}" sheetId="{i}" r:id="rId1"/>' for i in range(1, 51))
    parts["xl/workbook.xml"] = f"<workbook {NS} {RNS}><sheets>{sheets}</sheets></workbook>".encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in parts.items():
            z.writestr(name, blob)
    with open_ooxml(path, "XLSX") as archive:
        xlsx_extractor.read_member(archive, "xl/worksheets/s1.xml")
        once = archive.bytes_read
        for _ in range(50):
            xlsx_extractor.read_member(archive, "xl/worksheets/s1.xml")
        assert archive.bytes_read == once
    sections, diagnostics = extract_xlsx_with_diagnostics(path)
    assert [s.section_title for s in sections] == ["N1"]
    assert len(diagnostics) == 49
    assert diagnostics[0] == "sheet 'N2': duplicate part xl/worksheets/s1.xml, skipped"

    too_many = "".join(
        f'<sheet name="N{i}" sheetId="{i}" r:id="rId1"/>'
        for i in range(xlsx_extractor._MAX_SHEETS + 1)
    )
    parts["xl/workbook.xml"] = (
        f"<workbook {NS} {RNS}><sheets>{too_many}</sheets></workbook>".encode()
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in parts.items():
            z.writestr(name, blob)
    with pytest.raises(ExtractionError) as err:
        extract(path, "xlsx")
    assert err.value.error_type == "CORRUPTED_FILE"


def _cap_text(monkeypatch: pytest.MonkeyPatch, cap: int) -> None:
    """Fix the shared text budget at `cap` bytes (no share of the decompressed bytes)."""
    from app.services import docx_extractor

    monkeypatch.setattr(docx_extractor, "MIN_TEXT_BYTES", cap)
    monkeypatch.setattr(docx_extractor, "TEXT_RATIO", 0)


def test_total_section_text_is_capped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cell = '<c r="A{n}" t="inlineStr"><is><t>' + "x" * 50 + "</t></is></c>"
    rows = "".join(_row(n, cell.format(n=n)) for n in (1, 2))
    sheets = [(name, "visible", rows) for name in "ABC"]
    path = _xlsx(tmp_path / "t.xlsx", sheets)
    assert len(extract(path, "xlsx")) == 3
    _cap_text(monkeypatch, 250)  # each section is ~101 bytes
    with pytest.raises(ExtractionError) as err:
        extract(path, "xlsx")
    assert err.value.error_type == "CORRUPTED_FILE"


def _peak_of_rejected_extract(path: Path) -> int:
    import tracemalloc

    tracemalloc.start()
    try:
        with pytest.raises(ExtractionError) as err:
            extract(path, "xlsx")
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert err.value.error_type == "CORRUPTED_FILE"
    assert "text is too large" in str(err.value)  # the text budget, not another cap
    return peak


def test_shared_string_amplification_is_cut_while_building(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cap = 8 * 1024 * 1024
    _cap_text(monkeypatch, cap)
    big = "word " * 20_000  # 100 KB, one shared string
    cells = "".join(_row(n, _s(f"A{n}", 0)) for n in range(1, 5001))  # 500 MB if fully expanded
    path = _xlsx(tmp_path / "amp.xlsx", [("S", "visible", cells)], shared=[big])
    assert _peak_of_rejected_extract(path) < cap * 4


def test_repeated_large_header_is_cut_while_rendering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cap = 8 * 1024 * 1024
    _cap_text(monkeypatch, cap)
    big = "word " * 20_000  # 100 KB header cell, repeated on every row below it
    shared = [big, "b", "c", "d", "v"]
    rows = _row(1, *(_s(f"{col}1", i) for i, col in enumerate("ABCD")))
    rows += "".join(_row(n, _s(f"A{n}", 4)) for n in range(2, 5001))  # 500 MB if rendered fully
    path = _xlsx(tmp_path / "hdr.xlsx", [("S", "visible", rows)], shared=shared)
    assert _peak_of_rejected_extract(path) < cap * 4


def test_utf16_doctype_in_xlsx_part_is_rejected(tmp_path: Path) -> None:
    path = _xlsx(tmp_path / "d.xlsx", [("S", "visible", _row(1, _s("A1", 0)))], shared=["a"])
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    parts["xl/sharedStrings.xml"] = (
        f'<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE s [<!ENTITY a "PWN">]>'
        f"<sst {NS}><si><t>&a;</t></si></sst>"
    ).encode("utf-16")
    with zipfile.ZipFile(path, "w") as z:
        for name, blob in parts.items():
            z.writestr(name, blob)
    with pytest.raises(ExtractionError) as err:
        extract(path, "xlsx")
    assert err.value.error_type == "CORRUPTED_FILE"


def test_non_numeric_style_and_numfmt_ids_do_not_crash(tmp_path: Path) -> None:
    styles = (
        '<numFmts count="1"><numFmt numFmtId="x" formatCode="yyyy"/></numFmts>'
        '<cellXfs count="2"><xf numFmtId="abc"/><xf numFmtId="14"/></cellXfs>'
    )
    data = _row(1, '<c r="A1" s="zz"><v>5</v></c>', '<c r="B1" s="1"><v>45935</v></c>')
    path = _xlsx(tmp_path / "n.xlsx", [("S", "visible", data)], styles=styles)
    assert extract(path, "xlsx")[0].text == "[S] 5 | 2025-10-05"


def test_elapsed_time_format_is_not_a_date(tmp_path: Path) -> None:
    for code in ("[h]:mm:ss", "[hh]:mm", "[mm]:ss", "[ss]"):
        assert not _is_date_format(code)
    assert _is_date_format("yyyy-mm-dd") and _is_date_format("h:mm")
    styles = (
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="[h]:mm:ss"/></numFmts>'
        '<cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="164"/></cellXfs>'
    )
    data = _row(1, '<c r="A1" s="1"><v>1.5</v></c>')
    path = _xlsx(tmp_path / "e.xlsx", [("S", "visible", data)], styles=styles)
    assert extract(path, "xlsx")[0].text == "[S] 1.5"


def test_text_budget_counts_utf8_bytes_at_the_real_floor(tmp_path: Path) -> None:
    # 20 cells x 1 MB of 4-byte characters: 5M characters but 20 MB of text, above the real
    # 8 MB floor (the file is a few KB, so the floor is the cap). No monkeypatch.
    big = "\U0001f600" * 250_000
    cells = "".join(_row(n, _s(f"A{n}", 0)) for n in range(1, 21))
    path = _xlsx(tmp_path / "emoji.xlsx", [("S", "visible", cells)], shared=[big])
    assert path.stat().st_size < 64 * 1024
    assert _peak_of_rejected_extract(path) < 8 * 1024 * 1024 * 4


def test_highly_compressed_sheet_part_is_refused_before_parsing(tmp_path: Path) -> None:
    import tracemalloc

    cells = "<c><v>1</v></c>" * 160_000  # 2.4 MB of XML that deflates far more than 100x
    path = _xlsx(tmp_path / "ratio.xlsx", [("S", "visible", f"<row>{cells}</row>")])
    tracemalloc.start()
    try:
        with pytest.raises(ExtractionError) as err:
            extract(path, "xlsx")
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert err.value.error_type == "CORRUPTED_FILE"
    assert "compressed" in str(err.value)
    assert peak < 4 * 2_400_000  # the raw part, not a parsed tree (~40 MB)


def test_realistic_workbook_passes_the_caps(tmp_path: Path) -> None:
    """12 columns x 5,000 rows x 3 sheets with varied values (the kind of compression real
    workbooks have) stays under the part ratio and text caps."""
    import random
    import time

    rng = random.Random(7)
    words = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(3, 9)))]
    words += [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(3, 9)))
        for _ in range(3_000)
    ] + ["코멘트", "이상반응", "투약", "방문", "검사", "정상"]
    cols = [chr(65 + c) for c in range(12)]
    sheets = []
    for name in ("S1", "S2", "S3"):
        head = [f'<c r="{c}1" t="inlineStr"><is><t>Col{i}</t></is></c>' for i, c in enumerate(cols)]
        rows = [_row(1, *head)]
        for n in range(2, 5_002):
            subject = f"SUBJ-{rng.randint(0, 99999):05d}"
            cells = [f'<c r="A{n}" t="inlineStr"><is><t>{subject}</t></is></c>']
            cells.append(f'<c r="B{n}" s="1"><v>{rng.randint(40000, 46000)}</v></c>')
            cells += [f'<c r="{c}{n}"><v>{rng.random() * 1000:.3f}</v></c>' for c in cols[2:6]]
            for c in cols[6:]:
                comment = " ".join(rng.choices(words, k=rng.randint(1, 6)))
                cells.append(f'<c r="{c}{n}" t="inlineStr"><is><t>{comment}</t></is></c>')
            rows.append(_row(n, *cells))
        sheets.append((name, "visible", "".join(rows)))
    path = _xlsx(tmp_path / "real.xlsx", sheets)
    started = time.monotonic()
    sections = extract(path, "xlsx")
    assert time.monotonic() - started < 10
    assert [s.section_title for s in sections] == ["S1", "S2", "S3"]
    assert all(len(s.text.splitlines()) == 5_000 for s in sections)
    assert sections[0].text.splitlines()[0].startswith("[S1] Col0: SUBJ-")
