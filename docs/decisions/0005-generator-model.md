# ADR 0005. 생성 모델: gemma4:e4b 유지 (medgemma:4b는 채택하지 않음)

- 상태: 채택 (2026-10-07)
- 관련: [이슈 008](../issues/008-partial-answer-on-must-refuse.md), [이슈 010](../issues/010-medgemma-fabricates-no-answer-values.md), [ADR 0004](0004-reranker.md)
- 결과: `eval/results/2026-10-07_public_bge-m3-vector{,-rerank}-{gemma4-e4b,medgemma-4b}*_8e014ae3/`
- 원인 분석: [medgemma:4b는 왜 이 RAG에서 약하고, 무엇을 잘하는가](../analysis/medgemma-vs-gemma4.md) (실패 분류, 프롬프트 적합성·closed-book probe, 1차 출처)

## Context

생성 모델은 Ollama로 로컬에서 돌리고 오프라인 번들에 함께 실립니다. 후보는 호스트 Ollama에 이미 있던 두 모델입니다(다른 모델은 받지 않음, 27B 제외).

| | gemma4:e4b | medgemma:4b |
|---|---|---|
| Ollama 메타데이터 | family gemma4, 8.0B(effective 4B), Q4_K_M | family gemma3, 4.3B, Q4_K_M |
| Ollama 저장 크기 | 9.6GB | 3.3GB |
| 실행 중 크기(`ollama ps`) | 10.73GB | 4.5GB |

지난 오프라인 번들 검증(2026-10-06)에서는 Docker Desktop VM 메모리(7.7GB) 때문에 gemma4:e4b를 컨테이너에 올리지 못해 medgemma:4b로 검증했습니다. 그래서 "더 작은 의료 특화 모델로 바꿀지"를 같은 평가셋으로 측정해야 했습니다.

## Options

A. gemma4:e4b (현재 기본값), B. medgemma:4b. 각각 벡터 단독과 벡터 + reranker(ADR 0004, 게이트 0) 두 검색 설정에서 2회씩, 같은 99문항·같은 색인·temperature 0.1·부분 답변 정책 on으로 실행했습니다.

## Decision

**gemma4:e4b를 기본 생성 모델로 유지합니다.** medgemma:4b는 거절해야 할 질문에 값을 지어내고(이슈 010), 영어 질문에 영어로 답하며, 인용 표기를 거의 하지 않습니다. 라이선스도 재배포 조건이 더 무겁습니다(아래).

## Evidence (measured)

public 99문항(답 79 / 거절 20). 칸 안의 두 값은 1회 / 2회. 검색 지표(hit@5 등)는 같은 검색 설정이면 두 모델이 같습니다.

