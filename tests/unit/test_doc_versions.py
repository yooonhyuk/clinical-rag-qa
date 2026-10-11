"""Version tokens in file names, manifest matching, latest-edition resolution (synthetic names)."""

from datetime import date

import pytest

from app.services.doc_versions import (
    VersionInfo,
    compare_versions,
    infer_from_filename,
    latest_flags,
    parse_manifest,
    parse_version_key,
    resolve_version,
)


def _latest(*names: str, manifest=(), groups=None) -> dict[str, bool]:
    infos = [resolve_version(n, None, manifest) for n in names]
    flags = latest_flags(infos, groups or ["c"] * len(infos))
    return dict(zip(names, flags, strict=True))


@pytest.mark.parametrize(
    ("name", "family", "label", "when"),
    [
        ("Sample Guide v2.1.pdf", "sample guide", "v2.1", None),
        ("sample_guide_ver 3.docx", "sample guide", "ver 3", None),
        ("Sample-Guide-Rev6.pdf", "sample guide", "Rev6", None),
        ("sample guide (R3).pdf", "sample guide", "R3", None),
        ("Sample Protocol Amendment 2.pdf", "sample protocol", "Amendment 2", None),
        ("Sample Guide E6R3.pdf", "sample guide e6", "R3", None),
        ("Sample Guide E6(R2).pdf", "sample guide e6", "R2", None),
        (
            "report_20250915.xlsx",
            None,
            None,
            date(2025, 9, 15),
        ),  # a date alone: no family
        ("report 2025-09-15.xlsx", None, None, date(2025, 9, 15)),
        ("report v2 2025-09-15.xlsx", "report", "v2", date(2025, 9, 15)),
        ("Sample Guide V1.0 FINAL.PDF", "sample guide final", "V1.0", None),
        ("샘플 지침서_v3.pdf", "샘플 지침서", "v3", None),
        ("샘플 지침서 최종.docx", "샘플 지침서", "최종", None),
        ("샘플 지침서 제3차 개정.pdf", "샘플 지침서", "제3차 개정", None),
        ("샘플 지침서(개정2)_20240102.pdf", "샘플 지침서", "개정2", date(2024, 1, 2)),
    ],
)
def test_filename_tokens(name, family, label, when) -> None:
    info = infer_from_filename(name)
    assert info.source == "filename"
    assert info.family == family
    assert info.label == label
    assert info.date == when


def test_underscore_separated_amendment_stays_in_the_family() -> None:
    # "amendment_1" has an underscore, not a space: left in the family, still versioned by v2
    info = infer_from_filename("sample_protocol_v2_amendment_1.pdf")
    assert info.label == "v2" and info.family == "sample protocol amendment 1"


@pytest.mark.parametrize(
    "name",
    [
        "notes.pdf",
        "Server2.docx",
        "r2d2.md",
        "guide_v.pdf",
        "abc2025.pdf",
    ],
)
def test_names_without_a_token_are_standalone(name) -> None:
    info = infer_from_filename(name)
    assert info == VersionInfo()
    assert latest_flags([info], ["c"]) == [True]


def test_ich_style_editions_are_editions_and_group_into_one_family() -> None:
    flags = _latest("ICH E6(R2) guideline.pdf", "ICH E6(R3) guideline.pdf")
    assert list(flags.values()) == [False, True]
    flags = _latest("ICH_E6R2.pdf", "ICH_E6R3.pdf", "ICH_E10R1.pdf")
    assert list(flags.values()) == [False, True, True]
    assert infer_from_filename("Guide E10R3.pdf").label == "R3"
    assert infer_from_filename("02_ich_e6r3_2025.pdf").label == "r3"


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("NIH_R01_application.pdf", "NIH_R21_application.pdf"),
        (
            "NIH_R01_application.pdf",
            "NIH_R02_application.pdf",
        ),  # leading zero: never an edition
        ("Site R1 log.xlsx", "Site R2 log.xlsx"),
        ("COVID-19 R0 model.pdf", "COVID-19 R1 model.pdf"),
        ("회의록_20250101.docx", "회의록_20250301.docx"),
        (
            "Monitoring Visit Report 2025-01-10.pdf",
            "Monitoring Visit Report 2025-03-02.pdf",
        ),
        ("Lot 20250101.xlsx", "Lot 20250102.xlsx"),
        ("weekly 20250101.xlsx", "weekly 20250915.xlsx"),
        # same form version, dates only in the file name: both stay latest
        ("Minutes v1 20250101.pdf", "Minutes v1 20250301.pdf"),
        ("회의록_v1_20250101.docx", "회의록_v1_20250301.docx"),
        ("MVR_v1.0_2025-01-10.pdf", "MVR_v1.0_2025-03-02.pdf"),
        ("weekly report v1 2025-01-06.pdf", "weekly report v1 2025-01-13.pdf"),
        ("Protocol v2 Amendment 1 20250101.pdf", "Protocol v2 Amendment 1 20250301.pdf"),
        ("plan v2 20250101.pdf", "plan v2.0 20250915.pdf"),
    ],
)
def test_identifiers_and_date_series_are_not_editions(a, b) -> None:
    assert all(_latest(a, b).values())


