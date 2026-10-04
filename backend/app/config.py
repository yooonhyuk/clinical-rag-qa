"""Application settings loaded from environment variables (see `.env.example`)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa"
    embedding_dim: int = 768

    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "gemma4:e4b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout_sec: float = 60.0
    ollama_max_retries: int = Field(default=3, ge=0)

    parse_concurrency: int = Field(default=2, ge=1)
    embed_concurrency: int = Field(default=4, ge=1)
    embed_batch_size: int = Field(default=16, ge=1)

    top_k: int = Field(default=5, ge=1, le=50)
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)
    min_relevance_score: float = Field(default=0.45, ge=-1.0, le=1.0)

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
