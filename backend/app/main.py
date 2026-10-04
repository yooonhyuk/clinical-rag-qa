"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import dicom, documents, health, rag
from app.config import get_settings
from app.container import AppContainer, build_container
from app.services.llm_types import LLMError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(container: AppContainer | None = None) -> FastAPI:
    """`container` is injected by tests; otherwise it is built from settings at startup."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        owned = container is None
        app.state.container = container or build_container(get_settings())
        try:
            yield
        finally:
            if owned:
                await app.state.container.aclose()

    app = FastAPI(title="ClinicalRAG QA", version="0.1.0", lifespan=lifespan)
    if container is not None:
        app.state.container = container  # usable even without running the lifespan

    @app.exception_handler(LLMError)
    async def llm_error_handler(_: Request, exc: LLMError) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": str(exc), "errorType": exc.error_type}
        )

    for module in (health, documents, rag, dicom):
        app.include_router(module.router)
    return app


app = create_app()
