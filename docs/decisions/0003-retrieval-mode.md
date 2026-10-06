# ADR 0003. 검색 방식: 벡터 단독(pgvector) 기본, 하이브리드(pg_trgm + RRF)는 옵션

- 상태: 채택 (2026-10-06, public 코퍼스로 2026-10-07 재확인)
- 관련: [이슈 001](../issues/001-korean-embedding-unk.md), [이슈 005](../issues/005-ich-version-confusion-cross-language.md), commit `4dfa5f7`
- 관련 코드: `backend/app/services/vector_search_service.py`, `HYBRID_SEARCH`, `RRF_K`

## Context

하이브리드 검색(pgvector cosine 순위 + pg_trgm `word_similarity` 순위를 Reciprocal Rank Fusion k=60으로 합침)은 nomic-embed-text가 한국어를 `[UNK]`로 처리하던 시기의 임시 대응으로 들어왔습니다. embedding을 bge-m3로 바꾼 뒤([ADR 0002](0002-embedding-model.md)) 기본값으로 계속 둘지 정해야 했습니다.

## Options

| 옵션 | 설명 |
|---|---|
| A. 벡터 단독 | HNSW(cosine) top-k. 가장 단순하고 빠름 |
| B. 하이브리드 | 벡터 top-max(4k,20) + trigram top-max(4k,20)를 RRF로 합침. trigram 인덱스는 두지 않음(문서 100개 이하 가정) |
| C. 벡터 + cross-encoder rerank | [ADR 0004](0004-reranker.md)에서 따로 결정 |

## Decision

**기본값은 벡터 단독(`HYBRID_SEARCH=false`)** 입니다. 하이브리드는 한국어 어휘가 없는 embedding 모델을 써야 할 때를 위한 옵션으로 남깁니다. 거절 임계값(`MIN_RELEVANCE_SCORE`)에 쓰는 점수는 두 방식 모두 cosine입니다.

## Evidence (measured)

toy 25문항, bge-m3, gemma4:e4b (2026-10-06, 두 번씩 실행):

| 지표 | 벡터 | 하이브리드 |
|---|---|---|
| hit@5 / Section hit | 100% / 100% | 100% / 100% |
| Citation correctness | 94.7% | 89.5% (q06: lexical 채널이 올린 무관 chunk를 함께 인용) |
| Retrieval p50 | 78~81 ms | 94~96 ms |

public 99문항(답 79 / 거절 20), bge-m3, gemma4:e4b (2026-10-07, `eval/results/2026-10-07_public_bge-m3-{vector,hybrid}-gemma4-e4b_8e014ae3/`):

| 지표 | 벡터 | 하이브리드 |
|---|---|---|
| hit@5 (파일) | **94.9%** (75/79) | 92.4% (73/79) |
| 섹션/페이지 hit@5 | **86.1%** | 81.0% |
| cross_language hit@5 | **88.0%** | 76.0% |
| False refusal | **15.2%** | 25.3% |
| Refusal accuracy | 100% | 100% |
| Retrieval p50 / p95 | **111 / 168 ms** | 458 / 622 ms |

- 하이브리드는 한국어 질문을 한국어 문서(식약처 ICH GCP 안내서, E6(R2))로 더 끌어당겨 ICH E6(R3) 질문의 검색을 더 나쁘게 만들었습니다([이슈 005](../issues/005-ich-version-confusion-cross-language.md)).
- trigram 계산에 인덱스가 없어 검색 p50이 4배가 됐습니다.
- 벡터 단독은 같은 설정으로 두 번 실행해 검색 지표가 같았습니다. 하이브리드는 한 번만 실행했습니다.

## Not measured

- trigram GIN 인덱스를 둔 하이브리드의 지연.
- RRF 가중치(채널별 가중치, k 값) 조정.
- BM25(한국어 형태소 분석 포함) 기반 lexical 채널.
- 하이브리드 + reranker 조합.

## Consequences

- 기본 검색은 SQL 한 번(HNSW)으로 끝나고 p50이 약 0.1초입니다.
- 정확한 용어 일치(태그 번호, 조항 번호)는 embedding에만 의존합니다. 이 약점은 reranker로 보완합니다([ADR 0004](0004-reranker.md)).
- 하이브리드 코드와 통합 테스트(pg_trgm 채널이 무너진 embedding에서도 정답을 1위로 올리는지)는 유지합니다.
