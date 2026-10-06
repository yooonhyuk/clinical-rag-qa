# 006. 표 chunk 문제: DICOM Table E.1-1 행 chunk가 무관한 질문의 top-5를 차지하고, 작은 표(RANO·RECIL)는 검색되지 않음

- 상태: 일부 개선 (선택 기능인 reranker로 답이 있는 질문의 허브 제거·p59 해결, p65 미해결, 2026-10-07)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/7
- 발견: 2026-10-07, 공개 코퍼스 첫 평가(bge-m3 · 벡터 단독 / 하이브리드)
- 영향 범위: 표 조회(table_lookup) 문항, 표가 많은 문서가 섞인 코퍼스 전체의 검색
- 관련 코드: `backend/app/services/table_rows.py`, `html_extractor.py`, `jats_extractor.py`, `chunker.py`
- 결과 파일: `eval/results/2026-10-07_public_bge-m3-vector-gemma4-e4b_8e014ae3/questions.jsonl`

## 증상

**(a) DICOM 표 행 chunk가 허브가 됨.** PS3.15 Table E.1-1은 행 600여 개가 `Attribute Name: …; Tag: (gggg,eeee); …; Basic Prof.: X` 형태로 들어가, Annex E 문서의 167 chunk(코퍼스 2,029 chunk의 8.2%) 대부분이 이런 행 chunk입니다. 서로 거의 같은 모양이라, 형식이 비슷한 다른 질문에서도 top-5를 채웁니다(벡터 단독).

| 문항 | 질문 | top-5 중 DICOM 표 chunk |
|---|---|---|
| p68 | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에서 3D T1의 슬라이스 두께 | 5 / 5 (정답 문서 0) |
| p98 | 파이썬으로 버블 정렬 코드를 작성해 줘 (범위 밖) | 5 / 5 |
| p72 | MIDI 보고서가 권고하는 DICOM 비식별화 기준 프로파일 | 2 / 5 |
| p40, p74 | AI 폐결절 프로토콜의 판독자 수 / MIDI 범위 밖 항목 | 1 / 5 |

**(b) 작은 표는 검색되지 않음.** 질문에 표 번호가 들어 있어도 해당 표 chunk가 top-5에 들어오지 않았습니다.

| 문항 | 정답 위치 | top-5 | 결과 |
|---|---|---|---|
| p59 | RECIL vs Lugano Table 1 (환자 특성) | 같은 문서의 본문·그림 설명 | 모델 거절 |
| p65 | RANO 2.0 Table 3 (반응 범주, 3D PD 기준) | 같은 문서의 본문 | 모델 거절 |
| p68 | RANO 2.0 Table 2 (BTIP) | DICOM 표 5개 | 모델 거절 |

반면 DICOM 표의 개별 행 조회(p76~p82, 7문항)는 벡터 단독에서 모두 정확했습니다. 행마다 열 이름이 붙어 있어 "태그 + 조치"가 한 chunk 안에 함께 남기 때문입니다.

표 조회 유형 전체(11문항)는 hit@5 90.9%, 섹션/페이지 hit 72.7%, 오거절 27.3%로 유형 중 가장 나빴습니다.

## 원인

1. 행을 `헤더: 값; …`으로 펼치면 표 하나가 비슷한 문장 수백 개가 됩니다. bge-m3 dense 벡터에서 이 chunk들이 서로 가깝고, 코드·숫자가 많은 질문과도 가까워 허브처럼 동작합니다.
2. 작은 표 chunk는 캡션 한 줄과 `Category: 3D; CR: No lesion; PR: More than 65% reduction …` 같은 행으로만 되어 있습니다. 서술형 질문("3D 부피 변화가 얼마면 PD인가")과 embedding이 잘 맞지 않고, 같은 내용을 서술한 본문 chunk가 더 높게 나옵니다. 본문에는 표의 숫자가 없어 모델이 거절합니다.
3. 표가 두 chunk 이상으로 나뉘면 두 번째 chunk부터는 캡션이 없습니다(섹션 경로에만 `Table 3`).

## 수정 방향 (다음 단계)

- 표 chunk마다 캡션과 열 이름 요약을 반복해 넣고, 표가 무엇을 다루는지 한 문장 설명을 붙인다.
- 큰 참조표(DICOM Table E.1-1)는 일반 검색 색인에서 빼고 구조화 조회(태그 → 조치 SQL 테이블)로 제공하거나, 여러 행을 묶은 큰 chunk로 줄인다.
- top-k에 문서·섹션 다양성(문서당 상한, MMR)을 둔다.
- 질문에 "Table N"이 있으면 해당 캡션 chunk를 우선한다.
- reranker 비교(다음 단계)에서 p59/p65/p68과 허브 현상이 줄어드는지 확인한다.

## 재측정 (2026-10-07, B7 reranker, [ADR 0004](../decisions/0004-reranker.md))

같은 색인, gemma4:e4b, 각 2회(두 실행의 검색 결과는 같음).

| | 벡터 | 벡터 + bge-reranker-v2-m3 |
|---|---|---|
| 답이 있는 질문 top-5의 DICOM 표 chunk | 4개 / 3문항 (p40, p72, p74) | **0개** |
| 거절 대상 질문 top-5의 DICOM 표 chunk | 5개 / 2문항 (p83, p98) | 12개 / 4문항 (p92, p96, p98, p99) |
| p59 (RECIL Table 1) | 섹션 miss, 거절 | **섹션 hit, 답변** |
| p65 (RANO Table 3) | 섹션 miss, 거절 | 섹션 miss, 거절 |
| table_lookup 섹션 hit / 오거절 | 81.8% / 18.2% | 90.9% / 9.1% |

- 무관한 질문(평양냉면, 버블 정렬, 월드컵)에는 여전히 DICOM 표 chunk가 top-5를 채웁니다. 이 질문들은 거절되므로 결과에는 영향이 없지만 허브 현상 자체는 남아 있습니다.
- p68은 이번 색인에서는 벡터 단독도 정답 문서(RANO)를 찾았습니다. 첫 실행의 "DICOM 표 5개"는 재현되지 않았습니다([이슈 009](009-retrieval-differs-across-reindex.md)).
- reranker는 기본값이 꺼져 있고(지연 +2.6초, torch·모델 2.3GB), 표 chunk 구조(캡션 반복, 큰 참조표 분리)는 바꾸지 않았으므로 이슈는 열어 둡니다.
