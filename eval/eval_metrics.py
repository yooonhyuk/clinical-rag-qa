"""Pure metric functions for the RAG eval (unit-tested; no IO).

Question file format (eval/questions.yaml = toy, eval/public_questions.yaml = public):

    - id: p01
      type: factual            # factual | table_lookup | cross_language | cross_doc |
                               # no_answer | diagnosis_request | out_of_scope  (default factual)
      lang: ko                 # optional; detected from Hangul in the question
      question: "..."
      answerable: true
      expected_sources:        # any listed file in top-k = hit
        - {file: a.pdf, section: "6.1.2.4 Evaluation of activity", pages: [12]}
      evidence: ["verbatim quote from the source"]   # gold passage (validated by tests)
      answer_key: "short answer written from that passage"
      must_include: ["2GB"]    # optional keyword check on the generated answer

Location ("section") hit: a retrieved chunk from an expected file whose section path contains
the expected `section` (case-insensitive), or whose page is in `pages`. Sources without section
and pages fall back to the file hit. The legacy toy format (section names only) keeps its
original meaning: any retrieved chunk whose section title equals an expected section.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from statistics import quantiles
from typing import Any

_HANGUL_RE = re.compile(r"[가-힣]")

QUESTION_TYPES = (
    "factual",
    "table_lookup",
    "cross_language",
    "cross_doc",
    "no_answer",
    "diagnosis_request",
    "out_of_scope",
)


@dataclass(frozen=True, slots=True)
class ExpectedSource:
    file: str
    section: str | None = None
    pages: frozenset[int] = frozenset()

    def matches(self, file: str, section: str | None, page: int | None) -> bool:
        if file != self.file:
            return False
        if self.section is None and not self.pages:
            return True
        if self.section and section and self.section.lower() in section.lower():
            return True
        return page is not None and page in self.pages


@dataclass(frozen=True, slots=True)
class EvalQuestion:
    id: str
    question: str
    expected_files: frozenset[str]
    expected_sections: frozenset[str]
    must_include: tuple[str, ...]
    answerable: bool
    qtype: str = "factual"
    lang: str = "ko"
    sources: tuple[ExpectedSource, ...] = ()
    answer_key: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EvalQuestion":
        sources = raw.get("expected_sources") or []
        question = raw["question"]
        # the new format always carries a `pages` key (possibly empty for XML/HTML)
        located = any("pages" in s for s in sources)
        return cls(
            id=raw["id"],
            question=question,
            expected_files=frozenset(s["file"] for s in sources),
            expected_sections=frozenset(s["section"] for s in sources if s.get("section")),
            must_include=tuple(raw.get("must_include") or ()),
            answerable=bool(raw.get("answerable", True)),
            qtype=raw.get("type", "factual"),
            lang=raw.get("lang") or ("ko" if _HANGUL_RE.search(question) else "en"),
            # file-aware location matching only for the new format; the toy set keeps exact
            # section-title matching
            sources=tuple(
                ExpectedSource(s["file"], s.get("section"), frozenset(s.get("pages") or ()))
                for s in sources
            )
            if located
            else (),
            answer_key=raw.get("answer_key", ""),
        )


@dataclass(slots=True)
class EvalOutcome:
    question: EvalQuestion
    retrieved_files: list[str]
    retrieved_sections: list[str | None]
    cited_files: list[str]
    answer: str
    refused: bool
    refusal_reason: str | None
    retrieval_ms: int
    generation_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    retrieved_pages: list[int | None] = field(default_factory=list)
    cited_sections: list[str | None] = field(default_factory=list)
    cited_pages: list[int | None] = field(default_factory=list)

    def _located(
        self, files: list[str], sections: list[str | None], pages: list[int | None]
    ) -> bool:
        if not self.question.sources:
            # legacy toy format: exact section title, any file
            return bool(self.question.expected_sections & {s for s in sections if s})
        pages = pages or [None] * len(files)
        return any(
            src.matches(f, s, p)
            for f, s, p in zip(files, sections, pages, strict=False)
            for src in self.question.sources
        )

    @property
    def hit(self) -> bool:
        return bool(self.question.expected_files & set(self.retrieved_files))

    @property
    def section_hit(self) -> bool:
        if not self.question.expected_sections and not self.question.sources:
            return self.hit
        return self._located(self.retrieved_files, self.retrieved_sections, self.retrieved_pages)

    @property
    def citation_correct(self) -> bool:
        cited = set(self.cited_files)
        return bool(cited) and cited <= self.question.expected_files

    @property
    def citation_located(self) -> bool:
        """At least one cited chunk is in an expected section/page (file only if none given)."""
        if not self.cited_files:
            return False
        if not self.question.expected_sections and not self.question.sources:
            return bool(set(self.cited_files) & self.question.expected_files)
        sections = self.cited_sections or [None] * len(self.cited_files)
        return self._located(self.cited_files, sections, self.cited_pages)

    @property
    def keyword_coverage(self) -> float:
        terms = self.question.must_include
        if not terms:
            return 1.0
        answer = self.answer.lower()
        return sum(t.lower() in answer for t in terms) / len(terms)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def percentile(values: list[int], pct: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    return quantiles(values, n=100, method="inclusive")[pct - 1]


def summarize(outcomes: list[EvalOutcome]) -> dict[str, Any]:
    ok = [o for o in outcomes if o.error is None]
    answerable = [o for o in ok if o.question.answerable]
    unanswerable = [o for o in ok if not o.question.answerable]
    answered = [o for o in answerable if not o.refused]
    generated = [o for o in ok if o.generation_ms > 0]
    totals = [o.retrieval_ms + o.generation_ms for o in ok]
    tokens_in = [o.input_tokens for o in ok if o.input_tokens is not None]
    tokens_out = [o.output_tokens for o in ok if o.output_tokens is not None]
    return {
        "questions": len(outcomes),
        "errors": len(outcomes) - len(ok),
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        "hit_at_k": _ratio(sum(o.hit for o in answerable), len(answerable)),
        "section_hit_at_k": _ratio(sum(o.section_hit for o in answerable), len(answerable)),
        "citation_correctness": _ratio(sum(o.citation_correct for o in answered), len(answered)),
        "citation_location": _ratio(sum(o.citation_located for o in answered), len(answered)),
        "keyword_coverage": (
            sum(o.keyword_coverage for o in answered) / len(answered) if answered else None
        ),
        "refusal_correctness": _ratio(sum(o.refused for o in unanswerable), len(unanswerable)),
        "false_refusal_rate": _ratio(sum(o.refused for o in answerable), len(answerable)),
        "retrieval_ms_p50": percentile([o.retrieval_ms for o in ok], 50),
        "retrieval_ms_p95": percentile([o.retrieval_ms for o in ok], 95),
        "generation_ms_p50": percentile([o.generation_ms for o in generated], 50),
        "generation_ms_p95": percentile([o.generation_ms for o in generated], 95),
        "total_ms_p50": percentile(totals, 50),
        "total_ms_p95": percentile(totals, 95),
        "input_tokens_total": sum(tokens_in) if tokens_in else None,
        "output_tokens_total": sum(tokens_out) if tokens_out else None,
    }


def summarize_by(
    outcomes: list[EvalOutcome], key: Callable[[EvalOutcome], str]
) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[EvalOutcome]] = {}
    for o in outcomes:
        groups.setdefault(key(o), []).append(o)
    return {name: summarize(items) for name, items in sorted(groups.items())}


def refusal_reasons(outcomes: list[EvalOutcome]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for o in outcomes:
        name = str(o.refusal_reason) if o.refusal_reason else "ANSWERED"
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def failed_questions(outcomes: list[EvalOutcome]) -> list[tuple[str, str]]:
    """(id, reason) for every question that missed at least one applicable metric."""
    failures: list[tuple[str, str]] = []
    for o in outcomes:
        q = o.question
        if o.error:
            failures.append((q.id, f"error: {o.error}"))
        elif not q.answerable and not o.refused:
            failures.append((q.id, "should refuse but answered"))
        elif q.answerable and o.refused:
            failures.append((q.id, f"false refusal ({o.refusal_reason})"))
        elif q.answerable:
            reasons = []
            if not o.hit:
                reasons.append(f"retrieval miss (got {sorted(set(o.retrieved_files))})")
            elif not o.section_hit:
                reasons.append("section/page miss")
            if not o.citation_correct:
                reasons.append(f"citation {sorted(set(o.cited_files))}")
            if o.keyword_coverage < 1:
                reasons.append(f"keywords {o.keyword_coverage:.0%}")
            if reasons:
                failures.append((q.id, "; ".join(reasons)))
    return failures
