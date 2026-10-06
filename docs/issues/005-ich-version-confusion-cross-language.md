# 005. ICH E6(R3) 질문이 식약처 ICH GCP 안내서(E6(R2) 국·영문 병기)로 검색됨 — 버전 혼동과 한국어 쏠림

- 상태: 미해결 (reranker로 시도했으나 더 나빠짐, 2026-10-07)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/6
- 발견: 2026-10-07, 공개 코퍼스 첫 평가(`eval/public_questions.yaml`, bge-m3 · 벡터 단독)
- 영향 범위: 같은 규정의 여러 판·번역본이 한 코퍼스에 있을 때의 검색과 인용
- 관련 코드: `backend/app/services/chunker.py`(chunk 머리말), `backend/app/services/vector_search_service.py`
- 결과 파일: `eval/results/2026-10-07_public_bge-m3-vector-gemma4-e4b_8e014ae3/questions.jsonl`

## 증상

ICH E6(R3)(`02_ich_e6r3_2025.pdf`)에 대한 7문항(p10~p16) 가운데 6문항에서 top-5의 다수를 식약처 ICH GCP 민원인 안내서(`05_mfds_ich_gcp_ko.pdf`)가 차지했습니다. 이 안내서는 **E6(R2)** 를 국문 번역과 영어 원문을 나란히 싣고 있습니다.

| 문항 | 질문 언어 | top-5 구성 (02 = E6(R3), 05 = 식약처 R2 안내서) | 결과 |
|---|---|---|---|
| p10 시험자가 계획서에서 벗어날 수 있는 경우 | ko | 05 ×5 | 검색 실패. R2 4.5.2를 "ICH E6(R3)에 따르면"으로 인용 |
| p11 기본기록 보관 기간 | en | 05 ×4, 02 ×1 | 답은 맞지만 두 문서를 함께 인용 |
| p12 모니터링 빈도의 근거 | ko | 05 ×5 | 검색 실패, 모델 거절 |
| p13 모니터링 수행자 | en | 05 ×3, 02 ×2 | 정답 |
| p14 중앙 모니터링 | en | 05 ×4, 02 ×1 | 두 문서 인용 |
| p15 조기 종료 시 시험자 의무 | ko | 05 ×4, 02 ×1 | 정답 |
| p16 IRB 최소 위원 수 | ko | 02 ×4, 05 ×1 | 두 문서 인용 |

p10은 잘못된 답이 사실처럼 나간 사례입니다. 모델은 R2 4.5.2의 "행정상 단순 변경(모니터·전화번호 변경)" 예외까지 E6(R3)의 내용이라고 답했습니다. E6(R3) 2.5.4에는 이 예외가 없습니다("deviate only where necessary to eliminate an immediate hazard(s)").

## 원인

1. **같은 조항이 두 판으로 들어 있음.** R2 안내서는 465 chunk, R3는 268 chunk입니다. 문장 수준에서 거의 같은 조항이 R2 쪽에 국문과 영문으로 두 번 있어서, 어느 언어로 물어도 R2 chunk가 더 많이 잡힙니다.
2. **chunk에 문서 정체성이 없음.** chunk 머리말은 섹션 경로(`[2. INVESTIGATOR > 2.5 Compliance with Protocol]`)뿐이고 문서 제목이나 판(R2/R3)이 없습니다. 질문의 "E6(R3)"라는 단서가 embedding에서 판을 구분하지 못합니다.
3. **한국어 질문은 한국어 문서로 쏠림.** 한국어 질문(p10, p12)은 top-5가 모두 한국어 안내서였습니다. 영어 질문은 R3 chunk가 1~2개 섞였습니다.
4. 하이브리드 검색(pg_trgm)은 이 쏠림을 더 키웠습니다. 하이브리드 실행에서는 p15도 검색 실패였고 cross_language 유형의 hit@5가 88.0% → 76.0%로 떨어졌습니다(`..._public_bge-m3-hybrid-...`).

## 재현

```bash
docker run -d --rm --name crqa-eval-db -e POSTGRES_USER=clinical -e POSTGRES_PASSWORD=clinical \
  -e POSTGRES_DB=clinical_rag_qa -p 127.0.0.1:55432:5432 pgvector/pgvector:0.8.0-pg16
(cd backend && DATABASE_URL=postgresql+asyncpg://clinical:clinical@localhost:55432/clinical_rag_qa uv run alembic upgrade head)
make eval EVAL_DATABASE_URL=postgresql+asyncpg://clinical:clinical@localhost:55432/clinical_rag_qa \
  CORPUS=public EVAL_ARGS="--reindex --hybrid off"
# questions.jsonl의 p10~p16에서 retrieved / probe 의 file 구성을 확인
```

## 수정 방향 (다음 단계)

- chunk 머리말에 문서 식별 정보(제목, 발행처, 판·연도)를 넣는다. 예: `[ICH E6(R3) 2025 · 2.5 Compliance with Protocol]`. `.corpus.yaml` 또는 `corpus/SOURCES.md`에서 문서별 메타데이터를 읽는다.
- 질문에 문서·판 이름이 있으면(E6(R3), Rev.6, 2026d 등) 해당 문서로 필터링하거나 가중치를 준다.
- top-k에 문서 다양성(MMR 또는 문서당 상한)을 둔다.
- reranker 비교(다음 단계)에서 판 구분이 되는지 이 7문항으로 확인한다.
- 답변에 인용 문서의 판을 표시해, 사용자가 R2 근거임을 알 수 있게 한다.

## reranker 시도 (2026-10-07, [ADR 0004](../decisions/0004-reranker.md))

같은 색인, gemma4:e4b, 각 2회(검색 결과는 두 실행이 같음). p10~p16 7문항 합계.

| | 벡터 | 벡터 + bge-reranker-v2-m3 |
|---|---|---|
| top-5의 R3 chunk / R2 chunk | 9 / 26 | 6 / 28 |
| 파일 hit / 섹션 hit | 5 / 5 | **3 / 3** |

- cross-encoder는 한국어 질문에 국문 R2 번역 chunk를 더 높게 매겼습니다. p13(영어 질문)과 p15가 hit → miss가 됐고, p13은 거절로 바뀌었습니다.
- chunk에 문서 판(R2/R3) 정보가 없다는 원인 2는 순위 모델로 해결되지 않습니다. 다음 단계는 그대로 "chunk 머리말에 문서 식별 정보 추가"와 "질문의 판 이름으로 필터/가중치"입니다.
