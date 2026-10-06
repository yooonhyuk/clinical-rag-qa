"""DICOM tag analyzer: metadata only, never pixel data, never image reading.

pydicom.dcmread(stop_before_pixels=True) in a worker thread
-> Layer 1: standard conformance (PS3.3 IOD/module Types, PS3.5 value formats) + PET SUV
   quantitation readiness                                   (dicom_conformance.py)
-> Layer 2: de-identification per PS3.15 Annex E Table E.1-1 + site policy  (dicom_deid.py)
-> output allowlist (dicom_safe.py): only coded/numeric values of allowlisted attributes leave
   this module; findings carry codes, keywords, counts and citations - never values
-> explanation: local LLM sees only the allowlisted summary + finding codes/counts; falls back
   to a deterministic template (and always uses it for external providers)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pydicom
from pydicom.dataset import Dataset
from pydicom.errors import InvalidDicomError

from app.services.dicom_conformance import (
    check_conformance,
    check_quantitation_readiness,
    functional_group_item,
)
from app.services.dicom_deid import check_deid
from app.services.dicom_findings import Finding, severity_counts
from app.services.dicom_rules import DicomRules
from app.services.dicom_safe import EXISTS, SAFE_VALUE_ATTRIBUTES, presence, safe_summary
from app.services.document_loader import sha256_of
from app.services.llm_types import GenerationClient, LLMError
from app.services.prompt_builder import build_dicom_prompt

logger = logging.getLogger(__name__)

# pydicom's own value validation emits warnings / log records that quote the raw value
# ("Invalid value for VR UI: '<value>'"), which would put PHI into logs. Value formats are
# validated by Layer 1 instead (without echoing values), so pydicom's check is switched off.
pydicom.config.settings.reading_validation_mode = pydicom.config.IGNORE

DISCLAIMER = "이 설명은 DICOM 태그 기반 설명이며, 영상 판독은 수행하지 않습니다."

# Attributes summarised in `tag_summary` (values only for allowlisted ones, see dicom_safe).
KEY_TAGS: tuple[str, ...] = (
    "Modality",
    "SOPClassUID",
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
    "NumberOfFrames",
    "PixelSpacing",
    "SliceThickness",
    "ImagePositionPatient",
    "ImageOrientationPatient",
    "PatientID",
    "PatientName",
    "PatientBirthDate",
    "PatientSex",
    "AccessionNumber",
    "PatientIdentityRemoved",
    "BurnedInAnnotation",
)
# Enhanced multi-frame: spatial attributes live in functional group macros.
_FG_SPATIAL = {
    "PixelSpacing": 0x00289110,  # Pixel Measures Sequence
    "SliceThickness": 0x00289110,
    "ImageOrientationPatient": 0x00209116,  # Plane Orientation Sequence
    "ImagePositionPatient": 0x00209113,  # Plane Position Sequence (first frame)
}
_MISSING_CODES = {"L1-TYPE1-ABSENT", "L1-TYPE1-EMPTY", "L1-TYPE2-ABSENT", "L1-FG-MISSING"}


class DicomReadError(Exception):
    error_type = "DICOM_READ_FAILED"


@dataclass(slots=True)
class DicomAnalysis:
    file_name: str
    file_path: str
    checksum: str
    tag_summary: dict[str, Any]
    layer1: dict[str, Any]
    layer2: dict[str, Any]
    quantitation_readiness: dict[str, Any]
    counts: dict[str, dict[str, int]]
    rule_source: str
    summary: str = ""
    summary_source: str = "llm"  # "llm" | "template"
    extra: dict[str, Any] = field(default_factory=dict)

    # --- backward-compatible views (MVP-1 response fields) ---------------------------------
    @property
    def missing_required_tags(self) -> list[str]:
        return _unique(
            f["attribute"]
            for f in self.layer1["findings"]
            if f["code"] in _MISSING_CODES and f.get("attribute")
        )

    @property
    def privacy_warnings(self) -> list[str]:
        return _unique(
            f"{f['attribute']} exists"
            for f in self.layer2["findings"]
            if f["severity"] in ("error", "warning") and f.get("attribute")
        )

    @property
    def passed(self) -> list[str]:
        return list(self.layer1.get("passed", []))

    @property
    def warnings(self) -> list[str]:
        return [
            f["message"] for f in self.layer2["findings"] if f["severity"] in ("error", "warning")
        ]

    def stored_tags(self) -> dict[str, Any]:
        """What is persisted in dicom_files.tags (allowlisted values and findings only)."""
        return {
            "tagSummary": self.tag_summary,
            "layer1": self.layer1,
            "layer2": self.layer2,
            "quantitationReadiness": self.quantitation_readiness,
            "counts": self.counts,
        }


def _unique(items: Any) -> list[str]:
    return list(dict.fromkeys(items))


def read_dataset(path: Path) -> Dataset:
    """Read the DICOM header without loading pixel data. Blocking.

    The returned Dataset holds raw (possibly PHI) values: it must never leave this module
    except through `dicom_safe` (allowlist), presence markers or findings (no values).
    """
    try:
        return pydicom.dcmread(path, stop_before_pixels=True)
    except (InvalidDicomError, OSError, ValueError) as exc:
        raise DicomReadError(f"Cannot read DICOM file: {exc}") from exc


def _spatial_from_functional_groups(ds: Dataset, summary: dict[str, Any]) -> None:
    found = False
    for keyword, sequence_tag in _FG_SPATIAL.items():
        if summary.get(keyword) != "absent":
            continue
        item = functional_group_item(ds, sequence_tag)
        if item is None or keyword not in item:
            continue
        summary[keyword] = safe_summary(item, (keyword,))[keyword]
        found = True
    if found:
        summary["spatialSource"] = "Shared/PerFrameFunctionalGroupsSequence (frame 1)"


def _findings(items: list[Finding]) -> list[dict[str, Any]]:
    return [f.as_dict() for f in items]


def evaluate(ds: Dataset, rules: DicomRules) -> dict[str, Any]:
    """Pure rule evaluation. Only allowlisted values / presence markers / findings."""
    conf = rules.conformance
    terms = {
        "Modality": conf.modality_terms | conf.modality_retired_terms,
        "BodyPartExamined": conf.body_part_terms,
    }
    tag_summary = safe_summary(ds, KEY_TAGS, terms)
    if presence(ds, "SharedFunctionalGroupsSequence") == EXISTS:
        _spatial_from_functional_groups(ds, tag_summary)

    l1 = check_conformance(ds, conf)
    iod_types = l1.iod.spec.attribute_types() if l1.iod.spec is not None else {}
    l2 = check_deid(ds, rules.deid, rules.policy, iod_types)
    qr = check_quantitation_readiness(ds, l1.iod)

    layer1 = {
        "standard": f"PS3.3 / PS3.5 {conf.edition}",
        "iod": l1.iod.as_dict(),
        "passed": l1.passed,
        "findings": _findings(l1.findings),
    }
    layer2 = {**l2, "findings": _findings(l2["findings"])}
    counts = {
        "layer1": severity_counts(l1.findings),
        "layer2": severity_counts(l2["findings"]),
        "quantitationReadiness": {
            s: sum(1 for f in qr["findings"] if f["severity"] == s)
            for s in ("error", "warning", "info")
        },
    }
    return {
        "tag_summary": tag_summary,
        "layer1": layer1,
        "layer2": layer2,
        "quantitation_readiness": qr,
        "counts": counts,
    }


def _finding_codes(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Errors/warnings as code + standard keyword + count; info findings as unique codes."""
    return {
        "issues": [
            {k: f[k] for k in ("code", "severity", "attribute", "count") if k in f}
            for f in findings
            if f["severity"] != "info"
        ],
        "infoCodes": _unique(f["code"] for f in findings if f["severity"] == "info"),
    }


