# ADR 0002. embedding 모델: nomic-embed-text → bge-m3

- 상태: 채택 (2026-10-06)
- 관련: [이슈 001](../issues/001-korean-embedding-unk.md) (GitHub #1), commit `1c7cacc`, `c44e7d2`
- 관련 코드: `backend/app/config.py`(`KNOWN_EMBEDDING_MODELS`), `backend/app/services/embedding_schema.py`, Alembic `0004`, `scripts/diagnose_embedding.py`

## Context

MVP-1은 Ollama의 `nomic-embed-text`(768차원)로 chunk와 질문을 embedding했습니다. 질문의 대부분(toy 25문항 전부, public 99문항 중 66%)이 한국어이고, 문서는 한국어·영어가 섞여 있습니다. 첫 실제 평가(toy, 2026-10-06)에서 벡터 단독 검색의 hit@5가 63.2%, 오거절이 63.2%였습니다. 원인을 찾기 전까지는 "소형 생성 모델이 표를 놓친다"는 가설도 있었습니다.

## Options

| 옵션 | 장점 | 단점 |
|---|---|---|
| A. nomic-embed-text 유지 + 하이브리드(pg_trgm) | 모델 274MB, 이미 동작 | 한국어 벡터가 무너진 상태를 가림, cosine 거절 임계값이 무의미 |
| B. bge-m3 (Ollama, 1024차원) | 다국어 XLM-RoBERTa 어휘(250k, 한글 음절 토큰 5,373개), Ollama에서 바로 실행 | 모델 1.2GB, 질문 embedding 지연 증가, 차원 변경 → 전체 재인덱싱 |
| C. 다른 다국어 모델(e5, gte 등) | - | Ollama 공식 배포·오프라인 번들 경로를 따로 만들어야 함. 측정하지 않음 |

## Decision

기본 embedding 모델을 **bge-m3**로 바꿉니다. 모델·차원·prefix는 설정(`OLLAMA_EMBEDDING_MODEL`, `EMBEDDING_DIM`)으로 바꿀 수 있고, 모든 chunk·문서·인덱싱 작업에 `embedding_model`을 기록합니다. 검색은 설정된 모델의 chunk만 읽습니다.

## Evidence (measured)

토크나이저 진단(`scripts/diagnose_embedding.py`, Ollama 0.24.0, 2026-10-06):

| | nomic-embed-text | bge-m3 |
|---|---|---|
| 어휘 크기 | 30,522 | 250,002 |
| 한글 음절이 들어간 토큰 | **0** | 5,373 |
| cos("업로드", "태그") | **1.0000** | 0.5830 |
| cos("헬프데스크 운영 시간은 언제인가요?", "이 CT에 폐결절이 있나요?") | **1.0000** | 0.4159 |
| cos("upload", "tag") (대조군) | 0.4708 | 0.5430 |

toy 25문항(답 19 / 거절 6), gemma4:e4b, top_k=5, `MIN_RELEVANCE_SCORE=0.45` ([이슈 001](../issues/001-korean-embedding-unk.md) "전후 지표"):

| 지표 | nomic · 벡터 | nomic · 하이브리드 | **bge-m3 · 벡터** | bge-m3 · 하이브리드 |
|---|---|---|---|---|
| hit@5 (파일) | 63.2% | 94.7% | **100%** | 100% |
| Section hit@5 | 31.6% | 68.4% | **100%** | 100% |
| False refusal | 63.2% | 21.1% | **0%** | 0% |
| Refusal correctness | 100% | 100% | **100%** | 100% |
| Retrieval p50 | 26 ms | 43 ms | 78~81 ms | 94~96 ms |

- bge-m3에서 답이 있는 질문의 최대 cosine은 0.555~0.753, 거절 대상은 0.428~0.651로 nomic(0.614~0.749 vs 0.730~0.807)보다 잘 갈라졌습니다. 그래서 NO_EVIDENCE(cosine 0.45) 단계가 처음으로 실제로 동작했습니다(q24).
- public 99문항(2026-10-07, bge-m3 · 벡터)에서는 hit@5 94.9%, 섹션 hit 86.1%였습니다. nomic으로는 public을 실행하지 않았습니다.

## Not measured

- nomic-embed-text의 public 코퍼스 성능(실행하지 않음).
- bge-m3 외 다국어 embedding 모델(e5, gte, Qwen3-Embedding 등).
- bge-m3의 sparse·multi-vector(ColBERT) 출력: Ollama는 dense 벡터만 제공합니다.
- 인덱싱 처리량의 정밀 비교(public 2,029 chunk 인덱싱이 약 2분이라는 관찰만 있음).

## Consequences

- 오프라인 번들에 embedding 모델 1.2GB가 들어갑니다(nomic 274MB).
- 모델이나 차원을 바꾸면 벡터를 모두 지우고 재인덱싱해야 합니다(`make reset-embeddings` → `make index`). 그동안 검색 결과가 비고 `/api/health`가 `degraded`를 보고합니다.
- 하이브리드는 이 결정 이후 이득이 없어 기본값에서 뺐습니다([ADR 0003](0003-retrieval-mode.md)).
- 교훈: embedding 모델을 고를 때 대상 언어 문자가 어휘에 있는지, 무관한 문장 쌍의 cosine이 1.0이 아닌지부터 확인합니다.
