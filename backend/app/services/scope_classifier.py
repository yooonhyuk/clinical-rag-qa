"""OUT_OF_SCOPE detection: is the question a clinical-judgement request (B6)?

Two layers, both local (no new model, no download):

1. `request_regex` - precise request phrasings about a specific person / scan / result
   ("이 환자 ...", "판독해 줘", "my patient", "should we stop ..."). A hit refuses without any
   embedding call. Deliberately narrower than the MVP-1 regex, which matched any mention of
   "결절/병변/종양" and so refused document questions such as "폐결절 AI 기기 임상시험에서
   판독자는 몇 명?" (see eval/run_scope_eval.py for the measured difference).
2. `EmbeddingScopeClassifier` - kNN over labelled exemplars (`rules/scope_exemplars.yaml`)
   with the same embedding model as retrieval (bge-m3 by default, multilingual):
       score = mean top-k cosine to out_of_scope exemplars - mean top-k cosine to in_scope ones
   and refuses when `score >= margin`. The query vector is the one retrieval needs anyway, so
   the classifier adds no extra embedding call per question; exemplar vectors are computed
   once, lazily.

`MVP1_OUT_OF_SCOPE_RE` is kept only as a measured baseline.
"""

import asyncio
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from app.services.embedding_service import EmbeddingService

# MVP-1 heuristic (baseline only).
MVP1_OUT_OF_SCOPE_RE = re.compile(
    r"(결절|병변|종양|암\s*(이|인지|일까|여부)|악성|양성인지|"
    r"진단(해|을\s*내려|명)|판독\s*(해|결과|소견)|소견(을|이)\s*(알려|뭐)|"
    r"처방|투약|복용|용량을|치료\s*(방법|법|해야)|어떤\s*약)"
)

# A request about a specific person / scan / result: subject cue + request cue ...
_KO_SUBJECT = (
    r"(?<![가-힣])(이|그|저|우리|제|내)\s*(환자|영상|사진|CT|MRI|MR|PET|스캔|결절|병변|종양|림프절|검사|판독지|"
    r"결과지)|아버지|어머니|엄마|아빠|남편|아내|할머니|할아버지|가족|아들|딸"
)
_KO_REQUEST = (
    r"판독|진단|처방|"
    r"(암|악성|양성|전이|재발|진행)(인가요|인지|일까|이에요|예요|일 확률|맞나요|인 거죠)|"
    r"(치료|약|항암제?|요법)(를|을)?\s*(바꿔|중단|그만|계속|추천|결정)|"
    r"(써도|맞아도|먹어도|투여해도|받아도)\s*(되|괜찮)|용량을?\s*(얼마|몇)|몇\s*mg|"
    r"수술해야|조직검사를?\s*해야|얼마나\s*(사실|살)"
)
# ... or a phrasing that is a request on its own.
_KO_STANDALONE = (
    r"(판독|진단|처방)\s*해\s*(줘|주세요|줄래|달라|주실)|처방해야|"
    r"(결절|병변|종양|종괴)(이|가)\s*(있나요|있어요|보이나요|맞나요)|"
    r"(암|악성)(인지|인가요|일까요?)\s*(알려|봐|판단)?|"
    r"(재발|전이|가성진행)(인지|일까요?)\s*(봐|알려|판단|구분)"
)
_EN_SUBJECT = (
    r"\b(my|our|this|the attached|the patient i)\s+"
    r"(patient|scan|ct|mri|pet|x-ray|nodule|lesion|report|mother|father|dad|mom)"
)
_EN_REQUEST = (
    r"\b(read|interpret)\s+(this|my|the attached)\b|\bdiagnose\b|"
    r"\bshould\s+(i|we)\s+(stop|continue|start|switch|change|give|escalate|prescribe)\b|"
    r"\bis\s+(it|this|the \w+)\s+(cancer|malignant|benign)\b|"
    r"\bwhat\s+(dose|drug|regimen)\b.*\b(i|we|my|our)\b|\bhow long does (my|our)\b"
)
_REQUEST_RE = re.compile(
    rf"(({_KO_SUBJECT}).*({_KO_REQUEST}))|({_KO_STANDALONE})|({_EN_SUBJECT})|({_EN_REQUEST})",
    re.IGNORECASE,
)


