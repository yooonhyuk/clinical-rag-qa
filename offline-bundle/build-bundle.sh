#!/usr/bin/env bash
# Build clinical-rag-qa-offline-<version>.tar.gz on a machine WITH internet access.
#
#   images/   docker save of api, ui, db, ollama images
#   models/   Ollama model store (LLM + embedding model) as a tarball
#   wheels/   Python wheels for development/test installs (pip/uv --no-index)
#   samples/  fictional sample documents + synthetic DICOM
#   docker-compose.yml, docker-compose.offline.yml, install.sh, verify-offline.sh, .env.example
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${APP_VERSION:-0.1.0}"
LLM_MODEL="${LLM_MODEL:-gemma4:e4b}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-bge-m3}"   # multilingual (Korean); ~1.2GB
PLATFORM="${PLATFORM:-linux/amd64}"              # target machine architecture
WHEEL_PLATFORM="${WHEEL_PLATFORM:-manylinux_2_28_x86_64}"
DB_IMAGE="pgvector/pgvector:0.8.0-pg16"
OLLAMA_IMAGE="ollama/ollama:0.24.0"
NAME="clinical-rag-qa-offline-${VERSION}"
OUT="$ROOT/offline-bundle/out/$NAME"
MODEL_VOLUME="crqa_bundle_models_$$"

log() { printf '\n[build-bundle] %s\n' "$*"; }
cleanup() { docker volume rm -f "$MODEL_VOLUME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

rm -rf "$OUT" && mkdir -p "$OUT"/{images,models,wheels}
cd "$ROOT"

log "1/5 build app images for $PLATFORM"
APP_VERSION="$VERSION" DOCKER_DEFAULT_PLATFORM="$PLATFORM" docker compose build api ui
docker pull --platform "$PLATFORM" "$DB_IMAGE"
docker pull --platform "$PLATFORM" "$OLLAMA_IMAGE"

log "2/5 docker save"
docker save "clinical-rag-qa-api:$VERSION" | gzip > "$OUT/images/api.tar.gz"
docker save "clinical-rag-qa-ui:$VERSION" | gzip > "$OUT/images/ui.tar.gz"
docker save "$DB_IMAGE" | gzip > "$OUT/images/db.tar.gz"
docker save "$OLLAMA_IMAGE" | gzip > "$OUT/images/ollama.tar.gz"

log "3/5 pull Ollama models ($LLM_MODEL, $EMBEDDING_MODEL) into a scratch volume and export"
docker volume create "$MODEL_VOLUME" >/dev/null
cid=$(docker run -d --rm -v "$MODEL_VOLUME:/root/.ollama" "$OLLAMA_IMAGE")
until docker exec "$cid" ollama list >/dev/null 2>&1; do sleep 1; done
docker exec "$cid" ollama pull "$LLM_MODEL"
docker exec "$cid" ollama pull "$EMBEDDING_MODEL"
docker stop "$cid" >/dev/null
docker run --rm --entrypoint tar -v "$MODEL_VOLUME:/root/.ollama:ro" -v "$OUT/models:/out" \
  "$OLLAMA_IMAGE" czf /out/ollama-models.tgz -C /root/.ollama .

log "4/5 Python wheels ($WHEEL_PLATFORM, py3.12)"
uv export --project backend --frozen --no-hashes --all-groups --no-emit-project \
  > "$OUT/wheels/requirements.txt"
uv run --project backend --with pip python -m pip download -q \
  -r "$OUT/wheels/requirements.txt" -d "$OUT/wheels" \
  --only-binary=:all: --python-version 3.12 --platform "$WHEEL_PLATFORM"

log "5/5 copy compose files, scripts and samples"
cp docker-compose.yml docker-compose.offline.yml .env.example "$OUT/"
cp offline-bundle/install.sh offline-bundle/verify-offline.sh "$OUT/"
cp -R samples "$OUT/samples"
( cd "$OUT" && find . -type f ! -name SHA256SUMS -exec shasum -a 256 {} \; > SHA256SUMS )

tar -C "$ROOT/offline-bundle/out" -czf "$ROOT/offline-bundle/out/$NAME.tar.gz" "$NAME"
log "done: offline-bundle/out/$NAME.tar.gz"
