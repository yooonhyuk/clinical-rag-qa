"""Layer 2: PS3.15 Annex E (Table E.1-1) de-identification checks + site policy."""

import dataclasses
import json
import re

import pytest
from generate_sample_dicom import (
    build_dataset,
    build_enhanced_mr,
    build_phi_nested_private,
    build_pseudonymized_mr,
    declare_deidentified,
)
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence

from app.config import Settings
from app.services.dicom_deid import check_deid, resolve_action
from app.services.dicom_rules import load_rules


@pytest.fixture(scope="module")
def rules():
    return load_rules(Settings(_env_file=None, database_url="x://unused").rules_path)


def run(ds, rules, policy=None):
    from app.services.dicom_conformance import check_conformance

    iod = check_conformance(ds, rules.conformance).iod
    types = iod.spec.attribute_types() if iod.spec else {}
    return check_deid(ds, rules.deid, policy or rules.policy, types)


def by_code(result) -> dict[str, list]:
    out: dict[str, list] = {}
    for f in result["findings"]:
        out.setdefault(f.code, []).append(f)
    return out


@pytest.mark.parametrize(
    ("action", "iod_type", "expected"),
    [
        ("X/Z", "2", "Z"),
        ("X/Z", "3", "X"),
        ("X/D", "1", "D"),
        ("X/D", "3", "X"),
        ("Z/D", "1", "D"),
        ("Z/D", "2", "Z"),
        ("X/Z/D", "1", "D"),
        ("X/Z/D", "2", "Z"),
        ("X/Z/D", "3", "X"),
        ("X/Z/U*", "1", "U*"),
        ("X/Z/U*", "3", "X"),
        ("X/Z", None, "Z"),  # unknown Type -> most lenient alternative
        ("X", "1", "X"),
    ],
)
def test_resolve_combined_actions(action, iod_type, expected) -> None:
    assert resolve_action(action, iod_type)[0] == expected


def test_nested_phi_and_private_tags_are_found_without_values(rules) -> None:
    result = run(build_phi_nested_private(), rules)
    codes = by_code(result)
    private = codes["DEID-PRIVATE-PRESENT"][0]
    assert private.severity == "error" and private.count == 3
    assert "0011" in private.message and "Retain Safe Private" in private.message
    removed = {f.attribute for f in codes["DEID-X-PRESENT"]}
    assert {"RequestAttributesSequence", "OtherPatientIDsSequence"} <= removed
    dumped = json.dumps([f.as_dict() for f in result["findings"]], ensure_ascii=False)
    for fake in ("FAKE^PRIVATE^NAME", "FAKE-MRN-0099", "FAKE NESTED", "FAKE^DOCTOR", "FAKE-OTHER"):
        assert fake not in dumped


def test_nested_attributes_are_walked_with_keyword_paths(rules) -> None:
    ds = build_enhanced_mr()
    ds.SharedFunctionalGroupsSequence[0].PatientName = "FAKE^NESTED"  # not in E.1-1 -> descend
    item = Dataset()
    item.ReferencedSOPInstanceUID = "1.2.3.4"
    item.ReferencedSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"
    ds.ReferencedImageSequence = Sequence([item])  # X/Z/U*: kept, contained UIDs replaced
    codes = by_code(run(ds, rules))
    nested_name = next(f for f in codes["DEID-Z-NOT-EMPTY"] if f.attribute == "PatientName")
    assert nested_name.paths == ["SharedFunctionalGroupsSequence[0].PatientName"]
    assert "중첩" in nested_name.message
    uid = next(f for f in codes["DEID-U-PRESENT"] if f.attribute == "ReferencedSOPInstanceUID")
    assert uid.paths == ["ReferencedImageSequence[0].ReferencedSOPInstanceUID"]


def test_pseudonymized_and_declared_file_is_compliant(rules) -> None:
    result = run(build_pseudonymized_mr(), rules)
    severities = {f.severity for f in result["findings"]}
    assert severities == {"info"}
    claim = result["claimedDeid"]
    assert claim["patientIdentityRemoved"] == "YES"
    assert claim["basicProfileClaimed"] is True
    assert claim["methodCodes"][0]["meaning"] == "Basic Application Confidentiality Profile"


def test_pseudonym_policy_mismatch_is_an_error(rules) -> None:
    result = run(build_dataset("MR", {"PatientID": "12345678"}), rules)
    mismatch = by_code(result)["DEID-PSEUDONYM-MISMATCH"]
    assert [f.attribute for f in mismatch] == ["PatientID"]
    assert "12345678" not in mismatch[0].message


