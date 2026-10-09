"""Guardrail for the optional external (Claude API) generation provider.

Principle: "외부 LLM API 호출 금지". The only exception is an explicit opt-in for synthetic /
non-sensitive sample corpora. Anthropic mode is allowed only when ALL of these hold:

1. `ALLOW_EXTERNAL_LLM=true`
2. the corpus root (RAW_DOCS_PATH, and any folder indexed later) contains a marker file
   (`.corpus.yaml`) with `classification: synthetic-sample`, `non-sensitive` or
   `public-regulatory` (public regulatory guidance / open-licensed articles, corpus/public)
3. `ANTHROPIC_API_KEY` is set in the environment

Otherwise the app refuses to start. Even in anthropic mode, DICOM-derived data is never sent
externally (the DICOM explanation uses the deterministic template).

Every indexed document also stores its corpus classification (documents.classification). In
anthropic mode retrieval only reads documents whose classification is allowed, and a question
restricted to a local-only corpus (e.g. `licensed-local-only`: copyrighted sponsor protocols
kept on this machine, see .corpus.yaml.private.example) is rejected before retrieval. So a
DB that also holds such a corpus never sends its text to an external provider.
"""

from pathlib import Path

import yaml

from app.config import Settings

# `public-regulatory` is a non-sensitive subtype: published guidance and open-licensed text
# (corpus/public). It is allowed for the same reason as synthetic samples - nothing in it is
# confidential - but the eval in this repo still runs local-only (Ollama).
ALLOWED_CLASSIFICATIONS = frozenset({"synthetic-sample", "non-sensitive", "public-regulatory"})
# Named local-only classes (anything not in ALLOWED_CLASSIFICATIONS is local-only as well; these
# exist so a marker can say *why*). `licensed-local-only`: documents we may read and evaluate
# on locally but not redistribute or send to a third party (sponsor protocols, journal PDFs).
LOCAL_ONLY_CLASSIFICATIONS = frozenset({"licensed-local-only", "confidential"})


def allows_external(classification: str | None) -> bool:
    """True only for the explicitly non-sensitive classes; unknown / missing = local only."""
    return classification in ALLOWED_CLASSIFICATIONS


class ExternalLLMNotAllowedError(RuntimeError):
    pass


def read_marker(root: Path, marker_file: str) -> dict:
    """The parsed `.corpus.yaml` of `root` ({} when missing or invalid)."""
    marker = root / marker_file
    if not marker.is_file():
        return {}
    try:
        data = yaml.safe_load(marker.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def corpus_classification(root: Path, marker_file: str) -> str | None:
    value = read_marker(root, marker_file).get("classification")
    return str(value) if value is not None else None


def corpus_name(root: Path, marker_file: str) -> str:
    """`name:` from the corpus marker, else the folder name (e.g. "public", "originals")."""
    name = read_marker(root, marker_file).get("name")
    return str(name) if name else root.name


def corpus_include(root: Path, marker_file: str) -> tuple[str, ...] | None:
    """`include:` glob patterns (relative to the corpus root) or None = every file."""
    value = read_marker(root, marker_file).get("include")
    if not value:
        return None
    return tuple(str(v) for v in (value if isinstance(value, list) else [value]))


def ensure_corpus_allows_external(root: Path, marker_file: str) -> None:
    classification = corpus_classification(root, marker_file)
    if not allows_external(classification):
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
