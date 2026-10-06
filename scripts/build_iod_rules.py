"""Build the Layer 1 conformance rule file (IODs, modules, attribute Types) from the standard.

Sources (DocBook XML from dicom.nema.org, see dicom_docbook.py):
- PS3.3 Annex A  IOD module tables (e.g. Table A.3-1 CT Image IOD Modules, usage M/C/U) and
                 functional group macro tables of enhanced multi-frame IODs (e.g. Table A.38-2)
- PS3.3 Annex C  module / macro attribute tables (Type 1, 1C, 2, 2C, 3), "Include" rows resolved
- PS3.3 C.7.3.1.1.1  Modality Defined Terms
- PS3.16 Annex L     Body Part Examined Defined Terms (Tables L-1, L-2, L-3)

Output: backend/app/rules/standard/ps3.3_iod.yaml (committed, generated - do not edit).
Only module attributes at the top level (and the first nesting level for functional group
macros) are kept; deeper sequence contents are out of scope for the analyzer.

Usage: uv run --project backend python scripts/build_iod_rules.py [--edition current]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml
from dicom_docbook import DB, DEFAULT_CACHE, caption, index_by_id, load, parse_tag, rows, text
from pydicom.datadict import keyword_for_tag

OUT = Path(__file__).resolve().parents[1] / "backend/app/rules/standard/ps3.3_iod.yaml"

# IOD key -> (IOD module table caption, functional group table caption or None,
#             Storage SOP Class UIDs (PS3.4 Annex B), Modality values used as fallback)
IODS: dict[str, tuple[str, str | None, list[str], list[str]]] = {
    "cr": ("Computed Radiography Image IOD Modules", None, ["1.2.840.10008.5.1.4.1.1.1"], ["CR"]),
    "ct": ("CT Image IOD Modules", None, ["1.2.840.10008.5.1.4.1.1.2"], ["CT"]),
    "enhanced_ct": (
        "Enhanced CT Image IOD Modules",
        "Enhanced CT Image Functional Group Macros",
        ["1.2.840.10008.5.1.4.1.1.2.1"],
        [],
    ),
    "mr": ("MR Image IOD Modules", None, ["1.2.840.10008.5.1.4.1.1.4"], ["MR"]),
    "enhanced_mr": (
        "Enhanced MR Image IOD Modules",
        "Enhanced MR Image Functional Group Macros",
        ["1.2.840.10008.5.1.4.1.1.4.1"],
        [],
    ),
    "pet": (
        "Positron Emission Tomography Image IOD Modules",
        None,
        ["1.2.840.10008.5.1.4.1.1.128"],
        ["PT"],
    ),
    "enhanced_pet": (
        "Enhanced PET Image IOD Modules",
        "Enhanced PET Image Functional Group Macros",
        ["1.2.840.10008.5.1.4.1.1.130"],
        [],
    ),
    "us": ("Ultrasound Image IOD Modules", None, ["1.2.840.10008.5.1.4.1.1.6.1"], ["US"]),
    "us_multiframe": (
        "Ultrasound Multi-frame Image IOD Modules",
        None,
        ["1.2.840.10008.5.1.4.1.1.3.1"],
        [],
    ),
    "secondary_capture": (
        "Secondary Capture Image IOD Modules",
        None,
        ["1.2.840.10008.5.1.4.1.1.7"],
        ["OT", "SC"],
    ),
    "dx": (
        "Digital X-Ray Image IOD Modules",
        None,
        ["1.2.840.10008.5.1.4.1.1.1.1", "1.2.840.10008.5.1.4.1.1.1.1.1"],
        ["DX"],
    ),
}
TYPE_RE = re.compile(r"^[123]C?$")


class Standard:
    def __init__(self, root) -> None:
        self.tables = index_by_id(root, "table")
        self.sections = index_by_id(root, "section")
        self.by_caption = {caption(t): tid for tid, t in self.tables.items()}

    def label(self, table_id: str) -> str:
        return "Table " + table_id.removeprefix("table_")

    def section_table(self, section_id: str) -> str:
        """The attribute table that defines a module / macro section."""
        section = self.sections[section_id]
        for table in section.iter(f"{DB}table"):
            if caption(table).endswith("Attributes"):
                return table.get("{http://www.w3.org/XML/1998/namespace}id")
        raise RuntimeError(f"no attribute table in {section_id}")

    def flatten(self, table_id: str, level: int = 0, depth: int = 0) -> list[dict]:
        """Attribute rows with nesting level; "Include" rows are expanded recursively."""
        if depth > 8:
            raise RuntimeError(f"include depth exceeded at {table_id}")
        out: list[dict] = []
        for cells in rows(self.tables[table_id]):
            if not cells:
                continue
            first = cells[0].text
            nesting = len(first) - len(first.lstrip(">"))
            name = first.lstrip(">").strip()
            if name.startswith("Include"):
                targets = [link for link in cells[0].links if link in self.tables]
                for target in targets:
                    out.extend(self.flatten(target, level + nesting, depth + 1))
                continue
            if len(cells) < 3 or not TYPE_RE.match(cells[2].text):
                continue
            parsed = parse_tag(cells[1].text)
            if parsed is None or "x" in "".join(parsed):
                continue  # repeating groups (e.g. overlays) are out of scope
            tag = "".join(parsed)
            out.append(
                {
                    "level": level + nesting,
                    "tag": tag,
                    "keyword": keyword_for_tag(int(tag, 16)) or None,
                    "name": name,
                    "type": cells[2].text,
                }
            )
        return out


def usage(raw: str) -> tuple[str, str | None]:
    code = raw.strip()[:1]
    if code not in {"M", "C", "U"}:
        raise RuntimeError(f"unexpected usage {raw!r}")
    rest = raw.strip()[1:].strip(" -")
    return code, rest or None


def build_module(std: Standard, section_id: str, max_level: int) -> dict:
    table_id = std.section_table(section_id)
    attributes = []
    seen: set[str] = set()
    for row in std.flatten(table_id):
        if row["level"] > max_level:
            continue
        key = f"{row['level']}:{row['tag']}"
        if key in seen:
            continue
        seen.add(key)
        attributes.append(row)
    return {
        "table": std.label(table_id),
        "caption": caption(std.tables[table_id]),
        "section": section_id.removeprefix("sect_"),
        "attributes": attributes,
    }


def build_iod(std: Standard, modules: dict, iod_caption: str, fg_caption: str | None) -> dict:
    iod_table = std.by_caption.get(iod_caption)
    if iod_table is None:
        raise RuntimeError(f"IOD table {iod_caption!r} not found")
    entries = []
    for cells in rows(std.tables[iod_table]):
        if len(cells) < 3:
            continue
        ref_links = [link for link in cells[-2].links if link.startswith("sect_")]
        if not ref_links:
            continue
        module_name, section_id = cells[-3].text, ref_links[0]
        code, condition = usage(cells[-1].text)
        if code != "U" and section_id not in modules:
            modules[section_id] = build_module(std, section_id, max_level=0)
            modules[section_id]["name"] = module_name
        entries.append(
            {"module": module_name, "ref": section_id, "usage": code, "condition": condition}
        )
    iod = {"table": std.label(iod_table), "caption": iod_caption, "modules": entries}
    if fg_caption:
        fg_table = std.by_caption.get(fg_caption)
        if fg_table is None:
            raise RuntimeError(f"functional group table {fg_caption!r} not found")
        groups = []
        for cells in rows(std.tables[fg_table]):
            links = [link for c in cells[1:2] for link in c.links if link.startswith("sect_")]
            if len(cells) < 3 or not links:
                continue
            code, condition = usage(cells[-1].text)
            macro = build_module(std, links[0], max_level=1) if code == "M" else None
            groups.append(
                {
                    "macro": cells[0].text,
                    "ref": links[0],
                    "usage": code,
                    "condition": condition,
                    "per_frame_only": bool(condition and "not be used as a Shared" in condition),
                    **({"definition": macro} if macro else {}),
                }
            )
        iod["functional_groups"] = {
            "table": std.label(fg_table),
            "caption": fg_caption,
            "macros": groups,
        }
    return iod


def modality_terms(std: Standard) -> dict:
    section = std.sections["sect_C.7.3.1.1.1"]
    defined, retired = [], []
    for vlist in section.iter(f"{DB}variablelist"):
        title = text(vlist.find(f"{DB}title"))
        terms = [text(e.find(f"{DB}term")) for e in vlist.iter(f"{DB}varlistentry")]
        (retired if "Retired" in title else defined).extend(terms)
    if not defined:
        raise RuntimeError("no Modality Defined Terms found")
    return {"source": "PS3.3 C.7.3.1.1.1", "defined": defined, "retired": retired}


def body_part_terms(root16) -> dict:
    tables = index_by_id(root16, "table")
    terms: list[str] = []
    for tid in ("table_L-1", "table_L-2", "table_L-3"):
        t = tables[tid]
        header = [text(th) for th in t.find(f"{DB}thead").iter(f"{DB}th")]
        col = header.index("Body Part Examined")
        for cells in rows(t):
            value = cells[col].text if len(cells) > col else ""
            if value and value not in terms:
                terms.append(value)
    return {"source": "PS3.16 Annex L (Tables L-1, L-2, L-3)", "defined": sorted(terms)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--edition", default="current")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    try:
        root3, src3 = load(3, args.edition, args.cache)
        root16, src16 = load(16, args.edition, args.cache)
    except OSError as exc:
        print(f"ERROR: cannot fetch the DICOM standard ({exc}); no rules written.", file=sys.stderr)
        return 1
    std = Standard(root3)
    modules: dict = {}
    iods = {}
    for key, (iod_caption, fg_caption, sop_classes, modalities) in IODS.items():
        iods[key] = {
            "sop_classes": sop_classes,
            "modalities": modalities,
            **build_iod(std, modules, iod_caption, fg_caption),
        }
    doc = {
        "generated_by": "scripts/build_iod_rules.py",
        "sources": {"ps3.3": src3.as_dict(), "ps3.16": src16.as_dict()},
        "defined_terms": {
            "Modality": modality_terms(std),
            "BodyPartExamined": body_part_terms(root16),
        },
        "iods": iods,
        "modules": dict(sorted(modules.items())),
    }
    header = (
        "# GENERATED FILE - do not edit by hand. Regenerate with:\n"
        "#   uv run --project backend python scripts/build_iod_rules.py\n"
        f"# Source: DICOM {src3.part} {src3.edition} (Annex A IOD tables, Annex C module tables,\n"
        "#         C.7.3.1.1.1 Modality Defined Terms)\n"
        f"#         DICOM {src16.part} {src16.edition} (Annex L Body Part Examined Defined Terms)\n"
        f"# URL:    {src3.url}\n"
        f"#         {src16.url}\n"
        f"# Retrieved: {src3.retrieved}\n"
        "# DICOM(R) is the registered trademark of NEMA for its standards publications.\n"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    print(f"wrote {args.out} ({len(iods)} IODs, {len(modules)} modules, edition {src3.edition})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
