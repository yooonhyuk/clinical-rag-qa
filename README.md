# ClinicalRAG QA

**Local-first 의료문서 RAG + DICOM Tag Analyzer** — 포트폴리오 프로젝트 (MVP-1)

임상시험 문서(Markdown/TXT/텍스트 PDF)를 로컬에서 인덱싱하고, 질문에 **출처를 붙여** 답하며, 근거가 부족하면 **답변을 거절**합니다.
DICOM 파일은 픽셀을 읽지 않고 태그만 분석해 필수 태그 누락과 개인정보 가능 태그를 규칙 기반으로 검사합니다.
기본 구성은 외부 네트워크 없이 동작하며, 폐쇄망 설치용 오프라인 번들을 포함합니다.

> 모든 샘플 문서와 DICOM은 직접 만든 **가상 데이터**입니다(`TEST^PATIENT` 같은 가짜 값). 실제 환자 데이터나 회사 문서는 쓰지 않습니다.
> 이 시스템은 영상 판독·진단·치료 조언을 하지 않습니다.

기획서(v0.3) 기준 MVP-1 범위를 구현했습니다. 기술 스택은 Python 3.12, FastAPI(async), SQLAlchemy 2.0 async + asyncpg, Alembic, PostgreSQL 16 + pgvector, httpx.AsyncClient, Ollama(Gemma), PyMuPDF, pydicom, Streamlit, pytest, uv, Docker Compose입니다.

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
            D["/api/dicom/analyze"] --> DS["DicomService<br/>pydicom stop_before_pixels<br/>+ YAML 규칙"]
            P --> ES["EmbeddingService<br/>Semaphore(EMBED_CONCURRENCY)"]
            RAG --> ES
            RAG --> GEN{{"GenerationClient"}}
            DS -. 설명 생성 .-> GEN
        end
        ES -->|httpx.AsyncClient| OL["ollama<br/>nomic-embed-text · gemma"]
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
              dicom_service · dicom_rules · indexing_pipeline
              ollama_client · anthropic_client · llm_types · llm_guardrail
  models/     document chunk dicom_file index_job ask_log (SQLAlchemy 2.0)
  schemas/    Pydantic (camelCase 응답)
  prompts/    rag_prompt.txt dicom_summary_prompt.txt
  rules/      required_tags.yaml privacy_tags.yaml
backend/alembic/versions/  0001_initial_schema · 0002_ask_log_llm_usage
frontend/streamlit_app.py
eval/       questions.yaml (25문항) · eval_metrics.py · run_eval.py · reports/
tests/      unit/ (API 테스트 포함) · integration/ (PostgreSQL + pgvector)
offline-bundle/  build-bundle.sh · install.sh · verify-offline.sh
samples/    documents/ (가상 문서 6종 + .corpus.yaml) · dicom/ (합성 DICOM 3종)
scripts/    generate_sample_dicom.py · generate_sample_pdf.py
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
make up                   # api(8000), ui(8501), db(5432), ollama(11434)
make pull-models          # gemma4:e4b + nomic-embed-text (모델 이름은 LLM_MODEL=... 로 변경)
make index                # POST /api/index
open http://localhost:8501
```

- API 문서는 `http://localhost:8000/docs`, 상태 확인은 `GET /api/health`입니다(DB, pgvector, Ollama, 모델 존재 여부).
- Mac에서는 Docker 안의 Ollama가 GPU(Metal)를 쓰지 못해 느립니다. 개발할 때는 호스트 Ollama를 쓰는 편이 낫습니다(`.env`의 `OLLAMA_BASE_URL=http://host.docker.internal:11434`).

### 3) 오프라인(폐쇄망) 번들

인터넷이 되는 장비에서 번들을 만듭니다.

```bash
make bundle    # = offline-bundle/build-bundle.sh
# → offline-bundle/out/clinical-rag-qa-offline-0.1.0.tar.gz
#    images/  (docker save: api, ui, pgvector, ollama)
#    models/  (Ollama 모델 저장소 tarball)
#    wheels/  (개발/테스트용 Python wheel + requirements.txt)
#    samples/, docker-compose*.yml, install.sh, verify-offline.sh, SHA256SUMS
```

`PLATFORM`(기본 `linux/amd64`)과 `WHEEL_PLATFORM`으로 설치 대상 아키텍처를 고릅니다.

폐쇄망 장비에서는 다음과 같이 설치합니다.

