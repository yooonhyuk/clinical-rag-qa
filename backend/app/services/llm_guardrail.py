"""Guardrail for the optional external (Claude API) generation provider.

Principle: "외부 LLM API 호출 금지". The only exception is an explicit opt-in for synthetic /
non-sensitive sample corpora. Anthropic mode is allowed only when ALL of these hold:

1. `ALLOW_EXTERNAL_LLM=true`
2. the corpus root (RAW_DOCS_PATH, and any folder indexed later) contains a marker file
   (`.corpus.yaml`) with `classification: synthetic-sample` or `non-sensitive`
3. `ANTHROPIC_API_KEY` is set in the environment

Otherwise the app refuses to start. Even in anthropic mode, DICOM-derived data is never sent
externally (the DICOM explanation uses the deterministic template).
"""

from pathlib import Path

import yaml

from app.config import Settings

ALLOWED_CLASSIFICATIONS = frozenset({"synthetic-sample", "non-sensitive"})


class ExternalLLMNotAllowedError(RuntimeError):
    pass


def corpus_classification(root: Path, marker_file: str) -> str | None:
    marker = root / marker_file
    if not marker.is_file():
        return None
    try:
        data = yaml.safe_load(marker.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    value = data.get("classification") if isinstance(data, dict) else None
    return str(value) if value is not None else None


def ensure_corpus_allows_external(root: Path, marker_file: str) -> None:
    classification = corpus_classification(root, marker_file)
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise ExternalLLMNotAllowedError(
            f"Corpus '{root}' is not marked as sample/non-sensitive "
            f"({marker_file} classification={classification!r}; "
            f"allowed: {sorted(ALLOWED_CLASSIFICATIONS)}). "
            "External LLM providers may only see synthetic or non-sensitive documents."
        )


def validate_provider(settings: Settings) -> None:
    """Raise `ExternalLLMNotAllowedError` unless the configured provider is permitted."""
    if settings.llm_provider == "ollama":
        return
    if not settings.allow_external_llm:
        raise ExternalLLMNotAllowedError(
            "LLM_PROVIDER=anthropic requires ALLOW_EXTERNAL_LLM=true (explicit opt-in). "
            "The default, local-first mode is LLM_PROVIDER=ollama."
        )
    ensure_corpus_allows_external(settings.raw_docs_path, settings.corpus_marker_file)
    if settings.anthropic_api_key is None or not settings.anthropic_api_key.get_secret_value():
        raise ExternalLLMNotAllowedError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY.")
