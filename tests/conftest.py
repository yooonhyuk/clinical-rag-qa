import shutil
from pathlib import Path

import pytest

from app.config import Settings

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


@pytest.fixture
def sample_docs_dir() -> Path:
    return SAMPLES / "documents"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    docs = tmp_path / "raw-docs" / "documents"
    dicom = tmp_path / "raw-docs" / "dicom"
    docs.mkdir(parents=True)
    dicom.mkdir(parents=True)
    return Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://unused/unused",
        raw_docs_path=docs,
        dicom_path=dicom,
        samples_path=SAMPLES,
        min_relevance_score=0.3,
        embedding_query_prefix="",
        embedding_document_prefix="",
        # hash-based fake embeddings carry no meaning; the embedding classifier is tested
        # separately with controlled vectors (test_scope_classifier.py)
        scope_classifier="regex",
    )


@pytest.fixture
def sample_dicom(settings: Settings) -> Path:
    """Copy the synthetic CT sample into the (temporary) DICOM folder."""
    src = SAMPLES / "dicom" / "sample-ct-anonymized.dcm"
    dst = settings.dicom_path / src.name
    shutil.copy(src, dst)
    return dst
