# 008. 부분 답변 정책을 켜자 거절 대상 문항(p41)이 "부분 답변"으로 나감 — 거절 정확도 100% → 95%

- 상태: 열림 (원인 분석 완료, 정책은 유지하고 수치로 공개)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/9
- 발견: 2026-10-07, #8(이슈 007) 수정 후 첫 public 평가
- 영향 범위: `PARTIAL_ANSWERS=true`(기본값)일 때 must-refuse 문항의 Refusal accuracy
- 관련 코드: `backend/app/services/rag_service.py`(`_generate`의 partial 판정), `eval/eval_metrics.py`(`must_refuse_partial`)
- 결과 파일: `eval/results/2026-10-07_public_bge-m3-vector-gemma4-e4b-b7_8e014ae3/`, `..._public_bge-m3-vector-rerank-nogate-gemma4-e4b_8e014ae3/`

## 증상

이슈 007(#8)의 수정으로 "`insufficient_evidence=true`지만 유효한 인용이 있는 답변"을 거절 대신 caveat를 붙인 부분 답변으로 돌려주게 했습니다. 그 결과 답이 있는 질문의 오거절은 15.2% → 7.6%(벡터 단독)로 줄었지만, 거절 대상 20문항 중 1문항(p41, `no_answer`)이 부분 답변으로 나가 Refusal accuracy가 100% → 95.0%가 됐습니다. 벡터 단독과 벡터+reranker 두 설정 모두 같은 문항입니다.

| 문항 | 질문 | 모델 답변 (요약) |
|---|---|---|
| p41 | 식약처 AI 폐암·폐결절 임상시험 가이드라인 예시에서 요구하는 CT slice 간격은 정확히 몇 mm 이하인가요? | "구체적인 수치(mm 이하)는 확인할 수 없습니다. 다만, … 'OOmm 이하의 CT slice 간격'을 충족해야 한다고 언급되어 있습니다 [1]." (06 문서 8.1절 인용) |

## 원인

1. 원문(식약처 작성예시) 자체가 수치 자리를 `OOmm`로 비워 둔 **템플릿 문장**입니다. 모델은 "수치는 없다"고 정확히 말하고, 템플릿 문장을 근거로 인용했습니다. 내용상으로는 틀린 답이 아닙니다.
2. 부분 답변 판정은 "insufficient_evidence=true + 유효한 인용 + 거절 문장만이 아님"이라는 형식 조건뿐이라, "질문의 핵심(수치)이 없다"는 경우와 "질문의 일부만 근거가 있다"는 경우를 구분하지 못합니다.
3. reranker 게이트로도 막을 수 없습니다. p41의 top-1 rerank 점수는 0.941로, 답이 있는 문항 대부분보다 높습니다(같은 절이 실제로 질문 주제를 다루기 때문).

## 판단

- 평가에서는 **엄격하게 실패로 셉니다**(거절 대상인데 답했음). 정답 라벨을 바꾸지 않았습니다.
- 제품 동작은 유지합니다. 사용자에게 가는 응답은 `partial=true`와 caveat("문서에서 질문의 일부에 대한 근거만 확인됩니다…")가 붙고, 본문도 수치가 없다고 말합니다. 같은 평가에서 이 정책이 답이 있는 질문 6개를 살렸습니다(15.2% → 7.6%).
- MVP-1 정책(부분 답변도 거절)으로 같은 실행을 다시 채점한 값(`legacy_refusal_correctness`)은 100%입니다. README와 ADR에 두 값을 함께 적습니다.

## 수정 방향 (다음 단계)

- 응답 스키마에 `answer_status: full | partial | none`을 추가해, "질문의 핵심 값이 문서에 없다"를 모델이 `none`으로 표시하게 한다(프롬프트 변경 → 생성 모델별 재측정 필요).
- must-refuse 문항 중 "같은 주제, 값만 없음" 유형을 더 늘려(지금 7문항) 부분 답변 정책의 위험을 별도 지표로 본다.
