#!/usr/bin/env bash
# Build clinical-rag-qa-offline-<version>.tar on a machine that has Docker (and, only for the
# optional steps noted below, internet access).
#
#   images/   docker save of api, ui, db, ollama images (gzip)
#   models/   Ollama models (LLM + embedding) as an uncompressed tar (GGUF does not compress)
#   wheels/   Python wheels for development/test installs (optional, WHEELS=1 needs internet)
#   samples/  fictional sample documents + synthetic DICOM
#   docker-compose.yml, docker-compose.offline.yml, install.sh, verify-offline.sh, .env.example
#
# Models are copied from the local Ollama store (OLLAMA_MODELS_DIR, default ~/.ollama/models)
# when it already has them; only if it does not and MODELS_PULL=1 are they pulled into a
# scratch container. Base images are pulled only when they are not present locally.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${APP_VERSION:-0.1.0}"
LLM_MODEL="${LLM_MODEL:-gemma4:e4b}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-bge-m3}"     # multilingual (Korean); ~1.2GB
PLATFORM="${PLATFORM:-linux/amd64}"              # target machine architecture
WHEEL_PLATFORM="${WHEEL_PLATFORM:-manylinux_2_28_x86_64}"
WHEELS="${WHEELS:-1}"                            # 0 = skip the wheel download (no internet)
MODELS_PULL="${MODELS_PULL:-0}"                  # 1 = allow `ollama pull` if not in the store
OLLAMA_MODELS_DIR="${OLLAMA_MODELS_DIR:-$HOME/.ollama/models}"
DB_IMAGE="pgvector/pgvector:0.8.0-pg16"
OLLAMA_IMAGE="ollama/ollama:0.24.0"
NAME="clinical-rag-qa-offline-${VERSION}"
OUT="$ROOT/offline-bundle/out/$NAME"
MODEL_VOLUME="crqa_bundle_models_$$"
ARCH="${PLATFORM#linux/}"

log() { printf '\n[build-bundle] %s\n' "$*"; }
cleanup() { docker volume rm -f "$MODEL_VOLUME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

ensure_image() {  # pull only if the image is missing or built for another architecture
  local have
  have=$(docker image inspect --format '{{.Architecture}}' "$1" 2>/dev/null || true)
  if [ "$have" = "$ARCH" ]; then
    echo "  $1 ($ARCH) already present"
  else
    docker pull --platform "$PLATFORM" "$1"
  fi
}

rm -rf "$OUT" "$OUT.tar" && mkdir -p "$OUT"/{images,models}
cd "$ROOT"

log "1/5 build app images for $PLATFORM"
APP_VERSION="$VERSION" DOCKER_DEFAULT_PLATFORM="$PLATFORM" docker compose build api ui
ensure_image "$DB_IMAGE"
ensure_image "$OLLAMA_IMAGE"

log "2/5 docker save"
docker save "clinical-rag-qa-api:$VERSION" | gzip > "$OUT/images/api.tar.gz"
docker save "clinical-rag-qa-ui:$VERSION" | gzip > "$OUT/images/ui.tar.gz"
docker save "$DB_IMAGE" | gzip > "$OUT/images/db.tar.gz"
docker save "$OLLAMA_IMAGE" | gzip > "$OUT/images/ollama.tar.gz"

log "3/5 Ollama models ($LLM_MODEL, $EMBEDDING_MODEL)"
if python3 scripts/export_ollama_models.py --store "$OLLAMA_MODELS_DIR" \
     --out "$OUT/models/ollama-models.tar" "$LLM_MODEL" "$EMBEDDING_MODEL"; then
  :
elif [ "$MODELS_PULL" = "1" ]; then
  echo "  not in $OLLAMA_MODELS_DIR; pulling into a scratch volume (MODELS_PULL=1)"
  docker volume create "$MODEL_VOLUME" >/dev/null
  cid=$(docker run -d --rm -v "$MODEL_VOLUME:/root/.ollama" "$OLLAMA_IMAGE")
  until docker exec "$cid" ollama list >/dev/null 2>&1; do sleep 1; done
  docker exec "$cid" ollama pull "$LLM_MODEL"
  docker exec "$cid" ollama pull "$EMBEDDING_MODEL"
  docker stop "$cid" >/dev/null
  docker run --rm --entrypoint tar -v "$MODEL_VOLUME:/root/.ollama:ro" -v "$OUT/models:/out" \
    "$OLLAMA_IMAGE" cf /out/ollama-models.tar -C /root/.ollama models
else
  echo "  models missing locally; run 'ollama pull' on the host or set MODELS_PULL=1" >&2
  exit 1
fi

if [ "$WHEELS" = "1" ]; then
  log "4/5 Python wheels ($WHEEL_PLATFORM, py3.12)"
  mkdir -p "$OUT/wheels"
  uv export --project backend --frozen --no-hashes --all-groups --no-emit-project \
    > "$OUT/wheels/requirements.txt"
  uv run --project backend --with pip python -m pip download -q \
    -r "$OUT/wheels/requirements.txt" -d "$OUT/wheels" \
    --only-binary=:all: --python-version 3.12 --platform "$WHEEL_PLATFORM"
else
  log "4/5 Python wheels skipped (WHEELS=0)"
fi

log "5/5 copy compose files, scripts and samples"
cp docker-compose.yml docker-compose.offline.yml "$OUT/"
# The bundle's .env defaults to the models that are actually inside it.
sed -e "s|^OLLAMA_LLM_MODEL=.*|OLLAMA_LLM_MODEL=$LLM_MODEL|" \
    -e "s|^OLLAMA_EMBEDDING_MODEL=.*|OLLAMA_EMBEDDING_MODEL=$EMBEDDING_MODEL|" \
    .env.example > "$OUT/.env.example"
cp offline-bundle/install.sh offline-bundle/verify-offline.sh "$OUT/"
cp -R samples "$OUT/samples"
( cd "$OUT" && find . -type f ! -name SHA256SUMS -exec shasum -a 256 {} \; > SHA256SUMS )

# images are gzipped and model weights do not compress, so the outer archive is a plain tar.
tar -C "$ROOT/offline-bundle/out" -cf "$ROOT/offline-bundle/out/$NAME.tar" "$NAME"
log "done: offline-bundle/out/$NAME.tar ($(du -h "$ROOT/offline-bundle/out/$NAME.tar" | cut -f1))"
