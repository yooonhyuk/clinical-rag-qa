# 001. nomic-embed-text가 한국어를 `[UNK]`로 처리해 벡터 검색이 무너짐

- 상태: 해결 (기본 embedding 모델을 bge-m3로 교체)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/1
- 발견: 2026-10-06, 첫 실제 평가(`make eval`, 25문항)
- 영향 범위: 한국어 질문의 벡터 검색, `MIN_RELEVANCE_SCORE` 기반 NO_EVIDENCE 거절
- 관련 코드: `backend/app/config.py`(`KNOWN_EMBEDDING_MODELS`), `backend/app/services/embedding_schema.py`, `backend/alembic/versions/0004_embedding_model_tracking.py`, `scripts/diagnose_embedding.py`, `scripts/reset_embeddings.py`

## 증상

- 서로 다른 한국어 질문이 거의 같은 top-5 chunk를 받았습니다. 벡터 단독 검색의 Retrieval hit@5가 63.2%(12/19), 답이 있는 질문을 거절한 비율(False refusal)이 63.2%(12/19)였습니다.
- top-1 cosine이 답이 있는 질문 0.614~0.749, 거절해야 하는 질문 0.730~0.807로 겹쳤습니다. 거절 대상 q25가 가장 높았습니다. 어떤 `MIN_RELEVANCE_SCORE`로도 둘을 나눌 수 없어서 NO_EVIDENCE 단계가 사실상 동작하지 않았습니다.

## 재현 방법

```bash
ollama pull nomic-embed-text && ollama pull bge-m3
uv run --project backend python scripts/diagnose_embedding.py nomic-embed-text bge-m3
```

`diagnose_embedding.py`는 로컬 Ollama 저장소(`~/.ollama/models`)에서 모델의 GGUF 파일을 열어 토크나이저 어휘를 세고, Ollama API로 서로 무관한 텍스트 쌍의 cosine을 계산합니다.

평가 지표 재현(벡터 단독, 수정 전 동작):

```bash
docker compose up -d db
(cd backend && DATABASE_URL=postgresql+asyncpg://clinical:clinical@localhost:5432/clinical_rag_qa uv run alembic upgrade head)
make seed
OLLAMA_EMBEDDING_MODEL=nomic-embed-text make reset-embeddings
OLLAMA_EMBEDDING_MODEL=nomic-embed-text HYBRID_SEARCH=false make eval EVAL_ARGS=--reindex
```

## 원인: 토크나이저에 한글이 없음

2026-10-06 실행 결과(Ollama 0.24.0, `scripts/diagnose_embedding.py`):

| | nomic-embed-text | bge-m3 |
|---|---|---|
| 토크나이저 | `bert` (WordPiece) | `t5` (SentencePiece, XLM-RoBERTa 어휘) |
| 어휘 크기 | 30,522 | 250,002 |
| 한글 음절이 들어간 토큰 수 | **0** | 5,373 (`의`, `을`, `이`, `에`, `를` …) |
| unknown 토큰 | id 100 `[UNK]` | id 3 `<unk>` |
| 차원 | 768 | 1024 |
| cos("업로드", "태그") | **1.0000** | 0.5830 |
| cos("헬프데스크 운영 시간은 언제인가요?", "이 CT에 폐결절이 있나요?") | **1.0000** | 0.4159 |
| cos("upload", "tag") (대조군) | 0.4708 | 0.5430 |

- nomic-embed-text의 어휘에는 한글 음절 토큰이 하나도 없습니다(자모 토큰 70개만 있음). WordPiece는 어휘로 쪼갤 수 없는 단어 전체를 `[UNK]` 하나로 바꾸므로, 한글이 섞인 단어는 모두 같은 토큰이 됩니다.
- 그래서 단어 수가 같은 한국어 문장은 같은 토큰 열(`[UNK] [UNK] [UNK] [UNK]`)이 되고 embedding도 같아집니다. 위 표에서 "헬프데스크 운영 시간" 질문과 "폐결절" 질문의 cosine이 정확히 1.0입니다. "CT에"처럼 영문이 붙은 단어도 한글이 섞여 있으면 `[UNK]`입니다.
- 영어 쌍(대조군)은 정상적으로 0.47이 나오므로 모델 자체의 문제가 아니라 어휘 문제입니다.
- 질문 embedding이 사실상 "단어 수"만 담게 되어, cosine 순위와 점수 모두 질문 내용과 무관해졌습니다. 거절 임계값을 조정할 수 없었던 이유도 같습니다.

## 임시 대응: 하이브리드 검색 (commit `4dfa5f7`)

pgvector cosine 순위와 pg_trgm `word_similarity(질문, chunk)` 순위를 Reciprocal Rank Fusion(k=60)으로 합쳤습니다. 한글 trigram은 토크나이저와 무관하게 동작하므로 hit@5가 63.2%에서 94.7%로, False refusal이 63.2%에서 21.1%로 개선됐습니다.
그러나 다음 문제는 남았습니다.

- 무너진 벡터 채널이 RRF에서 같은 가중치를 가져, pg_trgm 1위인 정답 chunk가 top-5에서 밀렸습니다(q15, q05).
- 거절 임계값에 쓰는 cosine은 여전히 의미가 없었습니다.