def test_dates_only_never_hide_anything() -> None:
    flags = _latest("weekly 20250101.xlsx", "weekly 20250915.xlsx", "weekly 20250301.xlsx")
    assert all(flags.values())


def test_impossible_date_is_not_a_date() -> None:
    assert infer_from_filename("report_20251345.pdf") == VersionInfo()


def test_numeric_versions_compare_as_numbers_not_text() -> None:
    assert _latest("guide v2.9.pdf", "guide v2.10.pdf") == {
        "guide v2.9.pdf": False,
        "guide v2.10.pdf": True,
    }
    assert _latest("guide v2.0.pdf", "guide v2.pdf") == {  # 2.0 == 2: a tie keeps both
        "guide v2.0.pdf": True,
        "guide v2.pdf": True,
    }


def test_revisions_r2_vs_r3_and_rev_numbers() -> None:
    assert _latest("sample gcp (R2).pdf", "sample gcp (R3).pdf") == {
        "sample gcp (R2).pdf": False,
        "sample gcp (R3).pdf": True,
    }
    assert (
        _latest("sample label rev6.pdf", "sample label Rev 5.pdf")["sample label Rev 5.pdf"]
        is False
    )


def test_manifest_dates_compare_when_stated() -> None:
    manifest = parse_manifest(
        [
            {"match": "log_a.pdf", "family": "visit log", "date": "2025-01-10"},
            {"match": "log_b.pdf", "family": "visit log", "date": "2025-03-02"},
        ]
    )
    assert _latest("log_a.pdf", "log_b.pdf", manifest=manifest) == {
        "log_a.pdf": False,
        "log_b.pdf": True,
    }


def test_version_first_then_date_on_a_tie() -> None:
    # a date in a file name never breaks a tie: both stay latest
    assert _latest("plan v2 20250101.pdf", "plan v2 20250915.pdf") == {
        "plan v2 20250101.pdf": True,
        "plan v2 20250915.pdf": True,
    }
    # a higher version beats a later date
    assert _latest("plan v3 20240101.pdf", "plan v2 20250915.pdf") == {
        "plan v3 20240101.pdf": True,
        "plan v2 20250915.pdf": False,
    }


def test_manifest_dates_break_a_version_tie() -> None:
    manifest = parse_manifest(
        [
            {"match": "plan_a.pdf", "family": "plan", "version": "v2", "date": "2025-01-01"},
            {"match": "plan_b.pdf", "family": "plan", "version": "v2", "date": "2025-09-15"},
        ]
    )
    assert _latest("plan_a.pdf", "plan_b.pdf", manifest=manifest) == {
        "plan_a.pdf": False,
        "plan_b.pdf": True,
    }
    # a manifest date against a file-name date is not compared
    mixed = parse_manifest(
        [{"match": "plan_a.pdf", "family": "plan", "version": "v2", "date": "2025-01-01"}]
    )
    assert all(_latest("plan_a.pdf", "plan v2 20250915.pdf", manifest=mixed).values())


def test_amendment_breaks_a_version_tie() -> None:
    flags = _latest("sample protocol v2 Amendment 1.pdf", "sample protocol v2 Amendment 2.pdf")
    assert list(flags.values()) == [False, True]


def test_ties_and_incomparable_versions_keep_both_visible() -> None:
    assert _latest("guide v2.pdf", "guide v2 .pdf") == {
        "guide v2.pdf": True,
        "guide v2 .pdf": True,
    }
    # v vs R: different kinds, no dates -> cannot tell
    assert _latest("guide v2.pdf", "guide R3.pdf") == {
        "guide v2.pdf": True,
        "guide R3.pdf": True,
    }
    # a version on one side and only a date on the other
    assert all(_latest("guide v2.pdf", "guide 20250915.pdf").values())
    # a token without a number on both sides
    assert all(_latest("샘플 지침 최종.pdf", "샘플 지침 개정.pdf").values())
    # three docs: the two that cannot be ordered against each other stay, the older one goes
    flags = _latest("guide v1.pdf", "guide v2.pdf", "guide R3.pdf")
    assert flags == {"guide v1.pdf": False, "guide v2.pdf": True, "guide R3.pdf": True}


