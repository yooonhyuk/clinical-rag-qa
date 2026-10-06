"""Regression tests for issue #2: free-text DICOM values must never leave the analyzer.

PHI-like strings are injected into free-text attributes, private tags, nested sequences and even
into allowlisted coded attributes. None of them may appear in the analysis result, the HTTP
response, the persisted DB row, or any prompt handed to a generation client (ollama or anthropic).
"""

import json
from pathlib import Path

import httpx
import pytest
from generate_sample_dicom import build_dataset
from pydantic import SecretStr
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence

from app.config import Settings
from app.container import build_container
from app.main import create_app
from app.models import DicomFile
from app.services.dicom_rules import load_rules
from app.services.dicom_safe import SUPPRESSED
from app.services.dicom_service import DicomService, evaluate, read_dataset
from tests.fakes import FakeOllama, FakeSessionFactory

PHI_MARKERS = (
    "HONG^GILDONG",
    "MRN-77831904",
    "SECRET-STUDY-DESC",
    "SECRET-SERIES-DESC",
    "SECRET-PRIVATE",
    "SECRET-NESTED",
    "SECRET-CODE-MEANING",
    "19800101",
    "SEOUL NATIONAL",
)


def write_phi_dataset(path: Path, modality: str = "CT") -> Path:
    ds = build_dataset(
        modality,
        {
            "PatientName": "HONG^GILDONG",
            "PatientID": "MRN-77831904",
            "PatientBirthDate": "19800101",
            "StudyDescription": "SECRET-STUDY-DESC HONG^GILDONG",
            "SeriesDescription": "SECRET-SERIES-DESC MRN-77831904",
            "InstitutionName": "SEOUL NATIONAL HOSPITAL",
            "Manufacturer": "SECRET-PRIVATE vendor note",
            # free text typed into an allowlisted coded attribute must be suppressed too
            "BodyPartExamined": "hong gildong 19800101",
        },
    )
    block = ds.private_block(0x0011, "SECRET-PRIVATE CREATOR", create=True)
    block.add_new(0x01, "LO", "SECRET-PRIVATE HONG^GILDONG")
    request = Dataset()
    request.RequestedProcedureDescription = "SECRET-NESTED MRN-77831904"
    code = Dataset()
    code.CodeValue = "X1"
    code.CodingSchemeDesignator = "99LOCAL"
    code.CodeMeaning = "SECRET-CODE-MEANING HONG^GILDONG"
    request.RequestedProcedureCodeSequence = Sequence([code])
    ds.RequestAttributesSequence = Sequence([request])
    ds.save_as(path, enforce_file_format=True)
    return path


def assert_no_phi(text: str) -> None:
    leaked = [marker for marker in PHI_MARKERS if marker in text]
    assert leaked == [], f"PHI-like values leaked: {leaked}"


@pytest.fixture
def phi_file(settings: Settings) -> Path:
    return write_phi_dataset(settings.dicom_path / "phi.dcm")


def test_evaluate_reports_free_text_as_presence_only(phi_file: Path, settings: Settings) -> None:
    result = evaluate(read_dataset(phi_file), load_rules(settings.rules_path))
    summary = result["tag_summary"]
    assert summary["StudyDescription"] == "exists"
    assert summary["SeriesDescription"] == "exists"
    assert summary["Manufacturer"] == "exists"
    assert summary["BodyPartExamined"] == SUPPRESSED
    assert summary["Modality"] == "CT"
    assert summary["SOPClassUID"] == "CT Image Storage"
    assert summary["Rows"] == 64
    assert_no_phi(json.dumps(result, ensure_ascii=False))


class RecordingAnthropic(FakeOllama):
    """Stands in for AnthropicGenerationClient and records every prompt it would send."""

    provider = "anthropic"


@pytest.mark.parametrize("llm_cls", [FakeOllama, RecordingAnthropic])
async def test_service_prompt_and_result_carry_no_phi(phi_file, settings, llm_cls) -> None:
    llm = llm_cls(text="설명")
    service = DicomService(llm, load_rules(settings.rules_path), system_prompt="s")
    analysis = await service.analyze(phi_file)
    for prompt in llm.generate_calls:
        assert_no_phi(prompt)
    if llm.provider == "anthropic":
        # DICOM-derived data never goes to an external provider, whatever the caller passes.
        assert llm.generate_calls == []
        assert analysis.summary_source == "template"
    else:
        assert len(llm.generate_calls) == 1
    assert_no_phi(
        json.dumps([analysis.tag_summary, analysis.summary, analysis.warnings], ensure_ascii=False)
    )


def _mark_corpus(settings: Settings) -> None:
    (settings.raw_docs_path / ".corpus.yaml").write_text(
        "classification: synthetic-sample\n", encoding="utf-8"
    )


@pytest.mark.parametrize("provider", ["ollama", "anthropic"])
async def test_api_response_db_row_and_prompts_carry_no_phi(
    settings: Settings, phi_file: Path, provider: str
) -> None:
    ollama = FakeOllama(text="설명")
    generator: FakeOllama = ollama
    if provider == "anthropic":
        _mark_corpus(settings)
        settings = settings.model_copy(
            update={
                "llm_provider": "anthropic",
                "allow_external_llm": True,
                "anthropic_api_key": SecretStr("sk-ant-test"),
            }
        )
        generator = RecordingAnthropic(text="설명")
    factory = FakeSessionFactory()
    container = build_container(
        settings,
        ollama=ollama,  # type: ignore[arg-type]
        generator=generator,  # type: ignore[arg-type]
        session_factory=factory,  # type: ignore[arg-type]
    )
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(container)), base_url="http://test"
    )
    async with client:
        res = await client.post("/api/dicom/analyze", json={"filePath": phi_file.name})
    assert res.status_code == 200
    assert_no_phi(res.text)
    for llm in {id(c): c for c in (ollama, generator)}.values():
        for prompt in llm.generate_calls:
            assert_no_phi(prompt)
    if provider == "anthropic":
        assert generator.generate_calls == []
    else:
        assert len(ollama.generate_calls) == 1
    rows = [o for o in factory.added if isinstance(o, DicomFile)]
    assert rows
    assert_no_phi(json.dumps([r.tags for r in rows], ensure_ascii=False, default=str))


def test_upper_case_name_in_coded_attribute_is_suppressed(settings: Settings, tmp_path) -> None:
    """CS-shaped free text (passes the CS charset) is caught by the Defined Terms check."""
    path = tmp_path / "bodypart.dcm"
    build_dataset("CT", {"BodyPartExamined": "HONG GILDONG"}).save_as(
        path, enforce_file_format=True
    )
    result = evaluate(read_dataset(path), load_rules(settings.rules_path))
    assert result["tag_summary"]["BodyPartExamined"] == SUPPRESSED
    assert "HONG GILDONG" not in json.dumps(result, ensure_ascii=False)


def test_reading_malformed_values_does_not_log_them(settings: Settings, tmp_path, caplog) -> None:
    import warnings

    from generate_sample_dicom import build_malformed

    path = tmp_path / "bad.dcm"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ds = build_malformed()
        ds.PatientName = "HONG^GILDONG"
        ds.PatientID = "x" * 80  # over-long LO
        ds.save_as(path, enforce_file_format=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = evaluate(read_dataset(path), load_rules(settings.rules_path))
    emitted = " ".join(str(w.message) for w in caught) + caplog.text
    for value in ("1.2.840.01.5", "2026-01-01", "HONG^GILDONG", "x" * 80):
        assert value not in emitted
    assert result["counts"]["layer1"]["error"] >= 4  # still detected by Layer 1
