# ClinicalRAG QA — developer entry points. Run from the repository root.
UV      := uv run --project backend
RUFF    := $(UV) ruff
COMPOSE := docker compose
HOST_OLLAMA := docker compose -f docker-compose.yml -f docker-compose.host-ollama.yml
OFFLINE := docker compose -f docker-compose.yml -f docker-compose.offline.yml
LLM_MODEL       ?= gemma4:e4b
EMBEDDING_MODEL ?= bge-m3
# `make eval` runs on the host against the compose stack's published ports.
EVAL_DATABASE_URL ?= postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa
EVAL_OLLAMA_URL   ?= http://localhost:11434

.PHONY: help setup samples seed lint format test test-unit test-integration \
        up up-host-ollama down logs pull-models migrate reset-embeddings index eval api ui bundle offline-up verify-offline \
        dicom-scan dicom-rules corpus-verify fetch-originals

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-18s %s\n",$$1,$$2}'

setup:  ## install all Python deps (api + ui + dev) with uv
	uv sync --project backend --all-groups

samples:  ## regenerate synthetic DICOM + sample PDF
	$(UV) python scripts/generate_sample_dicom.py
	$(UV) python scripts/generate_sample_pdf.py

seed:  ## copy sample docs (incl. .corpus.yaml marker) and DICOM into data/raw-docs
	mkdir -p data/raw-docs/documents data/raw-docs/dicom
	cp -R samples/documents/. data/raw-docs/documents/
	cp -R samples/dicom/. data/raw-docs/dicom/

corpus-verify:  ## check corpus/public against corpus/SHA256SUMS
	cd corpus && shasum -a 256 -c SHA256SUMS

ORIGINALS_DIR ?= $(HOME)/clinical-rag-private/originals
fetch-originals:  ## LOCAL ONLY: download copyrighted originals to ORIGINALS_DIR (never into the repo)
	./scripts/fetch-originals.sh $(ORIGINALS_DIR)

dicom-scan:  ## Layer 1/2 DICOM check over a folder: make dicom-scan DIR=path [SCAN_ARGS="--json out.jsonl"]
	$(UV) python -m app.cli.dicom_scan $(or $(DIR),samples/dicom) $(SCAN_ARGS)

dicom-rules:  ## regenerate rules/standard/*.yaml from the DICOM standard (network: dicom.nema.org)
	$(UV) python scripts/build_iod_rules.py
	$(UV) python scripts/build_deid_rules.py

lint:  ## ruff check + format check
	$(RUFF) check --config backend/pyproject.toml backend tests eval scripts frontend
	$(RUFF) format --check --config backend/pyproject.toml backend tests eval scripts frontend

format:  ## ruff fix + format
	$(RUFF) check --fix --config backend/pyproject.toml backend tests eval scripts frontend
	$(RUFF) format --config backend/pyproject.toml backend tests eval scripts frontend

test:  ## all tests (integration tests skip without Docker / TEST_DATABASE_URL)
	$(UV) pytest

test-unit:  ## unit + API tests only
	$(UV) pytest tests/unit

test-integration:  ## PostgreSQL+pgvector tests (testcontainers or TEST_DATABASE_URL)
	$(UV) pytest tests/integration -v

up:  ## build and start api, ui, db, ollama
	$(COMPOSE) up -d --build

up-host-ollama:  ## build and start api, ui, db using the host's Ollama (no ollama container, no pulls)
	$(HOST_OLLAMA) up -d --build --wait

down:  ## stop the stack (online, host-ollama or offline; volumes are kept)
	$(COMPOSE) down --remove-orphans
	$(OFFLINE) down --remove-orphans

logs:
	$(COMPOSE) logs -f api

pull-models:  ## pull the LLM + embedding models into the ollama container (online only)
	$(COMPOSE) exec ollama ollama pull $(LLM_MODEL)
	$(COMPOSE) exec ollama ollama pull $(EMBEDDING_MODEL)

migrate:  ## alembic upgrade head (inside the api container)
	$(COMPOSE) exec api alembic upgrade head

reset-embeddings:  ## resize chunks.embedding for OLLAMA_EMBEDDING_MODEL and clear all vectors (then reindex)
	DATABASE_URL=$(EVAL_DATABASE_URL) $(UV) python scripts/reset_embeddings.py $(RESET_ARGS)

index:  ## index data/raw-docs/documents through the API
	curl -s -X POST localhost:8000/api/index -H 'Content-Type: application/json' -d '{}' | python3 -m json.tool

eval:  ## run the RAG eval (needs DB + Ollama reachable; see README). PROVIDERS="ollama anthropic"
	DATABASE_URL=$(EVAL_DATABASE_URL) OLLAMA_BASE_URL=$(EVAL_OLLAMA_URL) \
	$(UV) python eval/run_eval.py $(foreach p,$(or $(PROVIDERS),ollama),--provider $(p)) $(EVAL_ARGS)

api:  ## run the API locally (hot reload)
	cd backend && uv run uvicorn app.main:app --reload --port 8000

ui:  ## run the Streamlit UI locally
	uv run --project backend --group ui streamlit run frontend/streamlit_app.py

bundle:  ## build the offline bundle from local images/models (PLATFORM, LLM_MODEL, WHEELS=0)
	./offline-bundle/build-bundle.sh

offline-up:  ## start with the internal-only network override (images must exist locally)
	$(OFFLINE) up -d --wait

verify-offline:  ## prove no container has egress in offline mode and the app still answers
	./offline-bundle/verify-offline.sh
