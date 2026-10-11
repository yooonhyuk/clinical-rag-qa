"""The `.versions.yaml` draft: bundles, date candidates, round trip through parse_manifest
(synthetic file names only)."""

from datetime import date

import yaml
from draft_versions import draft_versions, render

from app.services.doc_versions import (
    latest_flags,
    parse_manifest,
    resolve_version,
)


def _entries(*paths: str) -> dict[str, tuple[str, str | None, date | None]]:
    return {e.path: (e.family, e.version, e.date) for e in draft_versions(list(paths)).entries}


def _applied(paths: list[str]) -> dict[str, bool]:
    """Latest flags after the draft is applied exactly as written."""
    manifest = parse_manifest(yaml.safe_load(render(draft_versions(paths)))["versions"])
    infos = [resolve_version(p.rsplit("/", 1)[-1], p, manifest) for p in paths]
    return dict(zip(paths, latest_flags(infos, ["c"] * len(infos)), strict=True))


def test_suffix_variants_of_one_document_are_one_candidate_bundle() -> None:
    paths = [f"plans/Sample plan {s}.docx" for s in ("clean", "tracked", "final", "구두보완")]
    draft = draft_versions(paths)
    assert draft.bundles == 1
    assert {e.family for e in draft.entries} == {"plans sample plan"}
    assert {e.path for e in draft.entries} == set(paths)


def test_similar_names_with_identical_digits_bundle_but_other_numbers_do_not() -> None:
    draft = draft_versions(
        [
            "a/Monitoring report template 2.docx",
            "a/Monitoring report template2 .docx",
            "a/Monitoring report template 3.docx",
        ]
    )
    assert draft.bundles == 1
    assert "a/Monitoring report template 3.docx" not in {e.path for e in draft.entries}


def test_different_folders_or_format_groups_are_not_bundled() -> None:
    assert (
        draft_versions(["studyA/Sample plan clean.docx", "studyB/Sample plan tracked.docx"]).entries
        == []
    )
    assert draft_versions(["a/Sample plan clean.docx", "a/Sample plan tracked.xlsx"]).entries == []
    assert draft_versions(["a/Sample plan clean.pdf", "a/Sample plan tracked.docx"]).entries == []


def test_change_documents_join_no_bundle() -> None:
    draft = draft_versions(
        [
            "a/Plan clean.docx",
            "a/Plan tracked.docx",
            "a/Plan v2.1 v2.2.docx",
            "a/Plan v2.2 v3.0.docx",
        ]
    )
    assert {e.path for e in draft.entries} == {
        "a/Plan clean.docx",
        "a/Plan tracked.docx",
    }


def test_same_version_in_a_family_gets_filename_date_as_a_candidate() -> None:
    got = _entries(
        "forms/Visit form v1.0 20250101.xlsx",
        "forms/Visit form v1.0 20250301.xlsx",
        "forms/Visit form v2.0.xlsx",
    )
    assert got["forms/Visit form v1.0 20250101.xlsx"][2] == date(2025, 1, 1)
    assert got["forms/Visit form v1.0 20250301.xlsx"][2] == date(2025, 3, 1)
    assert (
        got["forms/Visit form v2.0.xlsx"][2] is None
    )  # no date in the name: left for the operator


def test_comparable_editions_need_no_date() -> None:
    got = _entries("Protocol v1.docx", "Protocol v2.docx")
    assert {d for _, _, d in got.values()} == {None}


def test_draft_is_valid_yaml_that_parse_manifest_reads_back() -> None:
    paths = [
        "a/Sample plan clean.docx",
        "a/Sample plan tracked.docx",
        "b/Form [v1] 20250101.xlsx",
        "b/Form [v1] 20250201.xlsx",
    ]
    text = render(draft_versions(paths))
    entries = parse_manifest(yaml.safe_load(text)["versions"])
    assert len(entries) == 4
    assert text.count("# 확인 필요") == 4 and text.count("# 근거:") == 4
    body = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    assert not any("superseded" in ln for ln in body)  # never written as a key
    assert not any(e.superseded for e in entries)


def test_applying_the_draft_as_written_orders_editions_by_version_only() -> None:
    flags = _applied(["a/Plan v1.docx", "a/Plan v2.docx"])
    assert flags["a/Plan v1.docx"] is False and flags["a/Plan v2.docx"] is True


def test_filename_dates_are_comments_so_the_draft_hides_nothing_by_date() -> None:
    paths = [
        "a/Visit 1 minutes 20250105.docx",
        "a/Visit 1 minutes 20250405.docx",
        "a/Site 01 monitoring report 20250101.docx",
        "a/Site 01 monitoring report 20250301.docx",
    ]
    text = render(draft_versions(paths))
    assert "# date: 2025-01-05" in text and "# date: 2025-04-05" in text
    assert not any("date:" in e and not e.lstrip().startswith("#") for e in text.splitlines())
    assert set(_applied(paths).values()) == {True}


def test_removing_the_hash_and_space_of_a_date_candidate_hides_the_older_file() -> None:
    paths = ["a/Form v1 20250101.xlsx", "a/Form v1 20250301.xlsx"]
    text = render(draft_versions(paths))

    def hidden(body: str) -> list[bool]:
        manifest = parse_manifest(yaml.safe_load(body)["versions"])
        infos = [resolve_version(p.rsplit("/", 1)[-1], p, manifest) for p in paths]
        return latest_flags(infos, ["c"] * 2)

    assert hidden(text) == [True, True]  # before: nothing hidden by date
    # as the guidance says: delete only the two characters "# " of the candidate line
    lines = text.splitlines()
    out = [ln.replace("# ", "", 1) if ln.startswith("    # date: ") else ln for ln in lines]
    assert sum(a != b for a, b in zip(out, lines, strict=True)) == 2  # the two candidate lines
    manifest = parse_manifest(yaml.safe_load("\n".join(out))["versions"])
    infos = [resolve_version(p.rsplit("/", 1)[-1], p, manifest) for p in paths]
    assert [i.date for i in infos] == [date(2025, 1, 1), date(2025, 3, 1)]
    assert hidden("\n".join(out)) == [False, True]


def test_bundle_without_dates_hides_nothing() -> None:
    flags = _applied(["a/Sample plan clean.docx", "a/Sample plan tracked.docx"])
    assert set(flags.values()) == {True}


def test_single_files_and_empty_corpus_produce_an_empty_list() -> None:
    assert (
        yaml.safe_load(render(draft_versions(["a/Protocol v2.docx", "a/Other.docx"])))["versions"]
        == []
    )
