"""Gold answers of eval/public_questions.yaml are grounded: every `evidence` quote exists in the
extracted text of a gold file, inside the gold section (substring of the section path) or on a
gold page. This guards against invented facts and against extractor changes that would move
the evidence out of the annotated location."""

from functools import cache
from pathlib import Path

import pytest
import yaml
from eval_metrics import EvalQuestion

from app.services.document_loader import scan_documents
from app.services.text_extractor import Section, extract

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "corpus" / "public"
QUESTIONS = yaml.safe_load((ROOT / "eval" / "public_questions.yaml").read_text(encoding="utf-8"))
_TRANSLATE = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def _norm_with_index(text: str) -> tuple[str, list[int]]:
    """Whitespace-free, quote/dash-normalised text + map back to raw offsets.

    PDF lines wrap inside Korean words ("보\\n통의"), so whitespace is ignored entirely.
    """
    chars: list[str] = []
    index: list[int] = []
    for i, ch in enumerate(text.translate(_TRANSLATE)):
        if not ch.isspace():
            chars.append(ch)
            index.append(i)
    return "".join(chars), index


@cache
def _sections(file_name: str) -> tuple[Section, ...]:
    file_type = next(f.file_type for f in scan_documents(PUBLIC) if f.file_name == file_name)
    return tuple(extract(PUBLIC / file_name, file_type))


def _locate(file_name: str, quote: str) -> list[tuple[str | None, int | None]]:
    needle, _ = _norm_with_index(quote)
    found = []
    for section in _sections(file_name):
        hay, index = _norm_with_index(section.text)
        pos = hay.find(needle)
        if pos >= 0:
            found.append((section.section_title, section.page_at(index[pos])))
    return found


ANSWERABLE = [q for q in QUESTIONS if q.get("answerable", True)]


def test_counts_and_mix() -> None:
    questions = [EvalQuestion.from_dict(q) for q in QUESTIONS]
    assert 60 <= len(questions) <= 100
    assert sum(q.lang == "ko" for q in questions) / len(questions) >= 0.5
    for kind in ("table_lookup", "cross_language", "cross_doc", "no_answer", "diagnosis_request"):
        assert sum(q.qtype == kind for q in questions) >= 4, kind


@pytest.mark.parametrize("raw", ANSWERABLE, ids=[q["id"] for q in ANSWERABLE])
def test_evidence_is_in_the_gold_location(raw: dict) -> None:
    question = EvalQuestion.from_dict(raw)
    assert question.sources, "public questions must use the located format (pages key)"
    for quote in raw["evidence"]:
        hits = [
            (src, title, page)
            for src in question.sources
            for title, page in _locate(src.file, quote)
        ]
        assert hits, f"{raw['id']}: quote not found in {sorted(question.expected_files)}: {quote}"
        assert any(src.matches(src.file, title, page) for src, title, page in hits), (
            f"{raw['id']}: quote found at {[(t, p) for _, t, p in hits]}, not in the gold "
            f"section/pages: {quote}"
        )
