# RAG Eval Report — public / bge-m3-vector-rerank-nogate-gemma4-e4b (2026-10-07T01:47:23)

## Config

- run_at: `2026-10-07T01:47:23`
- label: `bge-m3-vector-rerank-nogate-gemma4-e4b`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `4875f26`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `bge-reranker-v2-m3`
- reranker_model: `BAAI/bge-reranker-v2-m3`
- reranker_revision: `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`
- reranker_device: `mps`
- rerank_candidates: `30`
- rerank_min_score: `0.0`
- partial_answers: `True`
- eval_process_max_rss_mb: `883`
- embedding_model: `bge-m3`
- embedding_dim: `1024`
- hybrid_search: `False`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `0.45`
- scope_classifier: `embedding`
- scope_margin: `0.056`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 94.9% |
| Section/page hit@k | 88.6% |
| Citation accuracy (cited files ⊆ gold) | 88.0% |
| Citation location (a cited chunk in gold section/page) | 86.7% |
| Keyword coverage | 94.7% |
| Refusal accuracy (must-refuse) | 95.0% |
| False refusal rate (answerable) | 5.1% |
| Partial answers with caveat (answerable) | 3.8% |
| False refusal if partial = refusal (MVP-1 policy) | 8.9% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 94.7% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 2,723 |
| Retrieval p95 (ms) | 3,305 |
| Generation p50 (ms) | 7,108 |
| Generation p95 (ms) | 12,195 |
| Total p50 (ms) | 9,313 |
| Total p95 (ms) | 14,756 |
| Input tokens (total) | 159,600 |
| Output tokens (total) | 9,477 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 72, 'ANSWERED_PARTIAL': 4, 'MODEL_REFUSED': 11, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 71.4% | 100.0% | 100.0% | - | 14.3% | 28.6% | 11,516 |
| cross_language | 25 | 88.0% | 88.0% | 84.0% | 100.0% | - | 0.0% | 4.0% | 9,869 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 97.2% | 91.7% | 85.3% | 88.2% | - | 5.6% | 0.0% | 9,429 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 7,319 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 2,444 |
| table_lookup | 11 | 100.0% | 90.9% | 100.0% | 100.0% | - | 9.1% | 0.0% | 11,065 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 87.5% | 87.5% | 100.0% | 11.1% | 3.7% | 8,420 |
| ko | 65 | 94.2% | 92.3% | 88.2% | 98.0% | 92.3% | 1.9% | 3.8% | 10,360 |

## Failed questions

