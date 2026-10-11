"""Document versions: where a version comes from and which one is the latest (pure functions).

Several editions of one document in a corpus make search return the old edition and answers
quote it as if it were current (docs/issues/005, docs/decisions/0006-document-versions.md).

Two sources, the explicit one wins:
1. `.corpus.yaml` `versions:` - entries `{match, family, version, date, superseded}`; `match` is
   a glob against the path relative to the corpus root (or just the file name).
2. The file name: a version token (`v2.1`, `ver 3`, `Rev6`, `(R3)`, `E6R3`, `Amendment 2`, `개정`,
   `최종`). A bare `R1`/`R01` is an identifier, not an edition. What is left after removing the
   tokens, with the folder it sits in, is the `family` key. A date alone is NOT an edition
   (minutes, visit reports and lot records differ by date): it is kept for display, the name has
   no family and nothing is hidden. A name without any token is a standalone document.

Latest = nobody in the same (corpus, family) is strictly newer. Versions compare numerically
within one kind (v / R / Amendment). A date is compared only when both documents got it from the
manifest; a date read from a file name never decides anything. Incomparable or equal means BOTH
stay latest.
Hiding a document is the costly mistake, so every doubt keeps it visible. `superseded: true`
(manifest only) removes a document from the latest set unless the whole family is superseded.
"""

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date as Date
from datetime import datetime
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import Any, Literal

VersionSource = Literal["manifest", "filename", "none"]

# one tuple per kind: ("ver", (2, 10)) etc.; trailing zeros are dropped so 2.0 == 2
VersionKey = tuple[tuple[str, tuple[int, ...]], ...]
_KIND_ORDER = ("ver", "rev", "amd")  # compared in this order when both sides have the kind

_FILE_SUFFIXES = (".pdf", ".docx", ".xlsx", ".md", ".markdown", ".txt", ".xml", ".html", ".htm")
_NUM = r"(\d+(?:\.\d+)*)"
_A = "0-9A-Za-z"  # ASCII alphanumerics: a Latin token must not touch these
_L, _R = f"(?<![{_A}])", f"(?![{_A}])"  # Latin-token boundaries ("_" counts as a separator)

_DATE_RE = re.compile(
    r"(?<!\d)((?:19|20)\d{2})(?:([-._])?(\d{2})\2?(\d{2}))(?!\d)"
)  # 20250915, 2025-09-15, 2025.09.15, 2025_09_15
_ID_BEFORE = "|".join(f"(?<=[A-Za-z]{'\\d' * n})" for n in (1, 2, 3))  # E6R3, E10R3, M14R2
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("amd", re.compile(rf"{_L}amend(?:ment)?\.?\s*{_NUM}{_R}", re.I)),
    ("rev", re.compile(r"제?\s*\d+\s*차\s*개정")),
    ("rev", re.compile(r"개정\s*\d+")),
    ("rev", re.compile(rf"{_L}rev(?:ision)?\.?\s*{_NUM}{_R}", re.I)),
    ("ver", re.compile(rf"{_L}ver(?:sion)?\.?\s*{_NUM}{_R}", re.I)),
    ("ver", re.compile(rf"{_L}v\.?{_NUM}{_R}", re.I)),
    # a bare R1/R01/R2 is a site, grant or model id: only "(R3)" or an id in front ("E6R3")
    ("rev", re.compile(rf"\(\s*(?P<label>r(?!0\d){_NUM})\s*\)", re.I)),
    ("rev", re.compile(rf"(?:{_ID_BEFORE})(?P<label>r(?!0\d){_NUM}){_R}", re.I)),
)
_LOOSE_R = re.compile(
    rf"{_L}r(?!0\d){_NUM}{_R}", re.I
)  # labels already vetted ("R3" from a manifest)
_BARE_WORDS = re.compile(r"개정|최종")  # a token without a number: removed from the family, no key
_BARE_NUMBER = re.compile(rf"^\s*{_NUM}\s*$")


@dataclass(frozen=True, slots=True)
class VersionInfo:
    family: str | None = None
    label: str | None = None
    date: Date | None = None
    source: VersionSource = "none"
    superseded: bool = False


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    match: str
    family: str
    version: str | None = None
    date: Date | None = None
    superseded: bool = False


