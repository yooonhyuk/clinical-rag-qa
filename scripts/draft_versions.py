"""Draft a `.versions.yaml` for a corpus folder from its file names (the operator confirms it).

    uv run --project backend python scripts/draft_versions.py <corpus_dir> [--out PATH]

Nothing is decided here: the draft only lists what the names suggest, every entry carries a
`# 근거:` and `# 확인 필요` comment, and `superseded` is never written. Which edition hides which
is still decided by `doc_versions` (version number, or a manifest date) once the operator has
checked the draft and saved it as `<corpus_dir>/.versions.yaml` (docs/decisions/0006).

Rules (also printed at the top of the draft):
 a. files whose names carry the same edition family are listed together (family = folder + the
    name without edition/date tokens);
 b. a CANDIDATE bundle joins files of ONE folder and ONE format group (pdf / word / sheet /
    slides / text) that look like one document under another name: after removing edition and
    date tokens and trailing suffix words (clean, tracked, final, 구두보완, ...) the names are
    equal, or their similarity is >= 0.85 and their digits are identical. Names with two
    edition tokens (`v2.1 v2.2`, a change document) never join a bundle;
 c. when the editions of a family are equal or cannot be compared, the date in the file name is
    offered as `date`. It takes effect only after the operator confirms it (only dates written in
    the manifest are compared).
"""

import argparse
import glob
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date as Date
from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.doc_versions import (  # noqa: E402
    VersionInfo,
    compare_versions,
    infer_from_filename,
    name_core,
    normalize_family,
    parse_version_key,
    resolve_version,
)
from app.services.document_loader import scan_documents  # noqa: E402
from app.services.llm_guardrail import corpus_include  # noqa: E402

SIMILARITY = 0.85
MIN_SIMILAR_LENGTH = 8
SUFFIX_WORDS = frozenset(
    "clean tracked track final draft redline marked markup copy "
    "구두보완 보완 수정 수정본 반영 반영본 사본 송부 제출".split()
)
FORMAT_GROUPS = {
    ".pdf": "pdf",
    ".doc": "word",
    ".docx": "word",
    ".xls": "sheet",
    ".xlsx": "sheet",
    ".csv": "sheet",
    ".ppt": "slides",
    ".pptx": "slides",
}
MARKER = "# 확인 필요"


@dataclass(slots=True)
class Entry:
    path: str
    family: str
    version: str | None
    date: Date | None
    reasons: list[str]


@dataclass(slots=True)
class Draft:
    files: int = 0
    families: int = 0
    bundles: int = 0
    entries: list[Entry] = field(default_factory=list)

    @property
    def date_candidates(self) -> int:
        return sum(e.date is not None for e in self.entries)


def _strip_suffix_words(core: str) -> str:
    words = core.split()
    while len(words) > 1 and words[-1] in SUFFIX_WORDS:
        words.pop()
    return " ".join(words)


def _digits(text: str) -> list[str]:
    out, run = [], ""
    for ch in text:
        if ch.isdigit():
            run += ch
        elif run:
            out.append(run)
            run = ""
    return [*out, run] if run else out


def _similar(a: str, b: str) -> bool:
    if min(len(a), len(b)) < MIN_SIMILAR_LENGTH or _digits(a) != _digits(b):
        return False
    return SequenceMatcher(None, a, b).ratio() >= SIMILARITY


class _Union:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def join(self, a: int, b: int) -> None:
        self.parent[self.find(a)] = self.find(b)


def _folder(path: str) -> str:
    return PurePosixPath(path).parent.as_posix()


def _bundle_family(path: str, core: str) -> str:
    folder = _folder(path)
    return core if folder == "." else f"{folder}/{core}"


def draft_versions(paths: list[str]) -> Draft:
    """Draft entries for corpus-relative POSIX paths (names only; no file is opened)."""
    paths = sorted(paths)
    infos = [resolve_version(PurePosixPath(p).name, p) for p in paths]
    cores = [name_core(PurePosixPath(p).name) for p in paths]
    cores = [None if c is None else _strip_suffix_words(c) or None for c in cores]
    union = _Union(len(paths))

    by_family: dict[str, list[int]] = defaultdict(list)
    for i, info in enumerate(infos):
        if info.family is not None:
            by_family[info.family].append(i)
    for members in by_family.values():
        for i in members[1:]:
            union.join(members[0], i)

    def group(i: int) -> tuple[str, str]:
        suffix = PurePosixPath(paths[i]).suffix.lower()
        return _folder(paths[i]), FORMAT_GROUPS.get(suffix, suffix)

    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            ci, cj = cores[i], cores[j]
            if ci is None or cj is None or group(i) != group(j):
                continue
            if ci == cj or _similar(ci, cj):
                union.join(i, j)

    components: dict[int, list[int]] = defaultdict(list)
    for i in range(len(paths)):
        components[union.find(i)].append(i)

    draft = Draft(files=len(paths))
    for members in components.values():
        if len(members) < 2:
            continue
        families = {infos[i].family for i in members}
        if len(families) == 1 and None not in families:
            draft.families += 1
            family = next(iter(families))
            assert family is not None
            reason = "같은 family(파일명 판 토큰을 뺀 이름과 폴더가 같음)"
        else:
            draft.bundles += 1
            core = min((c for i in members if (c := cores[i])), key=len, default=None)
            if core is None:
                continue
            family = normalize_family(_bundle_family(paths[members[0]], core)) or core
            reason = (
                f"후보 묶음 #{draft.bundles}(같은 폴더·형식 계열, 접미어 차이 또는 이름 유사도)"
            )
        draft.entries.extend(_entries(paths, infos, members, family, reason))
    draft.entries.sort(key=lambda e: (e.family, e.path))
    return draft


