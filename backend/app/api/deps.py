"""FastAPI dependencies."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


ContainerDep = Annotated[AppContainer, Depends(get_container)]


async def get_session(container: ContainerDep) -> AsyncIterator[AsyncSession]:
    async with container.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def resolve_allowed_path(raw: str, allowed_roots: list[Path], *, base: Path | None = None) -> Path:
    """Resolve a user-supplied path and reject anything outside the allowed roots."""
    candidate = Path(raw)
    if not candidate.is_absolute() and base is not None and not candidate.exists():
        candidate = base / candidate
    resolved = candidate.resolve()
    if not any(resolved.is_relative_to(root) for root in allowed_roots):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=f"Path is outside the allowed folders: {[str(r) for r in allowed_roots]}",
        )
    if not resolved.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Not found: {raw}")
    return resolved
