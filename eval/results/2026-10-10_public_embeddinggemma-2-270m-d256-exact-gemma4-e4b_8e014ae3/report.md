# RAG Eval Report — public / embeddinggemma-2-270m-d256-exact-gemma4-e4b (2026-10-10T19:44:09)

## Config

- run_at: `2026-10-10T19:44:09`
- label: `embeddinggemma-2-270m-d256-exact-gemma4-e4b`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_classification: `public-regulatory`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `3342ce5`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `none`
- partial_answers: `True`
- rag_prompt_variant: `default`
- eval_process_max_rss_mb: `140`
- ollama_version: `0.40.2`
- embedding_model: `embeddinggemma-2:270m`
- embedding_dim: `256`
- embedding_truncate_dim: `256`
- embedding_query_prefix: `task: search result | query: `
- embedding_document_prefix: `title: none | text: `
- hybrid_search: `False`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `-0.145`
- scope_classifier: `embedding`
- scope_margin: `0.0191`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 92.4% |
| Section/page hit@k | 79.7% |
| Citation accuracy (cited files ⊆ gold) | 88.9% |
| Citation location (a cited chunk in gold section/page) | 83.3% |
| Keyword coverage | 88.9% |
| Refusal accuracy (must-refuse) | 95.0% |
| False refusal rate (answerable) | 8.9% |
| Partial answers with caveat (answerable) | 12.7% |
| False refusal if partial = refusal (MVP-1 policy) | 21.5% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 95.0% |
| Answers in Korean (answered) | 94.4% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 49 |
| Retrieval p95 (ms) | 82 |
| Generation p50 (ms) | 3,007 |
| Generation p95 (ms) | 6,091 |
| Total p50 (ms) | 2,895 |
| Total p95 (ms) | 5,745 |
| Input tokens (total) | 153,819 |
| Output tokens (total) | 9,699 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 0 |

