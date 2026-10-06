"""Layer 2: de-identification check against DICOM PS3.15 Annex E.

The Basic Application Level Confidentiality Profile (Table E.1-1, generated into
rules/standard/ps3.15_e1-1_deid.yaml) is applied to every attribute of the dataset, recursively
into sequence items (PS3.15 E.1.1: "whether contained in the top level Data Set or embedded in
an Item of a Sequence of Items").

What can and cannot be verified from one file's header:
- X (remove) still present, Z (empty or dummy) not empty, D (dummy) empty: detectable.
- Whether a non-empty Z/D value is a dummy, whether a UID was replaced (U) or a value was
  cleaned (C): not decidable from the value alone -> reported as info / "verify".
- Pixel data is never read: burned-in PHI is only assessed from Burned In Annotation and the
  modality (risk hint).
Findings never contain attribute values.
"""

from typing import Any

from pydicom.dataelem import DataElement
from pydicom.dataset import Dataset

from app.services.dicom_conformance import element_state
from app.services.dicom_findings import Finding, FindingCollector
from app.services.dicom_rules import DeidPolicy, DeidProfile, DeidRule, tag_label
from app.services.dicom_safe import EMPTY, EXISTS

TEXT_VRS = {"LO", "LT", "SH", "ST", "UT", "PN", "UC"}
DATE_VRS = {"DA", "DT", "TM"}
PATIENT_IDENTITY_REMOVED = 0x00120062
DEID_METHOD = 0x00120063
DEID_METHOD_CODES = 0x00120064
BURNED_IN_ANNOTATION = 0x00280301
MODALITY = 0x00080060


def resolve_action(action: str, iod_type: str | None) -> tuple[str, str | None]:
    """Resolve combined actions (X/Z, X/D, Z/D, X/Z/D, X/Z/U*) with the attribute's IOD Type.

    Returns (single action, note). With an unknown Type (nested items, attributes outside the
    mandatory modules) the most lenient alternative is used and noted, to avoid false errors.
    """
    if "/" not in action:
        return action, None
    letters = action.replace("*", "").split("/")
    if action == "X/Z/U*":
        mapping = {"1": "U*", "1C": "U*", "2": "Z", "2C": "Z", "3": "X"}
    else:
        type1 = "D" if "D" in letters else "Z"
        type2 = "Z" if "Z" in letters else type1
        mapping = {"1": type1, "1C": type1, "2": type2, "2C": type2, "3": letters[0]}
    if iod_type in mapping:
        return mapping[iod_type], f"{action}, IOD Type {iod_type}"
    lenient = "U*" if action == "X/Z/U*" else letters[-1]
    return lenient, f"{action}, IOD Type 미확인 → 완화 적용({lenient})"