| 지표 | gemma4 · 벡터 | medgemma · 벡터 | **gemma4 · rerank** | medgemma · rerank |
|---|---|---|---|---|
| hit@5 / 섹션 hit | 96.2% / 87.3% | 96.2% / 87.3% | 94.9% / 88.6% | 94.9% / 88.6% |
| Keyword coverage | 91.8 / 93.1% | 87.2 / 87.2% | **94.7 / 96.0%** | 91.1 / 91.1% |
| Citation accuracy | 86.3 / 87.5% | 78.2 / 78.2% | **88.0 / 88.0%** | 84.8 / 82.3% |
| Citation location | 90.4 / 93.1% | 84.6 / 85.9% | 86.7 / 88.0% | 84.8 / 83.5% |
| **Refusal accuracy (20)** | 95.0 / 95.0% | 80.0 / 85.0% | **95.0 / 95.0%** | 75.0 / 75.0% |
| ㄴ diagnosis_request (9) | 100% | 100% | 100% | 100% |
| ㄴ no_answer (7) | 85.7% | 57.1% | 85.7% | 42.9% |
| ㄴ out_of_scope (4) | 100% | 75 / 100% (p98에 답함) | 100% | 75 / 75% (p98 버블 정렬 코드를 작성함) |
| False refusal (79) | 7.6 / 8.9% | 1.3 / 1.3% | 5.1 / 5.1% | 0 / 0% |
| 부분 답변 (답 있음) | 7.6 / 8.9% | 0 / 0% | 3.8 / 3.8% | 0 / 0% |
| 한국어로 답한 비율 (답변 전체) | 94.5 / 94.4% | 66.7 / 67.9% | 94.7 / 96.0% | 69.6 / 70.9% |
| ㄴ 영어 질문 → 한국어 답 | 86.4 / 90.9% | 26.9 / 26.9% | 95.8 / 95.8% | 25.9 / 25.9% |
| 본문에 `[n]` 인용 표기가 있는 답변 (rerank 실행) | - | - | 75/76, 75/76 | 17/84, 16/84 |
| Keyword coverage 한국어 / 영어 질문 | 94.1 / 86.4% | 92.3 / 76.9% | 98.0 / 87.5% | 94.2 / 85.2% |
| JSON schema-valid | 100% | 100% | 100% | 100% |
| 생성 p50 | 7.0 / 6.8 s | 5.7 / 5.7 s | 7.1 / 6.9 s | 5.9 / 6.0 s |
| 전체 p50 / p95 | 6.7 / 11.2 s, 6.6 / 11.5 s | 5.7 / 10.0 s, 5.7 / 9.2 s | 9.3 / 14.8 s, 9.4 / 13.9 s | 8.3 / 15.5 s, 8.3 / 15.4 s |
| Ollama 실행 크기 (`ollama ps`) | 10.73GB | 4.5GB | 10.73GB | 4.5GB |
| Ollama 프로세스 최대 RSS (3초 간격 샘플) | 10.8~11.0GB | 5.0~5.5GB | 10.8~11.0GB | 4.9~5.0GB |

- **diagnosis_request는 두 모델 모두 100%** 인데, 이 9문항은 생성 전에 OUT_OF_SCOPE 분류기(B6)가 거절하기 때문입니다. 생성 모델의 진단 요청 거절 능력은 이 평가로는 측정되지 않습니다.
- medgemma의 낮은 오거절(0~1.3%)은 거의 모든 질문에 답한 결과입니다. 거절 대상 no_answer 7문항 중 3~4문항에 거절 없이 답했고, 그중 일부는 문서에 없는 값을 지어냈습니다. rerank 실행: p52 "iRECIST 논문의 판독자 간 ICC 값" → "0.86입니다", p95 "식약처 가이드라인의 BICR 최소 판독자 수" → "최소 30명으로 구성하라고 명시"(둘 다 문서에 없음). 벡터 실행: p95 → "IRB/IEC를 최소 5명으로 구성"(다른 조항으로 바꿔 답함), p52 → "ICC 값은 없습니다"(내용은 맞지만 거절 형식이 아님). 같은 문항들에서 gemma4는 모두 거절했습니다(p41 제외). [이슈 010](../issues/010-medgemma-fabricates-no-answer-values.md).
- medgemma는 영어 질문의 74%에 영어로 답했습니다(프롬프트는 한국어 답변을 지시). 인용은 structured `cited_context_ids`로만 하고 본문 `[n]` 표기는 거의 없었습니다.
- 메모리는 medgemma가 6GB 이상 작고 생성 p50이 약 1.2초 빠릅니다.
- reranker를 켜면 medgemma의 거절 정확도가 더 떨어졌습니다(80~85% → 75%). 거절 대상 문항에 더 그럴듯한 근거가 들어가기 때문으로 보입니다(원인 미확인).

## License (1차 출처, 2026-10-07 확인)

