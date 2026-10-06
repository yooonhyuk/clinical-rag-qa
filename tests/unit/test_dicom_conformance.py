"""Layer 1: PS3.3 IOD / module Types, enhanced functional groups, PS3.5 value formats, SUV."""

import pytest
from generate_sample_dicom import SOP_CLASS, build_dataset, build_enhanced_mr, build_malformed
from pydicom.dataset import Dataset

from app.config import Settings
from app.services.dicom_conformance import (
    check_conformance,
    check_quantitation_readiness,
    da_problem,
    tm_problem,
    ui_problem,
)
from app.services.dicom_rules import load_rules
from app.services.dicom_service import evaluate


@pytest.fixture(scope="module")
def conf():
    return load_rules(Settings(_env_file=None, database_url="x://unused").rules_path).conformance


def found(result) -> set[tuple[str, str | None]]:
    return {(f.code, f.attribute) for f in result.findings}


@pytest.mark.parametrize(
    ("sop_class", "iod"),
    [
        ("1.2.840.10008.5.1.4.1.1.2", "CT Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.2.1", "Enhanced CT Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.4", "MR Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.4.1", "Enhanced MR Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.128", "Positron Emission Tomography Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.130", "Enhanced PET Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.6.1", "Ultrasound Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.3.1", "Ultrasound Multi-frame Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.7", "Secondary Capture Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.1", "Computed Radiography Image IOD"),
        ("1.2.840.10008.5.1.4.1.1.1.1", "Digital X-Ray Image IOD"),
    ],
)
def test_iod_is_determined_from_sop_class(conf, sop_class, iod) -> None:
    ds = Dataset()
    ds.SOPClassUID = sop_class
    result = check_conformance(ds, conf)
    assert result.iod.spec is not None and result.iod.spec.name == iod
    assert result.iod.determined_by == "SOPClassUID"


def test_iod_falls_back_to_modality_and_reports_unknown(conf) -> None:
    ds = Dataset()
    ds.Modality = "CT"
    assert check_conformance(ds, conf).iod.determined_by == "Modality"
    ds.Modality = "ZZ"
    result = check_conformance(ds, conf)
    assert result.iod.spec is None
    assert ("L1-IOD-UNKNOWN", None) in found(result)


def test_classic_ct_fixture_is_conformant(conf) -> None:
    result = check_conformance(build_dataset("CT"), conf)
    assert [f for f in result.findings if f.severity == "error"] == []


def test_type1_empty_vs_absent_and_type2_empty_is_fine(conf) -> None:
    ds = build_dataset("CT", {"Rows": None, "PatientName": ""}, omit=("Columns", "StudyID"))
    result = found(check_conformance(ds, conf))
    assert ("L1-TYPE1-EMPTY", "Rows") in result
    assert ("L1-TYPE1-ABSENT", "Columns") in result
    assert ("L1-TYPE2-ABSENT", "StudyID") in result
    assert not any(attr == "PatientName" for _, attr in result)  # Type 2, empty is allowed


def test_strictest_type_wins_across_modules(conf) -> None:
    # Image Type is Type 3 in General Image but Type 1 in CT Image.
    result = found(check_conformance(build_dataset("CT", omit=("ImageType",)), conf))
    assert ("L1-TYPE1-ABSENT", "ImageType") in result


def test_conditional_attributes_are_reported_as_not_evaluated(conf) -> None:
    result = check_conformance(build_dataset("CT"), conf)
    conditional = [f for f in result.findings if f.code == "L1-CONDITIONAL-NOT-EVALUATED"]
    assert conditional and all(f.severity == "info" for f in conditional)
    assert any("DeidentificationMethod" in f.details["attributes"] for f in conditional)
    assert not any("PixelData" in f.details["attributes"] for f in conditional)


def test_enhanced_mr_reads_spatial_info_from_functional_groups(conf) -> None:
    result = check_conformance(build_enhanced_mr(), conf)
    attrs = {f.attribute for f in result.findings if f.severity == "error"}
    # No false "missing" for top-level spatial attributes or the spatial macros.
    assert not attrs & {
        "PixelSpacing",
        "SliceThickness",
        "ImagePositionPatient",
        "ImageOrientationPatient",
        "PixelMeasuresSequence",
        "PlanePositionSequence",
        "PlaneOrientationSequence",
        "FrameContentSequence",
    }