def build_llm_payload(analysis: DicomAnalysis) -> dict[str, Any]:
    """The only DICOM-derived data an LLM may see: allowlisted values, presence markers,
    IOD name, finding codes / standard keywords / counts. No messages, paths or values."""
    return {
        "tagSummary": analysis.tag_summary,
        "iod": analysis.layer1["iod"].get("name"),
        "counts": analysis.counts,
        "layer1Findings": _finding_codes(analysis.layer1["findings"]),
        "quantitationReadiness": {
            "applicable": analysis.quantitation_readiness["applicable"],
            "ready": analysis.quantitation_readiness["ready"],
            "findings": _finding_codes(analysis.quantitation_readiness["findings"]),
        },
        "layer2Findings": _finding_codes(analysis.layer2["findings"]),
        "deidClaimed": {
            "patientIdentityRemoved": analysis.layer2["claimedDeid"]["patientIdentityRemoved"],
            "methods": [m["meaning"] for m in analysis.layer2["claimedDeid"]["methodCodes"]],
        },
    }


def _value(tags: dict[str, Any], keyword: str) -> Any:
    """A real (allowlisted) value, or None for presence markers / suppressed values."""
    value = tags.get(keyword)
    if keyword not in SAFE_VALUE_ATTRIBUTES:
        return None
    if isinstance(value, str) and value.startswith(("exists", "empty", "absent")):
        return None
    return value


