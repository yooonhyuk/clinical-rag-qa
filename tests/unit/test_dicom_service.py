import json
from pathlib import Path
from unittest.mock import patch

import pydicom
import pytest
from generate_sample_dicom import build_dataset, build_pseudonymized_mr

from app.config import Settings
from app.services.dicom_rules import load_rules
from app.services.dicom_service import (
    DISCLAIMER,
    DicomReadError,
    DicomService,
    build_llm_payload,
    evaluate,
    read_dataset,
)
from app.services.llm_types import LLMError
from tests.fakes import FakeOllama


@pytest.fixture(scope="module")
def rules():
    return load_rules(Settings(_env_file=None, database_url="x://unused").rules_path)


def _write(tmp_path: Path, name: str, ds) -> Path:
    path = tmp_path / name
    ds.save_as(path, enforce_file_format=True)
    return path


def codes(result: dict, layer: str) -> set[str]:
    return {f["code"] for f in result[layer]["findings"]}


def test_rules_are_generated_from_the_cited_standard_editions(rules) -> None:
    assert rules.conformance.edition == "2026d"
    assert rules.deid.edition == "PS3.15 2026d"
    assert "dicom.nema.org" in rules.deid.source_url
    assert "PS3.15 2026d" in rules.source and "PS3.3 2026d" in rules.source
    # Table E.1-1 sanity: well-known rows and actions
    assert rules.deid.by_tag[0x00100010].basic == "Z"  # Patient's Name
    assert rules.deid.by_tag[0x00081030].basic == "X"  # Study Description
    assert rules.deid.by_tag[0x0020000D].basic == "U"  # Study Instance UID
    assert rules.deid.private.basic == "X"


def test_conformant_pseudonymized_mr_has_no_errors(tmp_path, rules) -> None:
    result = evaluate(read_dataset(_write(tmp_path, "mr.dcm", build_pseudonymized_mr())), rules)
    assert result["layer1"]["iod"]["name"] == "MR Image IOD"
    assert result["counts"]["layer1"]["error"] == 0
    assert result["counts"]["layer2"]["error"] == 0
    assert result["counts"]["layer2"]["warning"] == 0
    assert "DEID-PSEUDONYM-OK" in codes(result, "layer2")
    assert result["layer2"]["claimedDeid"]["patientIdentityRemoved"] == "YES"


def test_ct_with_fake_phi_reports_profile_actions(tmp_path, rules) -> None:
    ds = build_dataset(
        "CT",
        {"PatientName": "TEST^PATIENT", "StudyDate": "20260101", "StudyDescription": "DEMO"},
    )
    result = evaluate(read_dataset(_write(tmp_path, "ct.dcm", ds)), rules)
    by_attr = {f["attribute"]: f for f in result["layer2"]["findings"] if f.get("attribute")}
    assert by_attr["PatientName"]["code"] == "DEID-PSEUDONYM-MISMATCH"
    assert by_attr["StudyDescription"]["code"] == "DEID-X-PRESENT"
    assert by_attr["StudyDescription"]["source"] == "PS3.15 2026d Table E.1-1"
    assert by_attr["StudyDate"]["code"] == "DEID-Z-NOT-EMPTY"
    assert "TEST^PATIENT" not in json.dumps(result)


def test_mr_missing_tags_are_reported_with_type_semantics(tmp_path, rules) -> None:
    ds = build_dataset("MR", omit=("SliceThickness", "ImageOrientationPatient", "Rows"))
    result = evaluate(read_dataset(_write(tmp_path, "mr.dcm", ds)), rules)
    found = {(f["code"], f.get("attribute")) for f in result["layer1"]["findings"]}
    assert ("L1-TYPE1-ABSENT", "Rows") in found
    assert ("L1-TYPE1-ABSENT", "ImageOrientationPatient") in found
    assert ("L1-TYPE2-ABSENT", "SliceThickness") in found  # Image Plane: Slice Thickness Type 2
    plane = next(f for f in result["layer1"]["findings"] if f.get("attribute") == "SliceThickness")
    assert plane["source"] == "PS3.3 C.7.6.2 Image Plane Module (Table C.7-10)"


def test_pixel_data_is_never_loaded(tmp_path) -> None:
    path = _write(tmp_path, "ct.dcm", build_dataset("CT"))
    with patch("app.services.dicom_service.pydicom.dcmread", wraps=pydicom.dcmread) as spy:
        read_dataset(path)
    assert spy.call_args.kwargs["stop_before_pixels"] is True


def test_non_dicom_file_raises(tmp_path) -> None:
    path = tmp_path / "fake.dcm"
    path.write_bytes(b"this is a jpg pretending to be dicom")
    with pytest.raises(DicomReadError):
        read_dataset(path)


async def test_service_sends_only_codes_to_llm_and_appends_disclaimer(sample_dicom, rules) -> None:
    llm = FakeOllama(text="CT 검사 데이터로 보입니다.")
    analysis = await DicomService(llm, rules, system_prompt="s").analyze(sample_dicom)
    assert analysis.summary_source == "llm"
    assert analysis.summary.endswith(DISCLAIMER)
    prompt = llm.generate_calls[0]
    assert "TEST^PATIENT" not in prompt and "DEMO CT CHEST" not in prompt
    assert "DEID-X-PRESENT" in prompt  # finding codes are passed ...
    payload = json.dumps(build_llm_payload(analysis))
    assert '"message"' not in payload and '"paths"' not in payload  # ... but no messages/paths


async def test_service_falls_back_to_template_when_llm_fails(sample_dicom, rules) -> None:
    class Broken(FakeOllama):
        async def generate(self, prompt, *, system=None):
            raise LLMError("down", error_type="OLLAMA_UNAVAILABLE")

    analysis = await DicomService(Broken(), rules, system_prompt="s").analyze(sample_dicom)
    assert analysis.summary_source == "template"
    assert "CT Image IOD" in analysis.summary
    assert "비식별화(Layer 2" in analysis.summary
    assert DISCLAIMER in analysis.summary


async def test_service_without_llm_uses_template(sample_dicom, rules) -> None:
    analysis = await DicomService(None, rules, system_prompt="s").analyze(sample_dicom)
    assert analysis.summary_source == "template"


async def test_backward_compatible_fields(sample_dicom, rules) -> None:
    analysis = await DicomService(None, rules, system_prompt="s").analyze(sample_dicom)
    assert "PatientName exists" in analysis.privacy_warnings
    assert analysis.missing_required_tags == []
    assert {"StudyInstanceUID", "Modality", "PixelSpacing"} <= set(analysis.passed)
    stored = analysis.stored_tags()
    assert set(stored) == {"tagSummary", "layer1", "layer2", "quantitationReadiness", "counts"}