def _entries(
    paths: list[str], infos: list[VersionInfo], members: list[int], family: str, reason: str
) -> list[Entry]:
    probes = [VersionInfo(family=family, label=infos[i].label, source="manifest") for i in members]
    need_date = any(
        compare_versions(a, b) not in (1, -1) for k, a in enumerate(probes) for b in probes[k + 1 :]
    )
    entries = []
    for i in sorted(members, key=lambda i: (parse_version_key(infos[i].label), paths[i])):
        info = infos[i]
        why = [reason]
        if info.label:
            why.append(f"파일명 판 토큰 {info.label}")
        else:
            why.append("판 토큰 없음")
        name_date = infer_from_filename(PurePosixPath(paths[i]).name).date
        date = None
        if need_date:
            if name_date is None:
                why.append("판이 같거나 비교 불가인데 파일명에 날짜도 없음 -> 날짜를 직접 확인")
            else:
                date = name_date
                why.append(
                    f"판이 같거나 비교 불가 -> 파일명 날짜 {name_date} 를 주석으로 둠"
                    " (날짜만 다른 이름이면 별개 문서일 수 있음)"
                )
        entries.append(Entry(paths[i], family, info.label, date, why))
    return entries


def render(draft: Draft) -> str:
    lines = [
        "# .versions.yaml 초안 - 파일명 추정이다. 확인·수정한 뒤 코퍼스 루트에 둔다.",
        "# 이 초안은 숨김을 확정하지 않는다(superseded 없음). 그대로 적용하면 판 번호로만",
        "# 최신판이 정해지고, 날짜로는 아무것도 숨기지 않는다.",
        "# 파일명 날짜는 주석(# date: ...)으로만 적혀 있다. 같은 문서의 판이 맞을 때만",
        "# 그 줄의 '# ' 두 글자만 지워라(들여쓰기는 그대로). 날짜만 다른 이름은",
        "# 별개 정기 문서(회의록·방문 보고서)일 수 있다.",
        "# 규칙: (a) 파일명 판 토큰을 뺀 이름·폴더가 같으면 같은 family.",
        "#   (b) 같은 폴더·형식 계열에서 판·날짜 토큰과 접미어(clean/tracked/final/구두보완 등)를",
        f"#       뺀 이름이 같거나 유사도 {SIMILARITY} 이상이고 숫자가 같으면 후보 묶음.",
        "#       판이 둘인 이름(v2.1 v2.2, 변경 문서)은 묶지 않는다.",
        "#   (c) 판이 같거나 비교 불가면 파일명 날짜를 주석 줄 `# date: ...` 로 둔다(효력 없음).",
        "versions:" if draft.entries else "versions: []",
    ]
    current = None
    for e in draft.entries:
        if e.family != current:
            current = e.family
            lines.append(f"  # --- family: {e.family}")
        lines.append(f"  # 근거: {'; '.join(e.reasons)}")
        lines.append(f"  {MARKER}")
        lines.append(f"  - match: {json.dumps(glob.escape(e.path), ensure_ascii=False)}")
        lines.append(f"    family: {json.dumps(e.family, ensure_ascii=False)}")
        if e.version:
            lines.append(f"    version: {json.dumps(e.version, ensure_ascii=False)}")
        if e.date:
            lines.append(f"    # date: {e.date.isoformat()}  # 확인 후 '# ' 두 글자만 지운다")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("corpus_dir", type=Path)
    parser.add_argument("--out", type=Path, help="write the draft here (default: stdout)")
    args = parser.parse_args()
    root = args.corpus_dir.expanduser().resolve()
    include = corpus_include(root, ".corpus.yaml")
    found = [f for f in scan_documents(root, include) if f.supported]
    draft = draft_versions([f.path.relative_to(root).as_posix() for f in found])
    text = render(draft)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    print(
        f"files {draft.files} · families {draft.families} · candidate bundles {draft.bundles}"
        f" · needs confirmation {len(draft.entries)} (date candidates {draft.date_candidates})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
