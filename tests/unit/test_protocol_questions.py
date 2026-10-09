"""Gold evidence of the LOCAL-ONLY protocol eval set (copyrighted sponsor protocols / SAPs).

The questions and the PDFs never enter the repository, so this test reads them from local paths
and is skipped when they are absent (CI, other machines):

    PROTOCOL_QUESTIONS   default ~/clinical-rag-private/eval/protocol_questions.yaml
    PRIVATE_CORPUS_DIR   default ~/clinical-rag-private  (searched recursively for gold files)

Same checks as test_public_questions: every `evidence` quote exists in the extracted text of a
gold file, inside the gold section (substring of the section path) or on a gold page. The
schema is the one of eval/protocol_questions.template.yaml (committed, without quotes).
"""

import os
from functools import cache
from pathlib import Path

import pytest
import yaml
from eval_metrics import EvalQuestion

from app.services.document_loader import scan_documents
from app.services.text_extractor import Section, extract
from tests.unit.test_public_questions import _norm_with_index

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = Path(
    os.getenv("PROTOCOL_QUESTIONS", "~/clinical-rag-private/eval/protocol_questions.yaml")
).expanduser()
CORPUS = Path(os.getenv("PRIVATE_CORPUS_DIR", "~/clinical-rag-private")).expanduser()
TEMPLATE = ROOT / "eval" / "protocol_questions.template.yaml"

QUESTIONS: list[dict] = (
    yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8")) if QUESTIONS_PATH.is_file() else []
)
local_only = pytest.mark.skipif(
    not QUESTIONS or not CORPUS.is_dir(),
    reason=f"local-only eval set not present ({QUESTIONS_PATH}, {CORPUS})",
)
TYPES = (
    "imaging_schedule",
    "bicr_process",
    "response_criteria",
    "eligibility_imaging",
    "sap_endpoint",
    "cross_trial",
    "cross_doc",
    "no_answer",
    "diagnosis_request",
    "out_of_scope",
)
MUST_REFUSE = {"no_answer", "diagnosis_request", "out_of_scope"}


@cache
def _files() -> dict[str, Path]:
    return {f.file_name: f.path for f in scan_documents(CORPUS) if f.file_type == "pdf"}


@cache
def _sections(file_name: str) -> tuple[Section, ...]:
    return tuple(extract(_files()[file_name], "pdf"))


def _locate(file_name: str, quote: str) -> list[tuple[str | None, int | None]]:
    needle, _ = _norm_with_index(quote)
    found = []
    for section in _sections(file_name):
        hay, index = _norm_with_index(section.text)
        pos = hay.find(needle)
        if pos >= 0:
            found.append((section.section_title, section.page_at(index[pos])))
    return found


def test_template_has_the_schema_but_no_document_text() -> None:
    """The committed template documents the format; quotes stay in the local file only."""
    items = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    assert {item["type"] for item in items} <= set(TYPES)
    for item in items:
        EvalQuestion.from_dict(item)  # same schema as the real set
        for quote in item.get("evidence", []):
            assert quote.startswith("<") and quote.endswith(">"), quote


@local_only
def test_counts_and_mix() -> None:
    questions = [EvalQuestion.from_dict(q) for q in QUESTIONS]
    assert 60 <= len(questions) <= 100
    assert sum(q.lang == "ko" for q in questions) / len(questions) >= 0.5
    assert {q.qtype for q in questions} == set(TYPES)
    for q in questions:
        assert q.answerable == (q.qtype not in MUST_REFUSE), q.id
    assert len({q.id for q in questions}) == len(questions)


ANSWERABLE = [q for q in QUESTIONS if q.get("answerable", True)]


@local_only
@pytest.mark.parametrize("raw", ANSWERABLE, ids=[q["id"] for q in ANSWERABLE])
def test_evidence_is_in_the_gold_location(raw: dict) -> None:
    question = EvalQuestion.from_dict(raw)
    assert question.sources, "protocol questions must use the located format (pages key)"
    for src in question.sources:
        assert src.file in _files(), f"{raw['id']}: gold file {src.file} not in {CORPUS}"
    for quote in raw["evidence"]:
        hits = [
            (src, title, page)
            for src in question.sources
            for title, page in _locate(src.file, quote)
        ]
        assert hits, f"{raw['id']}: quote not found in {sorted(question.expected_files)}"
        assert any(src.matches(src.file, title, page) for src, title, page in hits), (
            f"{raw['id']}: quote found at {[(t, p) for _, t, p in hits]}, not in the gold "
            "section/pages"
        )