def _top(findings: list[dict[str, Any]], severity: str, limit: int = 3) -> str:
    names = _unique(f.get("attribute") or f["code"] for f in findings if f["severity"] == severity)
    more = f" 외 {len(names) - limit}건" if len(names) > limit else ""
    return ", ".join(names[:limit]) + more


def template_summary(analysis: DicomAnalysis) -> str:
    tags = analysis.tag_summary
    lines: list[str] = []
    modality = _value(tags, "Modality")
    iod = analysis.layer1["iod"]
    if iod.get("name"):
        basis = "SOP Class UID" if iod["determinedBy"] == "SOPClassUID" else "Modality"
        lines.append(
            f"{basis} 기준으로 {iod['name']}로 판단했습니다(Modality: {modality or '없음'})."
        )
    elif modality:
        lines.append(f"Modality는 {modality}이지만 지원하는 IOD를 정하지 못했습니다.")
    else:
        lines.append("Modality와 SOP Class로 검사 종류를 확인할 수 없습니다.")
    rows, columns = _value(tags, "Rows"), _value(tags, "Columns")
    if rows is not None and columns is not None:
        lines.append(f"이미지 크기는 {rows} x {columns}입니다.")
    spatial = [t for t in ("PixelSpacing", "SliceThickness") if _value(tags, t) is not None]
    if spatial:
        where = " Functional Group에" if "spatialSource" in tags else ""
        lines.append(f"{', '.join(spatial)} 값이{where} 있어 기본 공간 정보 확인이 가능합니다.")

    c1 = analysis.counts["layer1"]
    l1 = analysis.layer1["findings"]
    if c1["error"]:
        lines.append(f"표준 적합성(Layer 1) 오류 {c1['error']}건: {_top(l1, 'error')}.")
    else:
        lines.append("표준 적합성(Layer 1) 검사에서 오류가 없습니다.")
    qr = analysis.quantitation_readiness
    if qr["applicable"] and qr["ready"] is False:
        lines.append(f"PET 정량(SUV) 준비도 경고: {_top(qr['findings'], 'warning')}.")
    elif qr["applicable"] and qr["ready"]:
        lines.append("PET 정량(SUV) 계산에 필요한 태그가 모두 있습니다.")

    c2 = analysis.counts["layer2"]
    l2 = analysis.layer2["findings"]
    if analysis.layer2["claimedDeid"]["patientIdentityRemoved"] == "YES":
        lines.append("파일은 비식별화되었다고 선언합니다(PatientIdentityRemoved=YES).")
    if c2["error"] or c2["warning"]:
        parts = []
        if c2["error"]:
            parts.append(f"오류 {c2['error']}건({_top(l2, 'error')})")
        if c2["warning"]:
            parts.append(f"경고 {c2['warning']}건({_top(l2, 'warning')})")
        lines.append(f"비식별화(Layer 2, PS3.15 Annex E) {', '.join(parts)}: 확인이 필요합니다.")
    else:
        lines.append("비식별화(Layer 2) 검사에서 오류·경고가 없습니다.")
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

    @property
    def rules(self) -> DicomRules:
        return self._rules

    async def analyze(self, path: Path, *, explain: bool = True) -> DicomAnalysis:
        ds = await asyncio.to_thread(read_dataset, path)
        checksum = await asyncio.to_thread(sha256_of, path)
        result = await asyncio.to_thread(evaluate, ds, self._rules)
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
