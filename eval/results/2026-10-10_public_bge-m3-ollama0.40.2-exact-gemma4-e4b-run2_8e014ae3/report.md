# RAG Eval Report — public / bge-m3-ollama0.40.2-exact-gemma4-e4b-run2 (2026-10-10T16:12:00)

## Config

- run_at: `2026-10-10T16:12:00`
- label: `bge-m3-ollama0.40.2-exact-gemma4-e4b-run2`
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
- eval_process_max_rss_mb: `142`
- ollama_version: `0.40.2`
- embedding_model: `bge-m3`
- embedding_dim: `1024`
- embedding_truncate_dim: `None`
- embedding_query_prefix: ``
- embedding_document_prefix: ``
- hybrid_search: `False`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `0.45`
- scope_classifier: `embedding`
- scope_margin: `0.056`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 96.2% |
| Section/page hit@k | 87.3% |
| Citation accuracy (cited files ⊆ gold) | 85.1% |
| Citation location (a cited chunk in gold section/page) | 91.9% |
| Keyword coverage | 91.9% |
| Refusal accuracy (must-refuse) | 95.0% |
| False refusal rate (answerable) | 6.3% |
| Partial answers with caveat (answerable) | 7.6% |
| False refusal if partial = refusal (MVP-1 policy) | 13.9% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 91.9% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 70 |
| Retrieval p95 (ms) | 84 |
| Generation p50 (ms) | 3,448 |
| Generation p95 (ms) | 8,545 |
| Total p50 (ms) | 3,049 |
| Total p95 (ms) | 8,582 |
| Input tokens (total) | 152,172 |
| Output tokens (total) | 10,107 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 68, 'ANSWERED_PARTIAL': 7, 'MODEL_REFUSED': 12, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | 100.0% | - | 14.3% | 42.9% | 4,885 |
| cross_language | 25 | 88.0% | 80.0% | 83.3% | 91.7% | - | 4.0% | 8.0% | 3,957 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 100.0% | 94.4% | 80.0% | 88.6% | - | 2.8% | 2.8% | 3,688 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 2,351 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 66 |
| table_lookup | 11 | 100.0% | 81.8% | 100.0% | 100.0% | - | 18.2% | 0.0% | 2,487 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 81.8% | 86.4% | 100.0% | 18.5% | 7.4% | 2,802 |
| ko | 65 | 96.2% | 90.4% | 86.5% | 94.2% | 92.3% | 0.0% | 7.7% | 3,049 |

## Failed questions