def test_enhanced_mr_without_shared_macros_reports_fg_missing(conf) -> None:
    result = check_conformance(build_enhanced_mr(shared_spatial=False), conf)
    missing = {f.attribute: f for f in result.findings if f.code == "L1-FG-MISSING"}
    assert "PixelMeasuresSequence" in missing
    assert "PlaneOrientationSequence" in missing
    assert "PlanePositionSequence" not in missing  # present in every per-frame item
    assert missing["PixelMeasuresSequence"].details == {"framesMissing": 2, "frames": 2}
    assert missing["PixelMeasuresSequence"].source.startswith("PS3.3 C.7.6.16.2.1 Pixel Measures")


def test_frame_content_must_not_be_shared(conf) -> None:
    ds = build_enhanced_mr()
    content = Dataset()
    content.FrameAcquisitionNumber = 1
    ds.SharedFunctionalGroupsSequence[0].FrameContentSequence = [content]
    assert ("L1-FG-SHARED-NOT-ALLOWED", "FrameContentSequence") in found(
        check_conformance(ds, conf)
    )


def test_enhanced_summary_takes_spatial_values_from_functional_groups(conf) -> None:
    rules = load_rules(Settings(_env_file=None, database_url="x://unused").rules_path)
    summary = evaluate(build_enhanced_mr(), rules)["tag_summary"]
    assert summary["PixelSpacing"] == [0.5, 0.5]
    assert summary["ImagePositionPatient"] == [0.0, 0.0, 0.0]
    assert summary["spatialSource"].startswith("Shared/PerFrame")


def test_malformed_values_are_detected(conf) -> None:
    result = found(check_conformance(build_malformed(), conf))
    assert ("L1-VR-UI", "StudyInstanceUID") in result
    assert ("L1-VR-UI", "SeriesInstanceUID") in result
    assert ("L1-VR-DA", "StudyDate") in result
    assert ("L1-VR-TM", "StudyTime") in result
    assert ("L1-MODALITY-TERM", "Modality") in result


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ("1.2.840.10008.5.1.4.1.1.2", True),
        ("1.2.0.3", True),
        ("1.2.03", False),
        ("1..2", False),
        ("1.2.a", False),
        ("1." + "2" * 64, False),
    ],
)
def test_ui_format(value, ok) -> None:
    assert (ui_problem(value) is None) is ok


def test_da_and_tm_formats() -> None:
    assert da_problem("20260228") is None
    assert da_problem("20260230") is not None
    assert da_problem("2026-02-28") is not None
    assert tm_problem("235959.123456") is None
    assert tm_problem("0930") is None
    assert tm_problem("2400") is not None


def test_body_part_must_be_a_defined_term(conf) -> None:
    ds = build_dataset("CT", {"BodyPartExamined": "HONG GILDONG"})
    assert ("L1-BODYPART-TERM", "BodyPartExamined") in found(check_conformance(ds, conf))
    assert ("L1-BODYPART-TERM", "BodyPartExamined") not in found(
        check_conformance(build_dataset("CT", {"BodyPartExamined": "CHEST"}), conf)
    )


def test_pet_quantitation_readiness(conf) -> None:
    ready = build_dataset("PT")
    iod = check_conformance(ready, conf).iod
    assert check_quantitation_readiness(ready, iod)["ready"] is True

    not_ready = build_dataset(
        "PT", omit=("PatientWeight", "RadiopharmaceuticalInformationSequence")
    )
    result = check_quantitation_readiness(not_ready, check_conformance(not_ready, conf).iod)
    assert result["applicable"] is True and result["ready"] is False
    missing = {f["attribute"] for f in result["findings"]}
    assert missing == {"PatientWeight", "RadiopharmaceuticalInformationSequence"}
    assert all(f["severity"] == "warning" for f in result["findings"])

    no_dose = build_dataset("PT", {"Units": "CNTS"})
    del no_dose.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose
    result = check_quantitation_readiness(no_dose, check_conformance(no_dose, conf).iod)
    attrs = {(f["code"], f["attribute"]) for f in result["findings"]}
    assert attrs == {("QR-MISSING", "RadionuclideTotalDose"), ("QR-UNITS", "Units")}


def test_quantitation_not_applicable_for_ct(conf) -> None:
    ds = build_dataset("CT")
    assert check_quantitation_readiness(ds, check_conformance(ds, conf).iod)["applicable"] is False


def test_sop_class_constants_cover_fixtures() -> None:
    assert set(SOP_CLASS) >= {"CT", "MR", "PT", "US", "ENHANCED_MR"}