class _Walker:
    def __init__(
        self,
        profile: DeidProfile,
        policy: DeidPolicy,
        options: list[str],
        iod_types: dict[int, str],
    ) -> None:
        self.profile = profile
        self.policy = policy
        self.options = options
        self.iod_types = iod_types
        self.source = f"{profile.edition} Table E.1-1"
        self.collector = FindingCollector()
        self.private_elements = 0
        self.private_groups: set[str] = set()
        self.private_paths: list[str] = []
        self.dates_present = 0

    def effective(self, rule: DeidRule) -> tuple[str, str | None]:
        for key in self.options:
            if key in rule.options:
                return rule.options[key], self.profile.options[key].name
        return rule.basic, None

    def walk(self, ds: Dataset, prefix: str = "", top: bool = True) -> None:
        for elem in ds:
            try:
                self.visit(elem, prefix, top)
            except (ValueError, TypeError, KeyError):  # undecodable element: still report presence
                continue

    def visit(self, elem: DataElement, prefix: str, top: bool) -> None:
        tag = int(elem.tag)
        if elem.tag.element == 0:  # group length
            return
        label = elem.keyword or tag_label(tag)
        path = f"{prefix}{label}"
        if elem.tag.is_private:
            self.private_elements += 1
            self.private_groups.add(f"{elem.tag.group:04X}")
            if len(self.private_paths) < 5:
                self.private_paths.append(f"{prefix}{tag_label(tag)}")
            return  # private sequences are not descended into
        state = element_state(elem)
        rule = self.profile.lookup(tag)
        recurse = elem.VR == "SQ"
        if rule is not None:
            if elem.VR in DATE_VRS and state == EXISTS:
                self.dates_present += 1
            action, option = self.effective(rule)
            resolved, note = resolve_action(action, self.iod_types.get(tag) if top else None)
            recurse = self.classify(elem, rule, resolved, note, option, state, path, top)
        if recurse and elem.VR == "SQ":
            for i, item in enumerate(elem.value or []):
                self.walk(item, f"{path}[{i}].", top=False)

    def classify(
        self,
        elem: DataElement,
        rule: DeidRule,
        action: str,
        note: str | None,
        option: str | None,
        state: str,
        path: str,
        top: bool,
    ) -> bool:
        """Add the finding for one attribute; return whether to descend into a sequence."""
        label = rule.label
        tag = tag_label(int(elem.tag))
        shown = action if note is None else f"{action} ({note})"
        if option:
            shown = f"{shown} via {option}"
        where = "" if top else " (중첩 sequence 내부)"

        def add(code: str, severity: str, message: str) -> None:
            self.collector.add(
                Finding(code, severity, message, self.source, label, tag, shown), path
            )

        if action == "X":
            if state == EXISTS:
                add("DEID-X-PRESENT", "error", f"삭제(X) 대상 {label}{where} 잔존(값 있음).")
            elif state == EMPTY:
                add("DEID-X-EMPTY", "warning", f"삭제(X) 대상 {label}{where} 잔존(빈 값).")
            return False
        if action == "Z":
            if state == EXISTS:
                if top and self.pseudonym(elem, label, tag, shown, path):
                    return False
                add(
                    "DEID-Z-NOT-EMPTY",
                    "warning",
                    f"빈 값/더미(Z) 대상 {label}{where}에 값이 있습니다(더미인지 자동 확인 불가).",
                )
            return elem.VR == "SQ"
        if action == "D":
            if state == EXISTS:
                add("DEID-D-VERIFY", "info", f"더미 치환(D) 대상 {label}{where}: 자동 확인 불가.")
            else:
                add("DEID-D-EMPTY", "warning", f"더미 치환(D) 대상 {label}{where}이(가) 비어 있음.")
            return elem.VR == "SQ"
        if action == "C":
            if state == EXISTS:
                severity = "warning" if elem.VR in TEXT_VRS else "info"
                add("DEID-C-VERIFY", severity, f"정제(C) 대상 {label}{where}: 자동 확인 불가.")
            return elem.VR == "SQ"
        if action == "U":
            if state == EXISTS:
                add("DEID-U-PRESENT", "info", f"UID {label}{where} 존재(프로파일: 새 UID로 치환).")
            return elem.VR == "SQ"
        return elem.VR == "SQ"  # K, U* (keep sequence, check its contents)

    def pseudonym(self, elem: DataElement, label: str, tag: str, shown: str, path: str) -> bool:
        rule = self.policy.pseudonyms.get(elem.keyword or "")
        if rule is None or rule.pattern is None:
            return False
        value = str(elem.value).strip()
        source = f"{self.source}; policy rules/deid_policy.yaml (pseudonymization)"
        if rule.pattern.fullmatch(value):
            self.collector.add(
                Finding(
                    "DEID-PSEUDONYM-OK",
                    "info",
                    f"{label} 값이 정책의 가명 형식과 일치합니다(준수).",
                    source,
                    label,
                    tag,
                    shown,
                ),
                path,
            )
        else:
            self.collector.add(
                Finding(
                    "DEID-PSEUDONYM-MISMATCH",
                    "error",
                    f"{label} 값이 비어 있지 않고 정책의 가명 형식과도 일치하지 않습니다.",
                    source,
                    label,
                    tag,
                    shown,
                ),
                path,
            )
        return True


def claimed_deid(
    ds: Dataset, profile: DeidProfile
) -> tuple[dict[str, Any], list[str], list[Finding]]:
    """What the file declares about its own de-identification (values only from CID 7050)."""
    source = "PS3.3 C.7.1.1 Patient Module; PS3.16 CID 7050"
    removed = ds.get(PATIENT_IDENTITY_REMOVED)
    removed_state = element_state(removed)
    removed_value = str(removed.value).strip() if removed_state == EXISTS else None
    if removed_value not in (None, "YES", "NO"):
        removed_value = "exists (non-standard value)"
    methods: list[dict[str, str]] = []
    unknown = 0
    claimed_options: list[str] = []
    by_code = {o.code: o.key for o in profile.options.values()}
    code_items = ds.get(DEID_METHOD_CODES)
    for item in (code_items.value or []) if code_items is not None else []:
        scheme = str(item.get("CodingSchemeDesignator", "")).strip()
        code = str(item.get("CodeValue", "")).strip()
        meaning = profile.cid7050.get((scheme, code))
        if meaning is None:
            unknown += 1
            continue
        methods.append({"scheme": scheme, "code": code, "meaning": meaning})
        if code in by_code:
            claimed_options.append(by_code[code])
    claim = {
        "patientIdentityRemoved": removed_value or removed_state,
        "deidentificationMethod": element_state(ds.get(DEID_METHOD)),
        "methodCodes": methods,
        "unknownMethodCodes": unknown,
        "basicProfileClaimed": any(m["code"] == "113100" for m in methods),
    }
    findings: list[Finding] = []
    if removed_value == "YES":
        if element_state(ds.get(DEID_METHOD)) != EXISTS and not methods and not unknown:
            findings.append(
                Finding(
                    "DEID-CLAIM-INCOMPLETE",
                    "error",
                    "PatientIdentityRemoved=YES이지만 DeidentificationMethod(0012,0063)와 "
                    "DeidentificationMethodCodeSequence(0012,0064)가 모두 없습니다(Type 1C).",
                    source,
                    "DeidentificationMethod",
                    "(0012,0063)",
                )
            )
    else:
        findings.append(
            Finding(
                "DEID-NOT-CLAIMED",
                "info",
                "파일이 비식별화를 선언하지 않습니다(PatientIdentityRemoved가 YES가 아님).",
                source,
                "PatientIdentityRemoved",
                "(0012,0062)",
            )
        )
    if unknown:
        findings.append(
            Finding(
                "DEID-CLAIM-UNKNOWN-CODE",
                "info",
                f"CID 7050에 없는 비식별화 방법 코드 {unknown}개(값은 표시하지 않음).",
                source,
                "DeidentificationMethodCodeSequence",
                "(0012,0064)",
                count=unknown,
            )
        )
    return claim, claimed_options, findings