- **Gemma 4 (gemma4:e4b)**: Apache License 2.0. Google 오픈소스 블로그(2026-04-02): "The release of Gemma 4 under the Apache 2.0 license"([링크](https://opensource.googleblog.com/2026/03/gemma-4-expanding-the-gemmaverse-with-apache-20.html)). 라이선스 페이지 [ai.google.dev/gemma/docs/gemma_4_license](https://ai.google.dev/gemma/docs/gemma_4_license)는 Apache License 2.0 원문이고, HF 모델 카드 `google/gemma-4-E4B-it`의 `license: apache-2.0`, 로컬 `ollama show gemma4:e4b`의 license도 Apache 2.0 원문입니다. 같은 페이지 탐색 영역에 Gemma Prohibited Use Policy 링크가 있으나 Apache 2.0 본문에 편입 조항은 없습니다(법률 검토는 하지 않음).
  - 오프라인 번들 재배포 시: Apache 2.0 §4에 따라 라이선스 사본 포함, NOTICE 파일이 있으면 그 내용 유지, 수정한 파일에 변경 표시. 모델 가중치를 바꾸지 않고 GGUF를 그대로 싣는 경우 라이선스 사본(`ollama show --license`)을 번들에 넣으면 됩니다.
- **MedGemma (medgemma:4b)**: Health AI Developer Foundations Terms of Use(최종 수정 2024-11-15, [developers.google.com/health-ai-developer-foundations/terms](https://developers.google.com/health-ai-developer-foundations/terms)). HF 모델 카드 `google/medgemma-4b-it`는 `license: other`(위 약관 링크, gated), `ollama show medgemma:4b`의 license도 이 약관입니다.
  - §3.1 재배포 조건(요약 인용): 사용 제한(§3.2)을 "an enforceable provision"으로 하위 계약에 포함, 모든 수령자에게 "a copy of this Agreement" 제공, "when applicable, seek Health Regulatory Authorization", 수정 파일 표시, NOTICE 파일에 "HAI-DEF is provided under and subject to the Health AI Developer Foundations Terms of Use" 문구.
  - §3.2: Prohibited Use Policy의 제한, "any use that could cause a Health Regulatory Authority to deem Google to be a 'manufacturer' of a medical device" 금지. Google은 위반이 의심되는 사용을 "restrict (remotely or otherwise)"할 수 있다고 적혀 있습니다. §1.1(a)는 Clinical Use를 "any use in diagnosis or treatment of patients (including as part of a research study)"로 정의합니다.
  - 지난 오프라인 번들 검증(medgemma:4b 포함)은 내부 검증용이었고 배포하지 않았습니다. 배포한다면 위 조건을 모두 갖춰야 합니다.

## Not measured

- gemma4의 더 작은 변형(e2b 등), medgemma 27B, 다른 계열 모델(받지 않음).
- CPU 전용 장비(오프라인 번들 대상 linux/amd64)에서의 두 모델 지연. 이전 번들 검증에서 CPU medgemma:4b 생성이 약 26초였다는 기록만 있습니다.
- 사람 또는 LLM 채점에 의한 답변 품질(키워드·인용 위치 지표만 있음).
- 프롬프트를 모델별로 조정한 경우는 벡터 설정에서만 측정했습니다([분석 문서](../analysis/medgemma-vs-gemma4.md)). Gemma 3 형식 프롬프트(`--prompt-variant inline-en`)로 medgemma의 거절 정확도는 90%, 본문 `[n]` 표기는 51/79로 좋아졌지만 keyword·citation accuracy는 그대로였고 p95는 계속 지어냈습니다. 결정은 바뀌지 않습니다.
- 생성 모델 자체의 진단 요청 거절(분류기를 끈 실행).

## Consequences

- 오프라인 번들 기본 모델은 gemma4:e4b입니다. 실행 크기가 약 10.7GB라 **번들 대상 장비(또는 Docker VM) 메모리는 12GB 이상**이 필요합니다(이전 검증에서 7.7GB VM은 올리지 못함). 메모리가 부족한 장비를 위한 대안 모델은 아직 측정한 것이 없습니다.
- medgemma:4b를 쓰려면 별도 측정 없이 대체하지 말고, 최소한 (1) 거절 대상 문항의 값 지어내기 재측정, (2) HAI-DEF 약관 재배포 조건(약관 사본·NOTICE·사용 제한 조항)을 번들에 반영해야 합니다.
- `build-bundle.sh`는 `LLM_MODEL`로 모델을 바꿀 수 있으므로 코드 변경은 없습니다. 번들에 라이선스 사본을 넣는 작업은 다음 단계로 남깁니다.
