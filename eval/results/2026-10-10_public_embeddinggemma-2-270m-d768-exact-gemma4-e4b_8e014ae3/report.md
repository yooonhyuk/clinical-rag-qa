# RAG Eval Report — public / embeddinggemma-2-270m-d768-exact-gemma4-e4b (2026-10-10T16:42:41)

## Config

- run_at: `2026-10-10T16:42:41`
- label: `embeddinggemma-2-270m-d768-exact-gemma4-e4b`
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
- eval_process_max_rss_mb: `141`
- ollama_version: `0.40.2`
- embedding_model: `embeddinggemma-2:270m`
- embedding_dim: `768`
- embedding_truncate_dim: `None`
- embedding_query_prefix: `task: search result | query: `
- embedding_document_prefix: `title: none | text: `
- hybrid_search: `False`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `-0.15`
- scope_classifier: `embedding`
- scope_margin: `0.0198`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 92.4% |
| Section/page hit@k | 81.0% |
| Citation accuracy (cited files ⊆ gold) | 92.9% |
| Citation location (a cited chunk in gold section/page) | 82.9% |
| Keyword coverage | 88.6% |
| Refusal accuracy (must-refuse) | 95.0% |
| False refusal rate (answerable) | 11.4% |
| Partial answers with caveat (answerable) | 12.7% |
| False refusal if partial = refusal (MVP-1 policy) | 24.1% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 97.1% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 66 |
| Retrieval p95 (ms) | 81 |
| Generation p50 (ms) | 3,000 |
| Generation p95 (ms) | 6,472 |
| Total p50 (ms) | 2,803 |
| Total p95 (ms) | 6,480 |
| Input tokens (total) | 157,938 |
| Output tokens (total) | 9,433 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 60, 'ANSWERED_PARTIAL': 11, 'MODEL_REFUSED': 18, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | 100.0% | - | 14.3% | 71.4% | 4,195 |
| cross_language | 25 | 84.0% | 76.0% | 90.9% | 90.9% | - | 12.0% | 12.0% | 3,469 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 94.4% | 86.1% | 94.1% | 82.4% | - | 5.6% | 5.6% | 3,386 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 1,971 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 1,214 |
| table_lookup | 11 | 100.0% | 72.7% | 87.5% | 100.0% | - | 27.3% | 0.0% | 2,430 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 92.6% | 74.1% | 95.5% | 81.8% | 100.0% | 18.5% | 7.4% | 3,138 |
| ko | 65 | 92.3% | 84.6% | 91.7% | 91.7% | 92.3% | 7.7% | 15.4% | 2,668 |

## Failed questions