def check_deid(
    ds: Dataset,
    profile: DeidProfile,
    policy: DeidPolicy,
    iod_types: dict[int, str] | None = None,
) -> dict[str, Any]:
    claim, claimed_options, claim_findings = claimed_deid(ds, profile)
    applied = [k for k in profile.options if k in policy.options]
    origin = {k: "policy" for k in applied}
    if policy.honor_claimed_options:
        for key in claimed_options:
            if key not in origin:
                origin[key] = "claimed"
    options = [k for k in profile.options if k in origin]  # Table E.1-1 column order

    walker = _Walker(profile, policy, options, iod_types or {})
    walker.walk(ds)
    collector = walker.collector
    collector.extend(claim_findings)
    source = f"{profile.edition} Table E.1-1"

    if walker.private_elements:
        retain = "retain_safe_private" in options
        collector.add(
            Finding(
                "DEID-PRIVATE-PRESENT",
                "info" if retain else "error",
                (
                    f"Private 속성 {walker.private_elements}개(그룹 "
                    f"{', '.join(sorted(walker.private_groups))})가 있습니다. "
                    + (
                        "Retain Safe Private Option 적용: 안전 목록 대조는 미구현, 수동 확인 필요."
                        if retain
                        else "기본 프로파일은 삭제(X)입니다(Retain Safe Private Option 미적용)."
                    )
                ),
                f"{source} (Private Attributes); PS3.15 E.3.10",
                "private attributes",
                "(gggg,eeee) odd group",
                walker.profile.private.basic if not retain else "C via Retain Safe Private Option",
                count=walker.private_elements,
                paths=walker.private_paths,
            )
        )

    burned = ds.get(BURNED_IN_ANNOTATION)
    modality = ds.get(MODALITY)
    modality_value = str(modality.value).strip() if element_state(modality) == EXISTS else ""
    burned_value = str(burned.value).strip().upper() if element_state(burned) == EXISTS else None
    if burned_value == "YES":
        collector.add(
            Finding(
                "DEID-BURNED-IN",
                "error",
                "BurnedInAnnotation=YES: 픽셀에 식별 정보가 새겨져 있을 수 있습니다(고위험). "
                "픽셀 정제(Clean Pixel Data Option) 또는 수동 확인이 필요합니다.",
                "PS3.3 C.7.6.1 General Image Module; PS3.15 E.3.1 Clean Pixel Data Option",
                "BurnedInAnnotation",
                "(0028,0301)",
            )
        )
    elif burned_value is None and modality_value in policy.high_risk_modalities:
        collector.add(
            Finding(
                "DEID-PIXEL-RISK",
                "warning",
                f"BurnedInAnnotation이 없고 Modality가 픽셀 내 텍스트가 흔한 유형({modality_value})"
                "입니다. 픽셀 PHI 위험: 수동/OCR 확인 권장(이 분석기는 픽셀을 읽지 않음).",
                "PS3.15 E.3.1 Clean Pixel Data Option; policy burned_in_high_risk_modalities",
                "BurnedInAnnotation",
                "(0028,0301)",
            )
        )

    if walker.dates_present:
        temporal = [
            profile.options[k].name
            for k in options
            if k in ("retain_longitudinal_full_dates", "retain_longitudinal_modified_dates")
        ]
        collector.add(
            Finding(
                "DEID-DATES",
                "info",
                f"날짜/시간 속성 {walker.dates_present}개가 값과 함께 있습니다. "
                + (
                    f"적용 옵션: {', '.join(temporal)}."
                    if temporal
                    else "Retain Longitudinal Temporal Information 옵션 미적용 → 기본 프로파일"
                    "(Z/X/D) 기준으로 판정했습니다. 시간축 유지가 필요하면 정책에서 옵션을 켜세요."
                ),
                f"{source}; PS3.15 E.3.6 Retain Longitudinal Temporal Information Options",
                count=walker.dates_present,
            )
        )

    return {
        "profile": "Basic Application Level Confidentiality Profile",
        "profileEdition": profile.edition,
        "optionsApplied": [
            {"key": k, "name": profile.options[k].name, "origin": origin[k]} for k in options
        ],
        "claimedDeid": claim,
        "findings": collector.findings(),
    }