- **p02**: keywords 0%
- **p06**: keywords 0%
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p11**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p13**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p15**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p19**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p22**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p34**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p35**: section/page miss; keywords 0%
- **p40**: false refusal (MODEL_REFUSED)
- **p41**: should refuse but a partial answer
- **p55**: section/page miss; keywords 0%
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: false refusal (MODEL_REFUSED)
- **p72**: section/page miss; citation ['11_dicom_ps3.15_annexE_2026d.html']; keywords 0%
- **p86**: false refusal (MODEL_REFUSED)

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가 변수 가이드라인에 따르면, 해석(case report forms 또는 assessment tabulations)과 같은 원본  |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 독자들이 이미지를 배치(batches)로 해석하는 경우, 임상시험 문서(charter)에는 배치 크기를 명시하고 해당 배치 크기가 정당화되어야  |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단되는 경우, 임상시험 개발자는 임상시험 문서(프로토콜 및 통계 분석 계획) |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA의 영상 챠터 지침은 독자 훈련 과정에서 독자들에게 제시될 수 있는 몇 가지 측면을 설명합니다. 여기에는 이미지 해석 과정의 주요 목표에  |
| p05 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 무작위 대조 임상시험에서 영상 판독자는 피험자의 치료 배정 정보에 대해 눈가림되어야 한다고 기대됩니다. 이는 배정 정보를 아는 것이 편향을 유발 |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존의 의료 관행 영상 프로세스 표준만으로 임상시험의 1차 영상 종점을 뒷받침하는 경우, 해당 종점이 임상 현장 간에 중요하게 변하지  |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 경우, 개발자는 세션당 읽을 수 있는 최대 이미지 수를 명시할지 여부를 고려해야 합니다 [3]. |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 데이터 잠금(locking data)이란, 이미지 평가가 허용되지 않는 시점을 의미합니다 [1]. 데이터 잠금은 이미지 해석 데이터(케이스 리포 |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면, 시험자는 다음의 경우를 제외하고는 의뢰자 및 IRB/IEC의 사전 검토와 문서화된 승인/우호적 의견 없이는 임상시 |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 임상시험자/기관은 해당 임상시험을 수행하기 전과 수행하는 동안 생성된 모든 필수 기록을 통제해야 하며 [1], 필수 기록은 해당 규제 요건에 따 |
| p12 | cross_language | ko | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R2)의 경우, 모니터링 활동의 범위와 성격은 임상시험의 목적, 목적, 설계, 복잡성, 눈가림(blinding), 규모, 그리고 평 |
| p13 | factual | en | ANSWERED_PARTIAL | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 제공된 문서에는 ICH E6(R3)에 따라 현장(site)에서 모니터링을 수행해야 하는 주체에 대한 직접적인 정보는 포함되어 있지 않습니다. 다 |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링은 현장 모니터링의 정도 및/또는 빈도를 보완하고 감소시킬 수 있는 추가적인 모니터링 기능을 제공하며, 신뢰할 수 있는 데이터와 잠 |
| p15 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면, 임상시험이 조기 종료되거나 중지될 경우 시험자/시험기관은 다음과 같은 조치를 취해야 합니다:  1. **일반적인  |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | ICH E6(R3)에 따르면, IRB/IEC는 최소 5명의 위원으로 구성되는 것이 권장됩니다 [2], [3]. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 사이토톡식 화합물의 임상 2상 단일제 치료 탐색 연구에서 ORR은 국제 표준(예: RECIST, Volumetric RECIST 또는 WHO 기 |
| p18 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 03_ema_anticancer_rev6.pdf | 식약처 항암제 가이드라인에서는 최대내약용량(MTD)에 대한 전통적인 정의를 명시하고 있지는 않으나, EMA 가이드라인에서는 MTD가 '가장 높은 |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 인간에게 최초 투여 시, 생체이용률과 관련된 변동성을 제거할 수 있기 때문에, 가능하다면 정맥투여가 권장됩니다 [1], [4]. |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 이전 치료의 TTP와 시험약의 PFS를 비교하는 외부 대조군 분석의 경우, 잠재적인 편향과 이질성을 줄일 수 있어 더 설득력이 있을 수 있습니다 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA(체표면적) 기반 용량 설정에 대한 과학적 근거는 전반적으로 약하며, 이는 높은 BSA를 가진 환자에게는 과소 노출, 낮은 BSA를 가진  |
| p22 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생하여 재투여하는 경우, 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. [1], [4] |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 다음과 같습니다:   *   정해진 투여 일정과 투여 방법에 따라 최대내약 |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 독성은 일반적으로 인정되는 시스템, 예를 들어 미국 국립암연구소(National Cancer Institute)의 이상반응에 대한 일반용어기준( |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제의 음식-약물 상호작용 시험은 임상시험 이전에 수행되어야 합니다 [1], [2]. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR(초기 불일치율)과 LDR(후기 불일치율)은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1] |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1], [3]. 또한, 사건의 대다수가 임상적 |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험(Basket trial)의 경우, 일반적으로 1차 평가변수는 전체 반응률(Overall Response Rate, ORR)로  |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 아니요, 우산형 임상시험에서 시험약물 간의 유효성 비교는 권장되지 않습니다 [1]. |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 시점이 아닌, 진행이 확인된 시점을 근거로 해야 합니다. 이러한 접근법은 배정된 대로 분석(intention-to-treat, IT |
| p31 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인에 따르면, 수용할 만한 독성이 발생하여 재투여가 가능한 경우, 환자가 회복될 때까지 기다린 후에는 동일 용량으로 최소 2주기  |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | ICH GCP 안내서에 따르면, 시험책임자/임상시험실시기관은 해당 기관의 모든 시험대상자에 대해 모든 관찰결과를 포함하여 적절하고 정확한 근거문 |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자가 확인된 위험요소를 평가할 때 고려해야 하는 세 가지 사항은 다음과 같습니다:  1. 오류 발생 가능도 (The likelihood of |
| p34 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(predefined quality tolerance limit)에서 일탈(deviation)이 감지되면, 조치(ac |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 본 임상시험은 인공지능을 활용하여 폐CT 영상에서 폐암을 검출하고, 의사의 폐암·폐결절 진단을 보조하는 폐CT 영상 기반 폐암·폐결절 진단보조소 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐결절 AI 임상시험 예시에서 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터는 1:2의 비율로 강화 배정(enrichment alloc |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 판독을 수행하며, 개별 판독 후 참 |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성되어야 합니다 [2]. |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋을 선정·배정할 때는 디지털의료기기의 개발 과정에서 사용된 학습 데이터와 독립성이 유지되어야 합니다 [2]. |
| p40 | cross_language | en | MODEL_REFUSED | N | N | - | 문서에서 확인할 수 없습니다. |
| p41 | no_answer | ko | ANSWERED_PARTIAL | - | - | 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에 따르면, CT 영상의 조건 중 하나로 'OOmm 이하의 CT slice 간격'을 충족해야 한다고 명시되어 있으나, 구체적인 수치( |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD의 경우, 가성진행(pseudoprogression)의 재평가 및 진단을 위해 정기적으로 권장되는 6–12주 간격과 달리 4–8주 후에  |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD(미확정 진행)로 판정하는 조건은 다음과 같습니다: 1. 모든 TL의 합이 가장 낮은 TL 합(Nadir) 대비 최소  |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD가 다음 추적 관찰에서 iCPD로 확인되는 경우는, 표적 부위(target sum)의 추가 진행이 있거나(≥ 5 mm), 비표적 부위(N |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 정기적인 추적 반응 평가(follow-up response assessment)는 6~12주 간격으로 권장됩니다 [1]. |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 표적 병변(target lesions)은 환자당 최대 5개까지 정의할 수 있으며, 이 중 각 장기별로는 최대 2개의 병변을 정 |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 추적 관찰 시, 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우 기본값으로 5 mm를 사용할 수 있습니다 [1]. |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 아니요, iUPD는 iSD, iPR 또는 iCR의 이후의 최적 전체 반응을 무효화하지 않습니다 [1]. |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 제공된 문서에서는 iRECIST가 면역항암제 투여 후의 hyperprogression에 대해 구체적으로 설명하고 있지는 않습니다. 다만, 면역체 |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi 등은 Pembrolizumab(anti-PD-1)을 사용한 진행성 흑색종 환자에서 초기 가성진행(week 12에서 ≥25% 종양 부하  |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 점수가 1–3점인 경우, 이는 완전 관해(CR)로 판정됩니다 [2]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4–5점이지만 기저 대비 FDG 섭취가 감소한 경우 부분 관해(PR)로 분류됩니다 [2]. |
| p55 | cross_language | ko | ANSWERED_PARTIAL | Y | N | 08_recil_vs_lugano_2019.xml | 제공된 문서에서는 RECIL의 minor response(MiR)에 대한 구체적인 기준을 명시하고 있지는 않습니다. 다만, MiR은 RECIL에 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대한 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR을 PR로 재코딩했을 때, 치료 종료 시점(EOT)의 RECIL과 Lugano 간의 일치도는 90.7%였습니다 [2]. |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었으며, Lugano의 경우 평균 판독 시 |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 방사선 치료 종료 후 약 4주(21–35일) 시점을 기저 스캔으로 설정하여, 주로 PsP(가성진행)의 영향을 최소화하는 것 |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD는 다음 중 하나로 정의됩니다: SPPD(Specific Progressive Disease)가 2 |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0의 2D 측정 기준에서 부분반응(PR)의 임계값은 50% 초과 감소입니다 [1]. |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 제공된 문서에서 RANO 2.0 검토의 표 3(Table 3)에 따른 진행성 질환(PD)을 정의하는 3D 부피 변화에 대한 정보는 확인할 수 없 |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능한 병변(Measurable disease)은 기본적으로 명확하게 경계가 구분되는 병변이며, 최소 단축 직경이 10 |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 조영 증강 또는 비조영 증강 종양을 평가할 때, 병변 선택은 최소 2개에서 최대 3개로 제한해야 합니다 [1]. 혼합 종양(enhancing 및 |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에 따르면, 3D-T1w Pre의 슬라이스 두께(Slice Thickness |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 치료 시작 전 표준화된 시간 간격(14일 이내)으로 사전 스캔을 기저 스캔으로 사용해야 합니다 [2]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | ANSWERED | Y | N | 11_dicom_ps3.15_annexE_2026d.html | 제공된 문서에서 MIDI 보고서가 DICOM 영상 비식별화 시 특정 표준 프로파일을 기준으로 삼으라고 명시적으로 권고하는 내용은 확인할 수 없습 |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | 아니요, 임의의 유한한 개수 또는 지정된 하위 집합의 간접 식별자를 위험 분석 없이 유지하는 것은 허용되지 않습니다 [5]. |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서에서 범위 밖(out of scope)으로 둔 원시 데이터의 예로는 MR k-space, CT 투영(projections), PE |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서에 따르면, 어떤 접근 방식(규칙 기반 또는 통계적)을 선택하든, 텍스트를 정리하거나 제거하거나 대체하는 경우에도 인코딩된 DIC |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Basic Profile에서 Patient's Name (0010,0010) 속성은 다음과 같이 처리됩니다: *   ** |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Instance UID (0020,000D)의 Basic Profile은 'U'이며, Retain UIDs Option은 'K'입니다 |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)의 Basic Profile은 'Z'이며, Retain Long. Full Dates Opt.은 'K'로 |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Institution Name (태그: (0008,0080))의 경우, Basic Profile은 X/Z/D이며, Rtn. Inst. Id. O |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | 조치 코드 X는 속성(Attribute)을 제거하며, 만약 해당 속성이 시퀀스(Sequence)인 경우 모든 시퀀스 항목과 그 안에 포함된 속성 |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (Tag: (0010,1010))는 Basic Profile에서는 'X'로 처리되며, Retain Patient Cha |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (0018,1000)에 대한 Table E.1-1의 Basic Profile 값은 X/Z/D입니다. [2] |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 09_rano2_review_2025.xml | 제공된 문서에는 iRECIST와 RANO 2.0에서 진행(PD)을 확인하기 위한 추가 스캔 시점에 대한 직접적인 비교 정보는 포함되어 있지 않습 |
| p85 | cross_doc | en | ANSWERED_PARTIAL | Y | Y | 09_rano2_review_2025.xml | 제공된 문서에서는 RECIL과 RANO 2.0 (2D)이 'minor response'를 어떻게 정의하는지에 대한 직접적인 비교 정보는 확인할  |
| p86 | cross_doc | en | MODEL_REFUSED | Y | N | - | 제공된 문서들에는 EMA 항암 가이드라인과 FDA 영상 종점 가이드라인 모두에서 종양 영상에 대한 독립적 또는 중앙 집중식 검토에 대해 명시적으 |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인에서는 인간에게 최초 투여 시 정맥투여를 권장하는 이유로, 대부분의 경우 정맥투여가 생체이용률에 따른 변화를 배제할 수 있기 때 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 제공된 문서에서 식약처 항암제 가이드라인이 BICR(Breast Cancer Imaging Reviewer 또는 유사한 약어) 판독자의 최소 인 |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 제공된 문서들은 DICOM 표준 및 데이터 요소 속성에 대한 정보를 포함하고 있으며, 파이썬 코드를 작성하는 내용과는 관련이 없습니다. 따라서  |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