def _strip_suffix(name: str) -> str:
    lowered = name.lower()
    for suffix in _FILE_SUFFIXES:
        if lowered.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _numbers(text: str) -> tuple[int, ...]:
    parts = [int(p) for p in text.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _parse_date(year: str, month: str, day: str) -> Date | None:
    try:
        return Date(int(year), int(month), int(day))
    except ValueError:
        return None


def _scan(text: str) -> tuple[str, list[tuple[int, str, str | None]], Date | None]:
    """(text with tokens blanked, [(position, label piece, kind)], first date found)."""
    found: list[tuple[int, str, str | None]] = []
    when: Date | None = None

    def blank(m: re.Match[str]) -> str:
        return " " * len(m.group(0))

    def take_date(m: re.Match[str]) -> str:
        nonlocal when
        parsed = _parse_date(m.group(1), m.group(3), m.group(4))
        if parsed is None:
            return m.group(0)
        when = when or parsed
        return blank(m)

    text = _DATE_RE.sub(take_date, text)
    for kind, pattern in _PATTERNS:

        def take(m: re.Match[str], kind: str = kind) -> str:
            found.append((m.start(), (m.groupdict().get("label") or m.group(0)).strip(), kind))
            return blank(m)

        text = pattern.sub(take, text)

    def take_bare(m: re.Match[str]) -> str:
        found.append((m.start(), m.group(0), None))
        return blank(m)

    text = _BARE_WORDS.sub(take_bare, text)
    return text, found, when


def _family_key(rest: str) -> str | None:
    rest = unicodedata.normalize("NFC", rest).casefold()
    rest = re.sub(r"[^0-9a-zㄱ-ㆎ가-힣]+", " ", rest).strip()
    return rest or None


def normalize_family(value: str) -> str | None:
    """Same normalisation for manifest families and filename-derived ones."""
    return _family_key(value)


def parse_version_key(label: str | None) -> VersionKey:
    """Comparable key of a version label ("v2.1 Amendment 2", "R3", "3"); () = not comparable."""
    if not label:
        return ()
    rest, found, _ = _scan(label)
    found = [*found, *((m.start(), m.group(0), "rev") for m in _LOOSE_R.finditer(rest))]
    numbers: dict[str, tuple[int, ...]] = {}
    for _, piece, kind in sorted(found):
        if kind is None:
            continue
        match = re.search(r"\d+(?:\.\d+)*", piece)
        if match:
            numbers.setdefault(kind, _numbers(match.group(0)))
    if not numbers and (bare := _BARE_NUMBER.match(label)):
        numbers["ver"] = _numbers(bare.group(1))
    return tuple((kind, numbers[kind]) for kind in _KIND_ORDER if kind in numbers)


def infer_from_filename(file_name: str) -> VersionInfo:
    """Version and family from the file name alone. No edition token -> no family (standalone);
    a date alone is kept as the date but never makes a family."""
    text, found, when = _scan(_strip_suffix(file_name))
    if not found:
        return VersionInfo() if when is None else VersionInfo(date=when, source="filename")
    label = " ".join(piece for _, piece, _ in sorted(found)) or None
    return VersionInfo(family=_family_key(text), label=label, date=when, source="filename")


def parse_manifest(raw: object) -> list[ManifestEntry]:
    """`versions:` of a `.corpus.yaml`; malformed entries are ignored (-> inference)."""
    if not isinstance(raw, list):
        return []
    entries: list[ManifestEntry] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        match, family = item.get("match"), item.get("family")
        if not isinstance(match, str) or not match or not isinstance(family, str):
            continue
        if normalize_family(family) is None:
            continue
        version = item.get("version")
        entries.append(
            ManifestEntry(
                match=match,
                family=family,
                version=None if version is None else str(version).strip() or None,
                date=_as_date(item.get("date")),
                superseded=item.get("superseded") is True,
            )
        )
    return entries


def _as_date(value: Any) -> Date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, Date):
        return value
    if isinstance(value, str):
        try:
            return Date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def resolve_version(
    file_name: str, relative_path: str | None = None, manifest: Sequence[ManifestEntry] = ()
) -> VersionInfo:
    """Manifest entry (first match) if any, else the file name inference."""
    candidates = [file_name] if relative_path is None else [relative_path, file_name]
    for entry in manifest:
        if any(fnmatchcase(c, entry.match) for c in candidates):
            return VersionInfo(
                family=normalize_family(entry.family),
                label=entry.version,
                date=entry.date,
                source="manifest",
                superseded=entry.superseded,
            )
    inferred = infer_from_filename(file_name)
    if inferred.family is None or relative_path is None:
        return inferred
    # same file name in another folder is another document (Protocol_v2 of study A vs B)
    folders = (
        _family_key(part) for part in PurePosixPath(relative_path.replace("\\", "/")).parent.parts
    )
    prefix = "/".join(part for part in folders if part)
    family = f"{prefix}/{inferred.family}" if prefix else inferred.family
    return replace(inferred, family=family)


def compare_versions(a: VersionInfo, b: VersionInfo) -> int | None:
    """1 if `a` is newer, -1 if older, 0 if equal, None if they cannot be compared."""
    keys_a, keys_b = dict(parse_version_key(a.label)), dict(parse_version_key(b.label))
    for kind in _KIND_ORDER:
        if kind in keys_a and kind in keys_b and keys_a[kind] != keys_b[kind]:
            return 1 if keys_a[kind] > keys_b[kind] else -1
    # a date from a file name is never a reason to hide anything (minutes, visit reports and
    # weekly reports share a form version and differ by date); only dates the manifest states
    # on both sides are compared
    if a.date is not None and b.date is not None and a.source == b.source == "manifest":
        if a.date != b.date:
            return 1 if a.date > b.date else -1
        return 0
    return 0 if keys_a.keys() & keys_b.keys() else None


def latest_flags(items: Sequence[VersionInfo], groups: Sequence[object]) -> list[bool]:
    """`is_latest` per item. `groups[i]` is the scope (e.g. the corpus) of item i; documents are
    compared only within the same (group, family). No family = standalone = always latest."""
    flags = [True] * len(items)
    members: dict[tuple[object, str], list[int]] = {}
    for i, (info, group) in enumerate(zip(items, groups, strict=True)):
        if info.family is not None:
            members.setdefault((group, info.family), []).append(i)
    for indexes in members.values():
        live = [i for i in indexes if not items[i].superseded]
        for i in indexes:
            if items[i].superseded and live:
                flags[i] = False  # replaced explicitly, and something replaces it
        pool = live or indexes  # whole family superseded: fall back to comparing everyone
        for i in pool:
            if any(compare_versions(items[j], items[i]) == 1 for j in pool if j != i):
                flags[i] = False
    return flags
