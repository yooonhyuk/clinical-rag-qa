# ClinicalRAG QA

**Local-first 의료문서 RAG + DICOM Tag Analyzer** — 포트폴리오 프로젝트 (MVP-1)

임상시험 문서(Markdown/TXT/텍스트 PDF)를 로컬에서 인덱싱하고, 질문에 **출처를 붙여** 답하며, 근거가 부족하면 **답변을 거절**합니다.
DICOM 파일은 픽셀을 읽지 않고 태그만 분석해, DICOM 표준 원문(PS3.3 / PS3.15, 2026d)에서 생성한 규칙으로 **표준 적합성(Layer 1)** 과 **비식별화(Layer 2)** 를 검사합니다.
기본 구성은 외부 네트워크 없이 동작하며, 폐쇄망 설치용 오프라인 번들을 포함합니다.

> 모든 샘플 문서와 DICOM은 직접 만든 **가상 데이터**입니다(`TEST^PATIENT` 같은 가짜 값). 실제 환자 데이터나 회사 문서는 쓰지 않습니다.
> 이 시스템은 영상 판독·진단·치료 조언을 하지 않습니다.

기획서(v0.4) 기준 MVP-1 범위를 구현했습니다. 기술 스택은 Python 3.12, FastAPI(async), SQLAlchemy 2.0 async + asyncpg, Alembic, PostgreSQL 16 + pgvector, httpx.AsyncClient, Ollama(Gemma, bge-m3 embedding), PyMuPDF, pydicom, Streamlit, pytest, uv, Docker Compose입니다.

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

인덱싱 흐름은 다음과 같습니다. 폴더 스캔(SHA-256) → 문서별 텍스트 추출(`asyncio.to_thread`) → 고정 크기 chunk(1000자 / overlap 150) → embedding(배치 gather + Semaphore) → **문서 단위 트랜잭션**으로 chunk 저장과 `INDEXED` 전환.

### 폴더 구조

```text
backend/app/
  main.py · config.py · db.py · container.py (composition root)
  api/        documents.py rag.py dicom.py health.py deps.py
  services/   document_loader · text_extractor · chunker · embedding_service
              vector_search_service · rag_service · prompt_builder
              embedding_schema · indexing_pipeline
              dicom_service · dicom_rules · dicom_safe(출력 allowlist)
              dicom_conformance(Layer 1) · dicom_deid(Layer 2) · dicom_findings
              ollama_client · anthropic_client · llm_types · llm_guardrail
  models/     document chunk dicom_file index_job ask_log (SQLAlchemy 2.0)
  schemas/    Pydantic (camelCase 응답)
  prompts/    rag_prompt.txt dicom_summary_prompt.txt
  rules/      standard/ps3.3_iod.yaml · standard/ps3.15_e1-1_deid.yaml (표준에서 생성)
              deid_policy.yaml (사이트 정책)
  cli/        dicom_scan.py (폴더 일괄 검사)
backend/alembic/versions/  0001_initial_schema · 0002_ask_log_llm_usage · 0003_pg_trgm
                           0004_embedding_model_tracking
frontend/streamlit_app.py · no_egress_entrypoint.py (폐쇄망 ui: default route 제거 후 권한 하강)
eval/       questions.yaml (25문항) · eval_metrics.py · run_eval.py · reports/
tests/      unit/ (API 테스트 포함) · integration/ (PostgreSQL + pgvector)
offline-bundle/  build-bundle.sh · install.sh · verify-offline.sh
samples/    documents/ (가상 문서 6종 + .corpus.yaml) · dicom/ (합성 DICOM 9종)
scripts/    generate_sample_dicom.py · generate_sample_pdf.py
            build_iod_rules.py · build_deid_rules.py · dicom_docbook.py (표준 → 규칙 YAML)
            diagnose_embedding.py (토크나이저/cosine 진단) · reset_embeddings.py
            export_ollama_models.py (번들용: 로컬 Ollama 저장소에서 모델 복사)
docs/       dicom-rules.md (DICOM 2계층 규칙 설계·출처·한계)
docs/issues/  001-korean-embedding-unk.md · 002-dicom-free-text-phi-to-llm.md
              003-offline-ui-egress.md · 004-compose-host-ollama-and-port-binding.md
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
make up && make pull-models && make seed
make eval EVAL_ARGS=--reindex                 # 인덱싱 후 25문항 평가 → eval/reports/<날짜>-ollama.md
make eval PROVIDERS="ollama anthropic"        # 두 Provider 나란히 비교 (아래 opt-in 조건 필요)
```

