"""Finding model shared by Layer 1 (conformance), quantitation readiness and Layer 2 (de-id).

A finding never carries an attribute *value*: only codes, standard keywords / tags, keyword
paths into sequences, counts, a fixed message template and the citation of its source.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

SEVERITIES = ("error", "warning", "info")
MAX_PATHS = 5


@dataclass(slots=True)
class Finding:
    code: str
    severity: str  # "error" | "warning" | "info"
    message: str  # fixed Korean template - never includes DICOM values
    source: str  # e.g. "PS3.15 2026d Table E.1-1"
    attribute: str | None = None  # standard keyword (or name) / "private attributes"
    tag: str | None = None  # "(gggg,eeee)"
    action: str | None = None  # Layer 2 profile action, e.g. "X" or "X/Z -> Z"
    count: int = 1
    paths: list[str] = field(default_factory=list)  # keyword paths of nested occurrences
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "source": self.source,
        }
        for key in ("attribute", "tag", "action"):
            if (value := getattr(self, key)) is not None:
                out[key] = value
        out["count"] = self.count
        if self.paths:
            out["paths"] = self.paths
        if self.details:
            out["details"] = self.details
        return out


class FindingCollector:
    """Merges repeated findings (same code/tag/action/attribute/source) into one with a count
    and up to MAX_PATHS example paths."""

    def __init__(self) -> None:
        self._items: dict[tuple[str | None, ...], Finding] = {}

    def add(self, finding: Finding, path: str | None = None) -> None:
        key = (finding.code, finding.tag, finding.action, finding.attribute, finding.source)
        existing = self._items.get(key)
        if existing is None:
            if path:
                finding.paths = [path]
            self._items[key] = finding
            return
        existing.count += finding.count
        if path and len(existing.paths) < MAX_PATHS and path not in existing.paths:
            existing.paths.append(path)

    def extend(self, findings: Iterable[Finding]) -> None:
        for finding in findings:
            self.add(finding)

    def findings(self) -> list[Finding]:
        order = {s: i for i, s in enumerate(SEVERITIES)}
        return sorted(self._items.values(), key=lambda f: (order[f.severity], f.code))


def severity_counts(findings: Iterable[Finding]) -> dict[str, int]:
    counter = Counter(f.severity for f in findings)
    return {s: counter.get(s, 0) for s in SEVERITIES}
