"""DICOM tag analyzer: metadata only, never pixel data, never image reading.

pydicom.dcmread(stop_before_pixels=True) in a worker thread
-> output allowlist (dicom_safe): only coded/numeric values of allowlisted attributes leave this
   module; everything else (free text, names, dates, UIDs, private tags) is presence only
-> rule checks (required / privacy YAML)
-> LLM explanation (falls back to a deterministic template if Ollama is unavailable)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pydicom
from pydicom.dataset import Dataset
from pydicom.errors import InvalidDicomError

from app.services.dicom_rules import DicomRules
from app.services.dicom_safe import EXISTS, SAFE_VALUE_ATTRIBUTES, presence, safe_summary
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
    "SOPClassUID",
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


def read_dataset(path: Path) -> Dataset:
    """Read the DICOM header without loading pixel data. Blocking.

    The returned Dataset holds raw (possibly PHI) values: it must never leave this module
    except through `dicom_safe` (allowlist) or presence markers.
    """
    try:
        return pydicom.dcmread(path, stop_before_pixels=True)
    except (InvalidDicomError, OSError, ValueError) as exc:
        raise DicomReadError(f"Cannot read DICOM file: {exc}") from exc


def evaluate(ds: Dataset, rules: DicomRules) -> dict[str, Any]:
    """Pure rule evaluation. Only allowlisted values / presence markers are returned."""
    tag_summary = safe_summary(ds, KEY_TAGS)
    modality = tag_summary.get("Modality")
    required = rules.required_for(modality if isinstance(modality, str) else None)
    present_privacy = [r for r in rules.privacy if presence(ds, r.name) == EXISTS]
    return {
        "tag_summary": tag_summary,
        "privacy_warnings": [f"{r.name} exists" for r in present_privacy],
        "missing_required_tags": [t for t in required if presence(ds, t) != EXISTS],
        "passed": [t for t in required if presence(ds, t) == EXISTS],
        "warnings": [r.message for r in present_privacy],
    }


def build_llm_payload(analysis: DicomAnalysis) -> dict[str, Any]:
    """The only DICOM-derived data an LLM may see: allowlisted values, presence, rule names."""
    return {
        "tagSummary": analysis.tag_summary,
        "missingRequiredTags": analysis.missing_required_tags,
        "privacyWarnings": analysis.privacy_warnings,
        "passed": analysis.passed,
    }


def _value(tags: dict[str, Any], keyword: str) -> Any:
    """A real (allowlisted) value, or None for presence markers / suppressed values."""
    value = tags.get(keyword)
    if (
        keyword not in SAFE_VALUE_ATTRIBUTES
        or isinstance(value, str)
        and value.startswith(("exists", "empty", "absent"))
    ):
        return None
    return value


def template_summary(analysis: DicomAnalysis) -> str:
    tags = analysis.tag_summary
    lines: list[str] = []
    modality = _value(tags, "Modality")
    lines.append(
        f"이 파일은 Modality 태그 기준으로 {modality} 검사 데이터로 보입니다."
        if modality
        else "Modality 태그가 없어 검사 종류를 확인할 수 없습니다."
    )
    ids = [
        t
        for t in ("StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID")
        if tags.get(t) == EXISTS
    ]
    if len(ids) == 3:
        lines.append("Study/Series/SOP Instance UID가 모두 존재하므로 단위별 추적이 가능합니다.")
    else:
        lines.append(f"식별자 중 {', '.join(ids) or '없음'}만 존재합니다.")
    rows, columns = _value(tags, "Rows"), _value(tags, "Columns")
    if rows is not None and columns is not None:
        lines.append(f"이미지 크기는 {rows} x {columns}입니다.")
    spatial = [t for t in ("PixelSpacing", "SliceThickness") if _value(tags, t) is not None]
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
        """`llm=None` => template-only explanations.

        Defense in depth: DICOM-derived data is never sent to an external provider, even if a
        caller passes one in (the container already passes None in that case).
        """
        self._llm = llm if llm is not None and llm.provider == "ollama" else None
        self._rules = rules
        self._system_prompt = system_prompt

    async def analyze(self, path: Path, *, explain: bool = True) -> DicomAnalysis:
        ds = await asyncio.to_thread(read_dataset, path)
        checksum = await asyncio.to_thread(sha256_of, path)
        result = evaluate(ds, self._rules)
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
            try:
                result = await self._llm.generate(
                    build_dicom_prompt(build_llm_payload(analysis)), system=self._system_prompt
                )
                if text := result.text:
                    return f"{text}\n\n{DISCLAIMER}", "llm"
            except LLMError as exc:
                logger.warning("DICOM explanation falls back to template: %s", exc)
        return f"{template_summary(analysis)}\n\n{DISCLAIMER}", "template"