`make eval`은 호스트에서 실행되고, compose가 열어 둔 `localhost:5432`와 `localhost:11434`에 붙습니다. 접속 주소는 `EVAL_DATABASE_URL`, `EVAL_OLLAMA_URL`로 바꿀 수 있습니다.

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

1. **OUT_OF_SCOPE**: 판독·진단·치료·처방 요청(정규식 휴리스틱). 예: "이 CT에 폐결절이 있나요?"
2. **NO_EVIDENCE**: 검색 결과가 없거나 top-1 cosine score가 `MIN_RELEVANCE_SCORE`(기본 0.45)보다 낮을 때. 프롬프트에는 이 값 이상인 chunk만 넣습니다.
3. **MODEL_REFUSED**: 모델이 structured output으로 `insufficient_evidence=true`를 돌려줄 때, 인용 없이 "문서에서 확인할 수 없습니다"라고 답할 때, 또는 Provider가 요청을 거절할 때(`stop_reason=refusal`).

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
  2. `RAW_DOCS_PATH/.corpus.yaml`에 `classification: synthetic-sample` 또는 `non-sensitive`. `/api/index`로 다른 폴더를 인덱싱할 때도 그 폴더의 표식을 확인합니다.
  3. `ANTHROPIC_API_KEY`(환경변수로만 받고 커밋하지 않음)
- anthropic 모드에서도 DICOM에서 나온 정보는 외부로 보내지 않습니다(설명은 템플릿으로 생성). 오프라인 번들과 compose는 기본값이 ollama이고, offline override는 외부 Provider를 강제로 끕니다.

---

## 테스트

| 구분 | 내용 | 도구 |
|---|---|---|
| 단위 | embedding 모델별 차원·prefix 해석과 잘못된 차원 거부, health의 embedding 인덱스 판정, 텍스트 추출(MD 헤딩, CP949, PDF 페이지, 암호화/손상/스캔 PDF), chunker, 폴더 스캔, DICOM Layer 1(IOD 11종 결정, Type 1/2, Functional Group, UI/DA/TM, Defined Terms, PET SUV)·Layer 2(E.1-1 조치·조합 해석, 중첩 sequence, private, 선언·가명·픽셀 위험·날짜 옵션)·PHI 비노출(응답·DB·프롬프트·로그), 규칙 생성기 파서, 폴더 스캔 CLI, Ollama 재시도(respx), Semaphore 상한, 거절 정책, Anthropic SDK 오류 매핑, 가드레일, Provider 간 응답 동일성, 평가 지표, 오프라인 번들(모델 export, ui default route 제거·권한 하강 순서, compose 포트·네트워크 하드닝) | pytest, respx, AsyncMock |
| API | `/api/ask`, `/api/retrieve`, `/api/index`, `/api/dicom/analyze`, `/api/health`, 경로 탈출 차단(403), LLM 장애 시 503 | httpx `ASGITransport` |
| 통합 | 인덱싱 파이프라인 → pgvector 저장 → 검색, 중복/실패/롤백, API로 인덱싱 후 질문하고 `ask_logs` 확인, embedding이 무너져도 pg_trgm 채널이 한국어 질문의 정답 chunk를 1위로 올리는지, 다른 embedding 모델의 chunk 제외·health 불일치 보고·자동 재embedding, 0004 마이그레이션의 차원 변경(768↔1024)·벡터 삭제·HNSW 재생성·REINDEX_REQUIRED | 실제 PostgreSQL 16 + pgvector |

