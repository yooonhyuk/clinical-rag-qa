# 012. chunk에 시험 식별자가 없어 다른 시험의 chunk가 섞이고, 엉뚱한 시험 문서로 답함

- 상태: 열림
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/13
- 발견: 2026-10-09, 실제 프로토콜 코퍼스(14개 시험의 프로토콜·SAP 26개 + 원문 5개) 평가
- 영향 범위: 여러 시험 문서를 한 코퍼스에 넣는 모든 사용(UI의 private 코퍼스), 검색·인용·답변
- 관련: [이슈 005](005-ich-version-confusion-cross-language.md)(문서 판 정보가 chunk에 없음)
- 결과 파일: `eval/results/2026-10-09_private-protocols_*/diagnostics.json` (집계만)

## 증상

- 답 있는 64문항의 top-5 chunk 중 **48.8%가 질문한 시험이 아닌 다른 시험**의 문서에서 왔습니다(같은 시험의 프로토콜↔SAP는 같은 시험으로 셈, `eval/retrieval_diagnostics.py`).
- 파일 hit@5(검색 단계만, OUT_OF_SCOPE로 막힌 문항 포함)는 79.7%로 공개 코퍼스(96.2%)보다 16.5%p 낮습니다.
- 생성 모델은 다른 시험의 chunk만 받고도 **질문한 시험의 답처럼** 씁니다. 예: 호지킨 림프종 시험의 mPFS 사건 정의를 물었는데, 같은 질환의 다른 시험(PET 적응형 2상) SAP의 정의를 인용해 답했고, 미만성 거대 B세포 림프종 시험의 1차 평가변수를 물었는데 흑색종 시험의 "RECIST 기반 ORR by BICR"로 답했습니다. 둘 다 출처는 붙어 있지만 출처 파일명이 다른 NCT 번호입니다.
- Citation accuracy(인용 파일 ⊆ 정답 파일)가 50%로 공개 코퍼스(86~88%)보다 크게 낮습니다. 일부는 같은 시험의 SAP를 함께 인용한 경우(지표가 엄격함)이고, 일부는 다른 시험 인용입니다.

- 검색 단계만 비교하면 cross-encoder reranker(exact top-30 → top-5)가 파일 hit@5를 85.9%, 섹션 hit를 71.9%(벡터 45.3%)로 올렸습니다. 질문의 시험 이름을 읽는 단계가 있으면 일부 회복되지만, chunk 자체에 시험 정보가 없는 문제는 그대로입니다.

## 원인

- 스폰서 문서는 시험을 **약칭(acronym)으로 거의 부르지 않습니다.** 추출 텍스트에서 시험 약칭이 나오는 줄 수: ELARA 0, ECHELON-1 0, DESTINY-Breast06 2, GeoMETry-III 2, CONDOR 2, CABINET 1. NCT 번호도 문서 26개 중 13개에는 0~2줄뿐입니다. 사용자는 약칭으로 묻고, 문서는 스폰서 과제 번호(예: D9670C00001)나 "the study"로 씁니다.
- chunk 머리말은 섹션 경로(`[8.1 Efficacy Assessments > 8.1.1 ...]`)뿐이라, "1.1 Synopsis"·"8.1.1 Tumor Imaging"처럼 **모든 프로토콜에 같은 이름으로 있는 섹션**의 chunk가 서로 구별되지 않습니다. 질문 속 시험 이름은 검색에 기여하지 못하고, 주제(영상 주기·BICR)만 맞는 chunk가 시험과 무관하게 올라옵니다.
- 이슈 005(ICH 판 혼동)와 같은 구조입니다. 문서 단위 메타데이터가 chunk에 없으면 cross-encoder reranker도 구별할 정보가 없습니다.

## 수정 방향 (이번에는 구현·재측정하지 않음 — 평가셋을 본 뒤라 별도 held-out으로 확인 필요)

1. 문서 메타데이터: `.corpus.yaml` 또는 manifest에 파일별 `trial: {nct, acronym, title, doc_type: protocol|sap}`를 두고, chunk 머리말에 `[NCT04494425 · <약칭> · Protocol > 8.1.1 ...]`처럼 넣어 embedding에 포함합니다.
2. 질문에 NCT 번호·약칭이 있으면 검색을 그 시험 문서로 제한하는 필터(코퍼스 필터와 같은 방식)를 둡니다. 없으면 UI에서 시험을 고르게 합니다.
3. 생성 프롬프트에 각 context의 시험 식별자를 표시하고, 질문한 시험과 다른 시험의 근거만 있으면 거절하도록 합니다.
4. 측정: 새 질문(이 평가셋과 다른 시험·다른 섹션)으로 "다른 시험 chunk 비율", 파일 hit@5, 엉뚱한 시험 인용률을 전후 비교합니다.
