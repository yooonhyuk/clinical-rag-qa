from pathlib import Path

import yaml
from eval_metrics import EvalOutcome, EvalQuestion, failed_questions, percentile, summarize

ROOT = Path(__file__).resolve().parents[2]


def q(qid: str, answerable: bool = True, files=("a.md",), must=("2GB",)) -> EvalQuestion:
    return EvalQuestion(
        id=qid,
        question="?",
        expected_files=frozenset(files if answerable else ()),
        expected_sections=frozenset(),
        must_include=tuple(must if answerable else ()),
        answerable=answerable,
    )


def outcome(question, *, retrieved=("a.md",), cited=("a.md",), answer="2GB", refused=False):
    return EvalOutcome(
        question=question,
        retrieved_files=list(retrieved),
        retrieved_sections=[None] * len(retrieved),
        cited_files=list(cited),
        answer=answer,
        refused=refused,
        refusal_reason="NO_EVIDENCE" if refused else None,
        retrieval_ms=10,
        generation_ms=0 if refused else 1000,
        input_tokens=100,
        output_tokens=20,
    )


def test_summary_metrics() -> None:
    outcomes = [
        outcome(q("q1")),  # perfect
        outcome(q("q2"), retrieved=("b.md",), cited=("b.md",), answer="없음"),  # miss
        outcome(q("q3"), refused=True, cited=(), answer="문서에서 확인할 수 없습니다."),
        outcome(q("q4", answerable=False), refused=True, cited=()),  # correct refusal
        outcome(q("q5", answerable=False), cited=("a.md",)),  # wrongly answered
    ]
    s = summarize(outcomes)
    assert s["hit_at_k"] == 2 / 3  # q3 retrieved a.md before refusing
    assert s["citation_correctness"] == 1 / 2  # among answered answerable (q1, q2)
    assert s["keyword_coverage"] == 1 / 2
    assert s["refusal_correctness"] == 1 / 2
    assert s["false_refusal_rate"] == 1 / 3
    assert s["input_tokens_total"] == 500
    ids = dict(failed_questions(outcomes))
    assert set(ids) == {"q2", "q3", "q5"}
    assert "false refusal" in ids["q3"] and "should refuse" in ids["q5"]


def test_percentile() -> None:
    assert percentile([], 50) is None
    assert percentile([5], 95) == 5
    assert percentile(list(range(1, 101)), 50) == 50.5


def test_question_set_shape() -> None:
    raw = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text(encoding="utf-8"))
    questions = [EvalQuestion.from_dict(r) for r in raw]
    assert 20 <= len(questions) <= 30
    assert len({x.id for x in questions}) == len(questions)
    refuse = sum(not x.answerable for x in questions)
    assert 0.2 <= refuse / len(questions) <= 0.3
    sample_files = {p.name for p in (ROOT / "samples" / "documents").iterdir()}
    for x in questions:
        assert x.expected_files <= sample_files, x.id
        assert x.answerable == bool(x.expected_files), x.id