Refusal reasons: {'ANSWERED': 63, 'ANSWERED_PARTIAL': 10, 'MODEL_REFUSED': 16, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 71.4% | 100.0% | 100.0% | - | 14.3% | 57.1% | 5,454 |
| cross_language | 25 | 80.0% | 64.0% | 86.4% | 86.4% | - | 12.0% | 16.0% | 3,216 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 97.2% | 91.7% | 85.7% | 85.7% | - | 2.8% | 2.8% | 3,358 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 1,583 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 1,137 |
| table_lookup | 11 | 100.0% | 81.8% | 100.0% | 100.0% | - | 18.2% | 9.1% | 2,399 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 92.6% | 74.1% | 87.0% | 82.6% | 100.0% | 14.8% | 11.1% | 3,056 |
| ko | 65 | 92.3% | 82.7% | 89.8% | 91.8% | 92.3% | 5.8% | 13.5% | 2,876 |

## Failed questions

- **p02**: keywords 0%
- **p05**: retrieval miss (got ['04_mfds_anticancer_guideline_ko.pdf', '05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']); citation ['04_mfds_anticancer_guideline_ko.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p06**: keywords 0%
- **p10**: false refusal (MODEL_REFUSED)
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p13**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p15**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']
- **p19**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p31**: false refusal (MODEL_REFUSED)
- **p33**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p35**: keywords 0%
- **p40**: false refusal (MODEL_REFUSED)
- **p41**: should refuse but answered
- **p43**: keywords 0%
- **p46**: false refusal (MODEL_REFUSED)
- **p50**: keywords 0%
- **p55**: section/page miss; keywords 0%
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: false refusal (MODEL_REFUSED)
- **p72**: section/page miss; keywords 0%
- **p73**: section/page miss
- **p74**: section/page miss
- **p86**: section/page miss

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가변수 가이드라인에 따르면, 해석(case report forms 또는 assessment tabulations)은 원본 데이터로 |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 독자들이 이미지를 배치(batches)로 해석하는 경우, 임상시험 문서(charter)에는 배치 크기를 명시하고 해당 배치 크기를 정당화해야 하 |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단되는 경우, 임상시험 문서(프로토콜 및 통계 분석 계획)에 이 비율 결정  |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA의 영상 챠터 지침은 독자들에게 다음과 같은 종류의 이미지 제시를 설명합니다: 이미지 표시 훈련 세션(image display traini |
| p05 | cross_language | ko | ANSWERED_PARTIAL | N | N | 04_mfds_anticancer_guideline_ko.pdf, 05_mfds_ich_gcp_ko.pdf | 제공된 문서들에는 무작위배정 대조 임상시험에서 1차 평가변수 영상 판독자가 무엇에 대해 눈가림되어야 하는지에 대한 FDA의 구체적인 기대 사항은 |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 관행의 영상 처리 표준만으로도 충분할 수 있는 임상시험의 영상 기반 1차 평가 변수의 경우, 해당 결과가 임상 사이트 간에  |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로로 인한 이미지 해석 품질 저하는 임상 의학에서 보고된 바 있습니다 [5], [1]입니다. 따라서 차터 개발 시에는 판독자 피로의 가 |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 데이터 잠금(locking data)은 이미지 평가가 허용되지 않는다는 것을 의미합니다 [1]. 데이터 잠금은 이미지 판독 과정 중 미리 정해진 |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | MODEL_REFUSED | N | N | - | 제공된 문서에서는 ICH E6(R3)에 따른 시험자가 임상시험계획서에서 벗어날 수 있는 경우에 대한 정보를 확인할 수 없습니다. |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | ICH E6(R3)에 따라 시험책임자/시험기관은 해당 규제 요건에 따라 필수 기록을 보관해야 하며, 또는 의뢰자가 해당 기록이 더 이상 필요하지 |
| p12 | cross_language | ko | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf | 제공된 문서에는 ICH E6(R3)에 대한 정보가 포함되어 있지 않으며, 시험기관 모니터링 활동의 빈도를 결정하는 근거에 대해서도 명시되어 있지 |
| p13 | factual | en | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf | 제공된 문서에는 ICH E6(R3)에 대한 정보가 포함되어 있지 않습니다. 다만, 모니터링과 관련하여, 방문 모니터링은 임상시험이 진행되는 임상 |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링은 현장 모니터링을 보완하고 그 범위나 빈도를 줄이는 데 도움이 될 수 있으며, 단독으로 사용될 수도 있습니다 [3]. 중앙 모니터 |
| p15 | cross_language | ko | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf, 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에서는 ICH E6(R3)에 대한 정보는 확인할 수 없으나, 임상시험이 중지된 경우 임상시험책임자는 중지된 시점까지 진행된 시험 데이 |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | ICH E6(R3)에 따르면, IRB/IEC는 최소 5명의 위원으로 구성되는 것이 권장됩니다 [4]. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 세포독성 화합물(cytotoxic compounds)의 임상 2상 단일제 치료 탐색 연구에서 ORR은 국제 표준(예: RECIST, Volume |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에 따르면, 최대내약용량(MTD)은 일반적으로 6명의 시험대상자 중 적어도 2명에서 용량제한독성(DLT)이 나타나는 용량 |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 최초 인간 투여 시, 정맥 투여는 생체이용률에 따른 변화를 배제할 수 있기 때문에 권장됩니다 [2]. 또한, 정맥 투여는 생체이용률과 관련된 변 |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 이전 치료의 TTP와 시험약의 PFS를 비교하는 외부 대조군 분석의 잠재적 편향과 이질성을 줄이기 위해, 이전 치료와 시험 치료를 받은 조건이  |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA(체표면적) 기반 용량 설정에 대한 과학적 근거는 전반적으로 약하며, 이는 높은 BSA를 가진 환자에게는 과소 노출, 낮은 BSA를 가진  |
| p22 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생하여 재투여하는 경우, 환자가 회복될 때까지 기다린 후에는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 다음과 같습니다:   1. 정해진 투여 일정과 투여 방법에 따라 최대내약용 |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 독성은 일반적으로 인정되는 시스템, 예를 들어 미국 국립암연구소(National Cancer Institute)의 이상반응에 대한 일반용어기준( |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제의 음식-약물 상호작용 시험은 임상시험 이전에 수행되어야 합니다 [1]. 또한, 다른 가이드라인에 따르면 3상 임상시험 이전에 음식 상호작 |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR(초기 불일치율)과 LDR(후기 불일치율)은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1] |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 맹검된 독립적 중앙평가(BICR)는 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1]. 또한, 사건의 |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험에서 일반적으로 1차 평가변수는 전체 반응률(Overall Response Rate, ORR)로 설정합니다 [1]. |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 아니요, 우산형 임상시험에서는 시험약물 간의 비교는 권장되지 않습니다. 유효성의 비교 분석은 시험약물과 공통 대조군 간에 수행되어야 합니다. |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 시기 사이의 계획되지 않은 평가에서 진행이 확인된 경우, 1차 분석 목적에서 진행일은 평가가 예정된 시점이 아니라 진행이 확인된 시 |
| p31 | cross_doc | ko | MODEL_REFUSED | Y | N | - | 문서에서 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대한 식약처 가이드라인과 EMA 가이드라인의 내용은 확인할 수 없습 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 시험책임자/임상시험실시기관은 해당 기관의 모든 시험대상자에 대해 모든 관찰결과를 포함하여 적절하고 정확한 근거문서와 임상시험 관련 기록을 유지해 |
| p33 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 의뢰자는 확인된 위험요소를 평가할 때 다음 세 가지 사항을 고려해야 합니다: (a) 오류 발생 가능도 [1], [2], [3]; (b) 해당 오 |
| p34 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(predefined quality tolerance limit)로부터 일탈(deviation)이 감지되면, 조치(a |
| p35 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐CT 영상 분석 관련 소프트웨어의 안전성·유효성 평가를 위한 임상시험은 다기관, 후향적, 우월성 확증 임상시험으로 설계할 수 있습니다 [4]. |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐결절이 있는 것으로 확인된 상당수의 증례(3000증례 이상) 중에서 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터를 1:2의 비율로  |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 수행합니다 [2]. AUC는 개별  |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다. [2] |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 디지털의료기기의 개발 과정 동안 사용된 학습 데이터와 독립성이 유지되어야 합니다 [1]. |
| p40 | cross_language | en | MODEL_REFUSED | N | N | - | 제공된 문서들에서는 MFDS AI 폐결절 프로토콜 예시에 참여하는 판독자의 수나 샘플 판독 기간에 대한 정보를 확인할 수 없습니다. |
| p41 | no_answer | ko | ANSWERED | - | - | 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에서 요구하는 CT slice 간격에 대한 구체적인 수치(mm 이하)는 확인할 수 없습니다. 다만, 임상시험 데이터셋 선정 기준 중  |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD의 경우, 가성진행(pseudoprogression)의 재평가 및 진단을 위해 추적 관찰은 일반적으로 권장되는 6~12주 간격과 달리 4 |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서는 종양 진행(iUPD)의 경우, 환자와 의뢰 의사 모두와 심도 깊고 비판적인 논의를 거쳐야 하며, 주관적인 안정적인 종양 질환 |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에 따라, 다음 추적 관찰 시점에 iUPD가 iCPD로 확인되는 경우는 다음과 같습니다: 표적 병변 합계가 ≥ 5mm 증가했거나,  |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST의 경우, 6~12주 간격으로 정기적인 추적 반응 평가가 권장됩니다 [1]. |
| p46 | cross_language | ko | MODEL_REFUSED | Y | N | - | 제공된 문서에서는 iRECIST에서 환자당 또는 장기당 설정할 수 있는 표적병변의 최대 개수에 대한 구체적인 정보를 확인할 수 없습니다. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 추적 관찰 시, 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우 기본값으로 5 mm를 사용할 수 있습니다 [1]. |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 아니요, iUPD는 iSD, iPR 또는 iCR의 이후 최적 전체 반응을 무효화하지 않습니다 [2]. |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 제공된 문서에 따르면, 면역관문억제제는 가성진행(pseudoprogression)과 같은 비정형적인 반응 양상을 보일 수 있으며, 이는 초기 종 |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi 등은 전이성 흑색종 환자에서 Pembrolizumab(anti-PD-1) 투여 시 초기 가성진행(week 12에 ≥25% 종양 부담 증 |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1–3점은 완전 관해(CR)로 판정됩니다 [2]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4–5점이지만 기저 대비 FDG 섭취가 감소한 경우, 부분 관해(PR)로 분류됩니다 [2]. |
| p55 | cross_language | ko | ANSWERED_PARTIAL | Y | N | 08_recil_vs_lugano_2019.xml | 제공된 문서에서는 RECIL의 minor response(MiR)에 대한 구체적인 기준을 명시하고 있지는 않습니다. 다만, MiR의 가치에 대해 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대한 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR를 PR로 재코딩했을 때, 치료 종료 시점(EOT)의 RECIL과 Lugano 간의 일치도는 90.7%였습니다 (54명 중 49명; $\k |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었으며, Lugano의 경우 평균 판독 시 |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 PET 재구성 설정(반복 횟수 및 서브셋)에 대한 정보는 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 방사선 치료의 영향을 최소화하고 치료 반응 평가의 정확도를 높이기 위해, 방사선 치료 완료 후 약 4주(21–35일) 시점 |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD(예비 진행)는 12주 초기 치료 기간 동안 SPPD가 25% 이상 증가했거나 새로운 조영 증강 병 |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 반응 범주 표(Table 3)에서 2D 측정 기준 부분반응(PR)의 임계값은 '50% 초과 감소'입니다 [1]. |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 제공된 문서에는 RANO 2.0 검토의 표 3에 대한 정보가 포함되어 있지 않아, 진행성 질환을 정의하는 3D 부피 변화에 대해 확인할 수 없습 |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능한 병변(Measurable disease)은 기본적으로 명확하게 경계가 구분된 병변 중 단축 직경이 최소 10 m |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 조영 증강 또는 비조영 증강 종양을 평가할 때, 병변 선택은 최소 2개에서 최대 3개로 제한해야 합니다 [1]. 조영 증강  |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에 따르면, 3D-T1w Pre의 슬라이스 두께 기준은 ≦ 1.5 mm입니다 |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 표준화된 시간 간격(치료 시작 전 14일 이내)을 두고 사전 치료 스캔을 기저선으로 사용하는 것이 권장됩니다 [1]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | ANSWERED | Y | N | 10_midi_deid_report_2023.pdf | MIDI 보고서는 DICOM 영상 비식별화 시, 2002년에 추가된 De-identification Profile을 포함하여, 이후 더 포괄적인 |
| p73 | factual | en | ANSWERED | Y | N | 10_midi_deid_report_2023.pdf | 아니요. 일부에서는 간접 식별자가 두세 개만 있는 경우 통계적 위험 평가가 필요하지 않다고 제안했지만, 전문가들은 그러한 주장의 근거가 없으며  |
| p74 | cross_language | ko | ANSWERED | Y | N | 10_midi_deid_report_2023.pdf | 제공된 문서에서는 MIDI 보고서가 범위 밖(out of scope)으로 둔 원시 데이터(raw data)의 구체적인 예시를 확인할 수 없습니다 |
| p75 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 10_midi_deid_report_2023.pdf | 제공된 문서에서는 MIDI 보고서와 DICOM PS3.15 Annex E 표가 비식별화 후 DICOM IOD 적합성 유지에 대해 각각 어떻게 언 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Basic Profile에서 Patient's Name (0010,0010) 속성은 다음과 같은 속성을 가집니다: Ret |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Instance UID (0020,000D)의 Basic Profile은 'U'이며, Retain UIDs Option은 'K'입니다 |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)의 Basic Profile은 'Z'이며, Retain Long. Full Dates Opt.은 'K'로 |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Institution Name (Tag: (0008,0080))의 경우, Basic Profile은 X/Z/D이며, PS3.6으로부터의 Retd |
| p80 | table_lookup | ko | ANSWERED_PARTIAL | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | 제공된 문서에서 DICOM 비식별화 조치 코드 'X'가 구체적으로 무엇을 의미하는지에 대한 설명은 확인할 수 없습니다. 다만, 'X'는 특정 조 |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (Tag: (0010,1010))는 Basic Profile에서는 'X'로 처리되며, Retain Patient Cha |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (Tag: (0018,1000))의 경우, De-identification Action은 X/Z/D입니다  |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 DICOM PS3.15 Annex E에 규정된 비식별화 영상의 최소 보관 기간에 대한 정보는 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml, 09_rano2_review_2025.xml | iRECIST에 대한 정보는 [2]에서 확인할 수 있습니다. RANO 2.0의 경우, 진행성 질환(PD) 평가와 관련하여 다음과 같은 변경 사항 |
| p85 | cross_doc | en | ANSWERED_PARTIAL | Y | Y | 09_rano2_review_2025.xml | 제공된 문서에서는 RECIL과 RANO 2.0의 2D 기준에 따른 '경미한 반응(minor response)'에 대한 직접적인 비교 정의를 확인 |
| p86 | cross_doc | en | ANSWERED_PARTIAL | Y | N | 01_fda_imaging_endpoint_2018.pdf | 제공된 문서들을 기반으로 EMA 항암제 가이드라인과 FDA 영상 종점 가이드라인 모두 종양 영상에 대한 독립적이거나 중앙 집중식 검토에 대해 구 |
| p87 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인에서는 인간에게 최초 투여 시 정맥투여를 권장하는 이유로, 대부분의 경우 정맥투여가 생체이용률에 따른 변화를 배제할 수 있기 때 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 BICR 판독자를 최소 몇 명으로 구성해야 하는지에 대한 정보는 확인할 수 없습니다. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 제공된 문서들은 임상시험 문서 및 의료영상 업로드 운영 문서에 관한 내용이며, 파이썬 버블 정렬 코드 작성에 대한 정보는 포함하고 있지 않습니다 |
| p99 | out_of_scope | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
