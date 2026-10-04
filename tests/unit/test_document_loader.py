from pathlib import Path

import pytest

from app.services.document_loader import scan_documents, sha256_of


def test_scan_is_recursive_skips_hidden_and_flags_unsupported(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.md").write_text("# A", encoding="utf-8")
    (tmp_path / "sub" / "b.TXT").write_text("b", encoding="utf-8")
    (tmp_path / "c.docx").write_bytes(b"PK")
    (tmp_path / ".corpus.yaml").write_text("classification: synthetic-sample")
    files = {f.file_name: f for f in scan_documents(tmp_path)}
    assert set(files) == {"a.md", "b.TXT", "c.docx"}
    assert files["b.TXT"].file_type == "txt" and files["b.TXT"].supported
    assert files["c.docx"].file_type == "docx" and not files["c.docx"].supported


def test_identical_content_has_identical_checksum(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("same", encoding="utf-8")
    (tmp_path / "y.md").write_text("same", encoding="utf-8")
    assert sha256_of(tmp_path / "x.md") == sha256_of(tmp_path / "y.md")
    assert len(sha256_of(tmp_path / "x.md")) == 64


def test_missing_folder_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scan_documents(tmp_path / "nope")
