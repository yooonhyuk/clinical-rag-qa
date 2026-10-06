"""Layer 1: DICOM standard conformance (PS3.3 IOD/module Types, PS3.5 value formats).

Scope (see docs/dicom-rules.md):
- IOD from SOP Class UID (fallback: Modality) using the generated PS3.3 rule file.
- Mandatory (M) modules only. Type 1 = present and non-empty, Type 2 = present (may be empty),
  Type 1C/2C = reported as "conditional - not evaluated", Type 3 = not checked.
  Conditional (C) modules are listed as not evaluated; user-optional (U) modules are ignored.
- Enhanced multi-frame IODs: mandatory functional group macros are looked up in the Shared /
  Per-frame Functional Groups Sequences (never at the top level).
- Value format (PS3.5 6.2) for checked attributes with VR UI, DA, TM, CS, plus Modality and
  Body Part Examined against their Defined Terms.
- PET: SUV "quantitation readiness" checks, reported separately (warnings, not conformance).
Nothing here reads pixel data or returns attribute values.
"""

import datetime as dt
import re
from dataclasses import dataclass
from typing import Any

from pydicom.datadict import dictionary_VR
from pydicom.dataelem import DataElement
from pydicom.dataset import Dataset
from pydicom.multival import MultiValue

from app.services.dicom_findings import Finding, FindingCollector
from app.services.dicom_rules import (
    AttributeSpec,
    ConformanceRules,
    FunctionalGroupSpec,
    IodSpec,
    tag_label,
)
from app.services.dicom_safe import EMPTY, EXISTS, is_empty_value

PS35_VR = "PS3.5 6.2 Value Representation"
_UI_RE = re.compile(r"^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*$")
_UI_CHARS_RE = re.compile(r"^[0-9.]+$")
_TM_RE = re.compile(r"^([01][0-9]|2[0-3])([0-5][0-9]([0-5][0-9]|60)?)?(\.[0-9]{1,6})?$")
_CS_RE = re.compile(r"^[A-Z0-9_ ]{0,16}$")

SHARED_FG = 0x52009229  # SharedFunctionalGroupsSequence
PER_FRAME_FG = 0x52009230  # PerFrameFunctionalGroupsSequence
SOP_CLASS_UID = 0x00080016


@dataclass(slots=True)
class IodMatch:
    spec: IodSpec | None
    determined_by: str | None  # "SOPClassUID" | "Modality" | None

    def as_dict(self) -> dict[str, Any]:
        if self.spec is None:
            return {"key": None, "name": None, "determinedBy": None, "source": None}
        return {
            "key": self.spec.key,
            "name": self.spec.name,
            "determinedBy": self.determined_by,
            "source": self.spec.source,
        }


def element_state(elem: DataElement | None) -> str:
    """'absent' / 'empty' / 'exists' for an element (sequence: zero items = empty)."""
    if elem is None:
        return "absent"
    try:
        if elem.VR == "SQ":
            return EXISTS if len(elem.value or []) else EMPTY
        return EMPTY if is_empty_value(elem.value) else EXISTS
    except (ValueError, TypeError, OverflowError):
        return EXISTS


def _get(ds: Dataset, tag: int) -> DataElement | None:
    try:
        return ds[tag] if tag in ds else None
    except (KeyError, ValueError, TypeError):
        return None


def _str_values(elem: DataElement) -> list[str]:
    value = elem.value
    if isinstance(value, MultiValue | list | tuple):
        return [str(v) for v in value]
    if isinstance(value, bytes):
        return [value.decode("ascii", "replace")]
    return [str(value)]


# --- value format (PS3.5) ------------------------------------------------------------------


def ui_problem(value: str) -> str | None:
    value = value.rstrip("\0")
    if len(value) > 64:
        return "64자 초과"
    if not _UI_CHARS_RE.match(value):
        return "숫자와 '.' 이외의 문자 포함"
    if not _UI_RE.match(value):
        return "빈 구성요소 또는 구성요소의 선행 0"
    return None


def da_problem(value: str) -> str | None:
    value = value.strip()
    if not re.fullmatch(r"[0-9]{8}", value):
        return "YYYYMMDD 형식 아님"
    try:
        dt.date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError:
        return "존재하지 않는 날짜"
    return None


def tm_problem(value: str) -> str | None:
    return None if _TM_RE.match(value.strip()) else "HHMMSS.FFFFFF 형식 아님"


def cs_problem(value: str) -> str | None:
    return None if _CS_RE.match(value.strip()) else "CS 문자셋(A-Z 0-9 _ 공백, 16자) 위반"


_CHECKS = {"UI": ui_problem, "DA": da_problem, "TM": tm_problem, "CS": cs_problem}


