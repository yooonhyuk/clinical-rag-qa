"""Scan a local folder for documents and compute content checksums (blocking IO)."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".md": "md",
    ".markdown": "md",
    ".txt": "txt",
    ".pdf": "pdf",
    ".xml": "xml",  # JATS full-text articles
    ".html": "html",
    ".htm": "html",
}


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    path: Path
    file_name: str
    file_type: str  # normalized type for supported files, raw extension otherwise
    supported: bool
    file_size: int
    modified_at: datetime
    checksum: str


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def scan_documents(root: Path, include: tuple[str, ...] | None = None) -> list[DiscoveredFile]:
    """Recursively list every non-hidden file under `root`, sorted by path.

    `include` (from the corpus marker) limits the scan to files matching any of the glob
    patterns relative to `root`, e.g. ("protocols/*.pdf", "originals/*.pdf"): a corpus folder
    can then also hold manifests, checksums and eval files that are not documents.
    """
    if not root.is_dir():
        raise FileNotFoundError(f"Document folder not found: {root}")
    files: list[DiscoveredFile] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if include is not None and not any(relative.match(pattern) for pattern in include):
            continue
        suffix = path.suffix.lower()
        file_type = SUPPORTED_EXTENSIONS.get(suffix)
        stat = path.stat()
        files.append(
            DiscoveredFile(
                path=path,
                file_name=path.name,
                file_type=file_type or suffix.lstrip(".") or "unknown",
                supported=file_type is not None,
                file_size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                checksum=sha256_of(path),
            )
        )
    return files