```bash
tar xzf clinical-rag-qa-offline-0.1.0.tar.gz && cd clinical-rag-qa-offline-0.1.0
./install.sh          # 체크섬 검증 → docker load → 모델 복원 → compose up(internal) → alembic → health
./verify-offline.sh   # api 컨테이너에서 pypi/anthropic/ollama registry 접속이 막혔는지, ollama 내부 통신은 되는지 확인
```

`docker-compose.offline.yml`의 설정은 다음과 같습니다.

- db·ollama·api는 `internal: true` 네트워크에만 연결합니다. 외부로 나가는 경로가 없고 호스트 포트도 열지 않습니다.
- 외부 LLM Provider를 강제로 끕니다(`LLM_PROVIDER=ollama`, `ALLOW_EXTERNAL_LLM=false`).
- `pull_policy: never`로 설정해 이미지를 받거나 빌드하지 않습니다.

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
- **하이브리드 검색(기본값, `HYBRID_SEARCH=true`)**: pgvector cosine 순위와 pg_trgm `word_similarity(질문, chunk)` 순위를 Reciprocal Rank Fusion(k=60)으로 합칩니다. 첫 평가에서 nomic-embed-text가 **한글 단어를 전부 `[UNK]` 토큰 하나로** 바꾼다는 것을 확인했기 때문입니다(영어 WordPiece 어휘). 예를 들어 "업로드"와 "태그"의 embedding cosine이 1.0이고, 서로 다른 한국어 질문들이 같은 top-5를 받았습니다. 거절 임계값에 쓰는 `score`는 계속 cosine입니다. 확장은 Alembic `0003`에서 만들고, 문서 100개 이하 규모라 trigram 인덱스는 두지 않았습니다.
- 공식 Docker 이미지 하나로 폐쇄망에 그대로 옮길 수 있습니다. 스키마는 Alembic으로 코드에서 관리합니다.
- 중복 문서: `checksum`에 UNIQUE를 걸었기 때문에 중복 파일은 `documents`에 행을 만들 수 없습니다. 그래서 `SKIPPED_DUPLICATE` 결과는 `index_jobs.details`(JSONB, 기획서 스키마에 추가한 컬럼)에 파일별로 기록합니다. 이전에 `FAILED`였던 문서는 다시 인덱싱할 때 같은 행을 재사용해 재시도합니다.

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

`MIN_RELEVANCE_SCORE=0.45`는 측정 후에도 **바꾸지 않았습니다**. 25문항의 top-1 cosine은 답이 있는 질문이 0.614~0.749, 거절해야 하는 질문이 0.730~0.807로 겹칩니다(벡터 단독 검색 기준, 가장 높은 값이 거절 대상 q25). 어떤 임계값도 둘을 가르지 못하고, 0.62 이상으로 올리면 거절 대상은 그대로 통과하고 답이 있는 q07부터 잘립니다. 한국어 코퍼스에서 nomic-embed-text의 cosine은 근거 판단에 쓸 수 없으므로 NO_EVIDENCE 단계는 사실상 동작하지 않고, 거절은 3단계(모델)와 1단계(정규식)가 맡습니다. 다국어 embedding 모델로 바꾼 뒤 다시 측정해야 합니다.

### DICOM Tag Analyzer

- `pydicom.dcmread(path, stop_before_pixels=True)`로 픽셀은 읽지 않습니다. 테스트에서 이 인자가 실제로 넘어가는지 확인합니다.
- 필수 태그(공통, CT/MR 추가)와 개인정보 가능 태그는 `rules/*.yaml`에 정의합니다.
- 응답과 DB의 `tags`에는 개인정보 태그와 UID의 **값을 넣지 않고** `"exists"`만 넣습니다. LLM 프롬프트에도 값이 들어가지 않습니다.
- 설명은 로컬 Gemma가 만들고, Ollama 장애 시에는 결정적 템플릿으로 대체합니다. 응답에는 항상 "영상 판독 아님" 안내 문구를 붙입니다.

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
| 단위 | 텍스트 추출(MD 헤딩, CP949, PDF 페이지, 암호화/손상/스캔 PDF), chunker, 폴더 스캔, DICOM 규칙과 PHI 비노출, Ollama 재시도(respx), Semaphore 상한, 거절 정책, Anthropic SDK 오류 매핑, 가드레일, Provider 간 응답 동일성, 평가 지표 | pytest, respx, AsyncMock |
| API | `/api/ask`, `/api/retrieve`, `/api/index`, `/api/dicom/analyze`, `/api/health`, 경로 탈출 차단(403), LLM 장애 시 503 | httpx `ASGITransport` |
| 통합 | 인덱싱 파이프라인 → pgvector 저장 → 검색, 중복/실패/롤백, API로 인덱싱 후 질문하고 `ask_logs` 확인, embedding이 무너져도 pg_trgm 채널이 한국어 질문의 정답 chunk를 1위로 올리는지 | 실제 PostgreSQL 16 + pgvector |

