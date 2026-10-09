# ClinicalRAG QA

**Local-first 의료문서 RAG + DICOM Tag Analyzer** — 포트폴리오 프로젝트 (MVP-1)

임상시험 문서(Markdown/TXT/텍스트 PDF/JATS XML/HTML)를 로컬에서 인덱싱하고, 질문에 **출처를 붙여** 답하며, 근거가 부족하면 **답변을 거절**합니다.
DICOM 파일은 픽셀을 읽지 않고 태그만 분석해, DICOM 표준 원문(PS3.3 / PS3.15, 2026d)에서 생성한 규칙으로 **표준 적합성(Layer 1)** 과 **비식별화(Layer 2)** 를 검사합니다.
기본 구성은 외부 네트워크 없이 동작하며, 폐쇄망 설치용 오프라인 번들을 포함합니다.

> 샘플 문서(toy 코퍼스)와 DICOM은 직접 만든 **가상 데이터**입니다(`TEST^PATIENT` 같은 가짜 값). 실제 환자 데이터나 회사 문서는 쓰지 않습니다.
> 평가용 **공개 코퍼스**(`corpus/public/`, 규제 가이드라인·CC BY 논문·DICOM 표준 발췌 11종)도 함께 들어 있습니다. 출처와 라이선스는 아래 [코퍼스와 출처 고지](#코퍼스와-출처-고지-notice)를 참고하세요.
> 이 시스템은 영상 판독·진단·치료 조언을 하지 않습니다.

기획서(v0.4) 기준 MVP-1 범위를 구현했습니다. 기술 스택은 Python 3.12, FastAPI(async), SQLAlchemy 2.0 async + asyncpg, Alembic, PostgreSQL 16 + pgvector, httpx.AsyncClient, Ollama(Gemma, bge-m3 embedding), pypdf, pydicom, Streamlit, pytest, uv, Docker Compose입니다.

---

## 아키텍처

```mermaid
flowchart LR
    subgraph host["Docker Compose (폐쇄망: internal 네트워크)"]
        UI["ui<br/>Streamlit"] -->|HTTP| API
        subgraph API["api — FastAPI (async)"]
            direction TB
            R["/api/ask · /api/retrieve"] --> RAG["RagService<br/>거절 정책 · 인용"]
            I["/api/index"] --> P["IndexingPipeline<br/>to_thread 파싱 → chunk → embed"]
            D["/api/dicom/analyze"] --> DS["DicomService<br/>pydicom stop_before_pixels<br/>L1 PS3.3 적합성 · L2 PS3.15 비식별화"]
            P --> ES["EmbeddingService<br/>Semaphore(EMBED_CONCURRENCY)"]
            RAG --> ES
            RAG --> GEN{{"GenerationClient"}}
            DS -. 설명 생성 .-> GEN
        end
        ES -->|httpx.AsyncClient| OL["ollama<br/>bge-m3 · gemma"]
        GEN -->|기본: ollama| OL
        API -->|SQLAlchemy async| DB[("db — PostgreSQL 16 + pgvector<br/>documents · chunks(HNSW)<br/>dicom_files · index_jobs · ask_logs")]
    end
    GEN -. "opt-in 전용: LLM_PROVIDER=anthropic<br/>(가드레일 통과 시에만)" .-> CL["Claude API"]
```

인덱싱 흐름은 다음과 같습니다. 폴더 스캔(SHA-256) → 문서별 텍스트 추출(`asyncio.to_thread`, 형식별 로더) → **섹션 단위** chunk(섹션 안에서 1000자 / overlap 150, 섹션 경계는 넘지 않음) → embedding(배치 gather + Semaphore) → **문서 단위 트랜잭션**으로 chunk 저장과 `INDEXED` 전환. 문서마다 코퍼스 이름(`.corpus.yaml`의 `name`, 없으면 폴더 이름)을 기록하고, 검색은 코퍼스 하나로 제한할 수 있습니다.

### 폴더 구조

```text
backend/app/
  main.py · config.py · db.py · container.py (composition root)
  api/        documents.py rag.py dicom.py health.py deps.py
  services/   document_loader · text_extractor(형식 분기) · pdf_extractor(pypdf) · jats_extractor
              html_extractor · headings(번호 헤딩 인식) · table_rows · chunker · embedding_service
              vector_search_service · rag_service · prompt_builder
              embedding_schema · indexing_pipeline
              dicom_service · dicom_rules · dicom_safe(출력 allowlist)
              dicom_conformance(Layer 1) · dicom_deid(Layer 2) · dicom_findings
              ollama_client · anthropic_client · llm_types · llm_guardrail
              scope_classifier(OUT_OF_SCOPE: 정규식 + bge-m3 kNN)
              reranker(선택: bge-reranker-v2-m3 cross-encoder, `rerank` extra)
  models/     document chunk dicom_file index_job ask_log (SQLAlchemy 2.0)
  schemas/    Pydantic (camelCase 응답)
  prompts/    rag_prompt.txt dicom_summary_prompt.txt
  rules/      standard/ps3.3_iod.yaml · standard/ps3.15_e1-1_deid.yaml (표준에서 생성)
              deid_policy.yaml (사이트 정책) · scope_exemplars.yaml (B6 분류기 예시 80개)
  cli/        dicom_scan.py (폴더 일괄 검사)
backend/alembic/versions/  0001_initial_schema · 0002_ask_log_llm_usage · 0003_pg_trgm
                           0004_embedding_model_tracking · 0005_document_corpus
frontend/streamlit_app.py · no_egress_entrypoint.py (폐쇄망 ui: default route 제거 후 권한 하강)
eval/       questions.yaml (toy 25문항) · public_questions.yaml (공개 99문항) · scope_heldout.yaml (B6 61문항)
            eval_metrics.py · run_eval.py · run_scope_eval.py · tune_gate.py(rerank 게이트 dev 조정) · results/ (날짜·설정·코퍼스 해시별 결과, 커밋함)
tests/      unit/ (API 테스트 포함) · integration/ (PostgreSQL + pgvector)
offline-bundle/  build-bundle.sh · install.sh · verify-offline.sh
samples/    documents/ (toy 코퍼스: 가상 문서 6종 + .corpus.yaml) · dicom/ (합성 DICOM 9종)
corpus/     public/ (공개 코퍼스 11종 + .corpus.yaml) · SOURCES.md · SHA256SUMS
scripts/    generate_sample_dicom.py · generate_sample_pdf.py · fetch-originals.sh (저작권 원문, 로컬 전용)
            build_iod_rules.py · build_deid_rules.py · dicom_docbook.py (표준 → 규칙 YAML)
            diagnose_embedding.py (토크나이저/cosine 진단) · reset_embeddings.py
            export_ollama_models.py (번들용: 로컬 Ollama 저장소에서 모델 복사)
docs/       dicom-rules.md (DICOM 2계층 규칙 설계·출처·한계) · journey.md (문제 → 시도 → 결과 → 교훈)
docs/decisions/  0001-pdf-library · 0002-embedding-model · 0003-retrieval-mode · 0004-reranker
                 0005-generator-model (ADR)
docs/issues/  001-korean-embedding-unk.md · 002-dicom-free-text-phi-to-llm.md
              003-offline-ui-egress.md · 004-compose-host-ollama-and-port-binding.md
              005-ich-version-confusion-cross-language.md · 006-table-chunks-hubs-and-misses.md
              007-hedged-answers-counted-as-refusals.md · 008-partial-answer-on-must-refuse.md
              009-retrieval-differs-across-reindex.md · 010-medgemma-fabricates-no-answer-values.md
```

---

## 실행 방법

### 1) 로컬 개발 (테스트만)

```bash
make setup        # uv sync --all-groups (Python 3.12)
make test         # 단위 + API + 통합(Docker 또는 TEST_DATABASE_URL 없으면 skip)
make lint
```

### 2) 온라인: Docker Compose

```bash
cp .env.example .env
make seed                 # samples → data/raw-docs (가상 문서, .corpus.yaml 표식 포함)
make up                   # api(8000), ui(8501), db(5432), ollama(11434) — 모두 127.0.0.1에만 공개
make pull-models          # gemma4:e4b + bge-m3 (LLM_MODEL=... / EMBEDDING_MODEL=... 로 변경)
make index                # POST /api/index
open http://localhost:8501
```

호스트에 이미 Ollama와 모델이 있으면 ollama 컨테이너 없이 띄울 수 있습니다(모델을 다시 받지 않음).

```bash
make seed
make up-host-ollama       # docker-compose.host-ollama.yml: api → host.docker.internal:11434
make index
```

- API 문서는 `http://localhost:8000/docs`, 상태 확인은 `GET /api/health`입니다(DB, pgvector, Ollama, 모델 존재 여부, embedding 인덱스의 차원·모델 일치 여부).
- Mac에서는 Docker 안의 Ollama가 GPU(Metal)를 쓰지 못해 느립니다. 개발할 때는 호스트 Ollama를 쓰는 편이 낫습니다(`make up-host-ollama`, 또는 `.env`의 `OLLAMA_BASE_URL`).
- api 컨테이너는 시작할 때 `alembic upgrade head`를 실행합니다.

### 3) 오프라인(폐쇄망) 번들

Docker가 있는 장비에서 번들을 만듭니다.

```bash
make bundle    # = offline-bundle/build-bundle.sh
# → offline-bundle/out/clinical-rag-qa-offline-0.1.0.tar (git에는 넣지 않음)
#    images/  (docker save + gzip: api, ui, pgvector, ollama)
#    models/  (ollama-models.tar: LLM + embedding 모델의 manifest·blob만)
#    wheels/  (선택: 개발/테스트용 Python wheel + requirements.txt)
#    samples/, docker-compose*.yml, install.sh, verify-offline.sh, .env.example, SHA256SUMS
```

| 변수 | 기본값 | 설명 |
|---|---|---|
| `PLATFORM` | `linux/amd64` | 설치 대상 아키텍처. 같은 아키텍처의 base 이미지가 로컬에 있으면 pull하지 않음 |
| `LLM_MODEL` / `EMBEDDING_MODEL` | `gemma4:e4b` / `bge-m3` | 번들에 넣을 모델. 번들의 `.env.example`도 이 값으로 바뀜 |
| `OLLAMA_MODELS_DIR` | `~/.ollama/models` | 모델을 복사할 로컬 Ollama 저장소 |
| `MODELS_PULL` | `0` | `1`이면 로컬에 없는 모델을 임시 컨테이너에서 pull(인터넷 필요) |
| `WHEELS` / `WHEEL_PLATFORM` | `1` / `manylinux_2_28_x86_64` | `0`이면 wheel 다운로드 생략 |

모델 가중치(GGUF)는 거의 압축되지 않아 모델과 바깥 묶음은 압축하지 않은 tar로 만듭니다. 크기는 다음과 같습니다(arm64, 2026-10-06).

| 구성 | 크기 |
|---|---|
| api 이미지 (gzip) | 179MB |
| ui 이미지 (gzip) | 292MB |
| pgvector 이미지 (gzip) | 161MB |
| ollama 이미지 (gzip) | 3.0GB |
| 모델: medgemma:4b + bge-m3 | 4.5GB |
| 모델: gemma4:e4b + bge-m3 (기본값) | 약 10.8GB |
| 번들 합계 (medgemma:4b 기준) | 7.8GB |

폐쇄망 장비에서는 다음과 같이 설치합니다.

```bash
tar xf clinical-rag-qa-offline-0.1.0.tar && cd clinical-rag-qa-offline-0.1.0
./install.sh          # 체크섬 검증 → docker load → 모델 복원 → compose up(internal) → alembic → health
./verify-offline.sh   # 47개 항목: 토폴로지·라우트·egress·ui 권한·내부 통신·앱 응답. 하나라도 실패하면 exit 1
```

`verify-offline.sh`가 확인하는 항목은 다음과 같습니다([이슈 003](docs/issues/003-offline-ui-egress.md)).

1. db·ollama·api는 internal 네트워크에만 연결되어 있고 포트를 공개하지 않는다. ui는 127.0.0.1:8501에만 공개한다.
2. 모든 컨테이너(ui 포함)에 IPv4 default route가 없다.
3. 모든 컨테이너에서 1.1.1.1, 8.8.8.8, pypi.org, registry.ollama.ai, api.anthropic.com, host.docker.internal 접속이 실패한다.
4. Streamlit이 uid 10001, capability 0으로 실행되고, 호스트에서 127.0.0.1:8501에 접속된다.
5. api→db, api→ollama, ui→api 내부 통신이 된다.
6. ui 컨테이너에서 api를 통해 샘플 인덱싱, 한국어 질문 답변(출처 포함), 범위 밖 질문 거절, DICOM 분석이 된다.

**실행 결과 (2026-10-06, Docker Desktop 29.5.2, macOS arm64)**: `PLATFORM=linux/arm64 WHEELS=0 LLM_MODEL=medgemma:4b make bundle`로 만든 번들을 다른 폴더에 풀어 `install.sh`(약 1분) → `verify-offline.sh` 순서로 실행했고, 47개 항목 모두 PASS였습니다. 질문 답변은 CPU의 medgemma:4b로 생성에 약 26초가 걸렸습니다. Docker Desktop VM 메모리가 7.7GB라 기본 LLM인 gemma4:e4b(9.6GB)는 컨테이너에 올릴 수 없어 medgemma:4b로 대신 검증했습니다. 이전 ui 설정으로 되돌려 실행하면 ui의 route·egress 7개 항목이 FAIL입니다(음성 대조).

`docker-compose.offline.yml`의 설정은 다음과 같습니다.

- db·ollama·api는 `internal: true` 네트워크에만 연결합니다. 외부로 나가는 경로가 없고 호스트 포트도 열지 않습니다.
- 외부 LLM Provider를 강제로 끕니다(`LLM_PROVIDER=ollama`, `ALLOW_EXTERNAL_LLM=false`).
- `pull_policy: never`로 설정해 이미지를 받거나 빌드하지 않습니다.
- ui는 호스트 포트(127.0.0.1:8501)를 열기 위해 일반 bridge `ui_edge`에도 연결합니다. Docker는 internal 네트워크에서 포트를 공개하지 못하고, `enable_ip_masquerade=false`도 Docker Desktop에서는 외부 접속을 막지 못했습니다. 그래서 ui의 entrypoint(`frontend/no_egress_entrypoint.py`)가 root(NET_ADMIN)로 default route를 지운 뒤 uid 10001로 내려가 capability를 모두 버리고 Streamlit을 실행합니다. 외부 DNS는 `dns: [127.0.0.1]`로 막습니다.
- CPU 전용 장비를 고려해 Ollama 타임아웃 기본값을 300초로 둡니다(`OFFLINE_OLLAMA_TIMEOUT_SEC`).
- `CRQA_VOLUME_PREFIX`(기본 `crqa`)로 데이터 볼륨 이름을 바꿀 수 있습니다. 기존 데이터를 건드리지 않고 시험 설치할 때 씁니다.

### 4) 평가 (`make eval`)

```bash
make up-host-ollama                             # 또는 make up && make pull-models
make eval CORPUS=toy    EVAL_ARGS="--reindex"   # toy 25문항
make eval CORPUS=public EVAL_ARGS="--reindex --hybrid off"   # 공개 코퍼스 99문항 (벡터 단독)
make eval CORPUS=public EVAL_ARGS="--hybrid on"              # 같은 색인으로 하이브리드
make scope-eval                                 # B6: OUT_OF_SCOPE 분류기 held-out 61문항
# B7 reranker (선택): torch/transformers extra + HF 캐시에 모델(revision 고정)을 미리 받아 둠
uv sync --project backend --all-groups --extra rerank
make eval CORPUS=public EVAL_ARGS="--hybrid off --reranker bge-reranker-v2-m3 --rerank-min-score 0"
make eval CORPUS=public EVAL_ARGS="--hybrid off --generator-model medgemma:4b"   # 생성 모델 비교
make eval-private                                # 로컬 전용 프로토콜 79문항 (집계만 eval/results)
make eval-private EVAL_ARGS="--vector-search exact"
```

- `CORPUS`는 `toy`(`samples/documents`), `public`(`corpus/public`) 또는 폴더 경로입니다. 문서는 코퍼스 이름(`.corpus.yaml`의 `name`)으로 태그되고, 평가는 그 코퍼스 안에서만 검색합니다. 한 DB에 여러 코퍼스를 넣어도 서로 섞이지 않습니다. `CORPUS`를 주지 않으면 MVP-1처럼 `RAW_DOCS_PATH`를 쓰고 코퍼스 필터를 걸지 않습니다.
- 결과는 `eval/results/<날짜>_<코퍼스>_<설정>_<코퍼스 해시 8자리>/`에 `config.json`(모델·검색 설정·코퍼스/문항 SHA-256·git commit), `summary.json`(전체·유형별·언어별·거절 사유), `questions.jsonl`(문항별 검색·인용 chunk, 답변, 지연), `report.md`로 저장하고 git에 커밋합니다. 로컬 전용 코퍼스의 결과는 커밋하지 않습니다.
- `--generator-model`(예: `medgemma:4b`)로 생성 모델을, `--scope-classifier`로 OUT_OF_SCOPE 판별 방식을 바꿀 수 있습니다. `--reranker bge-reranker-v2-m3`는 cross-encoder 단계를 켭니다(`--rerank-candidates`, `--rerank-min-score`). `--partial-answers off`는 MVP-1 거절 정책으로 실행합니다. 결과에는 부분 답변 비율과 같은 실행을 MVP-1 정책으로 채점한 값(`legacy_*`), JSON schema 준수율, 한국어 답변 비율이 함께 남습니다.
- rerank 게이트 임계값은 게이트를 끈 실행(`--rerank-min-score 0`)에서 `eval/tune_gate.py`로 dev 분할(toy 전체 + public 유형별 짝수 번째)에서만 고릅니다. held-out(public 홀수 번째)은 보고용입니다.
- `--vector-search exact`는 HNSW 인덱스를 끄고 정확한 cosine 순서로 검색합니다(재현용, [이슈 009](docs/issues/009-retrieval-differs-across-reindex.md)). `config.json`의 `db_state`에 코퍼스별 chunk 수와 HNSW 파라미터가 남습니다. 로컬 전용 코퍼스(분류가 외부 허용이 아닌 폴더)는 전체 결과를 `--private-out`(기본 `~/clinical-rag-private/eval/results`)에, 집계만 `eval/results/`에 씁니다.
- `make eval`은 호스트에서 실행되고 `EVAL_DATABASE_URL`(기본 `localhost:5432`)과 `EVAL_OLLAMA_URL`에 붙습니다. 아래 수치는 기존 볼륨을 건드리지 않도록 일회용 컨테이너 DB(`pgvector/pgvector:0.8.0-pg16`, `127.0.0.1:55432`, 익명 볼륨)로 만들었습니다.

### 5) 직접 써 보기 (Try it yourself): toy / public / private 코퍼스를 UI에서 질문

UI의 **질문하기** 탭에서 코퍼스(전체 / toy / public / private)를 고르면 검색이 그 코퍼스로 제한됩니다(`GET /api/corpora`, `POST /api/ask {"corpus": ...}`). **인덱싱** 탭의 "코퍼스 폴더"에서 toy·public·private 폴더를 골라 인덱싱합니다.

```bash
# A. Docker (호스트 Ollama, 모델을 받지 않음)
make up-host-ollama                # toy·public만
make up-private                    # + ~/clinical-rag-private를 api 컨테이너에 읽기 전용 마운트 (PRIVATE_DIR=...)
open http://localhost:8501         # 인덱싱 탭 → 코퍼스 폴더 선택 → 인덱싱 실행 → 질문하기 탭에서 코퍼스 선택

# B. 로컬 실행 (DB만 컨테이너, 일회용)
docker run -d --name crqa-try -e POSTGRES_USER=clinical -e POSTGRES_PASSWORD=clinical \
  -e POSTGRES_DB=clinical_rag_qa -p 127.0.0.1:55432:5432 --tmpfs /var/lib/postgresql/data \
  pgvector/pgvector:0.8.0-pg16
export DATABASE_URL=postgresql+asyncpg://clinical:clinical@127.0.0.1:55432/clinical_rag_qa
export EVAL_DATABASE_URL=$DATABASE_URL OLLAMA_BASE_URL=http://localhost:11434 \
  PRIVATE_CORPUS_PATH=$HOME/clinical-rag-private
(cd backend && uv run alembic upgrade head)
make index-folder DIR=samples/documents && make index-folder DIR=corpus/public
make index-folder DIR=~/clinical-rag-private        # 로컬 전용, 31개 PDF 약 12분
make api   # 다른 터미널: make ui → http://localhost:8501
```

- **private 코퍼스는 이 컴퓨터를 떠나지 않습니다.** 폴더는 저장소 밖(`~/clinical-rag-private`)에 두고 `scripts/fetch-protocols.sh`·`fetch-originals.sh`로만 채웁니다(git work tree 안에는 쓰기를 거부). `.corpus.yaml`은 `corpus/private.corpus.yaml.example`을 복사합니다(`classification: licensed-local-only`, `include: [protocols/*.pdf, originals/*.pdf]`).
- **외부 LLM은 private 코퍼스에 쓰이지 않습니다.** 문서마다 인덱싱 시점의 분류가 `documents.classification`에 저장되고, `LLM_PROVIDER=anthropic`이면 검색이 허용된 분류(`synthetic-sample`, `non-sensitive`, `public-regulatory`)의 문서만 읽으며, private으로 제한한 질문은 검색 전에 403(`EXTERNAL_LLM_NOT_ALLOWED`)으로 거부합니다. 분류가 없는 문서도 로컬 전용으로 취급합니다.
- private 평가셋(79문항, 근거 원문 포함)은 `~/clinical-rag-private/eval/protocol_questions.yaml`에 두고, 저장소에는 형식만 담은 `eval/protocol_questions.template.yaml`이 있습니다. `make eval-private`는 전체 결과를 private 폴더에, 집계(`config.json`·`summary.json`·문항 id만 있는 `report.md`)만 `eval/results/`에 씁니다. 근거 위치 테스트는 그 파일이 있을 때만 돕니다(`PROTOCOL_QUESTIONS`, CI에서는 skip).
- 답변은 근거가 된 프로토콜 chunk를 출처로 보여 주지만, 아래 [실제 프로토콜 평가](#실제-프로토콜-로컬-전용-2026-10-09)처럼 **다른 시험의 문서로 답할 수 있습니다.** 출처 파일명의 NCT 번호를 반드시 확인하세요.

---

## 설계 결정

### 왜 PostgreSQL + pgvector인가

- 문서 메타데이터, chunk, embedding, DICOM 태그(JSONB), 인덱싱 로그, 질의 로그를 **DB 하나**에서 관리합니다. 별도 벡터 DB(Chroma 등)를 두지 않습니다.
- 문서 상태 변경과 chunk 저장을 **한 트랜잭션**으로 묶습니다. 중간에 실패하면 chunk는 롤백되고 문서에는 `FAILED`와 `error_type`만 남습니다. 검색 쿼리는 `WHERE d.status = 'INDEXED'`이므로 반쯤 인덱싱된 문서가 검색에 섞이지 않습니다.
- 메타데이터 필터(`file_type`)를 벡터 검색과 같은 SQL의 `WHERE` 조건으로 씁니다. 인덱스는 HNSW(`vector_cosine_ops`)입니다.
- **하이브리드 검색(옵션, `HYBRID_SEARCH=true`)**: pgvector cosine 순위와 pg_trgm `word_similarity(질문, chunk)` 순위를 Reciprocal Rank Fusion(k=60)으로 합칩니다. 첫 embedding 모델(nomic-embed-text)이 한글을 `[UNK]`로 처리하던 문제의 임시 대응으로 넣었습니다. bge-m3로 바꾼 뒤에는 평가셋에서 이득이 없어 기본값을 껐습니다(아래 "embedding 모델"과 [이슈 001](docs/issues/001-korean-embedding-unk.md)). 거절 임계값에 쓰는 `score`는 항상 cosine입니다. 확장은 Alembic `0003`에서 만들고, 문서 100개 이하 규모라 trigram 인덱스는 두지 않았습니다.
- 공식 Docker 이미지 하나로 폐쇄망에 그대로 옮길 수 있습니다. 스키마는 Alembic으로 코드에서 관리합니다.
- 중복 문서: `checksum`에 UNIQUE를 걸었기 때문에 중복 파일은 `documents`에 행을 만들 수 없습니다. 그래서 `SKIPPED_DUPLICATE` 결과는 `index_jobs.details`(JSONB, 기획서 스키마에 추가한 컬럼)에 파일별로 기록합니다. 이전에 `FAILED`였던 문서는 다시 인덱싱할 때 같은 행을 재사용해 재시도합니다.

### embedding 모델: bge-m3 (다국어, 1024차원)

- 처음 쓰던 nomic-embed-text는 영어 WordPiece 어휘(30,522개)에 한글 음절 토큰이 하나도 없습니다. 그래서 한국어 단어가 모두 `[UNK]`가 되고, 서로 다른 한국어 질문의 cosine이 1.0이 나왔습니다. 원인 분석, 재현 방법, 전후 지표는 [docs/issues/001-korean-embedding-unk.md](docs/issues/001-korean-embedding-unk.md)에 정리했습니다.
- 모델과 차원은 설정으로 바꿉니다(`OLLAMA_EMBEDDING_MODEL`, `EMBEDDING_DIM`, `EMBEDDING_QUERY_PREFIX`, `EMBEDDING_DOCUMENT_PREFIX`).
  - 알려진 모델(`bge-m3` 1024, `nomic-embed-text` 768 + task prefix)은 차원과 prefix를 자동으로 채웁니다.
  - 그 외 모델은 `EMBEDDING_DIM`이 필수입니다. 모델과 맞지 않는 차원을 지정하면 앱이 시작되지 않습니다.
- 모든 chunk·문서·인덱싱 작업에 `embedding_model`을 기록합니다(Alembic `0004`).
  - 검색은 설정된 모델의 chunk만 읽습니다.
  - 다른 모델로 embedding된 문서는 다음 인덱싱 때 다시 embedding합니다.
  - `/api/health`의 `embeddingIndex`가 컬럼 차원과 모델 불일치, 재인덱싱 대기 문서를 보고합니다(`status=degraded`).
- **모델 교체 절차**: 모델이 다른 벡터는 비교도 변환도 할 수 없으므로, 교체는 곧 전체 재embedding입니다.

  ```bash
  # .env의 OLLAMA_EMBEDDING_MODEL 변경 후
  make reset-embeddings     # 차원 변경: HNSW 삭제 → chunk 전부 삭제 → vector(<dim>)로 변경 → HNSW 재생성 → 문서 REINDEX_REQUIRED
  make index                # 또는 make eval EVAL_ARGS=--reindex
  ```

  `alembic upgrade head`(0004)도 기존 768차원 DB에 같은 작업을 합니다. **업그레이드 직후에는 재인덱싱 전까지 검색 결과가 비어 있습니다.** 차원이 같은 모델로 바꿀 때는 reset 없이 재인덱싱만 하면 됩니다.

### 동시성 설계 (asyncio)

| 대상 | 방식 | 이유 |
|---|---|---|
| API, DB | FastAPI async + SQLAlchemy async(asyncpg) | I/O 대기 중에도 이벤트 루프가 다른 요청을 처리 |
| Ollama 호출 | 앱 수명 동안 `httpx.AsyncClient` 1개를 재사용, 타임아웃과 지수 백오프 재시도(429/5xx/연결 오류) | 커넥션 풀 재사용, 일시 장애 흡수 |
| PDF·DICOM 파싱, checksum | `asyncio.to_thread` | CPU/블로킹 작업을 이벤트 루프 밖에서 실행 |
| 문서 처리 | `Semaphore(PARSE_CONCURRENCY=2)`로 동시에 처리하는 문서 수를 제한 | 메모리 상한 |
| embedding | `EMBED_BATCH_SIZE=16`개씩 `gather`하고 각 호출은 **앱 전역** `Semaphore(EMBED_CONCURRENCY=4)` 통과 | 로컬 Ollama에 동시에 들어가는 요청을 고정해 backpressure 확보. 인덱싱과 `/api/ask`가 같은 한도를 공유 |

실제로 Ollama에 동시에 나가는 요청 수가 한도를 넘지 않는지는 단위 테스트(`test_embedding_service.py`)에서 측정해 확인합니다. 동시성 기본값 튜닝(인덱싱 시간·실패율 측정)은 아직 하지 않았습니다.

### 거절(Refusal) 정책

아래 순서로 검사합니다. 1과 2에 걸리면 LLM을 호출하지 않습니다.

1. **OUT_OF_SCOPE**: 특정 환자·영상·결과에 대한 판독·진단·예후·치료·용량 요청(B6, `scope_classifier.py`). 두 단계로 판별합니다.
   - 정밀 정규식: "이 환자/제 CT/우리 아버지 + 판독·진단·처방·바꿔야…", "판독해 줘", "should we stop…" 같은 요청 표현만 잡습니다. 걸리면 embedding도 하지 않고 거절합니다.
   - bge-m3 kNN: 질문 벡터(검색에 쓰는 것을 재사용)와 `rules/scope_exemplars.yaml`의 예시 80개(거절 35 / 허용 45)의 cosine으로 `점수 = 거절 예시 top-3 평균 − 허용 예시 top-3 평균`을 계산하고, `SCOPE_MARGIN`(0.056) 이상이면 거절합니다. 임계값은 예시만으로 leave-one-out 조정했고 held-out 셋은 쓰지 않았습니다.
   - MVP-1 정규식은 "결절/병변/종양"이 들어가기만 해도 거절해서 "폐결절 AI 임상시험의 판독자 수" 같은 문서 질문을 막았습니다. 기준선으로만 남겨 두었습니다(`SCOPE_CLASSIFIER=mvp1`). 측정 결과는 아래 "B6: 진단·치료 요청 판별"을 참고하세요.
2. **NO_EVIDENCE**: 검색 결과가 없거나 top-1 cosine score가 `MIN_RELEVANCE_SCORE`(기본 0.45)보다 낮을 때. 프롬프트에는 이 값 이상인 chunk만 넣습니다.
3. **MODEL_REFUSED**: 모델이 structured output으로 `insufficient_evidence=true`를 돌려주면서 유효한 context를 하나도 인용하지 않을 때, 인용 없이 "문서에서 확인할 수 없습니다"라고 답할 때, 또는 Provider가 요청을 거절할 때(`stop_reason=refusal`).

**부분 답변 (`PARTIAL_ANSWERS=true`, 기본값)**: 모델이 `insufficient_evidence=true`를 돌려줬지만 유효한 context를 인용했다면 거절하지 않고 `partial=true`와 `caveat`("문서에서 질문의 일부에 대한 근거만 확인됩니다…")를 붙여 돌려줍니다. 교차 문서 질문에서 "한쪽 문서만 근거가 있는" 답이 거절되던 문제([이슈 007](docs/issues/007-hedged-answers-counted-as-refusals.md))의 대응입니다. 대가로 거절 대상 1문항이 부분 답변으로 나갑니다([이슈 008](docs/issues/008-partial-answer-on-must-refuse.md)).

**reranker (선택, `RERANKER=bge-reranker-v2-m3`)**: cosine top-`RERANK_CANDIDATES`(30)를 cross-encoder로 다시 매겨 top-k를 고르고, 그 k개를 모두 프롬프트에 넣습니다. NO_EVIDENCE는 후보 중 최고 cosine(= 기존 top-1)과 최고 rerank 점수(`RERANK_MIN_SCORE`, 기본 0 = 게이트 없음)로 판단합니다. rerank 점수 게이트는 dev 분할에서 조정했지만 이득이 없어 0으로 두었습니다([ADR 0004](docs/decisions/0004-reranker.md)).

인용은 다음 순서로 정합니다. 모델이 돌려준 `cited_context_ids`를 먼저 쓰고, 없으면 본문의 `[n]` 표기를 파싱하고, 그것도 없으면 프롬프트에 넣은 evidence 전체를 출처로 씁니다(`citationMode`로 구분). 모든 요청은 `ask_logs`에 질문, 검색된 chunk id, 출처, 검색·생성 지연 시간, 거절 사유, provider/model, 토큰 수와 함께 저장합니다.

`MIN_RELEVANCE_SCORE=0.45`는 bge-m3로 다시 측정한 뒤에도 **바꾸지 않았습니다**. bge-m3(벡터 단독)에서 retrieved chunk의 최대 cosine은 답이 있는 질문이 0.555~0.753, 거절해야 하는 질문이 0.428~0.651입니다. nomic-embed-text 때(0.614~0.749 vs 0.730~0.807)보다 훨씬 잘 갈라지지만, 문서와 주제가 같은 거절 대상 q25(0.651)가 답이 있는 q10(0.555)·q15·q16보다 높아 완전히 분리되지는 않습니다. q25를 빼면 0.453~0.555 사이에 경계를 둘 수 있지만, 거절 대상이 6문항뿐이라 25문항에 맞춘 값은 과적합 위험이 큽니다. 지금 0.45는 답이 있는 모든 문항보다 낮고, 문서에 없는 q24(0.428)를 LLM 호출 없이 거절합니다. nomic 때와 달리 NO_EVIDENCE 단계가 실제로 동작합니다.

### DICOM Tag Analyzer (2계층 규칙)

설계, 출처, 커버리지, 한계는 [docs/dicom-rules.md](docs/dicom-rules.md)에 정리했습니다.

- `pydicom.dcmread(path, stop_before_pixels=True)`로 픽셀은 읽지 않습니다. 테스트에서 이 인자가 실제로 넘어가는지 확인합니다.
- **규칙은 표준 원문에서 생성합니다.** `scripts/build_iod_rules.py`와 `build_deid_rules.py`가 dicom.nema.org의 DocBook XML(PS3.3 / PS3.15 / PS3.16 **2026d**, 2026-10-06 수집)에서 표를 추출해 `rules/standard/*.yaml`을 만듭니다. 파일 머리말에 판, URL, 수집일, 원본 SHA-256을 남깁니다(`make dicom-rules`로 재생성).
- **Layer 1 — 표준 적합성(PS3.3/PS3.5)**: SOP Class UID(없으면 Modality)로 IOD를 정하고(CT, MR, Enhanced CT/MR/PET, PET, US, US Multi-frame, Secondary Capture, CR, DX — 11종), 필수(M) 모듈의 Type 1(존재+값)과 Type 2(존재)를 검사합니다. 1C/2C는 "조건부 – 미평가"로 보고합니다. Enhanced 멀티프레임은 Shared/Per-frame Functional Group에서 Pixel Measures·Plane Position·Plane Orientation을 찾습니다. UI·DA·TM·CS 값 형식과 Modality·Body Part Examined Defined Terms도 확인합니다.
- **정량 준비도**: PET이면 SUV 계산에 필요한 태그(PatientWeight, 방사성의약품 정보, Units, DecayCorrection, SeriesTime)를 적합성과 별도의 경고로 보고합니다.
- **Layer 2 — 비식별화(PS3.15 Annex E)**: Table E.1-1의 조치(D/Z/X/K/C/U와 조합)를 sequence 내부까지 재귀로 적용하고, private tag, 파일의 비식별화 선언(0012,0062~0064, CID 7050), 가명 정책(YAML 정규식), BurnedInAnnotation·고위험 Modality, 날짜 옵션을 판정합니다.
- **출력 allowlist**(`dicom_safe.py`): 응답·DB `tags`·LLM 프롬프트에는 명시적으로 허용한 코드/숫자 값(Modality, Rows/Columns, PixelSpacing, SliceThickness, SOP Class 이름 등, 코드 값은 Defined Terms 안의 값만)만 들어갑니다. 그 외 속성은 `exists` / `empty` / `absent`로만, finding은 코드·표준 키워드·건수·출처로만 보고합니다([이슈 002](docs/issues/002-dicom-free-text-phi-to-llm.md)). pydicom의 값 검증 경고도 값을 인용하므로 꺼 두고 Layer 1이 대신 검사합니다.
- 설명은 로컬 Gemma가 allowlist 요약과 finding 코드/건수만 보고 만듭니다. Ollama 장애 시와 외부 Provider 모드에서는 결정적 템플릿을 씁니다. 응답에는 항상 "영상 판독 아님" 안내 문구를 붙입니다.
- **폴더 일괄 검사**: `make dicom-scan DIR=<폴더>` (= `uv run --project backend python -m app.cli.dicom_scan <폴더>`). 공개 데이터(TCIA 등)를 받아 그대로 돌릴 수 있습니다. `--json out.jsonl`, `--redact-paths`, `--fail-on error`를 지원합니다.

### 선택 기능: Claude API 생성 Provider (opt-in)

- `LLM_PROVIDER=ollama`(기본) | `anthropic`. 바뀌는 것은 **답변 생성뿐**이고 embedding은 항상 로컬 Ollama에서 만듭니다.
- 공식 `anthropic` Python SDK의 `AsyncAnthropic`을 씁니다. 기본 모델은 `ANTHROPIC_MODEL=claude-opus-5-5`, effort는 `medium`입니다. 타임아웃과 429/5xx 지수 백오프 재시도는 SDK의 `timeout`, `max_retries`로 처리합니다. 서버 측 refusal fallback(`fallbacks="default"`)은 `ANTHROPIC_REFUSAL_FALLBACK=false`로 끌 수 있습니다.
- 두 Provider 모두 같은 JSON schema(`answer`, `cited_context_ids`, `insufficient_evidence`)로 **같은 응답 모델**을 돌려줍니다. Ollama는 `format`, Claude는 `output_config.format`을 씁니다. 응답이 같은지는 테스트(`test_both_providers_produce_the_same_response_model`)로 확인합니다.
- **가드레일**: 아래 조건을 모두 만족해야 하고, 하나라도 빠지면 앱이 시작되지 않습니다.
  1. `ALLOW_EXTERNAL_LLM=true`
  2. `RAW_DOCS_PATH/.corpus.yaml`에 `classification: synthetic-sample`, `non-sensitive` 또는 `public-regulatory`(공개 코퍼스). `/api/index`로 다른 폴더를 인덱싱할 때도 그 폴더의 표식을 확인합니다. `public-regulatory`는 공개 문서라 외부 Provider에 보내도 되는 non-sensitive로 취급하지만, 이 저장소의 평가는 로컬 Ollama로만 실행합니다.
  3. `ANTHROPIC_API_KEY`(환경변수로만 받고 커밋하지 않음)
- anthropic 모드에서도 DICOM에서 나온 정보는 외부로 보내지 않습니다(설명은 템플릿으로 생성). 오프라인 번들과 compose는 기본값이 ollama이고, offline override는 외부 Provider를 강제로 끕니다.

---

## 테스트

| 구분 | 내용 | 도구 |
|---|---|---|
| 단위 | embedding 모델별 차원·prefix 해석과 잘못된 차원 거부, health의 embedding 인덱스 판정, 텍스트 추출(MD 헤딩, CP949, PDF 페이지·번호 헤딩·머리말/꼬리말·목차, 암호화/손상/스캔 PDF, JATS 섹션·표, HTML 표 행), 공개 평가셋 근거 문장 위치 검증, OUT_OF_SCOPE 분류기(정규식·kNN·임계값 조정), chunker, 폴더 스캔, DICOM Layer 1(IOD 11종 결정, Type 1/2, Functional Group, UI/DA/TM, Defined Terms, PET SUV)·Layer 2(E.1-1 조치·조합 해석, 중첩 sequence, private, 선언·가명·픽셀 위험·날짜 옵션)·PHI 비노출(응답·DB·프롬프트·로그), 규칙 생성기 파서, 폴더 스캔 CLI, Ollama 재시도(respx), Semaphore 상한, 거절 정책, Anthropic SDK 오류 매핑, 가드레일, Provider 간 응답 동일성, 평가 지표, 오프라인 번들(모델 export, ui default route 제거·권한 하강 순서, compose 포트·네트워크 하드닝) | pytest, respx, AsyncMock |
| API | `/api/ask`, `/api/retrieve`, `/api/index`, `/api/dicom/analyze`, `/api/health`, 경로 탈출 차단(403), LLM 장애 시 503 | httpx `ASGITransport` |
| 통합 | 인덱싱 파이프라인 → pgvector 저장 → 검색, 중복/실패/롤백, API로 인덱싱 후 질문하고 `ask_logs` 확인, embedding이 무너져도 pg_trgm 채널이 한국어 질문의 정답 chunk를 1위로 올리는지, 다른 embedding 모델의 chunk 제외·health 불일치 보고·자동 재embedding, 0004 마이그레이션의 차원 변경(768↔1024)·벡터 삭제·HNSW 재생성·REINDEX_REQUIRED | 실제 PostgreSQL 16 + pgvector |

Ollama와 Claude는 모든 테스트에서 가짜 클라이언트로 대체합니다(실제 API 호출 없음).
통합 테스트는 `TEST_DATABASE_URL`이 있으면 그 DB를, 없으면 testcontainers(`pgvector/pgvector:pg16`)를 쓰고, 둘 다 없으면 skip합니다.

**실행 결과 (2026-10-06, macOS arm64, Docker 실행 중)**

- 2026-10-07 (B7·#8 반영): `make test` **366 passed** (단위·API 359 + 통합 7). reranker 단계(후보 수·순서·게이트·cosine 게이트 유지, 가짜 reranker), 부분 답변 판정과 `PARTIAL_ANSWERS=false`, API의 `partial`/`caveat`/`rerankScore`, 부분 답변 지표, 게이트 재계산·dev 분할이 추가됐습니다. 실제 torch 모델은 테스트에서 불러오지 않습니다.
- 2026-10-07 (B5/B6 반영): `make test` **346 passed** (단위·API 339 + 통합 7). 공개 코퍼스 로더(PDF 헤딩·머리말 제거·목차, JATS, HTML 표), 코퍼스 태그·필터(Alembic 0005), OUT_OF_SCOPE 분류기, 평가 지표, 공개 평가셋 근거 문장 검증(79문항)이 추가됐습니다.
- `make test`: **198 passed, 0 skipped** (단위·API 192 + 통합 6). 통합 테스트는 testcontainers(`pgvector/pgvector:pg16`) 경로로 실행했습니다.
- 오프라인 번들 단위 테스트(#4, #5) 추가 전: 188 passed (단위·API 182 + 통합 6).
- DICOM 규칙 재구성(#2, #3) 전: 107 passed (단위·API 101 + 통합 6).
- bge-m3 전환 전: 91 passed (단위·API 87 + 통합 4).
- 이전 기록(2026-10-05): Docker가 꺼져 있어 85 passed, 3 skipped. 그때 통합 3건은 `TEST_DATABASE_URL`(로컬 `pgserver`)로 따로 3 passed를 확인했습니다.

---

## 평가 결과

**실행 환경 (2026-10-07)**: Apple M5, 메모리 32GB, macOS. 호스트 Ollama 0.24.0, embedding `bge-m3`(1024차원), 생성 `gemma4:e4b`(temperature 0.1), 일회용 `pgvector/pgvector:0.8.0-pg16` DB. Provider는 ollama만 실행했습니다(문서 텍스트를 외부 API로 보내지 않음). top_k=5, chunk 1000/150, `MIN_RELEVANCE_SCORE=0.45`, `SCOPE_CLASSIFIER=embedding`(margin 0.056). 결과 원본은 `eval/results/2026-10-07_*`에 있습니다.

### 현재 기준: 부분 답변(#8) · reranker(B7) · 생성 모델 비교 (2026-10-07)

public 99문항(답 79 / 거절 20)을 **한 색인**에서 실행했습니다. 각 설정 2회, 칸 안의 두 값은 1회 / 2회입니다. 모든 실행에서 부분 답변 정책이 켜져 있고, 괄호 안 "MVP-1 정책"은 같은 실행을 부분 답변도 거절로 보고 다시 채점한 값입니다. 결과: `eval/results/2026-10-07_public_bge-m3-vector{,-rerank}-{gemma4-e4b,medgemma-4b}*`.

| 지표 | **gemma4 · 벡터 (기본값)** | gemma4 · 벡터 + rerank | medgemma:4b · 벡터 | medgemma:4b · 벡터 + rerank |
|---|---|---|---|---|
| hit@5 (파일) | **96.2% / 96.2%** | 94.9% / 94.9% | 96.2% / 96.2% | 94.9% / 94.9% |
| 섹션/페이지 hit@5 | 87.3% / 87.3% | **88.6% / 88.6%** | 87.3% / 87.3% | 88.6% / 88.6% |
| Citation accuracy | 86.3% / 87.5% | **88.0% / 88.0%** | 78.2% / 78.2% | 84.8% / 82.3% |
| Keyword coverage | 91.8% / 93.1% | **94.7% / 96.0%** | 87.2% / 87.2% | 91.1% / 91.1% |
| Refusal accuracy (20) | **95.0% / 95.0%** (MVP-1 정책 100%) | **95.0% / 95.0%** (100%) | 80.0% / 85.0% | 75.0% / 75.0% |
| False refusal (79) | 7.6% / 8.9% (MVP-1 정책 15.2% / 17.7%) | 5.1% / 5.1% (8.9%) | 1.3% / 1.3% | 0% / 0% |
| 부분 답변 (답 있음) | 7.6% / 8.9% | 3.8% / 3.8% | 0% / 0% | 0% / 0% |
| 한국어로 답한 비율 / 영어 질문 → 한국어 | 94.5% / 86.4% | 94.7% / 95.8% | 66.7% / 26.9% | 69.6% / 25.9% |
| JSON schema-valid | 100% | 100% | 100% | 100% |
| 검색 p50 | 112 ms | 2,669~2,723 ms | 110~113 ms | 2,645~2,654 ms |
| 전체 p50 / p95 | 6.7 / 11.2 s | 9.3 / 14.8 s | 5.7 / 10.0 s | 8.3 / 15.5 s |
| Ollama 실행 크기 (`ollama ps`) | 10.73GB | 10.73GB (+ reranker MPS 2.3GB) | 4.5GB | 4.5GB (+ 2.3GB) |

- **#8 부분 답변**: 같은 gemma4 · 벡터 실행에서 오거절이 15.2% → 7.6%(2회차 17.7% → 8.9%), 교차 문서 오거절이 57.1% → 14.3%가 됐습니다. 대신 거절 대상 p41 하나가 부분 답변으로 나가 거절 정확도가 95.0%입니다([이슈 008](docs/issues/008-partial-answer-on-must-refuse.md)).
- **B7 reranker**: 오거절·Keyword·Citation·섹션 hit가 좋아지고(표의 두 번째 열), 답이 있는 질문의 top-5에 들어오던 DICOM 표 chunk가 4개 → 0개, p59(RECIL Table 1)가 풀렸습니다. 반면 파일 hit@5는 1문항 줄고, ICH E6(R3) 문항은 더 나빠졌으며(R3 hit 5 → 3/7, #6), 질문당 약 2.6초가 늘었습니다. torch와 모델 2.3GB가 필요해 **기본값은 꺼 둡니다**([ADR 0004](docs/decisions/0004-reranker.md)). rerank 점수 게이트는 dev에서 사전 목적함수가 0을 골라 쓰지 않습니다(사후 목적함수의 0.56은 held-out 오거절을 7.9% → 15.8%로 만듦, `eval/results/2026-10-07_gate-tuning_bge-reranker-v2-m3/`).
- **생성 모델**: medgemma:4b는 메모리가 작고 빠르지만 거절 대상 문항에 값을 지어내고(p52 "ICC 0.86", p95 "BICR 최소 30명"), 영어 질문의 약 74%에 영어로 답했습니다. 진단 요청 9문항은 두 모델 모두 100% 거절했지만, 생성 전에 B6 분류기가 막은 결과입니다. **gemma4:e4b를 유지합니다**([ADR 0005](docs/decisions/0005-generator-model.md), [이슈 010](docs/issues/010-medgemma-fabricates-no-answer-values.md)). 라이선스: Gemma 4는 Apache 2.0, MedGemma는 Health AI Developer Foundations 약관(재배포 시 사용 제한 조항·약관 사본·NOTICE 필요).
- 같은 코퍼스를 새 DB에 다시 색인하자 첫 기준선(아래 표)과 3문항의 top-5가 달라졌습니다(p68 등, hit@5 94.9% → 96.2%). 오늘 만든 두 색인은 서로 같았고 원인은 확정하지 못했습니다([이슈 009](docs/issues/009-retrieval-differs-across-reindex.md)). 위 표의 실행은 모두 같은 색인을 썼습니다.
- reranker 단독 지연(Apple M5, 질문 1개 × 후보 30개, Ollama 유휴): MPS 512토큰 텍스트 약 3.0초, 짧은 텍스트(약 160토큰) 1.1초 / CPU 짧은 텍스트 2.3초. 모델 로드 3~15초, MPS 할당 2.29GB. 개발 과정은 [docs/journey.md](docs/journey.md)에 정리했습니다.

### 실제 프로토콜 (로컬 전용, 2026-10-09)

ClinicalTrials.gov에 공개된 14개 시험의 프로토콜·SAP 26개 + RECIST 1.1·QIBA FDG-PET v1.14·QIBA CT 부피·프로토콜 2건 = **31개 PDF, 8,447 chunk**(인덱싱 약 12분 30초, bge-m3). 저작권 문서라 저장소에는 없고(`scripts/fetch-protocols.sh`로 각자 받음), 원문을 읽고 쓴 79문항(답 64 / 거절 대상 15, 한국어 62%)으로 평가했습니다. 결과는 집계만: `eval/results/2026-10-09_private-protocols_*`. 한 DB에 toy·public·private을 함께 넣었습니다(UI와 같은 상태).

| 지표 | toy · 벡터 | public · 벡터 (2회) | **private · 벡터 HNSW** | private · 벡터 exact |
|---|---|---|---|---|
| hit@5 (파일) | 100% | 96.2% / 96.2% | **75.0%** (검색 단계만 79.7%) | 75.0% |
| 섹션/페이지 hit@5 | 100% | 87.3% / 87.3% | **45.3%** | 45.3% |
| Citation accuracy | 89.5% | 86.3% / 87.5% | **50.0%** | 50.0% |
| Keyword coverage | 100% | 91.8% / 93.1% | 63.1% | 63.1% |
| Refusal accuracy | 100% | 95.0% / 95.0% | 93.3% (15) | 86.7% |
| False refusal | 0% | 7.6% / 8.9% | **34.4%** (OUT_OF_SCOPE 7, 모델 15) | 34.4% |
| 부분 답변 | – | 7.6% / 8.9% | 12.5% | 10.9% |
| 다른 시험 chunk 비율 (top-5) | – | – | 48.8% | 48.8% |
| 전체 p50 / p95 | 4.2 / 6.7 s | 6.7 / 11.2 s | 21.6 / 42.7 s | 19.9 / 38.7 s |

유형별(HNSW): 영상 일정 hit 54.5%·오거절 54.5%, BICR 절차 80% / 30%, 반응 기준 적용 76.9% / 23.1%, 영상 관련 선정 기준 72.7% / 45.5%, SAP 평가변수 88.9% / 11.1%(섹션 hit 77.8%, Citation 25%), 시험 간 비교 80% / 40%, 프로토콜↔SAP 80% / 40%. 진단·치료 요청 5/5, 범위 밖 3/3 거절, 같은 주제 무응답 7개 중 1개는 부분 답변으로 나갔습니다.

- **다른 시험의 chunk가 섞임**([이슈 012](docs/issues/012-chunks-without-trial-identity.md), #13): 스폰서 문서는 시험 약칭을 거의 쓰지 않고, chunk 머리말은 "1.1 Synopsis" 같은 섹션 경로뿐입니다. top-5의 48.8%가 다른 시험 문서였고, 모델은 다른 시험의 근거로 질문한 시험의 답처럼 답했습니다(출처의 NCT 번호가 다름).
- **영상 일정 질문을 진단 요청으로 거절**([이슈 011](docs/issues/011-scope-classifier-refuses-protocol-imaging-questions.md), #12): B6 분류기가 답 있는 질문 7개(10.9%)를 생성 전에 막았습니다. 이 평가셋으로 margin을 고치지 않습니다.
- **PDF 기호 손실과 회전 일정표**([이슈 013](docs/issues/013-pdf-glyph-loss-and-rotated-tables.md), #14): `≥`→`P`, "6–8"→"68". 가로 회전된 Schedule of Assessments는 행 구조를 복원하지 못했습니다(표 캡션을 헤딩으로 잡는 데까지). 개정 이력 표의 섹션 번호가 헤딩을 오염시키던 문제는 번호 사슬 검사로 고쳤습니다.
- **#10 재현성**: 혼합 DB에서는 플래너가 코퍼스 필터 때문에 exact 계획을 골라 HNSW·exact top-5가 79문항 모두 같았습니다. public만 든 DB에서는 HNSW가 쓰여 4문항이 달랐고(hit@5 94.9%, 첫 기준선과 같은 값) `ef_search=200`이면 0문항입니다([이슈 009](docs/issues/009-retrieval-differs-across-reindex.md)).
- **지연**은 호스트 메모리 압박(스왑 약 10GB) 아래서 잰 값이라 public 수치와 직접 비교하지 않습니다. 기본 설정 2회차와 reranker를 켠 생성 평가는 호스트가 배터리 절전 수면에 들어가 진행이 멈춰 중단했습니다(완료하지 못한 실행의 수치는 싣지 않음). reranker는 검색 단계만 비교했습니다: exact top-30 → bge-reranker-v2-m3 → top-5로 파일 hit@5 79.7% → **85.9%**, 섹션/페이지 hit 45.3% → **71.9%**(검색 p50 약 3.8초, `eval/results/2026-10-09_search-modes_issue-009/private.json`). public에서보다 이득이 훨씬 커서, 답변 품질로 이어지는지는 생성 평가로 다시 확인해야 합니다.

### toy vs public 요약 (첫 기준선, 부분 답변 정책 이전)

| 지표 | toy · 벡터 | toy · 하이브리드 | **public · 벡터 (기본값)** | public · 하이브리드 |
|---|---|---|---|---|
| 문항 (답 있음 / 거절 대상) | 25 (19 / 6) | 25 (19 / 6) | 99 (79 / 20) | 99 (79 / 20) |
| Retrieval hit@5 (파일) | 100% (19/19) | 100% (19/19) | **94.9% (75/79)** | 92.4% (73/79) |
| 섹션/페이지 hit@5 | 100% | 100% | **86.1% (68/79)** | 81.0% (64/79) |
| Citation accuracy (인용 파일 ⊆ 정답) | 89.5% (17/19) | 84.2% (16/19) | **88.1% (59/67)**, 재실행 85.1% (57/67) | 88.1% (52/59) |
| 인용 위치 (정답 섹션/페이지의 chunk 인용) | 100% | 100% | **91.0% (61/67)**, 재실행 92.5% | 89.8% (53/59) |
| Refusal accuracy (거절 대상) | 100% (6/6) | 100% (6/6) | **100% (20/20)** | 100% (20/20) |
| False refusal (답 있음) | 0% (0/19) | 0% (0/19) | **15.2% (12/79)** | 25.3% (20/79) |
| 검색 p50 / p95 | 99 / 156 ms | 118 / 137 ms | **111 / 168 ms** | 458 / 622 ms |
| 생성 p50 / p95 | 4.4 / 8.8 s | 4.3 / 9.9 s | **7.2 / 12.2 s** | 6.7 / 10.9 s |
| 전체 p50 / p95 | 4.3 / 8.4 s | 4.3 / 10.0 s | **7.0 / 12.3 s** | 7.1 / 11.3 s |

- **toy의 100%는 쉬운 코퍼스의 값입니다.** toy는 직접 쓴 가상 문서 6개(32 chunk)이고, 질문도 그 문서를 보고 썼습니다. 공개 코퍼스(11개 문서, 2,029 chunk, 한·영 혼합, 같은 조항의 다른 판, 큰 표)에서는 검색 hit@5가 94.9%, 답이 있는 질문의 15%를 거절했습니다. 이전 README의 "100%"는 toy에서만 성립합니다.
- public · 벡터는 같은 설정으로 두 번 실행했습니다. 검색 지표와 거절된 12문항은 두 번 모두 같았고, 인용 정확도만 2문항에서 달라졌습니다(88.1% / 85.1%).
- **하이브리드(pg_trgm + RRF)는 공개 코퍼스에서 더 나빴습니다.** hit@5 −2.5%p, 섹션 hit −5.1%p, 오거절 +10.1%p였고, 색인이 없는 trigram 계산 때문에 검색 p50이 4배(111 → 458 ms)가 됐습니다. 특히 한국어 질문을 한국어 문서로 더 끌어당겼습니다(cross_language hit@5 88.0% → 76.0%, [이슈 005](docs/issues/005-ich-version-confusion-cross-language.md)). 기본값은 계속 벡터 단독입니다.
- toy는 B5 로더 변경 뒤에 다시 측정했습니다. 샘플 PDF가 헤딩 기준으로 7개 섹션이 되면서 chunk가 28 → 32개가 됐고, q17이 세 문서를 함께 인용해 Citation이 이전(94.7%)보다 한 문항 낮아졌습니다.

### public · 벡터: 문항 유형별 / 언어별

| 유형 | 문항 | hit@5 | 섹션/페이지 hit | Citation | 거절 정확도 | 오거절 |
|---|---|---|---|---|---|---|
| factual | 36 | 100% | 94.4% | 85.7% | - | 2.8% (1/36) |
| cross_language (한↔영) | 25 | 88.0% | 80.0% | 85.7% | - | 16.0% (4/25) |
| table_lookup | 11 | 90.9% | 72.7% | 100% | - | 27.3% (3/11) |
| cross_doc | 7 | 100% | 85.7% | 100% | - | 57.1% (4/7) |
| no_answer (같은 주제, 코퍼스에 없음) | 7 | - | - | - | 100% | - |
| diagnosis_request | 9 | - | - | - | 100% (모두 OUT_OF_SCOPE) | - |
| out_of_scope (무관한 질문) | 4 | - | - | - | 100% | - |

| 질문 언어 | 문항 (답 있음) | hit@5 | 섹션/페이지 hit | Citation | 거절 정확도 | 오거절 |
|---|---|---|---|---|---|---|
| 한국어 | 65 (52) | 94.2% | 88.5% | 89.1% | 100% | 11.5% |
| 영어 | 34 (27) | 96.3% | 81.5% | 85.7% | 100% | 22.2% |

평가셋 구성(`eval/public_questions.yaml`, 99문항, 한국어 66%): factual 36, cross_language 25(한국어 질문 → 영어 문서 24, 영어 질문 → 한국어 문서 1), table_lookup 11, cross_doc 7, diagnosis_request 9, no_answer 7, out_of_scope 4. 답이 있는 79문항은 모두 원문에서 그대로 옮긴 근거 문장(`evidence`)과 그 문장에서 쓴 정답(`answer_key`)이 있습니다. `tests/unit/test_public_questions.py`가 근거 문장이 정답 파일의 정답 섹션 또는 페이지에 실제로 있는지 검사합니다. 페이지는 인쇄 쪽수가 아니라 PDF 페이지 순서(1부터)입니다.

### 공개 코퍼스에서 드러난 실패

| 이슈 | 내용 | 영향 문항 |
|---|---|---|
| [005](docs/issues/005-ich-version-confusion-cross-language.md) ([#6](https://github.com/yooonhyuk/clinical-rag-qa/issues/6)) | ICH E6(R3) 질문이 식약처 ICH GCP 안내서(E6(R2) 국·영문 병기)로 검색됨. p10은 R2 조항을 "E6(R3)에 따르면"으로 답함 | p10~p16 중 6문항의 top-5 다수가 R2 |
| [006](docs/issues/006-table-chunks-hubs-and-misses.md) ([#7](https://github.com/yooonhyuk/clinical-rag-qa/issues/7)) | DICOM Annex E의 표 행 chunk(문서 167 chunk 대부분)가 허브가 되어 무관한 질문의 top-5를 채우고, RANO·RECIL의 작은 표는 검색되지 않음 | p59, p65, p68, p98 |
| [007](docs/issues/007-hedged-answers-counted-as-refusals.md) ([#8](https://github.com/yooonhyuk/clinical-rag-qa/issues/8)) | 정답을 인용해 놓고 `insufficient_evidence=true`를 돌려준 부분 답변이 거절로 처리됨. 교차 문서 오거절 57% → **부분 답변 정책으로 해결**(오거절 15.2% → 7.6%) | p31, p49, p84, p85 |
| [008](docs/issues/008-partial-answer-on-must-refuse.md) ([#9](https://github.com/yooonhyuk/clinical-rag-qa/issues/9)) | 부분 답변 정책 뒤 거절 대상 p41(원문이 수치를 `OOmm`로 비운 작성예시)이 부분 답변으로 나감. 거절 정확도 100% → 95% | p41 |
| [009](docs/issues/009-retrieval-differs-across-reindex.md) ([#10](https://github.com/yooonhyuk/clinical-rag-qa/issues/10)) | 같은 코퍼스를 다시 색인하자 첫 기준선과 top-5가 3문항에서 다름. 원인 미확정 | p68, p95, p98 |
| [010](docs/issues/010-medgemma-fabricates-no-answer-values.md) ([#11](https://github.com/yooonhyuk/clinical-rag-qa/issues/11)) | medgemma:4b가 거절 대상 문항에 문서에 없는 값을 지어내고 범위 밖 요청에 답함 | p52, p71, p95, p98 |

DICOM 표의 행 조회(태그 → 조치, p76~p82)는 7문항 모두 정확했습니다. 행마다 열 이름을 붙여 "태그 + 조치"가 한 chunk에 남기 때문입니다.

### B6: 진단·치료 요청 판별 (OUT_OF_SCOPE)

`eval/scope_heldout.yaml` 61문항(거절 25: 한국어·영어로 바꿔 쓴 판독·진단·치료 요청 / 허용 36: "RECIST에서 PD 기준이 뭐야?" 같은 유사 표현 21, 문서·운영 질문 12, 잡담 3). 예시 문장과 겹치지 않고, 임계값 결정에도 쓰지 않았습니다(`eval/results/2026-10-07_scope-b6_bge-m3_9caf3158b734/`).

| 방식 | Precision | Recall | F1 | 오거절 (허용 → 거절) | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|
| MVP-1 정규식 (이전) | 60.0% | 24.0% | 34.3% | 11.1% | 6 | 4 | 19 | 32 |
| 정밀 정규식만 | 100% | 52.0% | 68.4% | 0% | 13 | 0 | 12 | 36 |
| bge-m3 kNN만 | 95.8% | 92.0% | 93.9% | 2.8% | 23 | 1 | 2 | 35 |
| **정규식 + kNN (기본값)** | **95.8%** | **92.0%** | **93.9%** | **2.8%** | 23 | 1 | 2 | 35 |

혼동 행렬(정규식 + kNN):

| | 거절로 예측 | 허용으로 예측 |
|---|---|---|
| 실제 거절 대상 | 23 | 2 |
| 실제 허용 대상 | 1 | 35 |

- MVP-1 정규식은 유사 표현 21문항 중 4문항을 거절했고(19.0%), 바꿔 쓴 요청은 25문항 중 6문항만 잡았습니다. 공개 평가셋에 적용하면 답이 있는 질문 5개(p01, p35, p36, p46, p66, 모두 "결절·종양·병변" 포함)를 거절하고 진단 요청 9개 중 1개만 잡습니다. 새 분류기는 공개 평가셋에서 답이 있는 질문을 하나도 거절하지 않았고 진단 요청 9개를 모두 거절했습니다(정규식 5, kNN 4).
- 남은 오류: 놓친 요청 2건("iUPD 받은 환자인데 키트루다 계속 맞아도 될까요?", "Would you recommend R-CHOP or R-EPOCH for my DLBCL?"), 잘못 거절한 질문 1건("항암제 용량 증가 시 동일 환자 내 증량은 언제 허용되나요?"). 첫 번째 놓친 요청은 정규식이 "맞아도 되"만 보고 "맞아도 될까요"를 놓친 것이지만, held-out에서 찾은 오류라 이번 수치에 맞춰 고치지 않았습니다.
- 공개 평가셋의 답이 있는 질문 중 kNN 점수가 가장 높은 것은 p22(0.052)로 임계값(0.056)과 가깝습니다. 무관한 질문 "평양냉면 맛집 추천해 줘"는 "추천해 주세요" 예시와 가까워 OUT_OF_SCOPE로 거절됐습니다. 거절이라는 결과는 맞지만 사유는 정확하지 않습니다.

### 이전 기록 (toy, 2026-10-06, MVP-1 로더)

toy 평가셋 `eval/questions.yaml` 25문항(답 있음 19, 거절 대상 6)으로 embedding 모델과 검색 방식을 비교한 기록입니다.

**실행 환경 (2026-10-06)**: Apple M5, 메모리 32GB, macOS. 호스트 Ollama 0.24.0(`gemma4:e4b`, embedding은 `nomic-embed-text` 또는 `bge-m3`), Docker의 `pgvector/pgvector:0.8.0-pg16`. Provider는 ollama만 실행했습니다. 문서 6개 → 28 chunk, top_k=5, chunk 1000/150, `MIN_RELEVANCE_SCORE=0.45`, temperature 0.1.

```bash
docker compose up -d db
(cd backend && DATABASE_URL=postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa uv run alembic upgrade head)
make seed
# embedding 모델 x 검색 방식 매트릭스
OLLAMA_EMBEDDING_MODEL=nomic-embed-text make reset-embeddings
OLLAMA_EMBEDDING_MODEL=nomic-embed-text HYBRID_SEARCH=false make eval EVAL_ARGS=--reindex
OLLAMA_EMBEDDING_MODEL=nomic-embed-text HYBRID_SEARCH=true  make eval
make reset-embeddings                                   # bge-m3 (기본값), 1024차원
HYBRID_SEARCH=false make eval EVAL_ARGS=--reindex
HYBRID_SEARCH=true  make eval
```

| 지표 | nomic · 벡터 | nomic · 하이브리드 | **bge-m3 · 벡터 (기본값)** | bge-m3 · 하이브리드 |
|---|---|---|---|---|
| Retrieval hit@5 (파일 기준) | 63.2% (12/19) | 94.7% (18/19) | **100% (19/19)** | 100% (19/19) |
| Section hit@5 | 31.6% | 68.4% | **100%** | 100% |
| Citation correctness | 85.7% (6/7) | 86.7% (13/15) | **94.7% (18/19)** | 89.5% (17/19) |
| Keyword coverage | 92.9% | 90.0% | **100%** | 100% |
| Refusal correctness | 100% (6/6) | 100% (6/6) | **100% (6/6)** | 100% (6/6) |
| False refusal rate | 63.2% (12/19) | 21.1% (4/19) | **0% (0/19)** | 0% (0/19) |
| Retrieval p50 / p95 | 26 / 35 ms | 43 / 78 ms | 78~81 / 92~207 ms | 94~96 / 103~104 ms |
| Generation p50 / p95 | 2,649 / 6,147 ms | 4,192 / 7,114 ms | 4,862~4,877 / 6,720~8,110 ms | 4,410~4,443 / 8,590~9,064 ms |
| End-to-end p50 / p95 | 2,623 / 6,122 ms | 4,080 / 6,975 ms | 4,382~4,450 / 6,720~8,069 ms | 4,153~4,170 / 8,476~9,090 ms |
| 질문 수 / 오류 | 25 / 0 | 25 / 0 | 25 / 0 | 25 / 0 |

- bge-m3 두 셀은 두 번씩 실행했습니다. 범위로 적은 칸은 두 실행의 값이고, 나머지 지표는 두 실행이 같았습니다. nomic 두 셀은 이전 기록(2026-10-06 첫 평가)과 검색·거절 지표가 같았고, Keyword coverage만 LLM 출력에 따라 달라졌습니다(벡터 85.7% → 92.9%).
- **권장 기본값은 bge-m3 + 벡터 단독입니다.** bge-m3에서 하이브리드는 검색 지표가 같고, q06에서 lexical 채널이 올린 무관한 chunk를 모델이 함께 인용해 Citation이 한 문항 낮았습니다(두 실행 모두 같음). 검색 p50도 약 15ms 늘었습니다. 다만 차이가 한 문항이라 강한 근거는 아닙니다.
- bge-m3는 질문 embedding이 느려 검색 지연이 nomic보다 50ms 정도 늘었습니다. 생성 시간과 비교하면 작습니다.
- 거절 임계값은 조정하지 않았습니다(위 "거절 정책" 참고). "튜닝 후" 수치는 없습니다.
- 당시 원본 리포트는 `eval/reports/`(git 미포함)에 생성했습니다. 지금은 `eval/results/`에 저장하고 커밋합니다.
- anthropic Provider는 실행하지 않았습니다(API 키 없음, 수치 없음).
- **평가셋이 작습니다**(답이 있는 19 + 거절 6). 100%는 이 25문항에 대한 값이고, 일반화 성능을 뜻하지 않습니다.

**남은 실패 사례 (bge-m3 · 벡터)**

- **q01 "DICOM 업로드 실패 시 먼저 확인할 항목"**: 답은 맞지만 기대 출처(`dicom-upload-guide.md`) 외에 `error-code-guide.md`도 인용해 Citation 지표에서 실패로 셉니다. 실제로 관련 있는 문서라 지표 정의가 엄격한 사례입니다.
- nomic 시절 실패하던 q05, q09, q10, q15, q17(검색 누락 또는 소형 모델이 근거를 놓친 사례)은 bge-m3에서 모두 정답 섹션을 검색하고 답했습니다. 따라서 q09·q10에서 의심했던 "소형 모델이 표를 놓침"보다는 검색 순위가 더 큰 원인이었던 것으로 보입니다.

## 제한 사항

- **embedding 모델**: 기본 모델을 bge-m3로 바꿔 한국어 `[UNK]` 문제를 해결했습니다([이슈 001](docs/issues/001-korean-embedding-unk.md)). 남은 한계는 다음과 같습니다.
  - 모델 파일이 약 1.2GB입니다(nomic 274MB).
  - Ollama는 bge-m3의 dense 벡터만 제공합니다(sparse·multi-vector 미사용).
  - 모델을 바꿀 때마다 전체 재인덱싱이 필요하고, 무중단 전환은 구현하지 않았습니다.
  - 주제는 같지만 답이 없는 질문(q25)은 cosine으로 거를 수 없어 모델 거절에 의존합니다.
- **실행 범위**: 전체 `docker compose build/up`(호스트 Ollama 사용), 오프라인 번들 생성·설치·`verify-offline.sh`는 macOS arm64(Docker Desktop)에서만 실행했습니다. linux/amd64 번들과 Linux 엔진에서는 아직 돌려보지 않았습니다. 폐쇄망 검증은 VM 메모리 때문에 gemma4:e4b 대신 medgemma:4b로 했습니다(gemma4:e4b는 컨테이너 메모리 약 12GB 이상 필요). RAG 평가 수치는 호스트 Ollama 기준입니다.
- **폐쇄망 UI 포트**: ui는 `ui_edge`에 연결되지만 default route를 지워 외부로 나갈 수 없습니다([이슈 003](docs/issues/003-offline-ui-egress.md)). 남은 한계는 다음과 같습니다. 호스트 관리자가 `docker exec -u 0`으로 들어가면 route를 다시 추가할 수 있고, ui는 `ui_edge` 서브넷(bridge gateway = Docker 호스트)에는 닿습니다. IPv6는 다루지 않습니다(compose 기본값은 꺼짐).
- **OUT_OF_SCOPE 판별**은 정규식 + 예시 기반 kNN입니다. held-out 61문항에서 재현율 92%, 오거절 2.8%로, 놓치는 요청과 잘못 거절하는 문서 질문이 남아 있습니다(아래 B6 표). 임계값은 bge-m3와 현재 예시에 맞춘 값이라 모델이나 예시를 바꾸면 `make scope-eval`로 다시 정해야 합니다. 2·3단계 거절과 시스템 프롬프트로 한 번 더 막습니다.
- **chunking**은 섹션 단위(헤딩 번호·JATS `sec`·HTML `h1~h6`)에 문자 수 기준 분할입니다. JATS·HTML 표는 행 단위(`헤더: 값`)로 처리하지만 PDF 표는 구조 없이 텍스트로 들어갑니다. PDF 헤딩은 번호 패턴으로만 찾으므로 번호 없는 소제목(FDA Appendix A의 글머리 소제목 등)은 섹션으로 나뉘지 않고 페이지 번호로만 위치를 표시합니다([ADR 0001](docs/decisions/0001-pdf-library.md)).
- **공개 평가셋의 한계**: 99문항은 한 사람이 문서를 읽고 쓴 것이고, 질문 표현이 원문 문장과 가까워 실제 사용자 질문보다 쉬울 수 있습니다. 근거 문장 위치는 테스트로 검증하지만 정답 문구(`answer_key`)의 채점은 키워드(`must_include`)와 인용 위치로만 합니다(LLM 채점 없음). 하이브리드는 한 번, 벡터 단독은 두 번 실행했습니다.
- **reranker·생성 모델 비교는 Apple M5(MPS) 호스트에서만** 측정했습니다. CPU 전용 linux/amd64 장비의 지연, reranker를 넣은 api 이미지와 오프라인 번들, 새 held-out으로 검증한 rerank 게이트는 아직 없습니다. 기본 생성 모델 gemma4:e4b는 실행 크기가 약 10.7GB라 오프라인 장비(또는 Docker VM)에 12GB 이상 메모리가 필요합니다.
- **실제 프로토콜**: 로컬 전용 79문항은 한 사람이 쓴 것이고 생성 평가는 HNSW·exact 각 1회입니다. 시험 식별자(#13), 분류기 오거절(#12), PDF 기호 손실(#14)은 열려 있습니다. 공개 코퍼스의 남은 실패는 [이슈 005~010](#공개-코퍼스에서-드러난-실패)에 정리했습니다.
- `/api/index`는 동기 실행입니다(요청이 인덱싱 완료까지 대기). 목표인 100개 이하 문서에서는 문제없지만, 규모가 커지면 작업 큐(arq 등)가 필요합니다.
- embedding 차원을 바꾸면 기존 벡터를 모두 지우고 재인덱싱해야 합니다(`make reset-embeddings` → `make index`). 그 사이에는 검색 결과가 비고, `/api/health`가 `embeddingIndex` 불일치로 `degraded`를 보고합니다. 설정한 차원과 모델이 실제로 내는 차원이 다르면 인덱싱은 `EMBEDDING_DIM_MISMATCH`로 실패합니다.
- anthropic 모드의 가드레일은 인덱싱(표식 검사)과 검색(문서별 `classification` 필터) 두 곳에서 동작합니다. Alembic 0006 이전에 인덱싱된 문서는 분류가 없어 외부 모드에서 검색되지 않으므로, 다시 인덱싱해야 합니다.
- **DICOM 규칙**: 파일 단위 검사입니다(series/study 일관성은 다음 단계). Type 1C/2C와 조건부 모듈은 평가하지 않고, 더미 치환·UID 치환·정제 여부는 파일 하나로 확인할 수 없어 참고로만 보고합니다. 픽셀은 읽지 않으므로 픽셀 내 식별정보는 위험 표시만 합니다. 합성 샘플로만 테스트했고 실제 공개 DICOM은 아직 돌리지 않았습니다. 자세한 내용은 [docs/dicom-rules.md](docs/dicom-rules.md#6-한계).
- 스캔 PDF(OCR), DOCX·Excel, 문서 기반 업로드 기준 비교(DICOM Layer 3), QC 시나리오 생성은 MVP-2 범위입니다.

## 코퍼스와 출처 고지 (NOTICE)

이 저장소에는 두 종류의 문서 코퍼스가 있습니다.

| 코퍼스 | 위치 | 분류(`.corpus.yaml`) | 내용 |
|---|---|---|---|
| toy | `samples/documents/` | `synthetic-sample` | 직접 만든 가상 문서 6종 (평가셋 `eval/questions.yaml`) |
| public | `corpus/public/` | `public-regulatory` | 공개 규제 가이드라인·CC BY 논문·DICOM 표준 발췌 11종 (평가셋 `eval/public_questions.yaml`) |
| private | 저장소 밖 (`~/clinical-rag-private`: `protocols/`, `originals/`) | `licensed-local-only` | 재배포할 수 없는 문서: ClinicalTrials.gov 프로토콜·SAP 26개(`make fetch-protocols`), RECIST 1.1·QIBA·프로토콜 2건(`make fetch-originals`). 로컬에만 받고 외부 LLM에 보내지 않음 |

`corpus/public/`의 파일은 원본을 **수정하지 않고** 그대로 넣었습니다. 인덱싱 결과(섹션 수 / chunk 수, chunk 1000자·overlap 150)는 다음과 같습니다.

| 파일 | 형식 | 섹션 | chunk |
|---|---|---|---|
| 01 FDA Clinical Trial Imaging Endpoint (31p) | PDF | 16 | 95 |
| 02 ICH E6(R3) (86p) | PDF | 98 | 268 |
| 03 EMA anticancer Rev.6 (43p) | PDF | 94 | 218 |
| 04 식약처 항암제 임상시험 가이드라인 (70p) | PDF | 103 | 137 |
| 05 식약처 ICH GCP 안내서 (158p) | PDF | 389 | 465 |
| 06 식약처 AI 폐암·폐결절 가이드라인 (21p) | PDF | 79 | 82 |
| 07 iRECIST how-to | JATS XML | 12 | 33 |
| 08 RECIL vs Lugano | JATS XML | 15 | 33 |
| 09 RANO 2.0 review | JATS XML | 20 | 70 |
| 10 MIDI 비식별화 보고서 (138p) | PDF | 88 | 461 |
| 11 DICOM PS3.15 Annex E | HTML | 9 (표 2개 포함) | 167 |
| 합계 | | | 2,029 |

인덱싱(bge-m3, 호스트 Ollama)은 약 2분 걸렸습니다. 출처 URL, 판, 수집일, 라이선스는 [corpus/SOURCES.md](corpus/SOURCES.md)에, 무결성 해시는 `corpus/SHA256SUMS`(`make corpus-verify`)에 있습니다.

- **FDA** *Clinical Trial Imaging Endpoint Process Standards* (2018): 미국 연방정부 저작물(public domain).
- **ICH E6(R3)** (2025): © ICH. ICH 법적 고지에 따라 저작권 표시와 함께 복제(로고 제외).
- **EMA** *Guideline on the clinical evaluation of anticancer medicinal products* Rev.6: © European Medicines Agency, 출처 표시 조건으로 복제 허용.
- **식품의약품안전처** 안내서 3종(항암제 임상시험 가이드라인, ICH GCP 민원인 안내서, AI 디지털의료기기 폐암·폐결절 임상시험계획서 가이드라인): 공공저작물(저작권법 제24조의2), 출처: 식품의약품안전처.
- **Europe PMC JATS 전문 3편**(iRECIST how-to, RECIL vs Lugano, RANO 2.0 review): 각 저자, CC BY 4.0.
- **MIDI 비식별화 보고서**(arXiv:2303.10473): 각 저자, CC BY 4.0.
- **DICOM PS3.15 Annex E** (2026d) HTML: © NEMA. NEMA 저작권 허락 범위의 무수정 발췌입니다. DICOM®은 NEMA의 등록상표입니다.

이 문서들은 검색·평가용 코퍼스로만 쓰며, 이 시스템의 답변은 원문을 대신하지 않습니다. `public-regulatory` 분류는 외부 LLM 가드레일에서 non-sensitive로 취급합니다(`ALLOW_EXTERNAL_LLM=true`이면 외부 Provider 사용 가능). 다만 이 저장소의 평가는 모두 로컬 Ollama로만 실행합니다.