Ollama와 Claude는 모든 테스트에서 가짜 클라이언트로 대체합니다(실제 API 호출 없음).
통합 테스트는 `TEST_DATABASE_URL`이 있으면 그 DB를, 없으면 testcontainers(`pgvector/pgvector:pg16`)를 쓰고, 둘 다 없으면 skip합니다.

**실행 결과 (2026-10-06, macOS arm64, Docker 실행 중)**

- `make test`: **198 passed, 0 skipped** (단위·API 192 + 통합 6). 통합 테스트는 testcontainers(`pgvector/pgvector:pg16`) 경로로 실행했습니다.
- 오프라인 번들 단위 테스트(#4, #5) 추가 전: 188 passed (단위·API 182 + 통합 6).
- DICOM 규칙 재구성(#2, #3) 전: 107 passed (단위·API 101 + 통합 6).
- bge-m3 전환 전: 91 passed (단위·API 87 + 통합 4).
- 이전 기록(2026-10-05): Docker가 꺼져 있어 85 passed, 3 skipped. 그때 통합 3건은 `TEST_DATABASE_URL`(로컬 `pgserver`)로 따로 3 passed를 확인했습니다.

---

## 평가 결과

평가셋은 `eval/questions.yaml`의 25문항입니다. 문서에 답이 있는 질문이 19개(76%), 판독·진단·치료 요청이나 문서에 없는 내용이라 **거절해야 하는 질문**이 6개(24%)입니다.
hit@k와 False refusal은 답이 있는 19문항, Refusal correctness는 거절 대상 6문항, Citation correctness와 Keyword coverage는 실제로 답한(거절하지 않은) 문항 기준입니다.

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
- 원본 리포트는 `eval/reports/`에 생성됩니다(git에는 넣지 않음). 문항별 최대 cosine은 `*-questions.json`에 남습니다.
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
- **OUT_OF_SCOPE 판별**은 정규식 휴리스틱이라 표현이 바뀌면 놓치거나 잘못 거절할 수 있습니다. 그래서 2·3단계 거절과 시스템 프롬프트로 한 번 더 막습니다.
- **chunking**은 고정 크기(문자 수 기준)입니다. 표·목록 구조를 따로 처리하지 않습니다. 토큰 기준이나 표를 인식하는 chunking은 이후 버전에서 다룹니다.
- `/api/index`는 동기 실행입니다(요청이 인덱싱 완료까지 대기). 목표인 100개 이하 문서에서는 문제없지만, 규모가 커지면 작업 큐(arq 등)가 필요합니다.
- embedding 차원을 바꾸면 기존 벡터를 모두 지우고 재인덱싱해야 합니다(`make reset-embeddings` → `make index`). 그 사이에는 검색 결과가 비고, `/api/health`가 `embeddingIndex` 불일치로 `degraded`를 보고합니다. 설정한 차원과 모델이 실제로 내는 차원이 다르면 인덱싱은 `EMBEDDING_DIM_MISMATCH`로 실패합니다.
- anthropic 모드의 가드레일은 "표식이 붙은 폴더만 인덱싱한다"까지 보장합니다. 이전에 ollama 모드로 인덱싱해 DB에 이미 들어 있는 문서까지 검사하지는 않으므로, Provider를 바꿀 때는 DB를 새로 만드는 것을 권장합니다.
- **DICOM 규칙**: 파일 단위 검사입니다(series/study 일관성은 다음 단계). Type 1C/2C와 조건부 모듈은 평가하지 않고, 더미 치환·UID 치환·정제 여부는 파일 하나로 확인할 수 없어 참고로만 보고합니다. 픽셀은 읽지 않으므로 픽셀 내 식별정보는 위험 표시만 합니다. 합성 샘플로만 테스트했고 실제 공개 DICOM은 아직 돌리지 않았습니다. 자세한 내용은 [docs/dicom-rules.md](docs/dicom-rules.md#6-한계).
- 스캔 PDF(OCR), DOCX·Excel, 문서 기반 업로드 기준 비교(DICOM Layer 3), QC 시나리오 생성은 MVP-2 범위입니다.
