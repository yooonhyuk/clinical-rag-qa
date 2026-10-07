# 009. 같은 코퍼스·같은 설정인데 첫 public 기준선의 top-5가 재현되지 않음 (p68, p95, p98)

- 상태: 열림 (원인 미확정, 재현 조건 기록)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/10
- 발견: 2026-10-07, B7 평가를 위해 새 일회용 DB에 public 코퍼스를 다시 색인한 뒤
- 영향 범위: 평가 수치의 재현성(특히 이슈 006의 p68 사례), 운영 DB에서 다른 코퍼스가 섞일 때의 검색
- 관련 코드: `backend/app/services/vector_search_service.py`(HNSW + `WHERE corpus`), Alembic `0004`(HNSW 생성)

## 증상

첫 public 기준선(`eval/results/2026-10-07_public_bge-m3-vector-gemma4-e4b_8e014ae3/`, 커밋 `688b7e2`)과, 같은 코퍼스 해시(`8e014ae3`)·같은 모델·같은 설정으로 새 DB에 다시 색인한 실행(`..._public_bge-m3-vector-gemma4-e4b-b7_8e014ae3/`)의 top-5 파일 목록이 99문항 중 3문항에서 달랐습니다.

| 문항 | 첫 기준선 top-5 | 다시 색인한 뒤 top-5 |
|---|---|---|
| p68 (RANO Table 2) | 11 DICOM 표 ×5 | 09 RANO ×5 (정답) |
| p95 (거절 대상) | 04 ×5 | 04 ×3, 05, 02 |
| p98 (거절 대상) | 11 ×5 | 11 ×4, 10 |

그래서 hit@5가 94.9% → 96.2%가 됐습니다(p68). 이슈 006에서 "DICOM 표 허브" 사례로 든 p68은 이번 색인에서는 재현되지 않습니다.

## 확인한 것

- 새 일회용 DB 두 개(`127.0.0.1:55432`, `:55433`)에 각각 public을 색인했을 때 2,029 chunk의 embedding이 **비트 단위로 같았고**(최대 차이 0), 99문항의 exact 검색(인덱스 끔) top-5가 두 DB에서 같았습니다.
- 현재 DB에서 HNSW 검색과 exact 검색의 top-5 파일 목록이 99문항 모두 같았습니다.
- 따라서 지금의 색인·검색은 결정적입니다. 첫 기준선의 DB는 지웠기 때문에 그때의 차이는 다시 볼 수 없습니다.

- (추가, 2026-10-07) 세 번째 일회용 DB에 같은 코퍼스를 색인하자 HNSW top-5가 원래 실행과 3문항(p43, p95, p98) 달랐고, p43은 다섯 개가 모두 다른 문서였습니다. 같은 DB에서 HNSW 인덱스를 지우고 exact 검색으로 바꾸자 99문항 모두 원래 실행과 같았습니다(벡터, rerank 후보 30개 모두). 가설 1(근사 검색)을 지지합니다([분석 문서](../analysis/medgemma-vs-gemma4.md)).

## 원인 가설 (검증 못 함)

1. **HNSW 근사 검색 + 코퍼스 사후 필터**: `ORDER BY embedding <=> q LIMIT k`에 `WHERE d.corpus = 'public'`이 붙으면, pgvector 0.8은 기본값(`hnsw.iterative_scan=off`, `ef_search=40`)에서 인덱스가 돌려준 후보 40개를 필터링한 뒤 남은 것만 씁니다. 첫 기준선 DB에 다른 코퍼스 chunk가 더 많이 있었다면(색인 순서·이전 실행 잔여물) 후보가 줄어 다른 top-5가 나올 수 있습니다.
2. 첫 기준선 실행 이후 Ollama의 bge-m3 질문 embedding이 달라졌을 가능성. 같은 Ollama 0.24.0이고 오늘 두 번 색인한 결과가 같아 가능성은 낮습니다.

## 수정 방향

- 검색 세션에서 `SET hnsw.iterative_scan = relaxed_order`(pgvector 0.8)를 켜거나 `hnsw.ef_search`를 높여, 필터가 있어도 top-k를 채우게 한다. 지연을 측정해 결정한다.
- 평가 `config.json`에 DB의 코퍼스별 chunk 수, HNSW 파라미터(`m`, `ef_construction`, `ef_search`, `iterative_scan`)를 기록한다.
- 결과 비교는 같은 색인을 쓴 실행끼리만 한다(이번 B7 평가는 모두 같은 색인을 썼습니다).