Ollama와 Claude는 모든 테스트에서 가짜 클라이언트로 대체합니다(실제 API 호출 없음).
통합 테스트는 `TEST_DATABASE_URL`이 있으면 그 DB를, 없으면 testcontainers(`pgvector/pgvector:pg16`)를 쓰고, 둘 다 없으면 skip합니다.

**실행 결과 (2026-10-06, macOS arm64, Docker 실행 중)**

- `make test`: **91 passed, 0 skipped** (단위·API 87 + 통합 4). 통합 테스트는 testcontainers(`pgvector/pgvector:pg16`) 경로로 실행했습니다.
- 이전 기록(2026-10-05): Docker가 꺼져 있어 85 passed, 3 skipped. 그때 통합 3건은 `TEST_DATABASE_URL`(로컬 `pgserver`)로 따로 3 passed를 확인했습니다.

---

## 평가 결과

평가셋은 `eval/questions.yaml`의 25문항입니다. 문서에 답이 있는 질문이 19개(76%), 판독·진단·치료 요청이나 문서에 없는 내용이라 **거절해야 하는 질문**이 6개(24%)입니다.
hit@k와 False refusal은 답이 있는 19문항, Refusal correctness는 거절 대상 6문항, Citation correctness와 Keyword coverage는 실제로 답한(거절하지 않은) 문항 기준입니다.

**실행 환경 (2026-10-06)**: Apple M5, 메모리 32GB, macOS. 호스트 Ollama 0.24.0(`gemma4:e4b` + `nomic-embed-text`), Docker의 `pgvector/pgvector:0.8.0-pg16`. Provider는 ollama만 실행했습니다. top_k=5, chunk 1000/150, `MIN_RELEVANCE_SCORE=0.45`, temperature 0.1.

```bash
docker compose up -d db
(cd backend && DATABASE_URL=postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa uv run alembic upgrade head)
make seed
make eval EVAL_ARGS=--reindex      # 첫 실행: 6개 문서 → 28 chunk 인덱싱 후 평가
HYBRID_SEARCH=false make eval      # 벡터 단독(수정 전 동작) 재현
make eval                          # 하이브리드(기본값)
```

| 지표 | 벡터 단독 (수정 전) | 하이브리드 (pgvector + pg_trgm, RRF) |
|---|---|---|
| Retrieval hit@5 (파일 기준) | 63.2% (12/19) | **94.7%** (18/19) |
| Section hit@5 | 31.6% | 68.4% |
| Citation correctness | 85.7% (6/7) | 86.7% (13/15) |
| Keyword coverage | 85.7% | 83.3% / 90.0% |
| Refusal correctness | 100% (6/6) | 100% (6/6) |
| False refusal rate | 63.2% (12/19) | **21.1%** (4/19) |
| Retrieval p50 / p95 | 24 / 37 ms | 40~42 / 46~48 ms |
| Generation p50 / p95 | 2,783 / 6,596 ms | 4,014~4,156 / 7,011~7,021 ms |
| End-to-end p50 / p95 | 2,768 / 6,593 ms | 4,043~4,079 / 6,809~6,883 ms |
| 질문 수 / 오류 | 25 / 0 | 25 / 0 |

- 벡터 단독은 두 번 실행했고(`--reindex` 첫 실행, `HYBRID_SEARCH=false` 재실행) 검색·거절 지표가 같았습니다. 위 수치는 첫 실행입니다. 하이브리드도 두 번 실행했고, 범위로 적은 칸은 두 실행의 값입니다. 하이브리드에서 실행마다 달라진 지표는 Keyword coverage(83.3% → 90.0%)뿐이었습니다.
- 하이브리드 쪽 생성 시간이 긴 것은 실제로 답을 쓰는 문항이 많아졌기 때문입니다(거절 답변은 짧음).
- 원본 리포트는 `eval/reports/`에 생성됩니다(git에는 넣지 않음).
- anthropic Provider는 실행하지 않았습니다(API 키 없음, 수치 없음).

