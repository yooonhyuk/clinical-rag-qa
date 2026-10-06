"""Output allowlist for DICOM-derived values (the PHI boundary).

Only attributes listed here may have their *value* leave the analyzer (API response, DB row,
LLM prompt). Each allowlisted value must additionally pass a format check for its kind, so a
free-text string smuggled into a coded attribute (e.g. a name typed into BodyPartExamined) is
suppressed too. Coded values can further be restricted to the standard's Defined Terms
(Modality: PS3.3 C.7.3.1.1.1, Body Part Examined: PS3.16 Annex L), which also catches an
upper-case name typed into a CS attribute. Every other attribute is reported as presence only:
"exists" / "empty" / "absent".
"""

import re
from collections.abc import Iterable, Mapping
from typing import Any

from pydicom.dataset import Dataset
from pydicom.multival import MultiValue
from pydicom.uid import UID_dictionary

EXISTS = "exists"
EMPTY = "empty"
ABSENT = "absent"
SUPPRESSED = "exists (value suppressed: not a safe coded/numeric value)"

# Code String: uppercase letters, digits, space, underscore; max 16 chars (PS3.5 Table 6.2-1).
_CS_RE = re.compile(r"^[A-Z0-9_ ]{1,16}$")

# keyword -> kind. "cs": coded string; "number": numeric (US/IS/DS, possibly multi-valued);
# "sop_class": the UID is replaced by its registered standard name.
SAFE_VALUE_ATTRIBUTES: dict[str, str] = {
    "Modality": "cs",
    "BodyPartExamined": "cs",
    "SOPClassUID": "sop_class",
    "PatientIdentityRemoved": "cs",
    "BurnedInAnnotation": "cs",
    "Units": "cs",
    "DecayCorrection": "cs",
    "Rows": "number",
    "Columns": "number",
    "NumberOfFrames": "number",
    "PixelSpacing": "number",
    "SliceThickness": "number",
    "SpacingBetweenSlices": "number",
    "ImagePositionPatient": "number",
    "ImageOrientationPatient": "number",
    "SeriesNumber": "number",
    "InstanceNumber": "number",
    "SamplesPerPixel": "number",
    "BitsAllocated": "number",
    "BitsStored": "number",
}


def is_empty_value(value: Any) -> bool:
    """True for a zero-length value (the attribute may still be present in the dataset)."""
    if value is None:
        return True
    if isinstance(value, MultiValue | list | tuple):
        return len(value) == 0 or all(is_empty_value(v) for v in value)
    if isinstance(value, bytes):
        return len(value) == 0
    return str(value).strip() == ""


def presence(ds: Dataset, keyword: str) -> str:
    """ "absent" (not in the dataset), "empty" (zero-length) or "exists"."""
    if keyword not in ds:
        return ABSENT
    try:
        elem = ds.data_element(keyword)
        if elem is None:
            return ABSENT
        if elem.VR == "SQ":
            return EXISTS if len(elem.value or []) else EMPTY
        return EMPTY if is_empty_value(elem.value) else EXISTS
    except (ValueError, TypeError, OverflowError):  # value present but cannot be decoded
        return EXISTS


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    return None


def _safe(kind: str, value: Any) -> Any:
    """Return the JSON-safe value, or None when the value fails the kind's format check."""
    if kind == "number":
        if isinstance(value, MultiValue | list | tuple):
            numbers = [_number(v) for v in value]
            return None if any(n is None for n in numbers) else numbers
        return _number(value)
    if kind == "cs":
        text = str(value).strip()
        return text if _CS_RE.match(text) else None
    if kind == "sop_class":
        entry = UID_dictionary.get(str(value).strip())
        return entry[0] if entry else None
    return None


# Coded attributes whose value is only shown when it is one of the listed terms.
ENUMERATED: dict[str, frozenset[str]] = {
    "PatientIdentityRemoved": frozenset({"YES", "NO"}),
    "BurnedInAnnotation": frozenset({"YES", "NO"}),
    "DecayCorrection": frozenset({"NONE", "START", "ADMIN"}),
    "Units": frozenset(
        {"CNTS", "NONE", "CM2", "CM2ML", "PCNT", "CPS", "BQML", "MGMINML", "UMOLMINML"}
        | {"MLMING", "MLG", "1CM", "UMOLML", "PROPCNTS", "PROPCPS", "MLMINML", "MLML"}
        | {"GML", "STDDEV"}
    ),  # PS3.3 C.8.9.1.1.3 Units Defined Terms
}


def safe_value(ds: Dataset, keyword: str, terms: Mapping[str, frozenset[str]] | None = None) -> Any:
    """The output-safe representation of one attribute.

    `terms` optionally restricts coded attributes to a set of Defined Terms.
    """
    state = presence(ds, keyword)
    kind = SAFE_VALUE_ATTRIBUTES.get(keyword)
    if state != EXISTS or kind is None:
        return state
    try:
        rendered = _safe(kind, ds.data_element(keyword).value)
    except (ValueError, TypeError, OverflowError):  # malformed DS/IS etc.
        rendered = None
    allowed = (terms or {}).get(keyword) or ENUMERATED.get(keyword)
    if kind == "cs" and allowed is not None and rendered not in allowed:
        rendered = None
    return SUPPRESSED if rendered is None else rendered


def safe_summary(
    ds: Dataset, keywords: Iterable[str], terms: Mapping[str, frozenset[str]] | None = None
) -> dict[str, Any]:
    return {keyword: safe_value(ds, keyword, terms) for keyword in keywords}
