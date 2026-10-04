from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import ContainerDep, SessionDep
from app.schemas.health import ComponentStatus, HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


def _has_model(models: list[str], wanted: str) -> bool:
    # "nomic-embed-text" matches "nomic-embed-text:latest"
    return any(m == wanted or m.split(":")[0] == wanted for m in models)


@router.get("/health", response_model=HealthResponse, response_model_by_alias=True)
async def health(container: ContainerDep, session: SessionDep) -> HealthResponse:
    settings = container.settings
    try:
        await session.execute(text("SELECT 1"))
        database = ComponentStatus(ok=True)
        version = await session.scalar(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        pgvector = ComponentStatus(ok=version is not None, detail=version or "not installed")
    except Exception as exc:  # health must report, not raise
        database = ComponentStatus(ok=False, detail=str(exc).splitlines()[0])
        pgvector = ComponentStatus(ok=False, detail="database unavailable")

    try:
        models = await container.ollama.list_models()
        ollama = ComponentStatus(ok=True, detail=f"{len(models)} models")
    except Exception as exc:
        models = []
        ollama = ComponentStatus(ok=False, detail=str(exc).splitlines()[0])

    if settings.llm_provider == "anthropic":
        llm_model = ComponentStatus(
            ok=settings.anthropic_api_key is not None,
            detail=f"anthropic:{settings.anthropic_model} (external opt-in, not probed)",
        )
    else:
        llm_model = ComponentStatus(
            ok=_has_model(models, settings.ollama_llm_model),
            detail=f"ollama:{settings.ollama_llm_model}",
        )
    embedding_model = ComponentStatus(
        ok=_has_model(models, settings.ollama_embedding_model),
        detail=settings.ollama_embedding_model,
    )
    parts = (database, pgvector, ollama, llm_model, embedding_model)
    return HealthResponse(
        status="ok" if all(p.ok for p in parts) else "degraded",
        llm_provider=settings.llm_provider,
        database=database,
        pgvector=pgvector,
        ollama=ollama,
        llm_model=llm_model,
        embedding_model=embedding_model,
    )