**남은 실패 사례 (하이브리드)**

- **q15 "헬프데스크 운영 시간"**: `operator-faq.txt`에 질문 문장이 그대로 있고 pg_trgm 점수도 1.0(1위)인데 top-5에 들지 못했습니다. 이 chunk는 벡터 순위가 후보 20개 밖이라 RRF 점수가 1/61뿐이고, 벡터 1위인 무관한 chunk가 lexical 중간 순위만 받아도 이깁니다. 무너진 벡터 채널과 같은 가중치로 합치는 RRF의 한계입니다. 25문항에 맞춘 가중치 조정은 하지 않았습니다.
- **q05 "최대 업로드 용량"**: 파일(`dicom-upload-guide.md`)은 맞혔지만 정답 섹션(Supported File Formats, pg_trgm 0.786로 1위)이 같은 이유로 top-5에서 빠져 모델이 거절했습니다. 파일 단위 hit@k가 섹션 누락을 가리는 사례입니다.
- **q09, q10**: 정답 섹션(De-identification Policy)을 검색했는데도 gemma4:e4b가 "확인할 수 없습니다"라고 답했습니다. 근거가 표(`| PatientBirthDate | 삭제 |`)와 긴 섹션에 있어 소형 모델이 놓친 것으로 보입니다.
- **q17 "SliceThickness 기준"**: 기대 출처는 프로토콜 PDF와 QA 체크리스트인데, 모델이 업로드 가이드의 권장 태그 섹션을 인용해 "5mm"이 빠진 답을 했습니다.

---

## 제한 사항

- **embedding 모델이 한국어를 지원하지 않음**: nomic-embed-text는 한글을 `[UNK]`로 처리합니다. 하이브리드 검색으로 보완했지만 근본 해결은 다국어 embedding 모델(예: bge-m3, 1024차원 → 새 마이그레이션 필요)입니다. 이번 평가 환경에서는 모델을 새로 받지 않았으므로 측정하지 않았습니다.
- **미실행 항목**: RAG 평가는 호스트에서 `db` 컨테이너와 호스트 Ollama로 실행했습니다. api/ui 이미지 빌드, 전체 `docker compose up`, 오프라인 번들 생성·설치, `verify-offline.sh`는 아직 실행하지 않았습니다.
- **폐쇄망 UI 포트**: Docker는 internal 네트워크에서 호스트 포트를 열지 못합니다. 그래서 ui만 `ui_edge` 브리지 네트워크에 추가로 연결했고, 이 때문에 ui 컨테이너는 이론상 외부로 나갈 수 있습니다(api·db·ollama는 불가). 완전히 차단하려면 호스트 방화벽이나 리버스 프록시를 함께 써야 합니다.
- **OUT_OF_SCOPE 판별**은 정규식 휴리스틱이라 표현이 바뀌면 놓치거나 잘못 거절할 수 있습니다. 그래서 2·3단계 거절과 시스템 프롬프트로 한 번 더 막습니다.
- **chunking**은 고정 크기(문자 수 기준)입니다. 표·목록 구조를 따로 처리하지 않습니다. 토큰 기준이나 표를 인식하는 chunking은 이후 버전에서 다룹니다.
- `/api/index`는 동기 실행입니다(요청이 인덱싱 완료까지 대기). 목표인 100개 이하 문서에서는 문제없지만, 규모가 커지면 작업 큐(arq 등)가 필요합니다.
- embedding 차원은 마이그레이션에 `VECTOR(768)`로 고정되어 있습니다. 모델을 바꾸면 새 마이그레이션이 필요합니다(차원이 다르면 `EMBEDDING_DIM_MISMATCH`로 실패합니다).
- anthropic 모드의 가드레일은 "표식이 붙은 폴더만 인덱싱한다"까지 보장합니다. 이전에 ollama 모드로 인덱싱해 DB에 이미 들어 있는 문서까지 검사하지는 않으므로, Provider를 바꿀 때는 DB를 새로 만드는 것을 권장합니다.
- 스캔 PDF(OCR), DOCX·Excel, 문서 기반 업로드 기준 비교, QC 시나리오 생성은 MVP-2 범위입니다.
