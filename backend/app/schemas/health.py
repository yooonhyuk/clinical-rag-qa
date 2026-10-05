from app.schemas.common import CamelModel


class ComponentStatus(CamelModel):
    ok: bool
    detail: str | None = None


class HealthResponse(CamelModel):
    status: str
    llm_provider: str
    database: ComponentStatus
    pgvector: ComponentStatus
    ollama: ComponentStatus
    llm_model: ComponentStatus
    embedding_model: ComponentStatus
    # chunks.embedding dimension + models present in chunks vs the configured embedding model
    embedding_index: ComponentStatus
