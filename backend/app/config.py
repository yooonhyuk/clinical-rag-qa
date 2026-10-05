"""Application settings loaded from environment variables (see `.env.example`)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa"
    embedding_dim: int = 768

    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "gemma4:e4b"
    ollama_embedding_model: str = "nomic-embed-text"
    # nomic-embed-text is trained with task prefixes; set both to "" for models that are not.
    embedding_query_prefix: str = "search_query: "
    embedding_document_prefix: str = "search_document: "
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
    hybrid_search: bool = True
    rrf_k: int = Field(default=60, ge=1)

    raw_docs_path: Path = Path("./data/raw-docs/documents")
    dicom_path: Path = Path("./data/raw-docs/dicom")
    samples_path: Path = Path("./samples")
    rules_path: Path = _APP_DIR / "rules"
    prompts_path: Path = _APP_DIR / "prompts"

    @property
    def allowed_roots(self) -> list[Path]:
        """Directories the API is allowed to read from (path traversal guard)."""
        return [p.resolve() for p in (self.raw_docs_path, self.dicom_path, self.samples_path)]


@lru_cache
def get_settings() -> Settings:
    return Settings()