def value_format_findings(elem: DataElement, label: str) -> list[Finding]:
    vr = elem.VR
    if vr not in _CHECKS:
        try:
            vr = dictionary_VR(elem.tag)
        except KeyError:
            return []
    check = _CHECKS.get(vr)
    if check is None or element_state(elem) != EXISTS:
        return []
    try:
        values = _str_values(elem)
    except (ValueError, TypeError):
        return []
    problems = sorted({p for v in values if v != "" and (p := check(v))})
    return [
        Finding(
            code=f"L1-VR-{vr}",
            severity="error",
            message=f"{label} 값이 {vr} 형식을 위반합니다: {problem}.",
            source=PS35_VR,
            attribute=label,
            tag=tag_label(elem.tag),
        )
        for problem in problems
    ]


# --- IOD -----------------------------------------------------------------------------------


def determine_iod(ds: Dataset, rules: ConformanceRules) -> tuple[IodMatch, list[Finding]]:
    findings: list[Finding] = []
    sop = _get(ds, SOP_CLASS_UID)
    sop_uid = str(sop.value).strip() if sop is not None and element_state(sop) == EXISTS else ""
    if sop_uid in rules.by_sop_class:
        return IodMatch(rules.iods[rules.by_sop_class[sop_uid]], "SOPClassUID"), findings
    if sop_uid:
        findings.append(
            Finding(
                code="L1-IOD-NOT-COVERED",
                severity="info",
                message="SOP Class가 이 분석기의 IOD 범위 밖입니다. Modality로 IOD를 추정합니다.",
                source="PS3.4 Annex B / docs/dicom-rules.md (coverage)",
                attribute="SOPClassUID",
                tag=tag_label(SOP_CLASS_UID),
            )
        )
    modality = _get(ds, 0x00080060)
    mod_value = str(modality.value).strip() if modality is not None and modality.value else ""
    if mod_value in rules.by_modality:
        return IodMatch(rules.iods[rules.by_modality[mod_value]], "Modality"), findings
    findings.append(
        Finding(
            code="L1-IOD-UNKNOWN",
            severity="warning",
            message="SOP Class UID와 Modality로 IOD를 정할 수 없어 모듈 검사를 건너뜁니다.",
            source="PS3.3 Annex A",
        )
    )
    return IodMatch(None, None), findings


def _type_finding(attr: AttributeSpec, state: str, source: str, where: str = "") -> Finding | None:
    tag = tag_label(attr.tag)
    if attr.type == "1" and state == "absent":
        return Finding(
            "L1-TYPE1-ABSENT",
            "error",
            f"Type 1 속성 {attr.label}{where}이(가) 없습니다(존재 + 값 필수).",
            source,
            attr.label,
            tag,
        )
    if attr.type == "1" and state == EMPTY:
        return Finding(
            "L1-TYPE1-EMPTY",
            "error",
            f"Type 1 속성 {attr.label}{where}의 값이 비어 있습니다(값 필수).",
            source,
            attr.label,
            tag,
        )
    if attr.type == "2" and state == "absent":
        return Finding(
            "L1-TYPE2-ABSENT",
            "error",
            f"Type 2 속성 {attr.label}{where}이(가) 없습니다(빈 값이라도 존재 필수).",
            source,
            attr.label,
            tag,
        )
    return None


@dataclass(slots=True)
class ConformanceResult:
    iod: IodMatch
    findings: list[Finding]
    passed: list[str]  # Type 1/2 attributes that satisfied their Type
    checked_tags: set[int]


