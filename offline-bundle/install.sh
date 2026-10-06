#!/usr/bin/env bash
# Install ClinicalRAG QA on a machine WITHOUT internet access. Run inside the extracted bundle:
#   tar xf clinical-rag-qa-offline-<version>.tar && cd clinical-rag-qa-offline-<version>
#   ./install.sh
# CRQA_VOLUME_PREFIX (default crqa) names the data volumes, e.g. for a side-by-side test install.
set -euo pipefail

cd "$(dirname "$0")"
OLLAMA_IMAGE="ollama/ollama:0.24.0"
MODEL_VOLUME="${CRQA_VOLUME_PREFIX:-crqa}_ollama_data"
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.offline.yml)

log() { printf '\n[install] %s\n' "$*"; }

log "0/5 verify bundle checksums"
if command -v sha256sum >/dev/null; then sha256sum -c --quiet SHA256SUMS
else shasum -a 256 -c --quiet SHA256SUMS; fi

log "1/5 docker load images"
for f in images/*.tar.gz; do gunzip -c "$f" | docker load; done

log "2/5 restore Ollama models into volume $MODEL_VOLUME"
docker volume create "$MODEL_VOLUME" >/dev/null
docker run --rm --network none --entrypoint tar -v "$MODEL_VOLUME:/root/.ollama" \
  -v "$PWD/models:/in:ro" "$OLLAMA_IMAGE" xf /in/ollama-models.tar -C /root/.ollama

log "3/5 seed sample documents (fictional) into ./data"
mkdir -p data/raw-docs/documents data/raw-docs/dicom data/logs
cp -R samples/documents/. data/raw-docs/documents/
cp -R samples/dicom/. data/raw-docs/dicom/
[ -f .env ] || cp .env.example .env

log "4/5 start the stack on the internal-only network (the api runs migrations on start)"
"${COMPOSE[@]}" up -d --wait --wait-timeout 300
"${COMPOSE[@]}" exec -T api alembic upgrade head

log "5/5 health check (from inside the api container; no host port is published)"
for i in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T api python -c "
import json, sys, urllib.request
h = json.load(urllib.request.urlopen('http://localhost:8000/api/health'))
print(json.dumps(h, indent=2, ensure_ascii=False))
sys.exit(0 if h['status'] == 'ok' else 1)"; then
    log "healthy. UI: http://127.0.0.1:8501 (this host only). Next: ./verify-offline.sh"
    exit 0
  fi
  sleep 5
done
echo "[install] health check did not reach status=ok (see output above)" >&2
exit 1
