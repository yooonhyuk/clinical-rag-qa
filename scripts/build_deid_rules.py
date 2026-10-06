"""Build the Layer 2 de-identification rule file from the official DICOM standard.

Sources (DocBook XML from dicom.nema.org, see dicom_docbook.py):
- PS3.15 Table E.1-1   Application Level Confidentiality Profile Attributes
- PS3.15 Table E.1-1a  De-identification Action Codes
- PS3.16 CID 7050      De-identification Method (codes used in (0012,0064))

Output: backend/app/rules/standard/ps3.15_e1-1_deid.yaml (committed, generated - do not edit).

Usage (needs network the first time; downloads are cached under ~/.cache/clinical-rag-qa):
  uv run --project backend python scripts/build_deid_rules.py [--edition current|2025c|...]
If the download fails the script stops with an error - the table is never invented.
"""

import argparse
import sys
from pathlib import Path

import yaml
from dicom_docbook import DB, DEFAULT_CACHE, caption, index_by_id, load, parse_tag, rows, text
from pydicom.datadict import keyword_for_tag

OUT = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "rules"
    / "standard"
    / "ps3.15_e1-1_deid.yaml"
)

# Table E.1-1 option columns (index in the row) -> (option key, CID 7050 Code Meaning).
OPTION_COLUMNS: dict[int, tuple[str, str]] = {
    5: ("retain_safe_private", "Retain Safe Private Option"),
    6: ("retain_uids", "Retain UIDs Option"),
    7: ("retain_device_identity", "Retain Device Identity Option"),
    8: ("retain_institution_identity", "Retain Institution Identity Option"),
    9: ("retain_patient_characteristics", "Retain Patient Characteristics Option"),
    10: (
        "retain_longitudinal_full_dates",
        "Retain Longitudinal Temporal Information Full Dates Option",
    ),
    11: (
        "retain_longitudinal_modified_dates",
        "Retain Longitudinal Temporal Information Modified Dates Option",
    ),
    12: ("clean_descriptors", "Clean Descriptors Option"),
    13: ("clean_structured_content", "Clean Structured Content Option"),
    14: ("clean_graphics", "Clean Graphics Option"),
}
EXPECTED_HEADER = [
    "Attribute Name",
    "Tag",
    "Retd.",
    "In Std. Comp. IOD",
    "Basic Prof.",
    "Rtn. Safe Priv. Opt.",
    "Rtn. UIDs Opt.",
    "Rtn. Dev. Id. Opt.",
    "Rtn. Inst. Id. Opt.",
    "Rtn. Pat. Chars. Opt.",
    "Rtn. Long. Full Dates Opt.",
    "Rtn. Long. Modif. Dates Opt.",
    "Clean Desc. Opt.",
    "Clean Struct. Cont. Opt.",
    "Clean Graph. Opt.",
]


def table(root, table_id: str):
    tables = index_by_id(root, "table")
    if table_id not in tables:
        raise RuntimeError(f"{table_id} not found - the standard layout changed?")
    return tables[table_id]


def parse_e11(root) -> list[dict]:
    t = table(root, "table_E.1-1")
    header = [text(th) for th in t.find(f"{DB}thead").iter(f"{DB}th")]
    for got, want in zip(header, EXPECTED_HEADER, strict=True):
        if not got.startswith(want):
            raise RuntimeError(f"unexpected Table E.1-1 header {got!r} (expected {want!r})")
    out = []
    for cells in rows(t):
        values = [c.text for c in cells]
        name, raw_tag = values[0], values[1]
        entry: dict = {"name": name, "basic": values[4]}
        parsed = parse_tag(raw_tag)
        if parsed:
            group, element = parsed
            entry["tag"] = f"{group}{element}"
            if "x" not in entry["tag"]:
                entry["keyword"] = keyword_for_tag(int(entry["tag"], 16)) or None
        elif "gggg is odd" in raw_tag:
            entry["tag"] = "private"
        else:
            raise RuntimeError(f"unparsable tag {raw_tag!r} for {name!r}")
        entry["retired"] = values[2] == "Y"
        entry["in_std_comp_iod"] = values[3] == "Y"
        options = {
            OPTION_COLUMNS[i][0]: v for i, v in enumerate(values) if i in OPTION_COLUMNS and v
        }
        if options:
            entry["options"] = options
        out.append(entry)
    return out


def parse_action_codes(root) -> dict[str, str]:
    return {
        cells[0].text: cells[1].text
        for cells in rows(table(root, "table_E.1-1a"))
        if len(cells) >= 2
    }


def parse_cid7050(root16) -> list[dict]:
    section = index_by_id(root16, "section")["sect_CID_7050"]
    t = section.find(f".//{DB}table")
    out = []
    for cells in rows(t):
        if len(cells) >= 3 and cells[1].text.isdigit():
            out.append({"scheme": cells[0].text, "code": cells[1].text, "meaning": cells[2].text})
    if not out:
        raise RuntimeError("CID 7050 table is empty")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--edition", default="current")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    try:
        root15, src15 = load(15, args.edition, args.cache)
        root16, src16 = load(16, args.edition, args.cache)
    except OSError as exc:
        print(f"ERROR: cannot fetch the DICOM standard ({exc}); no rules written.", file=sys.stderr)
        return 1

    expected = "Application Level Confidentiality Profile Attributes"
    if caption(table(root15, "table_E.1-1")) != expected:
        raise RuntimeError("Table E.1-1 caption changed")
    attributes = parse_e11(root15)
    cid7050 = parse_cid7050(root16)
    meanings = {c["meaning"]: c["code"] for c in cid7050}
    options = {}
    for key, meaning in OPTION_COLUMNS.values():
        if meaning not in meanings:
            raise RuntimeError(f"{meaning!r} not in CID 7050")
        options[key] = {"name": meaning, "cid7050_code": meanings[meaning]}

    doc = {
        "generated_by": "scripts/build_deid_rules.py",
        "profile": "Basic Application Level Confidentiality Profile (PS3.15 Annex E)",
        "sources": {
            "table_E.1-1": {**src15.as_dict(), "table": "Table E.1-1"},
            "table_E.1-1a": {**src15.as_dict(), "table": "Table E.1-1a"},
            "cid_7050": {**src16.as_dict(), "table": "CID 7050"},
        },
        "action_codes": parse_action_codes(root15),
        "options": options,
        "cid7050": cid7050,
        "attributes": attributes,
    }
    header = (
        "# GENERATED FILE - do not edit by hand. Regenerate with:\n"
        "#   uv run --project backend python scripts/build_deid_rules.py\n"
        f"# Source: DICOM {src15.part} {src15.edition}, Table E.1-1 / E.1-1a "
        f"(Application Level Confidentiality Profile)\n"
        f"#         DICOM {src16.part} {src16.edition}, CID 7050 (De-identification Method)\n"
        f"# URL:    {src15.url}\n"
        f"#         {src16.url}\n"
        f"# Retrieved: {src15.retrieved}\n"
        "# DICOM(R) is the registered trademark of NEMA for its standards publications.\n"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    print(f"wrote {args.out} ({len(attributes)} attributes, edition {src15.edition})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