- **p02**: keywords 0%
- **p06**: keywords 0%
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p13**: false refusal (MODEL_REFUSED)
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p15**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p16**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p17**: citation ['04_mfds_anticancer_guideline_ko.pdf']
- **p19**: keywords 0%
- **p21**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p22**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p35**: section/page miss; keywords 0%
- **p41**: should refuse but a partial answer
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: false refusal (MODEL_REFUSED)
- **p84**: false refusal (MODEL_REFUSED)
- **p85**: section/page miss
- **p86**: section/page miss

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가 변수 가이드라인에 따르면, 해석(case report forms 또는 assessment tabulations)과 같은 원본  |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 이미지를 배치(batches)로 해석하는 경우, 임상시험 문서(charter)에는 배치 크기를 명시하고 그 근거를 제시해야 하며, 배치 세션 간 |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단될 경우, 임상시험 문서(프로토콜 및 통계 분석 계획)에 이 비율 결정 과 |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 이미징 헌장 지침은 독자에게 이미지를 제시하는 방식에 대해 다음과 같은 사항들을 기술하도록 권고합니다. 첫째, 이미지가 (또는 특정 시점 |
| p05 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 무작위 대조 임상시험에서 영상 판독자는 피험자의 치료 배정(treatment assignment)에 대해 눈가림되어야 하며, 이는 치료 배정 정 |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 관행의 영상 표준이 적절할 수 있는 임상시험의 1차 평가 변수로, 장골 골절이나 뇌내 출혈과 같이 임상 사이트 간에 중요하게 |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 경우, 개발자는 세션에서 판독할 수 있는 최대 이미지 수를 지정할지 고려해야 합니다 [1]. 또한, 판독자 피로 |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 임상시험 문서에서 '데이터 잠금(locking data)'은 이미지 평가가 더 이상 허용되지 않는 시점을 의미합니다 [1]. 데이터 잠금 |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 제공된 문서에서는 FDA 영상 평가변수 가이드라인이 요구하는 판독자 간 일치도(kappa)의 최소 기준값에 대한 정보를 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 대한 직접적인 언급은 문서에서 확인할 수 없습니다. 다만, 시험자가 임상시험계획서에서 벗어날 수 있는 경우에 대해 다음과  |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | ICH E6(R3)에 따라, 시험자/기관은 필수 기록을 적용 가능한 규제 요건에 따라 또는 의뢰자가 해당 기록이 더 이상 필요하지 않다고 통보할 |
| p12 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에서 시험기관 모니터링 활동의 빈도를 결정하는 근거는 임상시험의 목적, 설계, 복잡성, 눈가림, 대상자 수, 그리고 결과변수  |
| p13 | factual | en | MODEL_REFUSED | N | N | - | 제공된 문서에는 ICH E6(R3)에 따라 현장 모니터링을 수행해야 하는 주체에 대한 정보가 포함되어 있지 않습니다. [문서에서 확인할 수 없습 |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링은 현장 모니터링(site monitoring)을 보완하고 그 범위 및/또는 빈도를 줄이는 추가적인 모니터링 기능을 제공할 수 있으 |
| p15 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | 임상시험이 조기 종료되거나 중지된 경우, 시험자/시험기관은 다음과 같은 조치를 취해야 합니다.  1. **시험대상자 보호 및 보고:** 시험자/ |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면, IRB/IEC는 과학적, 의학적, 윤리적 측면을 검토하고 평가할 수 있는 자격과 경험을 종합적으로 갖춘 적절한 수 |
| p17 | factual | en | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 2상 단독요법 치료적 탐색 임상시험에서 객관적 반응률(ORR)은 국제 기준(예: RECIST, Volumetric RECIST  |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 최대내약용량(MTD)의 전통적인 정의에 대해 식약처 항암제 가이드라인과 EMA 가이드라인에서 확인된 내용은 다음과 같습니다.  **식약처 항암제 |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | EMA 가이드라인은 인간에게 최초 투여(first use in man) 시, 생체이용률과 관련된 변동성을 제거할 수 있기 때문에 가능한 경우 정 |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 이전 치료의 TTP와 시험약의 PFS를 비교하는 환자 내 외부 대조 분석을 더 설득력 있게 만들기 위해서는, 이전 치료와 시험 치료가 제공된 조 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | BSA(체표면적) 당 용량에 대한 과학적 뒷받침은 약하며, BSA가 높은 환자에서는 약물 과다 노출, BSA가 낮은 환자에서는 약물 과소 노출을 |
| p22 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생한 경우, 환자가 회복될 때까지 기다린 후 재투여할 때 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. [1 |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 다음과 같습니다. 첫째, 최대내약용량(MTD), 용량제한독성(DLT) 및  |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 독성은 일반적으로 인정되는 시스템(예: 미국 국립암연구소[National Cancer Institute]의 이상반응에 대한 일반용어기준[Comm |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제의 음식-약물 상호작용 시험은 임상 3상 이전에 수행되어야 합니다 [1], [2]. 또한, 식이 또는 공복 상태의 투여에 대한 합리적인 이 |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR(초기 불일치율)과 LDR(후기 불일치율)은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1] |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1], [2]. |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험의 1차 평가변수는 일반적으로 전체 반응률(Overall Response Rate, ORR)로 설정합니다 [1]. |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 우산형 임상시험에서 시험약물 간의 유효성 비교는 권장되지 않습니다. [1] 유효성 비교 분석은 시험약물과 공통 대조군 간에 수행되어야 하며, 시 |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 시점과 관계없이, 1차 분석 목적을 위해서는 진행일은 진행이 문서로 확인된 시점을 기준으로 해야 합니다 [2]. 즉, 예정된 평가  |
| p31 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 제공된 문서에는 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대한 식약처 가이드라인과 EMA 가이드라인을 비교하여 명시하 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | ICH GCP 안내서에 따르면, 시험책임자/임상시험실시기관이 유지하는 근거자료는 다음과 같은 특성을 갖추어야 합니다:  *   **포괄성:**  |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자는 확인된 위험요소를 평가할 때 다음 세 가지 사항을 고려해야 합니다: (a) 오류 발생 가능도 [1], [2], (b) 해당 오류의 탐지 |
| p34 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계에서 일탈이 감지되면, 조치가 필요한지 여부를 결정하기 위한 평가를 실시해야 합니다. [1], [2], [3] |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 폐CT 영상 기반 폐암·폐결절 진단보조 소프트웨어 임상시험계획서 예시의 연구 설계는 다음과 같습니다.  *   **임상시험 제목/설계:** 전산 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐결절 AI 임상시험 예시에서 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터는 1:2의 비율로 강화 배정(enrichment alloc |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 판독 수행하며, 개별 판독 후 참조 |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | AI 의료기기 임상시험에서 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다. [1] |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 디지털의료기기의 개발 과정 동안 사용된 학습 데이터와 독립성을 유지해야 합니다. [1] |
| p40 | cross_language | en | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자들에게 10일의 시간 동안 표본을 적절히 배분하고 판독하여 결과 값을 기록하도록 합니다. [2] |
| p41 | no_answer | ko | ANSWERED_PARTIAL | - | - | 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에서 CT slice 간격에 대한 구체적인 수치(mm 이하)는 확인할 수 없습니다. 다만, 임상시험 데이터셋 선정 기준 중 CT 영상 |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD가 확인된 경우, 잠재적인 가성진행(pseudoprogression)에 대한 재평가는 일반적으로 권장되는 6~12주 간 |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD(미확정 진행)로 판정하는 조건은 다음과 같습니다. 첫째, 모든 TL의 합이 가장 낮은 TL 합(Nadir) 대비 최소 |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD가 iCPD로 확정되는 경우는 다음 추적 관찰 시점에서 다음 중 하나가 있을 때입니다: 표적 합(target sum)의 추가 진행(≥ 5 |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 정기적인 반응 평가 추적 관찰은 6~12주 간격으로 권장됩니다. [1] |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 표적 병변(target lesions)은 환자당 최대 5개까지, 그리고 장기당 최대 2개까지 정의할 수 있습니다 [1], [2 |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 추적 관찰 시 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우, 기본값으로 5 mm를 사용할 수 있습니다. [1] |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 아니요, iUPD는 iRECIST에서 후속 최적 전체 반응(iSD, iPR, 또는 iCR)을 무효화하지 않습니다. iUPD는 iSD, iPR,  |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST는 면역항암제 투여 후 hyperprogression을 언급하며, 이는 치료 전 상태에 비해 종양 성장 동역학이 2배 이상 증가하는 |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi 등은 펨브롤리주맙(Pembrolizumab)을 사용한 진행성 흑색종 환자에서 총 7%의 가성 진행(pseudoprogression) 비 |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1–3점은 완전 관해(CR)로 판정합니다 [1]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4–5점이지만 기저 대비 FDG 섭취가 감소한 경우 부분 관해(PR)로 분류됩니다 [2]. |
| p55 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 minor response(MiR)는 모든 Deauville 점수와 관계없이 SLD(표적 병변의 최장 직경 합)가 10% 이상 감소 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대해 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR을 PR로 재코딩했을 때, 치료 종료 시점(EOT)의 RECIL과 Lugano 간의 일치도는 90.7%였고, Cohen의 kappa(κ)  |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분 및 3.8 ± 0.6분이었고, Lugano의 경우 평균 판독 시 |
| p59 | table_lookup | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL 대 Lugano 연구의 표 1에 따르면, DLBCL 환자의 평균 연령은 55.5 ± 17.5세입니다. [4] |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 제공된 문서에서는 RECIL 대 Lugano 연구에 사용된 PET 재구성 설정(반복 횟수 및 서브셋)에 대한 정보는 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 방사선 치료 종료 후 약 4주(21–35일)에 기저 스캔을 설정하여, 주로 PsP(pseudoprogression)의 영향 |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD는 다음의 방식으로 정의될 수 있습니다. 첫째, 초기 치료 기간 12주 이내에 SPPD(Short- |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 반응 범주 표(Table 3)에 따르면, 2D 측정 기준 부분반응(PR)의 임계값은 '50% 초과 감소'입니다 [1]. |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 제공된 문서에는 RANO 2.0 리뷰의 표 3(Table 3)에 대한 정보가 포함되어 있지 않아 3D 부피 변화를 정의하는 내용이 확인되지 않습 |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능한 병변은 기본적으로 최소 단축 직경 10 mm를 가져야 하며, 2D 영상에서는 최소 2개 슬라이스에 걸쳐 확장되어 |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 강화되거나 비강화된 종양의 경우, 측정 가능한 병변으로 평가할 때 최소 2개에서 최대 3개의 표적 병변을 선택해야 합니다 [ |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에 따르면, 3D-T1w Pre의 슬라이스 두께는 1.5 mm 이하입니다.  |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 표준화된 시간 간격(치료 시작 전 14일 이내)을 두고 사전 스캔을 기저 스캔으로 사용하는 것이 권장됩니다 [1]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서는 DICOM 영상 비식별화 시, 현재 릴리스 버전의 DICOM PS3.15 E.1 Application Level Confide |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | 아니요, 문서에 따르면 임의의 유한한 수 또는 지정된 하위 집합의 간접 식별자를 보유하는 것은 위험 분석이 없는 한 허용되지 않습니다 [1]. |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서에서 범위 밖(out of scope)으로 둔 원시 데이터의 예로는 MR k-space, CT 투영(projections), PE |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서는 비식별화 과정에서 DICOM 객체의 적합성(conformance)을 유지하는 것이 중요하며, 이는 데이터 요소의 값 제거, 제 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Basic Profile에서 Patient's Name (0010,0010) 속성은 Basic Profile이 Z로 지정 |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Instance UID (0020,000D)의 Basic Profile은 'U'로 지정되어 있습니다 [2], [3]. Retain U |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)의 Basic Profile은 Z이며 [1], Retain Longitudinal Temporal Inf |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Institution Name (0008,0080)의 Basic Profile은 X/Z/D이며, PS3.6에서 삭제(Retd.)되지 않았고, P |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM 비식별화 조치 코드 X는 해당 속성(Attribute)을 제거하며, 만약 해당 속성이 시퀀스(Sequence)인 경우 모든 시퀀스 항 |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)는 Basic Profile에서 'X'로 처리되며 [1], [3], [4] 참고, Retain Pa |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (0018,1000)의 기본 프로파일(Basic Prof.)은 X/Z/D입니다. [1] |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에는 iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔 시점에 대한 정보가 포함되어 있지 않아 답변할 수 없습니다. |
| p85 | cross_doc | en | ANSWERED | Y | N | 08_recil_vs_lugano_2019.xml, 09_rano2_review_2025.xml | RECIL은 'minor response'를 새로운 임시 범주로 정의하며, 이는 주로 중간 재분류(interim restaging)에서 흔하게  |
| p86 | cross_doc | en | ANSWERED_PARTIAL | Y | N | 01_fda_imaging_endpoint_2018.pdf | EMA 항암 가이드라인은 특정 내용을 직접적으로 언급하고 있지 않으나, FDA 이미징 엔드포인트 가이드라인에 따르면, 임상 시험 이미징 데이터는 |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인은 인간에게 최초 투여 시 정맥투여를 권장하는 이유로, 대부분의 경우 정맥투여가 생체이용률에 따른 변화를 배제할 수 있기 때문이 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 제공된 문서에서는 BICR(맹검된 독립적 중앙평가) 판독자를 최소 몇 명으로 구성해야 하는지에 대한 정보는 확인할 수 없습니다. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
