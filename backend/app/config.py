"""Application settings loaded from environment variables (see `.env.example`)."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class EmbeddingModelSpec:
    dimension: int
    query_prefix: str = ""
    document_prefix: str = ""


# Defaults for embedding models we have measured. Any other Ollama embedding model works too,
# but then EMBEDDING_DIM must be set explicitly (and the prefixes, if the model needs them).
KNOWN_EMBEDDING_MODELS: dict[str, EmbeddingModelSpec] = {
    # Multilingual (XLM-RoBERTa, 250k SentencePiece vocab incl. Hangul). No task prefixes.
    "bge-m3": EmbeddingModelSpec(1024),
    # English WordPiece vocab (30,522 tokens, no Hangul syllables): every Korean word -> [UNK].
    # See docs/issues/001-korean-embedding-unk.md. Trained with task prefixes.
    "nomic-embed-text": EmbeddingModelSpec(768, "search_query: ", "search_document: "),
}


def normalize_model_name(name: str) -> str:
    """`bge-m3:latest` and `bge-m3` are the same Ollama model."""
    return name.removesuffix(":latest")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa"

    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "gemma4:e4b"
    ollama_embedding_model: str = "bge-m3"
    # None = take the value from KNOWN_EMBEDDING_MODELS (required for unknown models).
    # Changing the dimension needs `make reset-embeddings` + reindex (vectors are not portable).
    embedding_dim: int | None = Field(default=None, ge=1, le=16000)
    # Task prefixes (nomic-embed-text: "search_query: " / "search_document: ", bge-m3: "").
    embedding_query_prefix: str | None = None
    embedding_document_prefix: str | None = None
    ollama_timeout_sec: float = 60.0
    ollama_max_retries: int = Field(default=3, ge=0)

    # --- Generation provider (embeddings always stay on local Ollama) ---
    llm_provider: Literal["ollama", "anthropic"] = "ollama"
    # External LLM opt-in. Requires BOTH this flag and a corpus marker file (see llm_guardrail).
    allow_external_llm: bool = False
    corpus_marker_file: str = ".corpus.yaml"
    anthropic_api_key: SecretStr | None = None  # read from ANTHROPIC_API_KEY only
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    anthropic_max_tokens: int = Field(default=16000, ge=256)
    anthropic_timeout_sec: float = 60.0
    anthropic_max_retries: int = Field(default=3, ge=0)
    anthropic_refusal_fallback: bool = True

    parse_concurrency: int = Field(default=2, ge=1)
    embed_concurrency: int = Field(default=4, ge=1)
    embed_batch_size: int = Field(default=16, ge=1)

    top_k: int = Field(default=5, ge=1, le=50)
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)
    min_relevance_score: float = Field(default=0.45, ge=-1.0, le=1.0)
    # Fuse pgvector ranking with a pg_trgm lexical ranking (RRF). See vector_search_service.
    # Off by default since bge-m3: no retrieval gain on the eval set (docs/issues/001); keep it
    # on for embedding models without Korean vocabulary.
    hybrid_search: bool = False
    rrf_k: int = Field(default=60, ge=1)
    # docs/issues/009: hnsw = approximate (index, default), exact = sequential scan with exact
    # cosine order (slower; reproducible regardless of what else is in the table).
    vector_search: Literal["hnsw", "exact"] = "hnsw"
    # pgvector 0.8 iterative index scans: keep scanning until filtered rows fill top_k.
    hnsw_iterative_scan: Literal["off", "relaxed_order", "strict_order"] = "off"
    # HNSW candidate list size (pgvector default 40). Larger = closer to exact, slower.
    hnsw_ef_search: int | None = Field(default=None, ge=1, le=1000)

    # Optional cross-encoder reranking (B7, needs `uv sync --extra rerank` and the model files in
    # the local Hugging Face cache or RERANKER_MODEL=<folder>). See services/reranker.py and
    # docs/decisions/0004-reranker.md. Retrieve RERANK_CANDIDATES by cosine, keep the best TOP_K
    # by cross-encoder score, and refuse (NO_EVIDENCE) when the best rerank score is below
    # RERANK_MIN_SCORE. The cosine gate (MIN_RELEVANCE_SCORE) still applies to the best candidate.
    reranker: Literal["none", "bge-reranker-v2-m3"] = "none"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"  # HF repo id (cache only) or a local folder
    reranker_revision: str = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    reranker_device: Literal["auto", "mps", "cuda", "cpu"] = "auto"
    rerank_candidates: int = Field(default=30, ge=1, le=200)
    rerank_min_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Return answers the model flagged as insufficient but that cite evidence, with a caveat
    # (docs/issues/007). False = MVP-1 behaviour: every flagged answer is a MODEL_REFUSED refusal.
    partial_answers: bool = True
    # Generator prompt. default = rag_prompt.txt as the system prompt (Korean, tuned on
    # gemma4:e4b). inline-en = EVAL-ONLY probe (docs/analysis/medgemma-vs-gemma4.md): English
    # instructions + one-shot examples in the user turn, answer in the question's language.
    rag_prompt_variant: Literal["default", "inline-en"] = "default"

    # OUT_OF_SCOPE (clinical-judgement request) detection, see services/scope_classifier.py.
    # embedding = precise regex + kNN margin over rules/scope_exemplars.yaml (default)
    # regex     = precise regex only;  mvp1 = the MVP-1 regex (baseline, over-refuses)
    scope_classifier: Literal["embedding", "regex", "mvp1"] = "embedding"
    # Refuse when mean top-k cosine(out_of_scope) - mean top-k cosine(in_scope) >= margin.
    # Tuned on the exemplars only (leave-one-out max Youden J with bge-m3, k=3 -> 0.056), not on
    # eval/scope_heldout.yaml. Re-run eval/run_scope_eval.py after changing model or exemplars.
    scope_margin: float = Field(default=0.056, ge=-1.0, le=1.0)
    scope_top_k: int = Field(default=3, ge=1)

    raw_docs_path: Path = Path("./data/raw-docs/documents")
    dicom_path: Path = Path("./data/raw-docs/dicom")
    samples_path: Path = Path("./samples")
    # Repo corpora (corpus/public, ...). Readable by /api/index like samples.
    corpora_path: Path = Path("./corpus")
    # Optional LOCAL-ONLY corpus folder outside the repo (e.g. ~/clinical-rag-private with a
    # `.corpus.yaml` classification: licensed-local-only). Added to the folders /api/index may
    # read; its documents are never searched in external-LLM mode (llm_guardrail).
    private_corpus_path: Path | None = None
    rules_path: Path = _APP_DIR / "rules"
    prompts_path: Path = _APP_DIR / "prompts"

    @field_validator("hnsw_ef_search", mode="before")
    @classmethod
    def _blank_ef_means_default(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("private_corpus_path", mode="before")
    @classmethod
    def _blank_path_means_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("embedding_dim", mode="before")
    @classmethod
    def _blank_dim_means_auto(cls, value: object) -> object:
        # docker compose passes `EMBEDDING_DIM: ${EMBEDDING_DIM:-}` as an empty string
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def _resolve_embedding_model(self) -> "Settings":
        spec = KNOWN_EMBEDDING_MODELS.get(normalize_model_name(self.ollama_embedding_model))
        if spec is None:
            if self.embedding_dim is None:
                raise ValueError(
                    f"EMBEDDING_DIM is required for unknown embedding model "
                    f"{self.ollama_embedding_model!r} (known: {sorted(KNOWN_EMBEDDING_MODELS)})"
                )
            spec = EmbeddingModelSpec(self.embedding_dim)
        elif self.embedding_dim is not None and self.embedding_dim != spec.dimension:
            raise ValueError(
                f"EMBEDDING_DIM={self.embedding_dim} does not match "
                f"{self.ollama_embedding_model} ({spec.dimension}-dim)"
            )
        self.embedding_dim = spec.dimension
        if self.embedding_query_prefix is None:
            self.embedding_query_prefix = spec.query_prefix
        if self.embedding_document_prefix is None:
            self.embedding_document_prefix = spec.document_prefix
        return self

    @property
    def embedding_dimension(self) -> int:
        assert self.embedding_dim is not None  # resolved by the validator
        return self.embedding_dim

    @property
    def allowed_roots(self) -> list[Path]:
        """Directories the API is allowed to read from (path traversal guard)."""
        roots = [self.raw_docs_path, self.dicom_path, self.samples_path, self.corpora_path]
        if self.private_corpus_path is not None:
            roots.append(self.private_corpus_path.expanduser())
        return [p.resolve() for p in roots]


@lru_cache
def get_settings() -> Settings:
    return Settings()
