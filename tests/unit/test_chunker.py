import pytest

from app.services.chunker import chunk_sections
from app.services.text_extractor import Section


def test_short_section_is_single_chunk_with_title_prefix() -> None:
    chunks = chunk_sections([Section("짧은 본문", section_title="Scope")], size=1000, overlap=150)
    assert len(chunks) == 1
    assert chunks[0].text == "[Scope]\n짧은 본문"
    assert chunks[0].section_title == "Scope"


def test_long_text_is_split_with_overlap_and_bounded_size() -> None:
    text = " ".join(f"word{i}" for i in range(600))  # ~4.5k chars
    chunks = chunk_sections([Section(text)], size=500, overlap=100)
    assert len(chunks) > 5
    assert all(len(c.text) <= 500 for c in chunks)
    # consecutive chunks share text (overlap)
    for a, b in zip(chunks, chunks[1:], strict=False):
        assert a.text[-40:].split()[-1] in b.text
    # every word survives chunking
    joined = " ".join(c.text for c in chunks)
    assert all(f"word{i}" in joined for i in range(600))


def test_chunks_never_span_sections_and_indexes_are_global() -> None:
    sections = [Section("a" * 50, page_number=1), Section("b" * 50, page_number=2)]
    chunks = chunk_sections(sections, size=100, overlap=10)
    assert [c.chunk_index for c in chunks] == [0, 1]
    assert [c.page_number for c in chunks] == [1, 2]


def test_overlap_must_be_smaller_than_size() -> None:
    with pytest.raises(ValueError):
        chunk_sections([Section("x")], size=100, overlap=100)