## 근본 해결: 다국어 embedding 모델 bge-m3

- 기본 모델을 `bge-m3`(1024차원, task prefix 없음)로 바꿨습니다. `KNOWN_EMBEDDING_MODELS`가 모델별 차원과 prefix를 정하고(`nomic-embed-text`는 768 + `search_query: `/`search_document: `), 그 외 모델은 `EMBEDDING_DIM`을 반드시 지정해야 합니다. 알려진 모델과 다른 차원을 지정하면 앱이 시작되지 않습니다.
- **embedding 모델 기록**: `chunks.embedding_model`(NOT NULL), `documents.embedding_model`, `index_jobs.embedding_model`을 추가했습니다(Alembic `0004`).
  - 검색은 설정된 모델의 chunk만 읽습니다. 다른 모델의 벡터와 cosine을 비교하지 않습니다.
  - 인덱싱 파이프라인은 다른 모델로 embedding된 문서를 중복으로 건너뛰지 않고 다시 embedding합니다.
  - `/api/health`의 `embeddingIndex`가 컬럼 차원, chunk에 섞인 모델, 재인덱싱 대기 문서 수를 보고하고, 어긋나면 `status=degraded`가 됩니다.
- **차원 변경 = 벡터 전체 삭제 + 재인덱싱**: 모델이 다른 벡터는 변환할 수 없습니다. `0004` 마이그레이션과 `make reset-embeddings`(같은 함수 `reset_embedding_column`)는 다음을 수행합니다.
  1. HNSW 인덱스 삭제
  2. 모든 chunk 삭제
  3. `chunks.embedding`을 `vector(<dim>)`으로 변경
  4. HNSW 인덱스 재생성
  5. 문서를 `FAILED / REINDEX_REQUIRED`로 표시

  이후 `/api/index`(또는 `make eval EVAL_ARGS=--reindex`)를 실행해야 검색이 다시 동작합니다. 차원이 이미 같으면 기존 chunk를 지우지 않고 `embedding_model='unknown'`으로 표시하며, health가 이를 보고하고 다음 인덱싱이 다시 embedding합니다.

실제 DB(이전 평가의 nomic 768차원 데이터 28 chunk)에 `alembic upgrade head`를 적용한 결과, 컬럼이 `vector(1024)`로 바뀌고 chunk 0개, 문서 6개가 `FAILED / REINDEX_REQUIRED`가 됐습니다. bge-m3로 설정한 API에서 nomic 768차원 인덱스를 보면 health는 다음과 같이 보고했습니다.

```json
"embeddingIndex": {"ok": false, "detail": "column is vector(768) but bge-m3 produces 1024-dim vectors -> make reset-embeddings + reindex; chunks embedded with nomic-embed-text (configured: bge-m3; they are excluded from search) -> reindex"}
```

## 전후 지표

2026-10-06, Apple M5 / 32GB, 호스트 Ollama 0.24.0(`gemma4:e4b`), Docker `pgvector/pgvector:0.8.0-pg16`, 문서 6개 → 28 chunk, top_k=5, chunk 1000/150, `MIN_RELEVANCE_SCORE=0.45`, temperature 0.1. 각 셀은 실제 실행 결과이며, bge-m3 두 셀은 두 번씩 실행했습니다(범위로 표기한 칸은 두 실행의 값, 나머지는 두 실행이 같았음).

| 지표 | nomic · 벡터 | nomic · 하이브리드 | **bge-m3 · 벡터** | bge-m3 · 하이브리드 |
|---|---|---|---|---|
| Retrieval hit@5 (파일) | 63.2% (12/19) | 94.7% (18/19) | **100% (19/19)** | 100% (19/19) |
| Section hit@5 | 31.6% | 68.4% | **100%** | 100% |
| Citation correctness | 85.7% (6/7) | 86.7% (13/15) | **94.7% (18/19)** | 89.5% (17/19) |
| Keyword coverage | 92.9% | 90.0% | **100%** | 100% |
| Refusal correctness | 100% (6/6) | 100% (6/6) | **100% (6/6)** | 100% (6/6) |
| False refusal rate | 63.2% (12/19) | 21.1% (4/19) | **0% (0/19)** | 0% (0/19) |
| Retrieval p50 / p95 (ms) | 26 / 35 | 43 / 78 | 78~81 / 92~207 | 94~96 / 103~104 |
| End-to-end p50 (ms) | 2,623 | 4,080 | 4,382~4,450 | 4,153~4,170 |
| 질문 수 / 오류 | 25 / 0 | 25 / 0 | 25 / 0 | 25 / 0 |