def test_custom_pseudonym_pattern_from_policy(rules) -> None:
    policy = dataclasses.replace(
        rules.policy,
        pseudonyms={
            "PatientID": dataclasses.replace(
                rules.policy.pseudonyms["PatientID"], pattern=re.compile(r"^SUBJ[0-9]{4}$")
            )
        },
    )
    ok = run(build_dataset("MR", {"PatientID": "SUBJ0001"}), rules, policy)
    assert "DEID-PSEUDONYM-OK" in by_code(ok)


def test_claimed_options_change_the_evaluation(rules) -> None:
    ds = build_dataset("CT", {"PatientID": "DEMO-001-0001", "StudyDescription": "FAKE"})
    assert "DEID-X-PRESENT" in by_code(run(ds, rules))
    declare_deidentified(
        ds,
        ("113100", "Basic Application Confidentiality Profile"),
        ("113105", "Clean Descriptors Option"),
    )
    result = run(ds, rules)
    clean = [f for f in by_code(result)["DEID-C-VERIFY"] if f.attribute == "StudyDescription"]
    assert clean and clean[0].severity == "warning" and "Clean Descriptors" in clean[0].action
    assert result["optionsApplied"] == [
        {"key": "clean_descriptors", "name": "Clean Descriptors Option", "origin": "claimed"}
    ]
    no_honor = dataclasses.replace(rules.policy, honor_claimed_options=False)
    assert "DEID-X-PRESENT" in by_code(run(ds, rules, no_honor))


def test_retain_longitudinal_modified_dates_policy(rules) -> None:
    ds = build_dataset("CT", {"PatientID": "DEMO-001-0001", "StudyDate": "20260101"})
    basic = by_code(run(ds, rules))
    assert any(f.attribute == "StudyDate" for f in basic["DEID-Z-NOT-EMPTY"])
    assert "옵션 미적용" in basic["DEID-DATES"][0].message
    policy = dataclasses.replace(rules.policy, options=("retain_longitudinal_modified_dates",))
    shifted = by_code(run(ds, rules, policy))
    assert any(f.attribute == "StudyDate" for f in shifted["DEID-C-VERIFY"])
    assert "Modified Dates" in shifted["DEID-DATES"][0].message


def test_yes_without_method_is_incomplete(rules) -> None:
    ds = build_dataset("CT", {"PatientIdentityRemoved": "YES"})
    assert "DEID-CLAIM-INCOMPLETE" in by_code(run(ds, rules))


def test_unknown_method_codes_are_counted_not_shown(rules) -> None:
    ds = build_dataset("CT")
    code = Dataset()
    code.CodeValue = "SECRET-LOCAL-CODE"
    code.CodingSchemeDesignator = "99LOCAL"
    code.CodeMeaning = "secret meaning"
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethodCodeSequence = Sequence([code])
    result = run(ds, rules)
    assert result["claimedDeid"]["unknownMethodCodes"] == 1
    assert "SECRET-LOCAL-CODE" not in json.dumps(result["claimedDeid"])


def test_burned_in_annotation_and_pixel_risk(rules) -> None:
    burned = by_code(run(build_dataset("US", {"BurnedInAnnotation": "YES"}), rules))
    assert burned["DEID-BURNED-IN"][0].severity == "error"
    risk = by_code(run(build_dataset("US"), rules))
    assert risk["DEID-PIXEL-RISK"][0].severity == "warning"
    assert "DEID-PIXEL-RISK" not in by_code(run(build_dataset("CT"), rules))
    clean = by_code(run(build_dataset("US", {"BurnedInAnnotation": "NO"}), rules))
    assert "DEID-PIXEL-RISK" not in clean and "DEID-BURNED-IN" not in clean


def test_retain_safe_private_option_downgrades_private_finding(rules) -> None:
    policy = dataclasses.replace(rules.policy, options=("retain_safe_private",))
    private = by_code(run(build_phi_nested_private(), rules, policy))["DEID-PRIVATE-PRESENT"][0]
    assert private.severity == "info"


def test_uids_are_info_only(rules) -> None:
    uids = by_code(run(build_dataset("CT"), rules))["DEID-U-PRESENT"]
    assert {f.attribute for f in uids} >= {"StudyInstanceUID", "SeriesInstanceUID"}
    assert {f.severity for f in uids} == {"info"}


def test_every_finding_cites_a_source(rules) -> None:
    result = run(build_phi_nested_private(), rules)
    assert all(f.source for f in result["findings"])
    assert all("PS3." in f.source or "policy" in f.source for f in result["findings"])
