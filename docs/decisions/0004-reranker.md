# ADR 0004. cross-encoder reranker: bge-reranker-v2-m3를 선택 기능으로, 거절 게이트는 cosine 유지

- 상태: 채택 (2026-10-07)
- 관련: [이슈 005](../issues/005-ich-version-confusion-cross-language.md) (#6), [이슈 006](../issues/006-table-chunks-hubs-and-misses.md) (#7), [이슈 007](../issues/007-hedged-answers-counted-as-refusals.md) (#8)
- 관련 코드: `backend/app/services/reranker.py`, `RagService._retrieve_with` / `_evidence`, `eval/tune_gate.py`
- 결과: `eval/results/2026-10-07_public_bge-m3-vector{,-rerank}-*`, `eval/results/2026-10-07_gate-tuning_bge-reranker-v2-m3/`

## Context

공개 코퍼스(B5)에서 bi-encoder(bge-m3) top-5만으로는 세 가지가 남았습니다. 표 행 chunk가 무관한 질문의 top-5를 채우고(#7), 작은 표가 검색되지 않으며(#7), 같은 조항의 다른 판이 섞입니다(#6). 또 거절 임계값(cosine 0.45)은 "같은 주제지만 답이 없는" 질문을 거르지 못합니다. B7의 목표는 질문과 chunk를 함께 읽는 cross-encoder로 순위를 다시 매기고, 그 점수를 답변 가능성 게이트로 쓸 수 있는지 측정하는 것이었습니다.

## Options

| 옵션 | 설명 |
|---|---|
| A. reranker 없음 (기존) | bge-m3 cosine top-5 |
| B. bge-reranker-v2-m3, cosine top-30 → rerank → top-5, 게이트 = rerank 점수 | 기획 원안 |
| C. B와 같지만 게이트는 cosine 유지 (rerank 게이트 0) | 순위만 바꿈 |
| D. 다른 reranker(bge-reranker-v2-gemma, LLM rerank 등) | 측정하지 않음. 이번 작업에서 다른 모델은 받지 않기로 함 |

## Decision

- **C를 선택 기능으로 넣습니다**: `RERANKER=bge-reranker-v2-m3`, `RERANK_CANDIDATES=30`, `RERANK_MIN_SCORE=0`(rerank 게이트 없음, cosine 게이트 0.45 유지). 기본값은 `RERANKER=none`입니다.
- torch·transformers는 선택 extra(`uv sync --project backend --extra rerank`)로 두고 기본 api 이미지에는 넣지 않습니다. 모델은 런타임에 받지 않습니다(`local_files_only=True`). HF 캐시 또는 `RERANKER_MODEL=<폴더>`에 미리 있어야 하고, 없으면 시작할 때 `RerankerUnavailableError`로 실패합니다.
- rerank 점수 게이트(B)는 채택하지 않았습니다. 이유는 아래 "게이트 조정"에 있습니다.

## Evidence (measured)

### 설정

- 모델: `BAAI/bge-reranker-v2-m3`, revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, `model.safetensors` 2,271,071,852 bytes(sha256 `d9e3e081…dd305847`), Apache-2.0. `~/.cache/huggingface/hub`에 한 번 받음(약 30초).
- 의존성(2026-10-07 PyPI): torch 2.14.1 wheel macOS arm64 127.3MB / manylinux x86_64 554.6MB(PyPI 기본 빌드는 CUDA 의존성 nvidia-*·triton이 따라옴), transformers 5.18.0 12.6MB, tokenizers 0.23.2 3.1MB, safetensors 0.8.0 0.5MB. 설치 후 venv: torch 528MB, transformers 53MB.
- 장치: Apple MPS(fp32). 질문 1개 × 후보 30개 단독 측정(Ollama 유휴): 짧은 텍스트(약 160토큰) MPS 1.06~1.23초 / CPU 2.33~2.35초, 512토큰으로 잘리는 텍스트 MPS 3.02~3.10초. 모델 로드 MPS 14.9초(첫 로드) / 2.9초(캐시 후), CPU 1.8초. MPS 할당 2.29GB(driver 3.26GB). eval 프로세스 최대 RSS 883~888MB(MPS 할당은 RSS에 다 잡히지 않음).
- 실제 평가(Ollama가 같은 GPU에서 생성하는 상태): **검색 p50 112ms → 2,669~2,723ms**, 전체 p50 6.6~6.7초 → 9.3~9.4초.

### public 99문항, gemma4:e4b, 부분 답변 정책 on, 각 2회

| 지표 | 벡터 (1회 / 2회) | 벡터 + rerank (1회 / 2회) |
|---|---|---|
| hit@5 (파일) | 96.2% / 96.2% | 94.9% / 94.9% |
| 섹션/페이지 hit@5 | 87.3% / 87.3% | **88.6% / 88.6%** |
| Citation accuracy | 86.3% / 87.5% | **88.0% / 88.0%** |
| Keyword coverage | 91.8% / 93.1% | **94.7% / 96.0%** |
| Refusal accuracy | 95.0% / 95.0% | 95.0% / 95.0% |
| False refusal | 7.6% / 8.9% | **5.1% / 5.1%** |
| 부분 답변(답 있음) | 7.6% / 8.9% | 3.8% / 3.8% |
| 같은 실행을 MVP-1 정책으로 채점한 오거절 | 15.2% / 17.7% | 8.9% / 8.9% |
| table_lookup 섹션 hit / 오거절 | 81.8% / 18.2% | 90.9% / 9.1% |
| cross_language 오거절 | 8.0% / 12.0% | 0% / 0% |
| 전체 p50 / p95 | 6.7 / 11.2 s, 6.6 / 11.5 s | 9.3 / 14.8 s, 9.4 / 13.9 s |

- 검색 결과(순위)는 두 실행이 같았습니다(같은 색인). 차이는 생성 쪽 변동입니다.
- reranker가 바꾼 문항(1회차 기준): 좋아진 것 p40(파일 miss → hit, 오거절 → 답변), p55·p72(섹션 hit), p59(RECIL Table 1 섹션 hit, 오거절 → 답변). 나빠진 것 p13(ICH E6(R3) hit → miss, 답변 → 거절), p15(R3 hit → miss).

### #7 (표 chunk 허브)

| | 벡터 | 벡터 + rerank |
|---|---|---|
| DICOM 표 문서가 아닌 질문의 top-5에 들어온 DICOM 표 chunk | 9개 / 5문항 (p40, p72, p74, 거절 대상 p83, p98) | 12개 / 4문항 (모두 거절 대상: p92, p96, p98, p99) |
| 답이 있는 질문에 들어온 DICOM 표 chunk | 4개 / 3문항 | **0개** |
| p59 (RECIL Table 1) | 섹션 miss, 거절 | **섹션 hit, 답변** |
| p65 (RANO Table 3) | 섹션 miss, 거절 | 섹션 miss, 거절 |
| p68 (RANO Table 2) | hit, 답변 | hit, 답변 |

답이 있는 질문에서는 허브가 사라졌지만, 무관한 질문(평양냉면·버블 정렬·월드컵)에는 여전히 DICOM 표 chunk가 들어옵니다. 이 질문들은 OUT_OF_SCOPE/모델 거절로 거절되므로 결과에는 영향이 없습니다. p65는 그대로입니다. p68은 이전 기록(2026-10-07 첫 실행)에서 DICOM 표 5개였지만 이번 색인에서는 벡터 단독도 정답 문서를 찾았습니다(같은 코퍼스를 다시 색인한 결과가 다름, [이슈 009](../issues/009-retrieval-differs-across-reindex.md)).

### #6 (ICH E6 R3/R2 혼동, p10~p16)

| | 벡터 | 벡터 + rerank |
|---|---|---|
| top-5의 R3 chunk / R2 chunk (7문항 합계) | 9 / 26 | 6 / 28 |
| 파일 hit / 섹션 hit | 5 / 5 | 3 / 3 |

reranker는 #6을 **더 나쁘게** 했습니다. 한국어 질문에 대해 국문 R2 번역 chunk를 더 높게 매깁니다. 판(R2/R3) 정보가 chunk에 없다는 원인(이슈 005)은 순위 모델로 해결되지 않습니다.

### 게이트 조정 (`eval/tune_gate.py`, `eval/results/2026-10-07_gate-tuning_bge-reranker-v2-m3/`)

- 게이트를 끈 실행(toy 25 + public 99)에서 문항별 top-1 rerank 점수를 기록하고, 임계값별 결과를 다시 계산했습니다. 게이트는 생성 전에 문항을 빼기만 하므로 이 재계산은 정확합니다.
- 분할(점수를 보기 전에 정함): **dev** = toy 25문항 전부 + public 문항을 유형별로 id 정렬했을 때 짝수 번째(52문항) = 77문항, **test(held-out)** = public 홀수 번째 47문항.
- 사전에 정한 목적함수(v1: 거절 정확도 − 오거절률, 동률이면 낮은 값)는 **0**을 골랐습니다. dev의 거절 대상 17문항은 OUT_OF_SCOPE와 모델 거절로 이미 모두 거절되어, 게이트가 더할 것이 없었습니다.
- dev 점수만 보고 만든 v2(게이트 단독 재현율 − 오거절률)는 0.56을 골랐습니다(toy q25 0.53 하나를 잡는 대신 dev 오거절 1개 추가). held-out에서 v2는 거절 정확도 88.9% → 88.9%(변화 없음), 오거절 7.9% → 15.8%로 나빴습니다. held-out을 본 뒤 규칙을 다시 바꾸는 것은 test 튜닝이므로 하지 않았고, v1 결과(0)를 채택했습니다.
- dev에서 답이 있는 문항의 최저 top-1 rerank 점수는 0.206(p80), 게이트에 닿는(OUT_OF_SCOPE가 아닌) 거절 대상 8문항의 점수는 0.0001~0.101과 q25 0.531이었습니다. held-out에서 부분 답변으로 나간 거절 대상 p41은 0.941이라 어떤 게이트로도 막을 수 없습니다([이슈 008](../issues/008-partial-answer-on-must-refuse.md)).

## Not measured

- rerank 점수 게이트를 따로 검증할 새 held-out 셋(0.11~0.20 구간이 dev에서 오거절 없이 게이트에 닿는 거절 대상 7/8을 생성 전에 거르는 것은 관찰만 함).
- 후보 수(`RERANK_CANDIDATES`) 10/20/50 비교, fp16·int8, CPU 전용 장비(오프라인 번들 대상 linux/amd64)에서의 전체 평가 지연.
- reranker를 Docker 이미지(api)에 넣었을 때의 이미지 크기와 오프라인 번들 경로.
- 하이브리드 + rerank 조합, 문서 다양성(MMR·문서당 상한)과의 조합.
- Ollama와 동시에 실행될 때의 MPS 메모리 최대치(단독 측정 2.29GB만 있음).

## Consequences

- 켜면 답변 품질 지표(오거절 −2.5~3.8%p, Keyword +2.9%p 이상, 섹션 hit +1.3%p)가 좋아지지만 질문당 약 2.6초가 늘고, 모델 2.3GB와 torch가 필요합니다. ICH 판 혼동(#6)은 나빠집니다.
- 기본값은 꺼 둡니다. 폐쇄망 번들에 넣으려면 모델 폴더와 `rerank` extra wheel(linux에서는 CPU 전용 torch 빌드 권장)을 함께 실어야 하며, 그 경로는 아직 만들지 않았습니다.
- 거절 게이트는 cosine 0.45 그대로입니다. rerank 점수는 응답 `sources[].rerankScore`와 `ask_logs.sources`에 기록되어, 나중에 새 held-out으로 게이트를 다시 정할 수 있습니다.