- nomic 두 셀은 이전 평가(README 기록)와 검색·거절 지표가 같았습니다. Keyword coverage만 LLM 출력에 따라 달라졌습니다(이전 85.7% → 이번 92.9%).
- bge-m3의 검색 지연이 늘어난 이유는 질문 embedding 모델이 커졌기 때문입니다(Ollama 모델 크기 1.2GB vs 274MB). 생성 시간과 비교하면 작습니다.
- nomic · 벡터의 생성 시간이 짧은 것은 12문항을 짧은 거절 답변으로 끝냈기 때문입니다.
- bge-m3에서 하이브리드는 검색 지표를 올리지 못했습니다. 오히려 q06에서 lexical 채널이 올린 무관한 chunk(`dicom-upload-guide.md`)를 모델이 함께 인용해 Citation이 한 문항 낮았습니다(두 실행 모두 같음).

### 권장 기본값: bge-m3 + 벡터 단독 (`HYBRID_SEARCH=false`)

bge-m3에서 하이브리드는 hit@5·Section hit·False refusal이 벡터 단독과 같고, Citation은 한 문항 낮으며, 검색 p50이 약 15ms 늘었습니다. 그래서 기본값을 끄고 옵션으로 남겼습니다. 한국어 어휘가 없는 embedding 모델을 써야 할 때 다시 켜면 됩니다. 차이가 한 문항이므로 강한 근거는 아닙니다.

### 거절 임계값(`MIN_RELEVANCE_SCORE`): 조정하지 않음

bge-m3 · 벡터 단독에서 retrieved chunk 중 최대 cosine 분포는 다음과 같습니다(`eval/reports/*-questions.json`의 `maxCosine`).

- 답이 있는 19문항: 0.555 ~ 0.753. 가장 낮은 문항은 q10 0.555, q15 0.605, q16 0.631, q07 0.642입니다.
- 거절해야 하는 6문항:
  - q24 0.428 → NO_EVIDENCE
  - q23 0.453 → 모델 거절
  - q20 0.483, q22 0.487, q21 0.541 → OUT_OF_SCOPE
  - q25 0.651 → 모델 거절

nomic 때보다 훨씬 잘 갈라지지만 **완전히 분리되지는 않습니다**. q25("DEMO-ONC-01 시험의 1차 유효성 평가변수 결과")는 프로토콜 문서와 주제가 같아 cosine이 높고, 답이 있는 q10·q15·q16보다 높습니다. q25를 빼면 0.453과 0.555 사이에 경계를 둘 수 있습니다. 하지만 근거는 다음처럼 부족합니다.

- 거절 대상이 6문항뿐이고, 그중 3문항은 이미 정규식(OUT_OF_SCOPE)이 처리합니다.
- 여백은 0.1 정도입니다.

25문항에 맞춘 값은 과적합 위험이 큽니다. 그래서 **기본값 0.45를 유지**했고, 별도의 "튜닝" 실행이나 수치도 만들지 않았습니다. 0.45는 bge-m3에서 답이 있는 모든 문항보다 낮고(최소 0.555), q24를 LLM 호출 없이 거절합니다. nomic 때와 달리 NO_EVIDENCE 단계가 실제로 동작하게 됐습니다.

## 남은 한계

- 평가셋이 작습니다(답이 있는 19 + 거절 6). 100%라는 숫자는 이 25문항에 대한 값일 뿐이고, 일반화 성능을 뜻하지 않습니다.
- q25처럼 주제는 같지만 답이 없는 질문은 cosine으로 거를 수 없습니다. 모델 거절(3단계)에 의존합니다.
- bge-m3는 모델 파일이 약 1.2GB입니다(nomic 274MB). 오프라인 번들이 커지고, 질문 embedding 지연이 50ms 정도 늘었습니다.
- bge-m3의 sparse·multi-vector 출력은 Ollama가 제공하지 않아 dense 벡터만 씁니다.
- 모델을 바꿀 때마다 전체 재인덱싱이 필요합니다. 무중단 전환(새 컬럼에 병행 인덱싱 후 교체)은 구현하지 않았습니다.
- api/ui 컨테이너 전체 compose와 오프라인 번들은 이번에도 실행하지 않았습니다. 평가는 호스트 Ollama와 `db` 컨테이너로만 했습니다.

## 교훈

- **embedding 모델은 토크나이저 어휘부터 확인합니다.** "다국어 지원" 표기나 영어 벤치마크 대신, 대상 언어 문자가 어휘에 있는지와 무관한 문장 쌍의 cosine이 1.0이 아닌지를 먼저 봅니다. 확인하는 데 1분이면 충분합니다(`scripts/diagnose_embedding.py`).
- **cosine 값의 분포를 먼저 봅니다.** 답이 있는 질문과 거절해야 하는 질문의 점수 범위가 겹치는 것이 이번 문제의 첫 신호였습니다. 평가 러너가 문항별 `maxCosine`을 남기게 했습니다.
- **임시 대응은 증상을 가립니다.** 하이브리드 검색으로 hit@5는 올랐지만 cosine 기반 거절은 그대로 망가져 있었습니다. 원인을 고친 뒤에는 임시 대응이 오히려 정밀도를 떨어뜨렸으므로, 수치를 보고 기본값에서 뺐습니다.
- **벡터에는 출처(모델)를 함께 저장합니다.** 모델이 다른 벡터를 섞으면 오류 없이 엉뚱한 결과만 나옵니다. 모델 이름을 기록해 두면 health 체크와 자동 재embedding을 할 수 있습니다.