def check_conformance(ds: Dataset, rules: ConformanceRules) -> ConformanceResult:
    collector = FindingCollector()
    match, iod_findings = determine_iod(ds, rules)
    collector.extend(iod_findings)
    passed: list[str] = []
    evaluated: set[int] = set()  # tags whose Type was already evaluated (first module wins)
    checked: set[int] = {SOP_CLASS_UID, 0x00080060, 0x00180015}  # tags for value-format checks
    iod = match.spec
    if iod is not None:
        not_evaluated_modules: list[str] = []
        strictest = iod.attribute_types()
        for usage in iod.modules:
            if usage.usage == "C":
                not_evaluated_modules.append(usage.name)
                continue
            if usage.usage != "M" or usage.module is None:
                continue
            conditional: list[str] = []
            for attr in usage.module.attributes:
                if attr.tag >> 16 == 0x7FE0:
                    continue  # Pixel Data & friends: never read (stop_before_pixels)
                checked.add(attr.tag)
                # An attribute can appear in several modules (e.g. Image Type: Type 3 in General
                # Image, Type 1 in CT Image): evaluate it once, with its strictest Type.
                if attr.tag in evaluated or attr.type != strictest[attr.tag]:
                    continue
                evaluated.add(attr.tag)
                state = element_state(_get(ds, attr.tag))
                if attr.type in ("1C", "2C"):
                    if state == "absent":
                        conditional.append(attr.label)
                    continue
                if attr.type not in ("1", "2"):
                    continue
                finding = _type_finding(attr, state, usage.module.source)
                if finding is None:
                    if attr.label not in passed:
                        passed.append(attr.label)
                else:
                    collector.add(finding)
            if conditional:
                collector.add(
                    Finding(
                        "L1-CONDITIONAL-NOT-EVALUATED",
                        "info",
                        f"{usage.module.name} 모듈의 조건부(Type 1C/2C) 속성 "
                        f"{len(conditional)}개는 조건을 평가하지 않았습니다(부재).",
                        usage.module.source,
                        count=len(conditional),
                        details={"attributes": conditional},
                    )
                )
        if not_evaluated_modules:
            collector.add(
                Finding(
                    "L1-CONDITIONAL-MODULE-NOT-EVALUATED",
                    "info",
                    f"조건부(C) 모듈 {len(not_evaluated_modules)}개는 평가하지 않았습니다.",
                    iod.source,
                    count=len(not_evaluated_modules),
                    details={"modules": not_evaluated_modules},
                )
            )
        if iod.functional_groups:
            collector.extend(_functional_group_findings(ds, iod))

    # Value formats of every checked attribute that is present at the top level.
    for tag in sorted(checked):
        elem = _get(ds, tag)
        if elem is None:
            continue
        label = elem.keyword or tag_label(tag)
        for finding in value_format_findings(elem, label):
            collector.add(finding)
    collector.extend(_defined_term_findings(ds, rules))
    return ConformanceResult(match, collector.findings(), passed, checked)


def _defined_term_findings(ds: Dataset, rules: ConformanceRules) -> list[Finding]:
    findings: list[Finding] = []
    modality = _get(ds, 0x00080060)
    if modality is not None and element_state(modality) == EXISTS:
        value = str(modality.value).strip()
        if value in rules.modality_retired_terms:
            findings.append(
                Finding(
                    "L1-MODALITY-RETIRED",
                    "warning",
                    "Modality 값이 폐기(Retired)된 Defined Term입니다.",
                    "PS3.3 C.7.3.1.1.1 Modality",
                    "Modality",
                    "(0008,0060)",
                )
            )
        elif value not in rules.modality_terms:
            findings.append(
                Finding(
                    "L1-MODALITY-TERM",
                    "warning",
                    "Modality 값이 PS3.3 Defined Terms에 없습니다.",
                    "PS3.3 C.7.3.1.1.1 Modality",
                    "Modality",
                    "(0008,0060)",
                )
            )
    body_part = _get(ds, 0x00180015)
    if body_part is not None and element_state(body_part) == EXISTS:
        if str(body_part.value).strip() not in rules.body_part_terms:
            findings.append(
                Finding(
                    "L1-BODYPART-TERM",
                    "warning",
                    "BodyPartExamined 값이 PS3.16 Annex L Defined Terms에 없습니다.",
                    "PS3.16 Annex L (Tables L-1..L-3)",
                    "BodyPartExamined",
                    "(0018,0015)",
                )
            )
    return findings


# --- enhanced multi-frame ------------------------------------------------------------------


def _items(ds: Dataset, tag: int) -> list[Dataset]:
    elem = _get(ds, tag)
    if elem is None or elem.VR != "SQ":
        return []
    return list(elem.value or [])


def functional_group_item(ds: Dataset, sequence_tag: int, frame: int = 0) -> Dataset | None:
    """The macro item for one frame: Shared Functional Groups first, then Per-frame."""
    for container in (_items(ds, SHARED_FG)[:1], _items(ds, PER_FRAME_FG)[frame : frame + 1]):
        for group in container:
            items = _items(group, sequence_tag)
            if items:
                return items[0]
    return None


def _functional_group_findings(ds: Dataset, iod: IodSpec) -> list[Finding]:
    shared = _items(ds, SHARED_FG)[:1]
    per_frame = _items(ds, PER_FRAME_FG)
    findings: list[Finding] = []
    for group in iod.functional_groups:
        sequence = group.sequence
        if group.usage != "M" or sequence is None:
            continue
        in_shared = bool(shared and _items(shared[0], sequence.tag))
        frames_with = [i for i, item in enumerate(per_frame) if _items(item, sequence.tag)]
        if group.per_frame_only and in_shared:
            findings.append(
                Finding(
                    "L1-FG-SHARED-NOT-ALLOWED",
                    "error",
                    f"{group.macro} 매크로({sequence.label})는 Shared Functional Group에 "
                    "둘 수 없습니다.",
                    group.source,
                    sequence.label,
                    tag_label(sequence.tag),
                )
            )
        satisfied = (len(frames_with) == len(per_frame) and per_frame) or (
            in_shared and not group.per_frame_only
        )
        if not satisfied:
            missing = len(per_frame) - len(frames_with) if per_frame else 1
            findings.append(
                Finding(
                    "L1-FG-MISSING",
                    "error",
                    f"필수 Functional Group 매크로 {group.macro}({sequence.label})가 "
                    f"Shared/Per-frame 어디에도 없는 프레임이 {missing}개 있습니다.",
                    group.source,
                    sequence.label,
                    tag_label(sequence.tag),
                    details={"framesMissing": missing, "frames": len(per_frame)},
                )
            )
            continue
        findings.extend(_macro_item_findings(ds, group, in_shared, per_frame, frames_with))
    return findings


