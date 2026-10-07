# medgemma:4b는 왜 이 RAG에서 약하고, 무엇을 잘하는가

- 작성: 2026-10-07. 관련: [ADR 0005](../decisions/0005-generator-model.md), [이슈 010](../issues/010-medgemma-fabricates-no-answer-values.md) (GitHub #11)
- 기존 결과: `eval/results/2026-10-07_public_bge-m3-vector{,-rerank}-{gemma4-e4b,medgemma-4b}*_8e014ae3/`
- 이번에 추가한 결과: `eval/results/2026-10-07_public_bge-m3-vector-{medgemma-4b,gemma4-e4b}-inline-en*_8e014ae3/`, `eval/results/2026-10-07_model-probes/`
- 실행 환경: Apple M5 / 32GB, 호스트 Ollama 0.24.0, 일회용 `pgvector/pgvector:0.8.0-pg16` DB(익명 볼륨). 새로 받은 모델·데이터셋·이미지는 없습니다.

## 요약

1. **이 과제에서 medgemma가 진 이유는 의학 지식이 아니라 근거 사용 방식입니다.** 같은 검색 결과에서 medgemma는 거절 대상에 답하고(no_answer 7문항 중 4문항만 거절, gemma4 6), 본문 `[n]` 표기를 거의 하지 않으며(답변 82개 중 15개, gemma4 74개 중 72개), context 다섯 개 중 네 개 이상을 한꺼번에 인용하고(20/82, gemma4 2/74), 원문을 길게 그대로 옮겼습니다(60자 이상 그대로 복사 19/82, gemma4 3/74).
2. **지어낸 값 7건은 모두 정답 근거가 context에 없을 때 나왔습니다.** 그중 4건은 context 안에 있던 *다른 맥락의 숫자*를 질문에 갖다 붙였고(예: 환자 수 "최소 30명"을 BICR 판독자 수로), 3건은 context에 없는 숫자를 만들었습니다(ICC "0.86", 재구성 "2 iterations / 16 subsets"). 정답 근거가 context에 있는데 모델이 사전 지식으로 덮어쓴 사례는 찾지 못했습니다(숫자 대조 기준 0건).
3. **프롬프트를 Gemma 3 방식으로 바꾸면 격차의 일부가 줄었습니다.** 지시문을 user turn에 영어로 넣고 예시(인용 표기, 거절)를 붙이자 medgemma의 거절 정확도 80/85% → 90/90%, `[n]` 표기 15/82 → 51/79, 과다 인용 20 → 8로 좋아졌습니다. Keyword(87%)와 citation accuracy(77~78%)는 그대로였고, p95("BICR 최소 5명")는 계속 지어냈습니다.
4. **closed-book 의학 지식 문항(자작 22개, 검정력 낮음)에서도 gemma4:e4b가 앞섰습니다.** 두 선택지 순서에서 모두 맞힌 문항이 gemma4 17개, medgemma 11개였습니다. medgemma의 지식 우위는 모델 카드가 비교한 *같은 크기의 Gemma 3 4B* 대비이며, 더 크고 더 새로운 Gemma 4 E4B 대비 우위는 이 작은 probe에서 보이지 않았습니다.
5. medgemma가 맞는 선택일 수 있는 곳은 1차 출처가 뒷받침하는 범위입니다. 학습한 영상 modality(흉부 X선, 피부, 안저, 병리)의 영상 과제, 의료 하위 과제에 fine-tuning할 기반 모델, 메모리가 부족한 환경(실행 4.5GB vs 10.7GB)입니다. 앞의 두 가지는 이 저장소에서 측정하지 않았습니다.

## 설정과 교란 요인

| | gemma4:e4b | medgemma:4b |
|---|---|---|
| `ollama show` | architecture gemma4, 8.0B, Q4_K_M, completion/vision/tools/thinking, Apache-2.0 | architecture gemma3, 4.3B, Q4_K_M, completion/vision, HAI-DEF 약관 |
| 세대 | Gemma 4. HF 카드: "4.5B effective (8B with embeddings)", "Native System Prompt Support", "Out-of-the-box support for 35+ languages" | Gemma 3 기반. Gemma 3 문서: "the `system` role or a system turn is not supported" |
| 컨텍스트 | 128K | 128K |
| Ollama 템플릿 | 렌더러 내장(`{{ .Prompt }}`) | `system`을 첫 user turn 앞에 붙임 (`printf "%s\n%s" $.System .Content`) |

- **크기·세대가 맞지 않습니다.** 총 파라미터가 약 2배이고 세대가 다릅니다. 아래 차이를 "의료 특화 vs 범용"으로만 읽으면 안 됩니다. 크기를 맞춘 비교(Gemma 3 4B, gemma4 e2b)는 받지 않아 하지 못했습니다.
- **프롬프트는 gemma4에서 만들었습니다.** `rag_prompt.txt`(한국어, 한국어로 답하라고 지시)는 gemma4로 조정했습니다. medgemma에서도 system 지시가 실제로 들어가는지 확인했습니다. `system`을 넣으면 prompt 토큰이 15 → 31로 늘고, "끝에 BANANA를 붙여라"는 따랐지만 같은 문장의 "한국어로만 답하라"는 따르지 않았습니다.
- **같은 검색 결과인지 확인했습니다.** 새 일회용 DB에 다시 색인한 뒤 HNSW 검색은 p43·p95·p98 세 문항의 top-5가 원래 실행과 달랐습니다([이슈 009](../issues/009-retrieval-differs-across-reindex.md)와 같은 현상). 이 DB에서만 HNSW 인덱스를 지우고 exact 검색으로 바꾸자 99문항 모두 원래 실행과 같았습니다(벡터, rerank 모두). 아래 probe 실행과 context 대조는 모두 이 exact 검색 결과를 씁니다.
- 양자화(Q4_K_M)는 두 모델이 같지만 4B급 모델이 더 크게 영향을 받을 수 있습니다(측정 안 함).

## medgemma가 진 곳 (기존 결과, 같은 검색, 생성기만 다름)

벡터 1회차 쌍(gemma4 `-b7` vs medgemma)과 rerank 1회차 쌍(gemma4 `-rerank-nogate` vs medgemma `-rerank`)의 문항별 비교입니다. 2회차도 거의 같았습니다(괄호).

| 범주 | 벡터 | rerank | 비고 |
|---|---|---|---|
| 거절 대상에 답함 (gemma4는 거절) | 3 (2): p52, p95, p98 | 4 (4): p52, p71, p95, p98 | p41은 두 모델 모두 실패(이슈 008) |
| 값을 지어냄: context에 없는 숫자 | 1: p60 | 2: p52, p60 | 아래 표 |
| 값을 지어냄: context 속 다른 맥락의 숫자 | 2: p95, p65 | 2: p95, p71 | 아래 표 |
| 본문 `[n]` 표기 있는 답변 | 15/82 (10/81) | 17/84 (16/84) | gemma4 72/74, 75/76 |
| 5개 중 4개 이상 인용 (과다 인용) | 20/82 (24/81) | 32/84 | gemma4 2/74, 2/76 |
| 60자 이상 원문 그대로 복사 | 19/82 | 16/84 | gemma4 3/74, 3/76 |
| 영어 질문에 영어로 답함 (프롬프트는 한국어 지시) | 19/26 | 20/28 | gemma4 3/22, 1/24 |
| 한국어 질문에 영어 위주로 답함 | 7/56 | 4/56 | gemma4 1/52. 대부분 영어 원문 표를 복사한 경우 |
| Citation 파일 틀림 (둘 다 답한 문항) | 5 | 3 | p29 등 5개 전부 인용 |
| Keyword 손실 (둘 다 답한 문항) | 2: p76, p79 | 3 | DICOM 표의 다른 열을 읽음 |
| 부분 답변 플래그 | 0 (p52 1건) | 0 | gemma4 6~7건. `insufficient_evidence`를 거의 쓰지 않음(MODEL_REFUSED 5 vs 13) |
| JSON schema | 100% | 100% | 차이 없음 |
| 길이 (중앙값, 글자) | 134.5 | 111.5 | gemma4 136, 122.5. **장황함은 원인이 아님** |

medgemma가 "이긴" 것처럼 보이는 낮은 오거절률(1.3% vs 7.6%)도 내용을 보면 대부분 이득이 아닙니다. gemma4가 거절하고 medgemma가 답한 벡터 5문항 중 p60은 숫자를 지어냈고, p65는 다른 기준을 답했고, p40은 관계없는 chunk를 그대로 붙였고, p86은 "언급하지 않는다"고 했으며, p12만 대체로 맞았습니다(retrieval miss 상태). rerank에서는 p65 하나("40% increase in 3D volume")가 정답이었습니다.

### 지어낸 값과 context

정답 근거가 context에 있었는지를 각 실행의 top-5 chunk 원문(exact 검색으로 재현)과 대조했습니다.

| 문항 | 설정 | medgemma 답변 | context에 정답 근거 | 숫자의 출처 |
|---|---|---|---|---|
| p52 (no_answer) ICC 값 | rerank ×2 | "ICC 값은 0.86입니다" | 없음 | context에 없음 (만듦) |
| p60 PET 재구성 설정 | 벡터 ×2 / rerank ×2 | "2 iterations and 16 subsets" / "10 iterations and 10 subsets" | 없음 (정답: 4 iterations, 21 subsets) | context에 없음 (만듦) |
| p95 (no_answer) BICR 판독자 수 | 벡터 ×2 | "IRB/IEC를 최소 5명으로 구성" | 없음 | [4] ICH GCP의 IRB 구성 "최소한 5명" |
| p95 (no_answer) | rerank ×2 | "BICR 판독자를 최소 30명으로 구성하라고 명시 [2]" | 없음 | [2] 우산형 임상시험 사례의 환자 수 "최소 30명, 최대 50명" |
| p71 (no_answer) amino-acid PET SUV 기준 | rerank ×2 | "25% 이상의 SPPD 증가 또는 40% 이상의 부피 증가 [4]" | 없음 (리뷰는 PET를 범위 밖으로 둠) | [4] MRI 확인 기준 |
| p65 RANO 2.0 3D 진행 기준 | 벡터 ×2 | "more than 25% increase in SPPD" | 없음 (벡터 top-5에 40% 부피 기준 없음) | context의 2D 기준 |

- 7건 모두 **근거가 빠진 자리를 채운** 경우입니다. 4건은 context 안의 숫자를 다른 주어에 붙였고(misbinding), 3건은 숫자를 만들었습니다. 같은 문항에서 gemma4는 모두 거절했습니다(p60·p65 벡터에서는 거절이 오거절로 집계됨).
- 반대 방향, 즉 근거가 있는데 사전 지식으로 덮어쓴 경우는 숫자 기준으로 찾지 못했습니다. 답변 속 숫자 가운데 context·질문에 없는 숫자는 medgemma 벡터 82개 중 p60 하나, rerank 84개 중 p52·p60 둘뿐이었습니다(gemma4는 목록 번호 외 0건).
- 숫자가 아닌 오류도 있습니다. p76에서 medgemma는 DICOM Basic Profile의 Patient's Name을 "기본적으로 유지"된다고 답했습니다(정답 Z: 빈 값/더미로 대체). 표의 다른 열(`Retd.`, `In Std. Comp. IOD`)을 읽은 결과입니다.

## Probe 결과

### a) 프롬프트 적합성 (`--prompt-variant inline-en`, 평가 전용)

`backend/app/prompts/rag_prompt_inline_en.txt`: 영어 지시문을 user turn 맨 앞에 넣고(system 메시지 없음), "질문과 같은 언어로 답하라", 문장마다 `[n]`, 근거가 없으면 정확히 "문서에서 확인할 수 없습니다."와 `insufficient_evidence=true`, 그리고 예시 3개(영어 답, 한국어 답, 거절)를 붙였습니다. 예시의 내용은 평가 문항과 겹치지 않게 지어낸 것입니다. 기본 프롬프트와 채점은 바꾸지 않았습니다(`RAG_PROMPT_VARIANT=default`).

벡터 단독, public 99문항, 같은 검색 결과. 칸 안의 두 값은 1회 / 2회.

| 지표 | gemma4 · 기본 | gemma4 · inline-en (1회) | medgemma · 기본 | **medgemma · inline-en** |
|---|---|---|---|---|
| Refusal accuracy (20) | 95.0 / 95.0% | 95.0% | 80.0 / 85.0% | **90.0 / 90.0%** |
| ㄴ no_answer (7) | 6 / 6 | 6 | 4 / 4 | **5 / 5** (p95 "BICR 최소 5명" 남음) |
| ㄴ out_of_scope (4) | 4 / 4 | 4 | 3 / 4 | 4 / 4 |
| False refusal (79) | 7.6 / 8.9% | 15.2% | 1.3 / 1.3% | 2.5 / 2.5% |
| 부분 답변 | 7.6 / 8.9% | 0% | 0 / 0% | 0 / 0% |
| Keyword coverage | 91.8 / 93.1% | 94.0% | 87.2 / 87.2% | 88.3 / 87.0% |
| Citation accuracy | 86.3 / 87.5% | 95.5% | 78.2 / 78.2% | 76.6 / 77.9% |
| Citation location | 90.4 / 93.1% | 92.5% | 84.6 / 85.9% | 70.1 / 68.8% |
| 본문 `[n]` 표기 | 72/74, 71/73 | 68/68 | 15/82, 10/81 | **51/79, 50/79** |
| 4개 이상 인용 | 2, 2 | 0 | 20, 24 | 8, 9 |
| 답변 언어 = 질문 언어 | 54/74, 51/73 | 48/68 | 68/82, 68/81 | 71/79, 71/79 |
| 영어 질문 → 한국어 답 | 19/22, 20/22 | 17/19 | 7/26, 7/26 | 2/25, 2/25 |
| JSON schema-valid | 100% | 100% | 100% | 100% |

- **움직인 것**: 거절(80~85 → 90%), `[n]` 표기(약 15% → 64%), 과다 인용 감소, 지시한 언어 따르기. 거절 예시를 보여 준 효과로 보입니다. p52·p71·p98은 이제 거절하고, p60도 지어내지 않고 거절했습니다.
- **움직이지 않은 것**: Keyword와 citation accuracy. 근거를 고르고 읽는 능력은 프롬프트로 바뀌지 않았습니다. 두 번 모두 p95("BICR 판독자를 최소 5명으로 구성하라고 권장합니다 [5]"), p65("25% increase in SPPD"), p40(관계없는 chunk 한 줄을 그대로 붙임)는 그대로였습니다. citation location은 오히려 85 → 70%로 떨어졌는데, 기본 프롬프트에서 위치가 맞은 답변 66개 중 18개가 4~5개를 한꺼번에 인용한 답변이었습니다. 과다 인용이 위치 지표를 부풀렸고, 인용을 좁히자 그만큼 드러난 것입니다.
- **gemma4에 같은 변형을 쓰면**: 거절 정확도는 같고 citation accuracy가 올랐지만(95.5%), 부분 답변이 사라지고 오거절이 두 배(15.2%)가 됐습니다. 거절 예시가 "일부만 근거가 있는" 질문까지 거절 쪽으로 밀었습니다. 또 gemma4는 "질문 언어로 답하라"를 받고도 영어 질문 19개 중 17개에 한국어로 답했습니다(context 대부분이 한국어이기 때문으로 보이나 확인하지 않음). 즉 이 변형은 medgemma에 맞춘 것이고 gemma4 기본값을 대체할 근거는 없습니다.
- **결론**: 프롬프트 적합성은 거절·인용 표기 격차의 상당 부분을 설명하지만 전부는 아닙니다. 변형 후에도 medgemma는 거절 1문항, keyword 약 5%p, citation accuracy 약 9%p 뒤집니다. 모델 카드도 "MedGemma's training may make it more sensitive to the specific prompt used than Gemma 3"라고 적고 있습니다.

### b) closed-book 의학 지식 (자작 22문항, 검색 없음)

`eval/probes/closed_book_items.yaml`. RECIST 1.1·iRECIST·Deauville/Lugano·PERCIST·SUV·조영제·Hounsfield·MRI·DICOM 태그·한영 해부/질환 용어·일반 의학의 4지선다 문항입니다. 정답은 기준 문서나 교과서에 정해진 사실이고 출처를 문항마다 적었습니다. 선택지 순서를 두 가지(원래 순서, 정답 위치를 A~D로 돌린 순서)로 묻고 글자만 채점했습니다. temperature 0, system 없음. **작은 자작 probe이고 검정력이 낮습니다. 1문항이 4.5%p입니다.**

| | 원래 순서 | 돌린 순서 | 두 순서 모두 정답 | 선택한 글자 분포 (44회) |
|---|---|---|---|---|
| gemma4:e4b | 17/22 | 18/22 | 17/22 | A 11, B 18, C 12, D 3 |
| medgemma:4b | 14/22 | 12/22 | 11/22 | A 17, B 20, C 6, D 1 |

- medgemma가 두 순서 모두 틀린 문항: RECIST 1.1 PR 기준 30%(k01), PD 기준 20% + 5mm(k02), 표적 병변 수 5개/장기당 2개(k05), iRECIST iUPD(k07), NSF와 gadolinium 조영제(k13), DICOM (0010,0010)(k16). gemma4는 RECIST 림프절 단축 15mm(k04), Lugano CMR = Deauville 1~3(k09), SUL = lean body mass(k12)를 두 순서 모두 틀렸습니다.
- 한영 용어 4문항(k17~k20)은 두 모델 모두 두 순서에서 맞혔습니다. 용어 보조로서의 차이는 이 probe로는 보이지 않습니다.
- medgemma는 44회 중 37회 A나 B를 골라 위치 편향이 있고, 순서를 바꾸면 결과가 3문항 달라졌습니다.
- 해석: 모델 카드의 MedQA 64.4(Gemma 3 4B 50.7)는 *같은 크기의 이전 세대* 대비입니다. 이 probe에서는 크기와 세대가 다른 gemma4:e4b가 더 많이 맞혔습니다. 표본이 작아 "medgemma가 의학 지식이 약하다"고 결론 내리지는 않습니다. 다만 "의료 특화라서 이 과제에 지식 면에서 유리하다"는 가정을 지지하는 근거도 없었습니다.

### c) 영상 (일화적, 1장)

로컬에 이미 설치된 pydicom 번들 테스트 파일 `CT_small.dcm`(GE CT, 128×128, axial)을 soft-tissue window(L40/W400)로 PNG(`eval/results/2026-10-07_model-probes/ct_small_soft_tissue.png`)로 만들어 "modality, 부위, 단면"을 물었습니다. 내려받은 영상은 없습니다.

- gemma4: "Computed Tomography (CT) … the spine, specifically a cross-section of a vertebral body … axial (or transverse)"
- medgemma: "a cross-sectional view of the spine, likely from a CT scan … a vertebral body and surrounding structures … axial plane"
- 영상은 척추체·척추관·늑골 관절부·인접 대동맥이 보이는 흉추 높이의 axial CT로 보입니다(작성자 판독, 영상 전문가 확인 아님). 두 모델 모두 modality·부위·단면을 맞혔고 높이는 말하지 않았습니다. 1장이고 CT는 medgemma의 주요 학습 modality(흉부 X선·피부·안저·병리)가 아니므로 영상 능력 비교의 근거로 쓰지 않습니다. **영상 능력은 측정하지 않은 것으로 봅니다.**

## MedGemma의 설계 목적 vs 이 RAG에 필요한 것

1차 출처(2026-10-07 확인):

- HF 모델 카드 [google/medgemma-4b-it](https://huggingface.co/google/medgemma-4b-it) (MedGemma 1, 2025-05-20 공개):
  - 용도: "intended to be used as a starting point that enables more efficient development of downstream healthcare applications involving medical text and images."
  - 영상 학습: "The model was pre-trained using chest X-ray, pathology, dermatology, and fundus images."
  - 텍스트 벤치마크(Gemma 3 4B → MedGemma 4B): MedQA (4-op) 50.7 → 64.4, MedMCQA 45.4 → 55.7, PubMedQA 68.4 → 73.4, MMLU Med 67.2 → 70.0.
  - 영상: MIMIC CXR macro F1 81.2 → 88.9, CheXpert CXR 32.6 → 48.1, US-DermMCQA 52.5 → 71.8, EyePACS fundus 14.4 → 64.9.
  - 한계: "MedGemma is not intended to be used without appropriate validation, adaptation and/or making meaningful modification by developers for their specific use case.", "A limitation of our evaluations was that they included primarily English language prompts.", "MedGemma has not been evaluated or optimized for multi-turn applications.", "MedGemma's training may make it more sensitive to the specific prompt used than Gemma 3."
- Google 개발자 문서 [MedGemma model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card): "not intended to directly inform clinical diagnosis, patient management decisions, treatment recommendations, or any other direct clinical practice applications", "All outputs from MedGemma should be considered preliminary and require independent verification". 이 페이지는 현재 MedGemma 1.5 4B 수치를 싣고 있습니다(MedQA 69.1 등). Ollama의 `medgemma:4b`가 어느 판인지는 확인하지 않았으므로 위의 MedGemma 1 수치를 기준으로 삼습니다.
- 기술 보고서 [arXiv:2507.05201](https://arxiv.org/abs/2507.05201) (Sellergren et al., 2025-07-07): "Fine-tuning MedGemma further improves performance in subdomains, reducing errors in electronic health record information retrieval by 50% …", "… while maintaining the general capabilities of the Gemma 3 base models."
- Gemma 3 형식 문서 [ai.google.dev/gemma/docs/core/prompt-structure](https://ai.google.dev/gemma/docs/core/prompt-structure): "the `system` role or a system turn is not supported", "provide system-level instructions directly within the initial user prompt."
- Gemma 4 E4B: HF 카드 [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it) "4.5B effective (8B with embeddings)", "Native System Prompt Support", "Out-of-the-box support for 35+ languages, pre-trained on 140+ languages", 128K 컨텍스트. 라이선스는 Apache 2.0([Google 오픈소스 블로그](https://opensource.googleblog.com/2026/03/gemma-4-expanding-the-gemmaverse-with-apache-20.html)).

| 이 RAG에 필요한 것 | 측정 결과 | 1차 출처와의 관계 |
|---|---|---|
| 근거 밖으로 나가지 않기 (grounding) | 근거가 없을 때 채움 7건, 근거가 있을 때 덮어쓰기 0건 | 모델 카드는 RAG grounding을 평가하지 않음 |
| 거절 | no_answer 4/7 (기본) → 5/7 (변형), gemma4 6/7 | "appropriate validation, adaptation" 필요 |
| 인용 형식 `[n]` | 15/82 → 51/79, gemma4 72/74 | 프롬프트 민감도 높음 |
| 한국어 | 영어 질문에 영어로 답함 19/26, 영어 원문 복사 | 평가가 "primarily English" |
| system 지시 따르기 | Gemma 3에는 system 역할이 없음. 템플릿이 user turn에 붙이지만 언어 지시는 따르지 않음 | Gemma 4는 "Native System Prompt Support" |
| 의학 지식 회상 | 이 과제는 거의 필요 없음. closed-book probe에서도 gemma4가 앞섬 | MedGemma 강점은 같은 크기 Gemma 3 대비 |

## 원인 순위 (근거 강도 순)

1. **근거가 부족할 때 거절하지 않고 채우는 경향 (강함)**. 지어낸 7건이 모두 정답 근거가 없는 경우였고 4건은 context 속 다른 숫자를 붙였습니다. `insufficient_evidence`를 거의 쓰지 않았습니다(MODEL_REFUSED 5 vs 13). 프롬프트를 바꿔도 p95는 남았습니다.
2. **프롬프트 적합성: Gemma 3 형식과 한국어 지시문 (강함, 일부만 설명)**. 변형 프롬프트로 거절 +5~10%p, `[n]` 표기 약 4배, 과다 인용 절반 이하가 됐습니다. keyword·citation accuracy는 바뀌지 않았습니다.
3. **인용과 표 읽기 (중간)**. 4개 이상 한꺼번에 인용, 긴 원문 복사, DICOM 표 열 혼동(p76, p79). 변형 후에도 citation location 70%.
4. **크기·세대 차이 (간접 근거)**. 크기를 맞춘 비교를 하지 못했습니다. closed-book probe에서도 gemma4가 앞선 것과, Gemma 4가 system 역할·다국어를 공식 지원한다는 점이 이 방향을 가리키지만 분리해서 측정하지는 않았습니다.
5. **의학 지식 부족은 원인이 아님 (근거 없음)**. 이 과제의 실패는 지식이 아니라 근거 사용에서 나왔습니다.

## medgemma가 더 나은 선택일 수 있는 경우

근거가 있는 것만 적습니다.

- **학습한 영상 modality의 영상 과제**(흉부 X선, 피부, 안저, 병리): 모델 카드 수치(MIMIC CXR 88.9 vs Gemma 3 4B 81.2 등). 이 저장소에서는 측정하지 않았고, 이 시스템은 영상 판독을 하지 않습니다.
- **의료 하위 과제의 fine-tuning 기반**: 기술 보고서의 EHR 정보 검색 오류 50% 감소. 우리 RAG 형식(거절·`[n]`·한국어)을 학습시키는 데 쓸 수 있는지는 측정하지 않았습니다.
- **같은 크기의 범용 모델 대비 영어 의료 QA**: MedQA 64.4 vs Gemma 3 4B 50.7(카드). 더 새로운 Gemma 4 E4B와 비교할 때는 이 우위가 이 저장소의 probe에서 보이지 않았으므로, 고르기 전에 같은 문항으로 다시 재야 합니다.
- **메모리가 부족한 오프라인 장비**: 실행 4.5GB vs 10.7GB, 생성 p50 약 1초 빠름(ADR 0005). 이때는 `inline-en` 같은 Gemma 3용 프롬프트, 생성 전 거절 게이트, 인용 없는 수치 제거 같은 안전장치와 HAI-DEF 약관 조건이 함께 필요합니다.
- 용어 보조(한영 의학 용어): 4문항에서 두 모델이 같았습니다. medgemma를 고를 근거는 되지 않습니다.

## 측정하지 않은 것

- 크기를 맞춘 비교(Gemma 3 4B, gemma4 e2b), medgemma 27B, MedGemma 1.5. 받지 않았습니다.
- 공개 벤치마크(MedQA 등)에서의 직접 측정. 데이터셋을 받지 않았습니다.
- medgemma의 영상 능력(흉부 X선·피부·안저·병리). 영상을 받지 않았고 CT 1장은 일화입니다.
- rerank 설정에서의 `inline-en` 변형, 변형 프롬프트의 구성 요소별(언어 지시, 예시, user turn 배치) 기여.
- 숫자가 아닌 내용의 근거 대조. 숫자 대조는 문자열 일치라 형식이 다른 숫자(예: "four" vs "4")는 놓칠 수 있습니다.
- 사람 또는 LLM 채점에 의한 답변 품질.

## 재현

```bash
# 일회용 DB (익명 볼륨)에 색인한 뒤, 이 분석에서는 HNSW 인덱스를 지워 exact 검색으로 원래 top-5를 재현했다
DATABASE_URL=postgresql+asyncpg://clinical:clinical@127.0.0.1:55432/clinical_rag_qa \
  uv run --project backend python eval/run_eval.py --corpus public --hybrid off \
  --generator-model medgemma:4b --prompt-variant inline-en --label bge-m3-vector-medgemma-4b-inline-en
uv run --project backend python eval/probes/run_model_probes.py \
  --models gemma4:e4b medgemma:4b --out eval/results/2026-10-07_model-probes
```

`inline-en` 결과의 `config.json`에 적힌 `git_commit`(05ebae8)은 변형 코드를 커밋하기 전 작업 트리에서 실행했다는 뜻입니다. 변형 코드는 이 문서와 같은 커밋에 들어 있습니다.