- **p02**: keywords 0%
- **p05**: false refusal (MODEL_REFUSED)
- **p06**: keywords 0%
- **p10**: false refusal (MODEL_REFUSED)
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p13**: false refusal (MODEL_REFUSED)
- **p14**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p15**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']
- **p19**: keywords 0%
- **p24**: section/page miss; keywords 0%
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p31**: false refusal (MODEL_REFUSED)
- **p35**: keywords 0%
- **p40**: false refusal (MODEL_REFUSED)
- **p41**: should refuse but a partial answer
- **p50**: keywords 0%
- **p55**: section/page miss; keywords 0%
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: false refusal (MODEL_REFUSED)
- **p72**: section/page miss; keywords 0%
- **p73**: section/page miss
- **p76**: citation ['10_midi_deid_report_2023.pdf', '11_dicom_ps3.15_annexE_2026d.html']
- **p80**: false refusal (MODEL_REFUSED)
- **p86**: section/page miss

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가변수 가이드라인에 따르면, 해석(case report forms 또는 assessment tabulations)은 원본 자료로  |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 독자들이 이미지를 배치(batches)로 해석하는 경우, 임상시험 문서(charter)에는 배치 크기를 명시하고 해당 배치 크기를 정당화해야 하 |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단되는 경우, 임상시험 문서(프로토콜 및 통계 분석 계획)에 해당 비율 결정 |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 이미징 헌장 지침은 교육 자료(예: 교육 매뉴얼, 교육 이미지), 이미지 표시 교육 세션, 그리고 이미지 판독 테스트 과정을 언급합니다  |
| p05 | cross_language | ko | MODEL_REFUSED | N | N | - | 제공된 문서에서는 무작위배정 대조 임상시험에서 1차 평가변수 영상 판독자가 구체적으로 무엇에 대해 눈가림(blind)되어야 하는지에 대한 FDA |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 관행의 영상 처리 표준만으로도 충분할 수 있는 임상시험의 영상 기반 1차 평가 변수의 경우, 해당 결과가 임상 사이트 간에  |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로로 인한 이미지 해석 품질 저하는 임상 의학에서 보고된 바 있습니다 [1], [4]입니다. 따라서, 임상시험에서 판독자 피로의 가능성 |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 데이터 잠금(Locking data)이란, 이미지 검토 과정 중 미리 정해진 시점에 판독자(readers)가 생성한 이미지 해석 데이터(케이스  |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | MODEL_REFUSED | N | N | - | 제공된 문서에서는 ICH E6(R3)에 따른 시험자가 임상시험계획서에서 벗어날 수 있는 경우에 대한 내용은 확인할 수 없습니다. |
| p11 | factual | en | ANSWERED_PARTIAL | Y | Y | 02_ich_e6r3_2025.pdf | 시험자/임상시험실시기관은 해당 규제 요건에 따라 또는 의뢰자가 해당 기록이 더 이상 필요하지 않다고 통보할 때까지, 두 기간 중 더 긴 기간 동 |
| p12 | cross_language | ko | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf | 제공된 문서에는 ICH E6(R3)에 대한 정보는 포함되어 있지 않으며, 시험기관 모니터링 활동의 빈도를 결정하는 근거에 대해서도 명확하게 언급 |
| p13 | factual | en | MODEL_REFUSED | N | N | - | 제공된 문서에는 ICH E6(R3)에 대한 정보가 포함되어 있지 않아, 현장 모니터링을 누가 수행해야 하는지에 대해 확인할 수 없습니다. |
| p14 | factual | en | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링은 방문 모니터링의 범위나 빈도를 줄이고 보완할 수 있는 추가적인 모니터링 기능을 제공하며, 신뢰할 수 있는 데이터와 잠재적으로 신 |
| p15 | cross_language | ko | ANSWERED_PARTIAL | N | N | 05_mfds_ich_gcp_ko.pdf, 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에서는 ICH E6(R3)에 대한 정보는 확인할 수 없으나, 임상시험이 완료(조기종료 포함)된 후 확보해야 하는 기본문서의 종류 및  |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | ICH E6(R3)에 따르면, IRB/IEC는 최소 5명의 위원으로 구성되어야 합니다 [3]. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 세포독성 화합물의 임상 2상 단일제 치료 탐색 연구에서 ORR(Objective Response Rate)은 국제 표준(예: RECIST, Vo |
| p18 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에 따르면, 최대내약용량(MTD)은 일반적으로 6명의 시험대상자 중 적어도 2명에서 용량제한독성(DLT)이 나타나는 용량 |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | EMA 가이드라인에 따르면, 인간에게 최초 투여 시 정맥 투여가 가능한 경우 가장 바람직합니다. 이는 생체이용률과 관련된 변동성을 제거하기 때문 |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 이전 치료의 TTP와 시험약의 PFS를 비교하는 외부 대조 분석의 설득력을 높이기 위해서는, 이전 치료와 시험 치료를 받은 조건들이 전반적으로  |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA(체표면적) 기반 용량 설정에 대한 과학적 근거가 전반적으로 약하며, 이는 높은 BSA를 가진 환자에게는 과소 노출, 낮은 BSA를 가진  |
| p22 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생한 경우, 환자가 회복될 때까지 기다린 후 재투여할 때는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 다음과 같습니다:   *   정해진 투여 일정과 투여 방법에 따라 최대내약 |
| p24 | factual | ko | ANSWERED_PARTIAL | Y | N | 04_mfds_anticancer_guideline_ko.pdf | 제공된 문서에서는 1상 임상시험의 독성 등급을 매기는 구체적인 기준에 대해서는 확인할 수 없습니다. 다만, 3상 임상시험 계획 시에는 예상되는  |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제의 음식-약물 상호작용 시험은 임상 3상 이전에 수행되어야 합니다 [2]. 또한, 식이 또는 공복 상태의 투여에 대한 합리적인 이유가 제시 |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR(초기 불일치율)과 LDR(후기 불일치율)은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1] |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1], [3]. |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험에서 일반적으로 1차 평가변수는 전체 반응률(Overall Response Rate, ORR)로 설정합니다 [1]. |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 아니요, 우산형 임상시험에서는 시험약물 간의 비교는 권장되지 않습니다. 유효성의 비교 분석은 시험약물과 공통 대조군 간에 수행되어야 합니다. |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 시기 사이의 계획되지 않은 평가에서 진행이 확인된 경우, 1차 분석 목적에서 진행일은 평가가 예정된 시점이 아니라 진행이 확인된 시 |
| p31 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | 문서에서 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대한 식약처 가이드라인이나 EMA 가이드라인의 구체적인 내용은 확인 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 시험책임자/임상시험실시기관은 해당 기관의 모든 시험대상자에 대해 모든 관찰결과를 포함하여 적절하고 정확한 근거문서와 임상시험 관련 기록을 유지해 |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자가 확인된 위험요소를 평가할 때 고려해야 하는 세 가지 사항은 다음과 같습니다: 1. 오류 발생 가능도(The likelihood of e |
| p34 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(predefined quality tolerance limit)로부터 일탈(deviation)이 감지되면, 조치(a |
| p35 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐CT 영상 분석 관련 소프트웨어의 안전성 및 유효성 평가를 위한 임상시험 설계는 다기관, 후향적, 우월성 확증 임상시험입니다 [4]. |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐결절 AI 임상시험 예시에서는 폐결절이 있는 것으로 확인된 상당수의 증례(3000증례 이상) 중에서 폐암 확진 환자 데이터와 양성 폐결절 확진 |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 판독을 수행하며, 개별 판독 후 참 |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다. [2] |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 디지털의료기기의 개발 과정에서 사용된 학습 데이터와 독립성이 유지되어야 합니다 [1]. |
| p40 | cross_language | en | MODEL_REFUSED | Y | Y | - | 제공된 정보에 따르면, 임상시험용 디지털의료기기의 사용 전/후 비교 시, 사용 전에는 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임 |
| p41 | no_answer | ko | ANSWERED_PARTIAL | - | - | 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에서 요구하는 CT slice 간격에 대한 구체적인 수치(예: OOmm 이하)는 확인할 수 없습니다. 다만, 임상시험 데이터셋 선정  |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD의 경우, 가성진행(pseudoprogression)의 재평가 및 진단을 위한 추적 관찰은 일반적으로 권장되는 6–12주 간격과 달리 4 |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 미확정 진행(iUPD)으로 판정하는 조건은 다음 중 하나가 충족될 때입니다: 1) 모든 표적 병변(TL)의 합이 가장 낮은 T |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD가 다음 추적 관찰에서 iCPD로 확진되는 경우는 다음과 같습니다: 표적 부위 합계가 (Nadir 시점 대비) $\ge 5 \text{  |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST의 경우, 6~12주 간격으로 정기적인 추적 반응 평가가 권장됩니다 [1]. |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 표적병변은 환자당 최대 5개까지, 그리고 장기당 최대 2개까지 정의할 수 있습니다. 흉부나 신장과 같은 짝을 이루는 장기 또는 |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 추적 관찰 시, 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우 기본값으로 5 mm를 사용할 수 있습니다 [1]. |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 아니요, iUPD는 iSD, iPR 또는 iCR의 이후 최적 전체 반응을 덮어쓰지 않습니다 [1]. |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 제공된 문서에서는 iRECIST가 면역항암제 투여 후의 반응 평가에 대한 지침을 제공하며, 특히 가성진행(pseudoprogression)의 가 |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi 등은 전이성 흑색종 환자에서 Pembrolizumab(anti-PD-1) 투여 시 초기 가성 진행(week 12에 종양 부담이 $\ge |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1–3점은 완전 관해(CR)로 판정됩니다 [2]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4–5점이지만 기저 대비 FDG 섭취가 감소한 경우 부분 관해(PR)로 분류됩니다 [2]. |
| p55 | cross_language | ko | ANSWERED_PARTIAL | Y | N | 08_recil_vs_lugano_2019.xml | RECIL의 Minor response(MiR)에 대한 구체적인 기준은 문서에서 확인할 수 없습니다. 다만, MiR은 RECIL에서 관찰된 반응 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대한 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR를 PR로 재코딩했을 때, 치료 종료 시점(EOT)의 RECIL과 Lugano 간의 일치도는 90.7%였습니다 (54명 중 49명; κ = |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었으며, Lugano의 경우 평균 판독 시 |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 방사선 치료의 영향을 최소화하기 위해, 기저 스캔을 방사선 치료 완료 후 약 4주(21–35일) 시점으로 설정했습니다 [1 |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD는 다음 중 하나로 정의됩니다: SPPD가 25% 이상 증가했거나 초기 치료 기간 12주 이내에 새 |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0의 2D 측정 기준에서 부분반응(PR)의 임계값은 50% 초과 감소입니다 [1]. |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 제공된 문서에서 RANO 2.0 검토의 표 3(Table 3)에 대한 정보는 확인할 수 없습니다. |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능한 병변은 기본적으로 명확하게 경계가 구분된 병변 중 단축 직경이 최소 10mm 이상인 경우를 의미합니다 [1].  |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 강화되거나 비강화된 종양의 경우, 측정 가능한 병변을 평가할 때 최소 2개에서 최대 3개의 병변을 선택해야 합니다 [1],  |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에 따르면, 3D-T1w Pre의 슬라이스 두께 기준은 ≦ 1.5 mm입니다 |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 표준화된 시간 간격(치료 시작 전 14일 이내)을 두고 사전 치료 스캔을 기저선으로 사용하는 것이 권장됩니다 [1]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | ANSWERED | Y | N | 10_midi_deid_report_2023.pdf | MIDI 보고서는 DICOM 영상 비식별화 시, 비식별화 프로세스를 설명하는 방법으로 DICOM 표준에 포함된 특정 요소들을 언급하고 있으며,  |
| p73 | factual | en | ANSWERED | Y | N | 10_midi_deid_report_2023.pdf | 아니요, 전문가들은 소수의 간접 식별자만 존재할 경우 통계적 위험 평가가 필요 없다는 주장에 근거가 없으며, 항상 적절한 분석을 수행해야 한다고 |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서에서 범위 밖(out of scope)으로 둔 원시 데이터의 예로는 MR k-space, CT 투영(projections), PE |
| p75 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 10_midi_deid_report_2023.pdf | DICOM IOD 적합성 유지에 관하여, MIDI 보고서는 DICOM PS3.15 E.1 애플리케이션 레벨 기밀성 프로파일을 참조하여 비식별화가 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf, 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Basic Profile에서 Patient's Name (0010,0010) 속성은 다음과 같은 속성 정보를 가집니다:  |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Instance UID (0020,000D)의 Basic Profile은 'U'이며, Retain UIDs Option은 'K'입니다 |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)의 경우, Basic Profile은 'Z'로 설정되어 있으며, Retain Long. Full Date |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Institution Name (Tag: (0008,0080))의 경우, Basic Profile은 X/Z/D이며, PS3.6에서 제거(Retd |
| p80 | table_lookup | ko | MODEL_REFUSED | Y | N | - | 제공된 문서에서 'DICOM 비식별화 조치 코드 X'가 무엇을 의미하는지에 대한 정보는 확인할 수 없습니다. |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)의 경우, Basic Profile은 'X'로 처리되며, Retain Patient Characte |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (Tag: (0018,1000))에 대한 Table E.1-1의 기본 프로파일(Basic Prof.)은 X |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 09_rano2_review_2025.xml | iRECIST에서 진행 확인을 위한 추가 스캔 시기에 대한 정보는 문서에서 확인할 수 없습니다. RANO 2.0의 경우, 진행(PD)에 대한 확 |
| p85 | cross_doc | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml, 09_rano2_review_2025.xml | RECIL-2는 'no or minor response'를 MiR, SD, 또는 PD로 정의하며, RECIL-1은 'response'와 'no  |
| p86 | cross_doc | en | ANSWERED_PARTIAL | Y | N | 01_fda_imaging_endpoint_2018.pdf | 제공된 문서들은 EMA 항암 가이드라인에 대해서는 언급하고 있지 않으며, FDA 영상 종점 가이드라인에서 영상 과정(imaging process |
| p87 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 제공된 문서에서는 첫 인체 투여(First-In-Human, FIH) 시 정맥투여를 권장하는 이유에 대해 식약처(MFDS)의 가이드라인만 언급하 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 BICR 판독자에 대한 최소 구성 인원수에 대한 정보는 확인할 수 없습니다. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 제공된 문서들은 임상시험 문서 및 의료영상 업로드 운영 문서에 관한 내용이며, 파이썬 버블 정렬 코드 작성에 대한 정보는 포함하고 있지 않습니다 |
| p99 | out_of_scope | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