def _macro_item_findings(
    ds: Dataset,
    group: FunctionalGroupSpec,
    in_shared: bool,
    per_frame: list[Dataset],
    frames_with: list[int],
) -> list[Finding]:
    assert group.definition is not None and group.sequence is not None
    inner = [a for a in group.definition.attributes if a.level == 1 and a.type in ("1", "2")]
    items: list[Dataset] = []
    if in_shared:
        items = _items(_items(ds, SHARED_FG)[0], group.sequence.tag)[:1]
    else:
        items = [_items(per_frame[i], group.sequence.tag)[0] for i in frames_with]
    collector = FindingCollector()
    where = f" ({group.sequence.label} 내부)"
    for item in items:
        for attr in inner:
            finding = _type_finding(attr, element_state(_get(item, attr.tag)), group.source, where)
            if finding is not None:
                finding.code = finding.code.replace("L1-", "L1-FG-")
                collector.add(finding)
    return collector.findings()


# --- quantitation readiness (PET SUV) -----------------------------------------------------

QR_SOURCE_NOTE = "정량(SUV) 준비도 – 적합성 요건 아님"


def check_quantitation_readiness(ds: Dataset, iod: IodMatch) -> dict[str, Any]:
    modality = _get(ds, 0x00080060)
    is_pet = (iod.spec is not None and iod.spec.key in ("pet", "enhanced_pet")) or (
        modality is not None and str(modality.value).strip() == "PT"
    )
    if not is_pet:
        return {"applicable": False, "ready": None, "findings": []}
    if iod.spec is not None and iod.spec.key == "enhanced_pet":
        note = Finding(
            "QR-NOT-EVALUATED",
            "info",
            "Enhanced PET의 정량 정보는 Functional Group 구조라 이번 범위에서 평가하지 않았습니다.",
            "PS3.3 C.8.22 Enhanced PET Modules",
        )
        return {"applicable": True, "ready": None, "findings": [note.as_dict()]}

    findings: list[Finding] = []

    def need(tag: int, label: str, source: str, ds_: Dataset = ds, where: str = "") -> bool:
        if element_state(_get(ds_, tag)) == EXISTS:
            return True
        findings.append(
            Finding(
                "QR-MISSING",
                "warning",
                f"SUV 계산에 필요한 {label}{where} 값이 없습니다({QR_SOURCE_NOTE}).",
                source,
                label,
                tag_label(tag),
            )
        )
        return False

    need(0x00101030, "PatientWeight", "PS3.3 C.7.2.2 Patient Study Module")
    need(0x00080031, "SeriesTime", "PS3.3 C.7.3.1 General Series Module")
    if need(0x00541001, "Units", "PS3.3 C.8.9.1 PET Series Module"):
        if str(ds[0x00541001].value).strip() != "BQML":
            findings.append(
                Finding(
                    "QR-UNITS",
                    "warning",
                    f"Units가 BQML이 아니어서 SUVbw를 바로 계산할 수 없습니다({QR_SOURCE_NOTE}).",
                    "PS3.3 C.8.9.1 PET Series Module",
                    "Units",
                    "(0054,1001)",
                )
            )
    need(0x00541102, "DecayCorrection", "PS3.3 C.8.9.1 PET Series Module")
    isotope = "PS3.3 C.8.9.2 PET Isotope Module"
    radiopharm = _items(ds, 0x00540016)
    if not radiopharm:
        need(0x00540016, "RadiopharmaceuticalInformationSequence", isotope)
    else:
        item, where = radiopharm[0], " (RadiopharmaceuticalInformationSequence 내부)"
        need(0x00181074, "RadionuclideTotalDose", isotope, item, where)
        need(0x00181075, "RadionuclideHalfLife", isotope, item, where)
        has_start = element_state(_get(item, 0x00181072)) == EXISTS or (
            element_state(_get(item, 0x00181078)) == EXISTS
        )
        if not has_start:
            need(0x00181072, "RadiopharmaceuticalStartTime", isotope, item, where)
    return {
        "applicable": True,
        "ready": not findings,
        "label": QR_SOURCE_NOTE,
        "findings": [f.as_dict() for f in findings],
    }
