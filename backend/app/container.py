"""Composition root: builds long-lived objects once per process (no global singletons)."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import Settings
from app.db import create_engine, create_session_factory
from app.services.anthropic_client import AnthropicGenerationClient
from app.services.dicom_rules import load_rules
from app.services.dicom_service import DicomService
from app.services.embedding_service import EmbeddingService
from app.services.indexing_pipeline import IndexingPipeline
from app.services.llm_guardrail import validate_provider
from app.services.llm_types import GenerationClient
from app.services.ollama_client import OllamaClient
from app.services.prompt_builder import load_prompt
from app.services.rag_service import RagService, ScopeClassifier
from app.services.reranker import CrossEncoderReranker, Reranker
from app.services.scope_classifier import (
    EmbeddingScopeClassifier,
    Mvp1RegexScopeClassifier,
    RegexScopeClassifier,
    ScopeExemplars,
)


@dataclass
class AppContainer:
    settings: Settings
    session_factory: async_sessionmaker[AsyncSession]
    ollama: OllamaClient  # embeddings (+ local generation / model listing) - always local
    generator: GenerationClient
    embeddings: EmbeddingService
    rag: RagService
    dicom: DicomService
    pipeline: IndexingPipeline
    engine: AsyncEngine | None = None

    async def aclose(self) -> None:
        for client in {id(c): c for c in (self.ollama, self.generator)}.values():
            if hasattr(client, "aclose"):
                await client.aclose()
        if self.engine is not None:
            await self.engine.dispose()


def build_generator(settings: Settings, ollama: OllamaClient) -> GenerationClient:
    """Pick the generation provider. Raises if the external-LLM guardrail is not satisfied."""
    validate_provider(settings)
    if settings.llm_provider == "anthropic":
        assert settings.anthropic_api_key is not None  # guaranteed by validate_provider
        return AnthropicGenerationClient.create(
            api_key=settings.anthropic_api_key.get_secret_value(),
            model=settings.anthropic_model,
            timeout_sec=settings.anthropic_timeout_sec,
            max_retries=settings.anthropic_max_retries,
            max_tokens=settings.anthropic_max_tokens,
            effort=settings.anthropic_effort,
            refusal_fallback=settings.anthropic_refusal_fallback,
        )
    return ollama


def build_scope_classifier(settings: Settings, embeddings: EmbeddingService) -> ScopeClassifier:
    match settings.scope_classifier:
        case "regex":
            return RegexScopeClassifier()
        case "mvp1":
            return Mvp1RegexScopeClassifier()
        case _:
            return EmbeddingScopeClassifier(
                embeddings,
                ScopeExemplars.load(settings.rules_path / "scope_exemplars.yaml"),
                margin=settings.scope_margin,
                k=settings.scope_top_k,
            )


def build_reranker(settings: Settings) -> Reranker | None:
    if settings.reranker == "none":
        return None
    reranker = CrossEncoderReranker(
        settings.reranker_model,
        revision=settings.reranker_revision,
        device=settings.reranker_device,
    )
    reranker.load()  # fail at startup (RerankerUnavailableError), not on the first question
    return reranker


def build_container(
    settings: Settings,
    *,
    ollama: OllamaClient | None = None,
    generator: GenerationClient | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    reranker: Reranker | None = None,
) -> AppContainer:
    if ollama is None:
        ollama = OllamaClient.create(
            settings.ollama_base_url,
            llm_model=settings.ollama_llm_model,
            embedding_model=settings.ollama_embedding_model,
            timeout_sec=settings.ollama_timeout_sec,
            max_retries=settings.ollama_max_retries,
        )
    if reranker is None:
        reranker = build_reranker(settings)
    if generator is None:
        generator = build_generator(settings, ollama)
    else:
        validate_provider(settings)

    engine = None
    if session_factory is None:
        engine = create_engine(settings.database_url)
        session_factory = create_session_factory(engine)

    embeddings = EmbeddingService(
        ollama,
        dimension=settings.embedding_dimension,
        model=settings.ollama_embedding_model,
        concurrency=settings.embed_concurrency,
        batch_size=settings.embed_batch_size,
        query_prefix=settings.embedding_query_prefix,
        document_prefix=settings.embedding_document_prefix,
    )
    # DICOM-derived data never leaves the machine: with an external generator the
    # explanation falls back to the deterministic template.
    dicom_llm = generator if generator.provider == "ollama" else None
    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        ollama=ollama,
        generator=generator,
        embeddings=embeddings,
        rag=RagService(
            embeddings,
            generator,
            system_prompt=load_prompt(
                settings.prompts_path,
                "rag_prompt_inline_en.txt"
                if settings.rag_prompt_variant == "inline-en"
                else "rag_prompt.txt",
            ),
            inline_instructions=settings.rag_prompt_variant == "inline-en",
            min_score=settings.min_relevance_score,
            hybrid=settings.hybrid_search,
            rrf_k=settings.rrf_k,
            scope=build_scope_classifier(settings, embeddings),
            reranker=reranker,
            rerank_candidates=settings.rerank_candidates,
            rerank_min_score=settings.rerank_min_score,
            partial_answers=settings.partial_answers,
            exact_search=settings.vector_search == "exact",
            hnsw_iterative_scan=settings.hnsw_iterative_scan,
            hnsw_ef_search=settings.hnsw_ef_search,
        ),
        dicom=DicomService(
            dicom_llm,
            load_rules(settings.rules_path),
            system_prompt=load_prompt(settings.prompts_path, "dicom_summary_prompt.txt"),
        ),
        pipeline=IndexingPipeline(
            session_factory,
            embeddings,
            parse_concurrency=settings.parse_concurrency,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            marker_file=settings.corpus_marker_file,
        ),
    )
