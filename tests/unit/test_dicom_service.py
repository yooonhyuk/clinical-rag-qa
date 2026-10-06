from pathlib import Path
from unittest.mock import patch

import pydicom
import pytest
from generate_sample_dicom import build_dataset
from pydicom.dataset import Dataset

from app.config import Settings
from app.services.dicom_rules import load_rules
from app.services.dicom_service import (
    DISCLAIMER,
    DicomReadError,
    DicomService,
    evaluate,
    read_dataset,
)
from app.services.llm_types import LLMError
from tests.fakes import FakeOllama


@pytest.fixture
def rules(settings: Settings):
    return load_rules(settings.rules_path)


def _write(tmp_path: Path, name: str, modality: str, tags: dict, omit: tuple = ()) -> Path:
    path = tmp_path / name
    build_dataset(modality, tags, omit=omit).save_as(path, enforce_file_format=True)
    return path


def test_ct_with_fake_phi_yields_privacy_warnings_and_passes_required(tmp_path, rules) -> None:
    path = _write(
        tmp_path, "ct.dcm", "CT", {"PatientName": "TEST^PATIENT", "StudyDate": "20260101"}
    )
    result = evaluate(read_dataset(path), rules)
    assert result["missing_required_tags"] == []
    assert "PatientName exists" in result["privacy_warnings"]
    assert "StudyDate exists" in result["privacy_warnings"]
    assert set(result["passed"]) >= {"StudyInstanceUID", "Modality", "PixelSpacing"}
    assert any("비식별화" in w for w in result["warnings"])


def test_phi_and_uid_values_are_never_echoed(tmp_path, rules) -> None:
    path = _write(tmp_path, "ct.dcm", "CT", {"PatientName": "TEST^PATIENT", "PatientID": "FAKE-1"})
    summary = evaluate(read_dataset(path), rules)["tag_summary"]
    assert summary["PatientName"] == "exists"
    assert summary["PatientID"] == "exists"
    assert summary["StudyInstanceUID"] == "exists"
    assert "TEST^PATIENT" not in str(summary)
    assert summary["Rows"] == 64 and summary["PixelSpacing"] == [0.7, 0.7]


def test_mr_missing_tags_are_reported(tmp_path, rules) -> None:
    path = _write(
        tmp_path, "mr.dcm", "MR", {}, omit=("SliceThickness", "ImageOrientationPatient", "Rows")
    )
    missing = evaluate(read_dataset(path), rules)["missing_required_tags"]
    assert missing == ["Rows", "SliceThickness", "ImageOrientationPatient"]


def test_modality_specific_rules_do_not_apply_to_cr(rules) -> None:
    ds = Dataset()
    ds.StudyInstanceUID = "1.2.3"
    ds.SeriesInstanceUID = "1.2.4"
    ds.SOPInstanceUID = "1.2.5"
    ds.Modality = "CR"
    ds.Rows = 10
    ds.Columns = 10
    assert evaluate(ds, rules)["missing_required_tags"] == []


def test_pixel_data_is_never_loaded(tmp_path) -> None:
    path = _write(tmp_path, "ct.dcm", "CT", {})
    with patch("app.services.dicom_service.pydicom.dcmread", wraps=pydicom.dcmread) as spy:
        read_dataset(path)
    assert spy.call_args.kwargs["stop_before_pixels"] is True


def test_non_dicom_file_raises(tmp_path) -> None:
    path = tmp_path / "fake.dcm"
    path.write_bytes(b"this is a jpg pretending to be dicom")
    with pytest.raises(DicomReadError):
        read_dataset(path)


async def test_service_uses_llm_and_appends_disclaimer(sample_dicom, rules) -> None:
    llm = FakeOllama(text="CT 검사 데이터로 보입니다.")
    analysis = await DicomService(llm, rules, system_prompt="s").analyze(sample_dicom)
    assert analysis.summary_source == "llm"
    assert analysis.summary.endswith(DISCLAIMER)
    # The LLM prompt contains no PHI values, only "exists" markers.
    assert "TEST^PATIENT" not in llm.generate_calls[0]


async def test_service_falls_back_to_template_when_llm_fails(sample_dicom, rules) -> None:
    class Broken(FakeOllama):
        async def generate(self, prompt, *, system=None):
            raise LLMError("down", error_type="OLLAMA_UNAVAILABLE")

    analysis = await DicomService(Broken(), rules, system_prompt="s").analyze(sample_dicom)
    assert analysis.summary_source == "template"
    assert "CT 검사 데이터" in analysis.summary
    assert DISCLAIMER in analysis.summary


async def test_service_without_llm_uses_template(sample_dicom, rules) -> None:
    analysis = await DicomService(None, rules, system_prompt="s").analyze(sample_dicom)
    assert analysis.summary_source == "template"
