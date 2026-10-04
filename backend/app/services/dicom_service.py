"""DICOM tag analyzer: metadata only, never pixel data, never image reading.

pydicom.dcmread(stop_before_pixels=True) in a worker thread
-> normalize key tags (privacy tags are reduced to "exists", raw PHI never leaves this module)
-> rule checks (required / privacy YAML)
-> LLM explanation (falls back to a deterministic template if Ollama is unavailable)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pydicom
from pydicom.errors import InvalidDicomError
from pydicom.multival import MultiValue

from app.services.dicom_rules import DicomRules
from app.services.document_loader import sha256_of
from app.services.llm_types import GenerationClient, LLMError
from app.services.prompt_builder import build_dicom_prompt

logger = logging.getLogger(__name__)

DISCLAIMER = "이 설명은 DICOM 태그 기반 설명이며, 영상 판독은 수행하지 않습니다."

# Tags extracted for the summary (plan §14.4). Order is preserved in the output.
KEY_TAGS: tuple[str, ...] = (
    "Modality",
    "Manufacturer",
    "BodyPartExamined",
    "StudyInstanceUID",
    "StudyDate",
    "StudyDescription",
    "SeriesInstanceUID",
    "SeriesDescription",
    "SeriesNumber",
    "SOPInstanceUID",
    "Rows",
    "Columns",
    "PixelSpacing",
    "SliceThickness",
    "ImagePositionPatient",
    "ImageOrientationPatient",
    "PatientID",
    "PatientName",
    "PatientBirthDate",
    "PatientSex",
    "AccessionNumber",
)
_IDENTIFIER_TAGS = {"StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID"}
EXISTS = "exists"


class DicomReadError(Exception):
    error_type = "DICOM_READ_FAILED"


@dataclass(slots=True)
class DicomAnalysis:
    file_name: str
    file_path: str
    checksum: str
    tag_summary: dict[str, Any]
    privacy_warnings: list[str]
    missing_required_tags: list[str]
    passed: list[str]
    warnings: list[str]
    rule_source: str
    summary: str = ""
    summary_source: str = "llm"  # "llm" | "template"
    extra: dict[str, Any] = field(default_factory=dict)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, MultiValue | list | tuple):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, bool):
        return value
    # DSfloat / IS are float / int subclasses: convert to plain Python types for JSON.
    if isinstance(value, float):
        return float(value)
    if isinstance(value, int):
        return int(value)
    return str(value)


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, MultiValue | list | tuple):
        return len(value) > 0
    return str(value).strip() != ""


def read_dicom_tags(path: Path) -> dict[str, Any]:
    """Read the key tags of a DICOM file without loading pixel data. Blocking."""
    try:
        ds = pydicom.dcmread(path, stop_before_pixels=True)
    except (InvalidDicomError, OSError, ValueError) as exc:
        raise DicomReadError(f"Cannot read DICOM file: {exc}") from exc
    raw: dict[str, Any] = {}
    for keyword in KEY_TAGS:
        value = ds.get(keyword)
        if _is_present(value):
            raw[keyword] = _to_jsonable(value)
    # Extra privacy-relevant tags that are not part of the summary but must be checked.
    for keyword in (
        "InstitutionName",
        "ReferringPhysicianName",
        "PerformingPhysicianName",
        "OperatorsName",
    ):
        value = ds.get(keyword)
        if _is_present(value):
            raw[keyword] = _to_jsonable(value)
    return raw


def evaluate(raw: dict[str, Any], rules: DicomRules) -> dict[str, Any]:
    """Pure rule evaluation. `raw` maps tag keyword -> value for tags that are present."""
    privacy_names = {r.name for r in rules.privacy}
    tag_summary: dict[str, Any] = {}
    for keyword in KEY_TAGS:
        if keyword not in raw:
            continue
        if keyword in _IDENTIFIER_TAGS or keyword in privacy_names:
            tag_summary[keyword] = EXISTS  # never echo identifiers / PHI values
        else:
            tag_summary[keyword] = raw[keyword]

    required = rules.required_for(raw.get("Modality"))
    present_privacy = [r for r in rules.privacy if r.name in raw]
    return {
        "tag_summary": tag_summary,
        "privacy_warnings": [f"{r.name} exists" for r in present_privacy],
        "missing_required_tags": [t for t in required if t not in raw],
        "passed": [t for t in required if t in raw],
        "warnings": [r.message for r in present_privacy],
    }


def template_summary(analysis: DicomAnalysis) -> str:
    tags = analysis.tag_summary
    lines: list[str] = []
    modality = tags.get("Modality")
    lines.append(
        f"이 파일은 Modality 태그 기준으로 {modality} 검사 데이터로 보입니다."
        if modality
        else "Modality 태그가 없어 검사 종류를 확인할 수 없습니다."
    )
    ids = [t for t in ("StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID") if t in tags]
    if len(ids) == 3:
        lines.append("Study/Series/SOP Instance UID가 모두 존재하므로 단위별 추적이 가능합니다.")
    else:
        lines.append(f"식별자 중 {', '.join(ids) or '없음'}만 존재합니다.")
    if "Rows" in tags and "Columns" in tags:
        lines.append(f"이미지 크기는 {tags['Rows']} x {tags['Columns']}입니다.")
    spatial = [t for t in ("PixelSpacing", "SliceThickness") if t in tags]
    if spatial:
        lines.append(f"{', '.join(spatial)} 값이 존재해 기본 공간 정보 확인이 가능합니다.")
    if analysis.missing_required_tags:
        lines.append(f"누락된 필수 태그: {', '.join(analysis.missing_required_tags)}.")
    if analysis.privacy_warnings:
        names = ", ".join(w.removesuffix(" exists") for w in analysis.privacy_warnings)
        lines.append(f"개인정보 가능 태그({names})가 있어 비식별화 확인이 필요합니다.")
    return " ".join(lines)


class DicomService:
    def __init__(
        self, llm: GenerationClient | None, rules: DicomRules, *, system_prompt: str
    ) -> None:
        """`llm=None` => template-only explanations (used when generation is external)."""
        self._llm = llm
        self._rules = rules
        self._system_prompt = system_prompt

    async def analyze(self, path: Path, *, explain: bool = True) -> DicomAnalysis:
        raw = await asyncio.to_thread(read_dicom_tags, path)
        checksum = await asyncio.to_thread(sha256_of, path)
        result = evaluate(raw, self._rules)
        analysis = DicomAnalysis(
            file_name=path.name,
            file_path=str(path),
            checksum=checksum,
            rule_source=self._rules.source,
            **result,
        )
        analysis.summary, analysis.summary_source = await self._explain(analysis, explain)
        return analysis

    async def _explain(self, analysis: DicomAnalysis, use_llm: bool) -> tuple[str, str]:
        if use_llm and self._llm is not None:
            payload = {
                "tagSummary": analysis.tag_summary,
                "missingRequiredTags": analysis.missing_required_tags,
                "privacyWarnings": analysis.privacy_warnings,
                "passed": analysis.passed,
            }
            try:
                result = await self._llm.generate(
                    build_dicom_prompt(payload), system=self._system_prompt
                )
                if text := result.text:
                    return f"{text}\n\n{DISCLAIMER}", "llm"
            except LLMError as exc:
                logger.warning("DICOM explanation falls back to template: %s", exc)
        return f"{template_summary(analysis)}\n\n{DISCLAIMER}", "template"
