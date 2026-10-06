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


def test_location_hit_uses_file_section_substring_or_page() -> None:
    raw = {
        "id": "p1",
        "type": "table_lookup",
        "question": "What does the Basic Profile do with Patient's Name?",
        "expected_sources": [
            {"file": "dicom.html", "section": "Table E.1-1.", "pages": []},
            {"file": "fda.pdf", "section": "Appendix A", "pages": [24]},
        ],
    }
    question = EvalQuestion.from_dict(raw)
    assert question.lang == "en" and question.qtype == "table_lookup"
    assert len(question.sources) == 2  # `pages` key present -> file-aware matching
    toy = EvalQuestion.from_dict({**raw, "expected_sources": [{"file": "a.md", "section": "X"}]})
    assert not toy.sources  # toy format (no pages key) keeps exact section-title matching
    located = EvalQuestion.from_dict(
        {**raw, "expected_sources": [{"file": "fda.pdf", "section": "Appendix A", "pages": [24]}]}
    )
    base = outcome(located, retrieved=("fda.pdf",), cited=("fda.pdf",))
    base.retrieved_sections = ["III > B. Something else"]
    base.retrieved_pages = [24]  # page match
    assert base.section_hit
    base.retrieved_pages = [3]
    assert not base.section_hit
    base.retrieved_sections = ["APPENDIX A: BEFORE IMAGING"]  # case-insensitive substring
    assert base.section_hit
    other_file = outcome(located, retrieved=("dicom.html",))
    other_file.retrieved_sections = ["APPENDIX A"]
    other_file.retrieved_pages = [24]
    assert not other_file.section_hit  # same section name in another file does not count


def test_korean_detection_and_grouping() -> None:
    from eval_metrics import refusal_reasons, summarize_by

    ko = EvalQuestion.from_dict({"id": "a", "question": "판독자는 몇 명?", "type": "no_answer"})
    en = EvalQuestion.from_dict({"id": "b", "question": "How many readers?"})
    assert (ko.lang, en.lang) == ("ko", "en")
    outs = [outcome(ko, refused=True), outcome(en)]
    groups = summarize_by(outs, lambda o: o.question.lang)
    assert set(groups) == {"ko", "en"} and groups["ko"]["questions"] == 1
    assert refusal_reasons(outs) == {"ANSWERED": 1, "NO_EVIDENCE": 1}


def test_public_question_set_is_well_formed() -> None:
    from eval_metrics import QUESTION_TYPES

    path = ROOT / "eval" / "public_questions.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    ids = [r["id"] for r in raw]
    assert len(ids) == len(set(ids)) and 60 <= len(raw) <= 100
    questions = [EvalQuestion.from_dict(r) for r in raw]
    assert all(q.qtype in QUESTION_TYPES for q in questions)
    assert sum(q.lang == "ko" for q in questions) >= len(questions) / 2
    public = ROOT / "corpus" / "public"
    for r, q in zip(raw, questions, strict=True):
        if q.answerable:
            assert q.expected_files and r.get("evidence") and r.get("answer_key"), q.id
            assert all((public / f).is_file() for f in q.expected_files), q.id
        else:
            assert q.qtype in {"no_answer", "diagnosis_request", "out_of_scope"}, q.id
