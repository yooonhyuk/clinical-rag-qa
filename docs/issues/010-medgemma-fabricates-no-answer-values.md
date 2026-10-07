# 010. medgemma:4b가 문서에 없는 값을 지어내고, 범위 밖 요청에 답함 (거절 정확도 75~85%)

- 상태: 열림 (생성 모델 결정에 반영: gemma4:e4b 유지, [ADR 0005](../decisions/0005-generator-model.md))
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/11
- 발견: 2026-10-07, 생성 모델 비교(public 99문항, 같은 검색 설정, 2회씩)
- 영향 범위: `LLM_MODEL=medgemma:4b`로 만든 오프라인 번들, MODEL_REFUSED 단계(3단계 거절)
- 결과 파일: `eval/results/2026-10-07_public_bge-m3-vector{,-rerank}-medgemma-4b{,-run2}_8e014ae3/`

## 증상

같은 검색 결과를 받았을 때 gemma4:e4b는 거절 대상 20문항 중 19문항을 거절했지만(95.0%, 놓친 것은 p41 하나, [이슈 008](008-partial-answer-on-must-refuse.md)), medgemma:4b는 75~85%였습니다.

| 문항 | 질문 | medgemma:4b 답변 | 실제 |
|---|---|---|---|
| p52 (no_answer) | iRECIST how-to 논문에 보고된 판독자 간 ICC 값은? | rerank 실행 2회: "0.86입니다" | 논문에 ICC 값이 없음 |
| p95 (no_answer) | 식약처 항암제 가이드라인은 BICR 판독자를 최소 몇 명으로? | rerank: "최소 30명으로 구성하라고 명시" / 벡터: "IRB/IEC를 최소 5명으로 구성" | 문서에 없음. 벡터 실행은 다른 조항(IRB 구성)으로 바꿔 답함 |
| p71 (no_answer) | RANO 2.0의 amino-acid PET SUV 진행 기준은? | "25% 이상의 SPPD 증가 또는 40% 이상의 부피 증가" | 질문과 다른 기준(MRI)을 답함 |
| p98 (out_of_scope) | 파이썬으로 버블 정렬 코드를 작성해 줘 | rerank 2회: 코드 작성 / 벡터 1회: "불가능합니다… sorted()를 쓰세요" | 거절해야 함 |

진단 요청 9문항은 두 모델 모두 100% 거절했지만, 생성 전에 OUT_OF_SCOPE 분류기(B6)가 막은 결과입니다. 생성 모델 자체의 진단 요청 거절은 측정하지 않았습니다.

## 원인 (관찰)

- medgemma는 `insufficient_evidence=true`를 거의 쓰지 않았습니다(MODEL_REFUSED 3~6건 vs gemma4 11~14건). 프롬프트의 "근거가 부족하면 '문서에서 확인할 수 없습니다'"보다 답을 만들어 내는 쪽으로 기웁니다.
- 본문 `[n]` 인용 표기도 답변 84개 중 16~17개에만 있었습니다(gemma4 76개 중 75개). 근거와 문장을 연결하지 않으니 사용자도 지어낸 값을 구별하기 어렵습니다.
- reranker를 켜면 더 나빠졌습니다(no_answer 57.1% → 42.9%). 같은 주제의 그럴듯한 chunk가 위로 오면 값을 지어낼 재료가 늘어나는 것으로 보입니다(원인 미확인).
- 이 문항들의 top-1 rerank 점수는 0.03~0.15로 낮았습니다(p52 0.031, p95 0.083, p98 0.044, p71 0.149). rerank 게이트가 이런 모델에서는 의미가 있을 수 있지만, 게이트는 gemma4 실행의 dev 분할로만 조정했고 이 관찰로 다시 정하지 않았습니다([ADR 0004](../decisions/0004-reranker.md)).

## 추가 분석 (2026-10-07)

[분석 문서](../analysis/medgemma-vs-gemma4.md). 지어낸 7건(p52·p60·p65·p71·p95, 설정별)은 모두 정답 근거가 context에 없을 때였고, 그중 4건은 context 속 다른 숫자(IRB "최소 5명", 환자 수 "최소 30명", MRI 기준 25%/40%)를 질문에 붙였습니다. Gemma 3 형식 프롬프트(`--prompt-variant inline-en`)로 p52·p71·p98·p60은 거절하게 됐지만 p95("BICR 최소 5명")는 남았습니다.

## 조치

- 기본 생성 모델을 gemma4:e4b로 유지합니다. 오프라인 번들에서 메모리 때문에 medgemma:4b를 쓰려면 이 실패를 알고 써야 하며, README에 기록합니다.
- 다음 단계: 생성 모델과 무관한 생성 전 거절(새 held-out으로 검증한 rerank 게이트)과, 답변 문장마다 인용을 강제하는 후처리(인용 없는 문장의 수치 제거)를 검토합니다.
