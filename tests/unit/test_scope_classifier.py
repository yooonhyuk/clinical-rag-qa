"""OUT_OF_SCOPE classifier (B6): precise regex layer + embedding kNN margin layer."""

from pathlib import Path

import pytest

from app.config import Settings
from app.container import build_scope_classifier
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RagService, RefusalReason
from app.services.scope_classifier import (
    EmbeddingScopeClassifier,
    Mvp1RegexScopeClassifier,
    RegexScopeClassifier,
    ScopeExemplars,
    margin_score,
    mvp1_regex,
    request_regex,
)
from tests.fakes import FakeSession, make_chunk


@pytest.mark.parametrize(
    "question",
    [
        "이 환자의 CT에서 폐결절이 있나요?",
        "이 영상 판독해줘",
        "어떤 약을 처방해야 하나요?",
        "이 환자 PET에서 Deauville 4점이면 치료를 바꿔야 해?",
        "남편이 교모세포종 진단받았는데 약을 몇 mg 먹어야 하나요?",
        "Should we stop immunotherapy for this patient?",
        "Is a 14 mm node in my patient malignant?",
        "Read this CT for me please",
    ],
)
def test_request_regex_catches_explicit_requests(question: str) -> None:
    assert request_regex(question)


@pytest.mark.parametrize(
    "question",
    [
        # look-alikes the MVP-1 regex refused (it matched any 결절/병변/종양 mention)
        "폐결절 검출 AI 임상시험에서 판독자는 몇 명으로 구성하나요?",
        "림프절 표적병변은 단축 몇 mm 이상이어야 하나요?",
        "항암제 2상 시험에서 종양 반응을 독립적으로 검토하라고 하나요?",
        "RECIST에서 PD 기준이 뭐야?",
        "DICOM 분석 기능이 영상 판독을 수행하나요?",
        "암호화된 PDF는 어떻게 처리되나요?",
        "What is the definition of measurable disease in RANO 2.0?",
    ],
)
def test_request_regex_allows_document_questions(question: str) -> None:
    assert not request_regex(question)


def test_mvp1_regex_is_kept_as_a_baseline_and_over_refuses() -> None:
    assert mvp1_regex("폐결절 검출 AI 임상시험에서 판독자는 몇 명으로 구성하나요?")
    assert Mvp1RegexScopeClassifier().precheck("종양 반응 평가 주기는?") is not None


class _VectorClient:
    """Embeds by keyword so exemplar geometry is controlled: 'judge' words -> axis 0."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.extend(texts)
        out = []
        for t in texts:
            request = any(w in t for w in ("바꿔", "맞는 거죠", "stop", "recommend"))
            out.append([1.0, 0.1, 0.0] if request else [0.1, 1.0, 0.0])
        return out


def _classifier(margin: float = 0.0) -> tuple[EmbeddingScopeClassifier, _VectorClient]:
    client = _VectorClient()
    embeddings = EmbeddingService(client, dimension=3)
    exemplars = ScopeExemplars(
        out_of_scope=("약을 바꿔야 하나요", "should I stop it", "recommend a drug"),
        in_scope=("기준이 뭐야", "정의는?", "what is the threshold"),
    )
    return EmbeddingScopeClassifier(embeddings, exemplars, margin=margin, k=2), client


async def test_embedding_layer_refuses_paraphrased_requests_without_regex_cues() -> None:
    clf, client = _classifier()
    question = "SUVmax가 13이면 림프종 맞는 거죠?"
    assert not request_regex(question)
    decision = await clf.classify(question, [1.0, 0.1, 0.0])
    assert decision.out_of_scope and decision.method == "embedding" and decision.score > 0
    allowed = await clf.classify("Deauville 4의 정의는?", [0.1, 1.0, 0.0])
    assert not allowed.out_of_scope and allowed.method == "none" and allowed.score < 0
    # exemplars embedded once (6 texts), the query vectors were given -> no extra calls
    assert len(client.calls) == 6


async def test_regex_layer_short_circuits_before_embedding() -> None:
    clf, client = _classifier()
    decision = await clf.classify("이 환자 판독해줘")
    assert decision.method == "regex" and client.calls == []


def test_margin_score_is_mean_top_k_difference() -> None:
    q = [1.0, 0.0]
    pos = [[1.0, 0.0], [0.0, 1.0]]
    neg = [[0.0, 1.0]]
    assert margin_score(q, pos, neg, k=1) == pytest.approx(1.0)
    assert margin_score(q, pos, neg, k=2) == pytest.approx(0.5)


async def test_rag_service_refuses_on_embedding_decision_without_searching() -> None:
    clf, _ = _classifier()
    searched: list[str] = []

    async def search(session, vector, **_):
        searched.append("x")
        return [make_chunk()]

    class _Llm:
        provider = "ollama"

        async def embed(self, texts):
            return [[1.0, 0.1, 0.0] for _ in texts]

    embeddings = EmbeddingService(_Llm(), dimension=3)
    rag = RagService(embeddings, _Llm(), system_prompt="s", min_score=0.1, search=search, scope=clf)
    result = await rag.ask(FakeSession(), "SUVmax 13이면 림프종 맞는 거죠?", top_k=5)
    assert result.refused and result.refusal_reason == RefusalReason.OUT_OF_SCOPE
    assert result.meta["scope"]["method"] == "embedding" and searched == []


def test_container_picks_classifier_from_settings(tmp_path: Path) -> None:
    base = Settings(_env_file=None, database_url="x://unused")
    embeddings = EmbeddingService(_VectorClient(), dimension=3)
    assert isinstance(build_scope_classifier(base, embeddings), EmbeddingScopeClassifier)
    regex = base.model_copy(update={"scope_classifier": "regex"})
    assert type(build_scope_classifier(regex, embeddings)) is RegexScopeClassifier
    mvp1 = base.model_copy(update={"scope_classifier": "mvp1"})
    assert isinstance(build_scope_classifier(mvp1, embeddings), Mvp1RegexScopeClassifier)


def test_shipped_exemplars_load_and_are_balanced() -> None:
    settings = Settings(_env_file=None, database_url="x://unused")
    ex = ScopeExemplars.load(settings.rules_path / "scope_exemplars.yaml")
    assert len(ex.out_of_scope) >= 30 and len(ex.in_scope) >= 30
    assert not set(ex.out_of_scope) & set(ex.in_scope)


def test_margin_tuning_uses_leave_one_out_on_exemplars_only() -> None:
    from run_scope_eval import Confusion, tune_margin

    pos = [[1.0, 0.0], [0.9, 0.1], [0.95, 0.05]]
    neg = [[0.0, 1.0], [0.1, 0.9], [0.05, 0.95]]
    tuned = tune_margin(pos, neg, k=1)
    assert tuned["youden_j"] == 1.0
    assert all((s >= tuned["margin"]) == y for s, y in tuned["loo_scores"])

    cm = Confusion()
    for pred, actual in [(True, True), (True, False), (False, True), (False, False)]:
        cm.add(pred, actual)
    m = cm.metrics()
    assert (m["precision"], m["recall"], m["false_refusal_rate"]) == (0.5, 0.5, 0.5)


def test_heldout_set_does_not_overlap_exemplars() -> None:
    import yaml

    root = Path(__file__).resolve().parents[2]
    heldout = {h["q"] for h in yaml.safe_load((root / "eval/scope_heldout.yaml").read_text())}
    settings = Settings(_env_file=None, database_url="x://unused")
    ex = ScopeExemplars.load(settings.rules_path / "scope_exemplars.yaml")
    assert not heldout & (set(ex.out_of_scope) | set(ex.in_scope))