def test_same_name_in_other_folders_is_another_document() -> None:
    def info(name: str, path: str) -> VersionInfo:
        return resolve_version(name, path)

    a, b = (
        info("Protocol_v2.0.pdf", "studyA/Protocol_v2.0.pdf"),
        info("Protocol_v3.0.pdf", "studyB/Protocol_v3.0.pdf"),
    )
    assert a.family != b.family
    assert latest_flags([a, b], ["c", "c"]) == [True, True]
    # same folder (any case/separator) still competes; so do files at the corpus root
    c = info("Protocol_v3.0.pdf", "StudyA/Protocol_v3.0.pdf")
    assert latest_flags([a, c], ["c", "c"]) == [False, True]
    root = info("Protocol_v1.pdf", "Protocol_v1.pdf")
    assert latest_flags([root, info("Protocol_v2.pdf", "Protocol_v2.pdf")], ["c", "c"]) == [
        False,
        True,
    ]
    # manifest families are used as written, whatever the folder
    manifest = parse_manifest([{"match": "*.pdf", "family": "P", "version": "1"}])
    assert resolve_version("x.pdf", "studyA/x.pdf", manifest).family == "p"


def test_different_families_and_corpora_never_mix() -> None:
    assert all(_latest("alpha guide v1.pdf", "beta guide v2.pdf", "gamma.pdf").values())
    infos = [infer_from_filename("guide v1.pdf"), infer_from_filename("guide v2.pdf")]
    assert latest_flags(infos, ["public", "private"]) == [True, True]
    assert latest_flags(infos, ["public", "public"]) == [False, True]


def test_manifest_wins_over_filename_and_marks_superseded() -> None:
    manifest = parse_manifest(
        [
            {
                "match": "02_ich_e6r3_2025.pdf",
                "family": "ICH E6",
                "version": "R3",
                "date": "2025-01-06",
            },
            {
                "match": "05_*.pdf",
                "family": "ich e6",
                "version": "R2",
                "superseded": True,
            },
            {"match": "no family here"},  # malformed: ignored
            "not a mapping",
        ]
    )
    assert len(manifest) == 2 and manifest[0].date == date(2025, 1, 6)
    new = resolve_version("02_ich_e6r3_2025.pdf", "docs/02_ich_e6r3_2025.pdf", manifest)
    old = resolve_version("05_mfds_ich_gcp_ko.pdf", "docs/05_mfds_ich_gcp_ko.pdf", manifest)
    assert (new.source, new.family, new.label) == ("manifest", "ich e6", "R3")
    assert old.family == new.family and old.superseded
    assert latest_flags([new, old], ["p", "p"]) == [True, False]
    # not in the manifest -> filename inference
    other = resolve_version("06_notes_v2.pdf", "06_notes_v2.pdf", manifest)
    assert other.source == "filename"


def test_manifest_matches_relative_path_glob() -> None:
    manifest = parse_manifest([{"match": "protocols/*.pdf", "family": "p", "version": "2"}])
    assert resolve_version("a.pdf", "protocols/a.pdf", manifest).source == "manifest"
    assert resolve_version("a.pdf", "other/a.pdf", manifest).source == "none"


def test_superseded_alone_in_its_family_is_not_hidden() -> None:
    old = VersionInfo(family="f", label="R2", source="manifest", superseded=True)
    assert latest_flags([old], ["c"]) == [True]
    # every member superseded: fall back to comparing them
    older = VersionInfo(family="f", label="R1", source="manifest", superseded=True)
    assert latest_flags([old, older], ["c", "c"]) == [True, False]


def test_superseded_beats_a_higher_version() -> None:
    withdrawn = VersionInfo(family="f", label="v9", source="manifest", superseded=True)
    current = VersionInfo(family="f", label="v2", source="manifest")
    assert latest_flags([withdrawn, current], ["c", "c"]) == [False, True]


def test_adding_a_newer_edition_changes_the_previous_latest() -> None:
    names = ["guide v1.pdf", "guide v2.pdf"]
    assert list(_latest(*names).values()) == [False, True]
    assert list(_latest(*names[:1]).values()) == [True]  # removing the newer one restores v1
    assert list(_latest(*names, "guide v3.pdf").values()) == [False, False, True]


def test_version_key_and_compare_helpers() -> None:
    assert parse_version_key("v2.10") == (("ver", (2, 10)),)
    assert parse_version_key("3") == (("ver", (3,)),)
    assert parse_version_key("R3") == (("rev", (3,)),)
    assert parse_version_key("최종") == ()
    assert parse_version_key(None) == ()
    a, b = VersionInfo(family="f", label="v2.10"), VersionInfo(family="f", label="v2.9")
    assert (compare_versions(a, b), compare_versions(b, a), compare_versions(a, a)) == (
        1,
        -1,
        0,
    )
    assert compare_versions(VersionInfo(label="v1"), VersionInfo(label="R1")) is None