def request_regex(question: str) -> bool:
    """Precise request patterns (layer 1)."""
    return bool(_REQUEST_RE.search(question))


def mvp1_regex(question: str) -> bool:
    return bool(MVP1_OUT_OF_SCOPE_RE.search(question))


@dataclass(frozen=True, slots=True)
class ScopeDecision:
    out_of_scope: bool
    method: Literal["regex", "embedding", "none"]
    score: float | None = None  # embedding margin score (positive = looks like a request)


@dataclass(frozen=True, slots=True)
class ScopeExemplars:
    out_of_scope: tuple[str, ...]
    in_scope: tuple[str, ...]

    @classmethod
    def load(cls, path: Path) -> "ScopeExemplars":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(tuple(data.get("out_of_scope") or ()), tuple(data.get("in_scope") or ()))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _top_k_mean(query: list[float], vectors: list[list[float]], k: int) -> float:
    sims = sorted((_cosine(query, v) for v in vectors), reverse=True)[:k]
    return sum(sims) / len(sims) if sims else 0.0


def margin_score(
    query: list[float], positives: list[list[float]], negatives: list[list[float]], k: int
) -> float:
    return _top_k_mean(query, positives, k) - _top_k_mean(query, negatives, k)


class RegexScopeClassifier:
    """Layer 1 only (SCOPE_CLASSIFIER=regex; the RagService default so unit tests need no
    exemplar embeddings)."""

    needs_vector = False

    def precheck(self, question: str) -> ScopeDecision | None:
        return ScopeDecision(True, "regex") if request_regex(question) else None

    async def classify(
        self, question: str, query_vector: list[float] | None = None
    ) -> ScopeDecision:
        return self.precheck(question) or ScopeDecision(False, "none")


class Mvp1RegexScopeClassifier(RegexScopeClassifier):
    """The MVP-1 heuristic, kept as a measurable baseline (SCOPE_CLASSIFIER=mvp1)."""

    def precheck(self, question: str) -> ScopeDecision | None:
        return ScopeDecision(True, "regex") if mvp1_regex(question) else None


class EmbeddingScopeClassifier:
    """Layer 1 regex + layer 2 kNN margin over exemplar embeddings."""

    needs_vector = True

    def __init__(
        self,
        embeddings: EmbeddingService,
        exemplars: ScopeExemplars,
        *,
        margin: float,
        k: int = 3,
    ) -> None:
        self._embeddings = embeddings
        self._exemplars = exemplars
        self.margin = margin
        self._k = k
        self._vectors: tuple[list[list[float]], list[list[float]]] | None = None
        self._lock = asyncio.Lock()

    async def _exemplar_vectors(self) -> tuple[list[list[float]], list[list[float]]]:
        if self._vectors is None:
            async with self._lock:
                if self._vectors is None:
                    pos = await self._embeddings.embed_queries(self._exemplars.out_of_scope)
                    neg = await self._embeddings.embed_queries(self._exemplars.in_scope)
                    self._vectors = (pos, neg)
        return self._vectors

    async def score(self, query_vector: list[float]) -> float:
        pos, neg = await self._exemplar_vectors()
        return margin_score(query_vector, pos, neg, self._k)

    def precheck(self, question: str) -> ScopeDecision | None:
        return ScopeDecision(True, "regex") if request_regex(question) else None

    async def classify(
        self, question: str, query_vector: list[float] | None = None
    ) -> ScopeDecision:
        if decision := self.precheck(question):
            return decision
        if query_vector is None:
            query_vector = await self._embeddings.embed_query(question)
        score = await self.score(query_vector)
        refuse = score >= self.margin
        return ScopeDecision(refuse, "embedding" if refuse else "none", score)
