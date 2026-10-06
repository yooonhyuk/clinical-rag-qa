"""Offline tests for the standard -> YAML rule builders (no network: tiny DocBook fixtures)."""

import xml.etree.ElementTree as ET

import build_deid_rules
from build_iod_rules import Standard, usage
from dicom_docbook import parse_tag

NS = 'xmlns="http://docbook.org/ns/docbook" xmlns:xl="http://www.w3.org/1999/xlink"'


def _row(*cells: str) -> str:
    return "<tr>" + "".join(f"<td><para>{c}</para></td>" for c in cells) + "</tr>"


def test_parse_tag_handles_repeating_groups() -> None:
    assert parse_tag("(0010,0010)") == ("0010", "0010")
    assert parse_tag("(60xx,3000)") == ("60xx", "3000")
    assert parse_tag("(gggg,eeee) where gggg is odd") is None


def test_table_e11_parsing() -> None:
    header = "".join(f"<th><para>{h}</para></th>" for h in build_deid_rules.EXPECTED_HEADER)
    blank = [""] * 10
    xml = f"""<book {NS}><table xml:id="table_E.1-1"><caption>x</caption>
      <thead><tr>{header}</tr></thead><tbody>
      {_row("Patient's Name", "(0010,0010)", "N", "Y", "Z", *blank)}
      {_row("Study Date", "(0008,0020)", "N", "Y", "Z", "", "", "", "", "", "K", "C", "", "", "")}
      {_row("Overlay Data", "(60xx,3000)", "N", "Y", "X", *blank[:-1], "C")}
      {_row("Private Attributes", "(gggg,eeee) where gggg is odd", "N", "N", "X", "C", *blank[1:])}
      </tbody></table>
      <table xml:id="table_E.1-1a"><tbody>{_row("X", "remove")}{_row("Z", "zero")}</tbody></table>
    </book>"""
    root = ET.fromstring(xml)
    rows = build_deid_rules.parse_e11(root)
    assert rows[0] == {
        "name": "Patient's Name",
        "basic": "Z",
        "tag": "00100010",
        "keyword": "PatientName",
        "retired": False,
        "in_std_comp_iod": True,
    }
    assert rows[1]["options"] == {
        "retain_longitudinal_full_dates": "K",
        "retain_longitudinal_modified_dates": "C",
    }
    assert rows[2]["tag"] == "60xx3000" and rows[2]["options"] == {"clean_graphics": "C"}
    assert rows[3]["tag"] == "private" and rows[3]["options"] == {"retain_safe_private": "C"}
    assert build_deid_rules.parse_action_codes(root) == {"X": "remove", "Z": "zero"}


def test_module_include_rows_are_expanded_with_nesting() -> None:
    xml = f"""<book {NS}>
      <section xml:id="sect_C.1"><table xml:id="table_C.1-1">
        <caption>Demo Module Attributes</caption>
        <tbody>
        {_row("Rows", "(0028,0010)", "1", "d")}
        <tr><td><para>Include <xref linkend="table_M-1"/></para></td></tr>
        {_row("Some Sequence", "(0008,1140)", "3", "d")}
        <tr><td><para>&gt;Include <xref linkend="table_M-1"/></para></td></tr>
        {_row("Overlay Rows", "(60xx,0010)", "1", "d")}
        </tbody></table></section>
      <table xml:id="table_M-1"><caption>Macro Attributes</caption><tbody>
        {_row("Columns", "(0028,0011)", "1C", "d")}
      </tbody></table>
    </book>"""
    std = Standard(ET.fromstring(xml))
    rows = std.flatten("table_C.1-1")
    assert [(r["level"], r["keyword"], r["type"]) for r in rows] == [
        (0, "Rows", "1"),
        (0, "Columns", "1C"),
        (0, "ReferencedImageSequence", "3"),
        (1, "Columns", "1C"),
    ]  # repeating-group overlay attribute skipped
    assert std.section_table("sect_C.1") == "table_C.1-1"


def test_usage_parsing() -> None:
    assert usage("M") == ("M", None)
    assert usage("C - Required if contrast media was used") == (
        "C",
        "Required if contrast media was used",
    )
