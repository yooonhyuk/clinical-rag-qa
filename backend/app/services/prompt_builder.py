"""Prompt construction for RAG answers and DICOM summaries."""

import json
from functools import cache
from pathlib import Path
from typing import Any

from app.services.vector_search_service import RetrievedChunk


@cache
def load_prompt(prompts_dir: Path, name: str) -> str:
    return (prompts_dir / name).read_text(encoding="utf-8").strip()


def format_source_label(chunk: RetrievedChunk) -> str:
    parts = [chunk.file_name]
    if chunk.page_number is not None:
        parts.append(f"p.{chunk.page_number}")
    if chunk.section_title:
        parts.append(f"section: {chunk.section_title}")
    return " / ".join(parts)


def build_rag_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    blocks = [
        f"[{i}] 출처: {format_source_label(chunk)}\n{chunk.text}"
        for i, chunk in enumerate(chunks, start=1)
    ]
    context = "\n\n---\n\n".join(blocks)
    return f"### Context\n{context}\n\n### 질문\n{question}\n\n### 답변"


def build_dicom_prompt(analysis: dict[str, Any]) -> str:
    payload = json.dumps(analysis, ensure_ascii=False, indent=2)
    return f"### DICOM 태그 분석 결과(JSON)\n{payload}\n\n### 설명"
