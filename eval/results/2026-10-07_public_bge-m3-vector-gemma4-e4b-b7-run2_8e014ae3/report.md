# RAG Eval Report — public / bge-m3-vector-gemma4-e4b-b7-run2 (2026-10-07T02:04:27)

## Config

- run_at: `2026-10-07T02:04:27`
- label: `bge-m3-vector-gemma4-e4b-b7-run2`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `b96c482`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `none`
- partial_answers: `True`
- eval_process_max_rss_mb: `155`
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
| Retrieval hit@k (file) | 96.2% |
| Section/page hit@k | 87.3% |
| Citation accuracy (cited files ⊆ gold) | 87.5% |
| Citation location (a cited chunk in gold section/page) | 93.1% |
| Keyword coverage | 93.1% |
| Refusal accuracy (must-refuse) | 95.0% |
| False refusal rate (answerable) | 8.9% |
| Partial answers with caveat (answerable) | 8.9% |
| False refusal if partial = refusal (MVP-1 policy) | 17.7% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 94.4% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 113 |
| Retrieval p95 (ms) | 126 |
| Generation p50 (ms) | 6,793 |
| Generation p95 (ms) | 11,409 |
| Total p50 (ms) | 6,641 |
| Total p95 (ms) | 11,476 |
| Input tokens (total) | 151,950 |
| Output tokens (total) | 9,259 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 65, 'ANSWERED_PARTIAL': 8, 'MODEL_REFUSED': 14, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | 100.0% | - | 14.3% | 42.9% | 8,574 |
| cross_language | 25 | 88.0% | 80.0% | 86.4% | 95.5% | - | 12.0% | 8.0% | 6,229 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 100.0% | 94.4% | 82.9% | 88.6% | - | 2.8% | 2.8% | 7,194 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 4,509 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 123 |
| table_lookup | 11 | 100.0% | 81.8% | 100.0% | 100.0% | - | 18.2% | 9.1% | 7,091 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 86.4% | 86.4% | 100.0% | 18.5% | 7.4% | 5,990 |
| ko | 65 | 96.2% | 90.4% | 88.0% | 96.0% | 92.3% | 3.8% | 9.6% | 6,801 |

## Failed questions

- **p02**: keywords 0%
- **p06**: keywords 0%
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p11**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p12**: false refusal (MODEL_REFUSED)
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p15**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p16**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
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
- **p72**: false refusal (MODEL_REFUSED)
- **p86**: false refusal (MODEL_REFUSED)

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가 변수 가이드라인에 따르면, 해석(case report forms 또는 assessment tabulations)과 같은 원본  |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 독자들이 이미지를 배치(batches)로 해석하는 경우, 임상시험 문서(charter)에는 배치 크기를 명시하고 해당 배치 크기를 정당화해야 합 |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단될 경우, 임상시험 개발자는 임상시험 프로토콜 및 차터/지원 문서에 이 비 |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 이미징 헌장 지침은 독자에게 제공되는 이미지 제시 방식에 대해 다음과 같은 내용을 설명합니다:  *   **훈련 자료:** 훈련 매뉴얼, |
| p05 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 무작위 대조 임상시험에서 영상 기반 1차 평가변수를 사용하는 경우, 임상시험의 1차 평가변수 영상 판독자는 피험자의 치료 배정 정보에 대해 눈가 |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 관행 영상 표준이 적절할 수 있는 임상시험 종점의 경우, 임상시험 종점 측정 또는 결과가 임상 현장에서 획득, 표시 및 해석 |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 경우, 개발자는 세션당 최대 판독 이미지 수를 지정할지 여부를 고려해야 합니다 [3]. |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 임상시험 문서에서 '데이터 잠금(data locking)'은 이미지 평가가 더 이상 허용되지 않는 시점을 의미합니다 [1]. 이 과정은  |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면, 시험자는 다음의 경우에 한하여 임상시험 계획서에서 벗어나거나 변경할 수 있습니다 [4.5.2].  1. 시험대상자 |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 임상시험 책임자/기관은 해당 규제 요건에 따라 필수 기록을 보유해야 하며, 의뢰자가 해당 기록이 더 이상 필요하지 않다고 통보할 때까지 또는 그 |
| p12 | cross_language | ko | MODEL_REFUSED | N | N | - | ICH E6(R3)에 대한 정보는 문서에서 확인할 수 없습니다. |
| p13 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | ICH E6(R3)에 따르면, 모니터링은 임상시험실시기관에서 수행되는 임상시험 활동과 관련하여 수행될 수 있습니다 [3]. 모니터링 활동의 빈도 |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링은 현장 모니터링의 정도 및/또는 빈도를 보완하고 감소시킬 수 있는 추가적인 모니터링 역량을 제공하며, 신뢰할 수 있는 데이터와 잠 |
| p15 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면, 임상시험이 조기 종료되거나 중지될 경우 시험자/시험기관은 상황별로 다음과 같은 조치를 취해야 합니다.  1. ** |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면, IRB/IEC는 과학적, 의학적, 윤리적 측면을 검토하고 평가할 수 있는 자격과 경험을 종합적으로 갖춘 적절한 수 |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 세포독성 화합물(cytotoxic compounds)의 임상 2상 단일제 탐색 연구에서 ORR(Objective Response Rate)은 국 |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에서는 최대내약용량(MTD)을 일반적으로 6명의 시험대상자 중 적어도 2명에서 용량제한독성(DLT)이 나타나는 용량으로  |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | EMA 가이드라인은 인간에게 최초 투여(first-in-man) 시 정맥투여가 가능한 경우, 생체이용률에 따른 변화를 배제할 수 있기 때문에 권 |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 이전 치료의 TTP와 시험약의 PFS를 비교하는 외부 대조 분석을 더 설득력 있게 만들기 위해서는, 이전 치료와 시험 치료가 제공된 전반적인 조 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA(Body Surface Area) 기반 용량 설정에 대한 과학적 근거는 약하며, 이는 높은 BSA를 가진 환자에게는 과소 노출, 낮은 B |
| p22 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생한 경우, 환자가 회복될 때까지 기다린 후 재투여할 때는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. [ |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 다음과 같습니다 [1]:  *   정해진 투여 일정과 투여 방법에 따라 최 |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 독성은 일반적으로 인정되는 시스템(예: 미국 국립암연구소[National Cancer Institute]의 이상반응에 대한 일반용어기준[Comm |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제의 음식-약물 상호작용 시험은 3상 임상시험 이전에 수행되어야 합니다 [1], [2]. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR(초기 불일치율)과 LDR(후기 불일치율)은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1] |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1], [3]. 또한, 사건의 대다수가 임상적 |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험에서 1차 평가변수는 일반적으로 전체 반응률(Overall Response Rate, ORR)로 설정합니다 [1]. |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 아니요, 우산형 임상시험에서 시험약물 간의 유효성 비교는 권장되지 않습니다. [1] |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 시점이 아닌, 진행이 확인된 시점을 근거로 진행일을 설정해야 합니다. 이러한 접근법은 배정된 대로 분석(intention-to-tr |
| p31 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 제공된 문서에서 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대한 식약처(MFDS) 가이드라인과 EMA 가이드라인을 명확 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | ICH GCP 안내서에 따르면, 시험책임자/임상시험실시기관이 유지하는 근거자료(source data)는 다음과 같은 특성을 갖추어야 합니다:   |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자가 확인된 위험요소를 평가할 때 고려해야 하는 세 가지 사항은 다음과 같습니다:  1. 오류 발생 가능도 (The likelihood of |
| p34 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(predefined quality tolerance limit)에서 일탈(deviation)이 감지되면, 조치(ac |
| p35 | factual | ko | ANSWERED_PARTIAL | Y | N | 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에는 폐CT 기반 폐암·폐결절 진단보조 소프트웨어 임상시험계획서의 구체적인 연구 설계에 대한 정보는 명시되어 있지 않습니다. 다만,  |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐결절 AI 임상시험 예시에서는 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터의 비율을 1:2로 강화 배정(enrichment allo |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 판독 수행하며, 개별 판독 후 참조 |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | AI 의료기기 임상시험에서 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성되어야 합니다 [2]. |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋을 선정·배정할 때는 디지털의료기기의 개발 과정에서 사용된 학습 데이터와 독립성을 유지해야 합니다. [2] |
| p40 | cross_language | en | MODEL_REFUSED | N | N | - | 제공된 문서에서는 MFDS AI 폐 결절 프로토콜 예시에 참여하는 판독자 수나 샘플 판독 기간에 대한 정보를 확인할 수 없습니다. |
| p41 | no_answer | ko | ANSWERED_PARTIAL | - | - | 06_mfds_ai_device_lung_ko.pdf | 제공된 문서에서 AI 폐암·폐결절 임상시험 가이드라인 예시가 요구하는 CT slice 간격에 대한 구체적인 수치(mm 이하)는 확인할 수 없습니 |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD가 확인된 경우, 가성진행(pseudoprogression)의 재평가를 위한 추적검사는 일반적으로 권장되는 6~12주 간격과 달리 4~8 |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 미확정 진행(iUPD)으로 판정하는 조건은 다음과 같습니다. 첫째, 모든 표적 병변(TL)의 합이 가장 낮은 TL 합(Nadi |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD가 확인된 후, 다음 추적 관찰에서 iCPD로 확정되는 경우는 다음 중 하나가 있을 때입니다: 표적 합(target sum)의 추가 진행 |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 정기적인 반응평가 추적검사는 6~12주 간격으로 권장됩니다. [1] |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 표적 병변(target lesions)은 환자당 최대 5개까지, 그리고 장기당 최대 2개까지 정의할 수 있습니다 [1]. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 추적 관찰 시, 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우 기본값으로 5 mm를 사용할 수 있습니다. [1] |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 아니요, iUPD는 iRECIST에서 후속 최적 전체 반응(iSD, iPR, 또는 iCR)을 무효화할 수 없습니다. iUPD는 iSD, iPR, |
| p49 | cross_language | ko | ANSWERED_PARTIAL | Y | Y | 07_irecist_how_to_2020.xml | 제공된 문서에서 iRECIST가 면역항암제 투여 후 hyperprogression을 구체적으로 설명하는 내용은 확인할 수 없습니다. 다만, 면역 |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi 등은 펨브롤리주맙(Pembrolizumab)을 사용한 진행성 흑색종 환자에서 초기 가성 진행(week 12에서 ≥25% 종양 부하 증가 |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 점수가 1~3점인 경우, 완전 관해(CR)로 판정합니다 [2]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4–5점이지만 기저 대비 FDG 섭취가 감소했다면 부분 관해(PR)로 분류됩니다 [2]. |
| p55 | cross_language | ko | ANSWERED_PARTIAL | Y | N | 08_recil_vs_lugano_2019.xml | 제공된 문서에는 RECIL의 minor response(MiR)에 대한 구체적인 기준은 명시되어 있지 않습니다. 다만, MiR은 RECIL의 임 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대한 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR을 PR로 재코딩했을 때, 치료 종료 시점(EOT)에서 RECIL과 Lugano 간의 일치도는 90.7%였습니다 [2], [4]. |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었으며, Lugano의 경우 평균 판독 시 |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 방사선 치료 종료 후 약 4주(21–35일) 시점에 후방사선 치료 MRI를 기저 스캔으로 설정하여, PsP(가성 진행)의  |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD(예비 진행)는 다음 두 가지 조건 중 하나로 정의됩니다: 12주 이내 초기 치료 기간 동안 SPP |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 반응 범주 표(Table 3)에서 2D 측정 기준 부분반응(PR)의 임계값은 '50% 초과 감소'입니다 [1]. |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 제공된 문서에는 RANO 2.0 검토의 표 3(Table 3)에 따른 진행성 질환(PD)을 정의하는 3D 부피 변화에 대한 정보가 없습니다. |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능한 병변(Measurable disease)은 기본적으로 최소 단축 직경이 10mm인, 명확하게 경계가 구분된 병변 |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 조영 증강 종양 또는 비조영 증강 종양을 평가할 때는 최소 2개에서 최대 3개의 병변을 선택해야 합니다 [1]. 혼합 종양( |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에 따르면, 3D-T1w Pre의 슬라이스 두께(Slice Thickness |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 치료 시작 전 표준화된 시간 간격(14일 이내)으로 사전 스캔을 기저 스캔으로 사용해야 합니다 [2]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | MODEL_REFUSED | Y | N | - | 제공된 문서에서는 MIDI 보고서가 DICOM 영상 비식별화 시 특정 표준 프로파일을 기준으로 삼으라고 권고하는 내용은 확인할 수 없습니다. |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | 아니요, 위험 분석 없이 고정된 수의 간접 식별자를 보유하는 것은 허용되지 않습니다. 위험 분석은 데이터 요소가 선택적으로 유지되거나 제거되는  |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서에서 범위 밖(out of scope)으로 둔 원시 데이터의 예로는 MR k-space, CT 투영(projections), PE |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf, 11_dicom_ps3.15_annexE_2026d.html | MIDI 보고서에 따르면, 어떤 접근 방식(규칙 기반 또는 통계적)을 선택하든, 인코딩된 DICOM 이미지가 DICOM 표준의 적합성을 유지하는 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Basic Profile에서 Patient's Name (0010,0010) 속성은 Standard Composition |
| p77 | table_lookup | en | ANSWERED_PARTIAL | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Instance UID (0020,000D)의 Basic Profile은 'U'이며, 이는 'Unique'를 의미합니다 [2]. 이  |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)의 경우, Basic Profile은 'Z'로 설정되어 있으며 [2], Retain Longitudina |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM Basic Application Level Confidentiality Profile에 따르면, Institution Name (00 |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM 비식별화 조치 코드 X는 속성(Attribute)을 제거하며, 만약 해당 속성이 시퀀스(Sequence)인 경우 모든 시퀀스 항목과  |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)는 Basic Profile에서는 'X'로 처리되며, Retain Patient Characteri |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (0018,1000)에 대한 Table E.1-1의 기본 프로파일(Basic Prof.)은 X/Z/D입니다 |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED_PARTIAL | Y | Y | 09_rano2_review_2025.xml | 제공된 문서에는 iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔 시점에 대한 정보가 없습니다. 다만, RANO 2.0의 경우 |
| p85 | cross_doc | en | ANSWERED_PARTIAL | Y | Y | 09_rano2_review_2025.xml | 제공된 문서에서 RECIL과 RANO 2.0 (2D)이 '경미한 반응(minor response)'을 어떻게 정의하는지에 대한 직접적인 비교 정 |
| p86 | cross_doc | en | MODEL_REFUSED | Y | N | - | 제공된 문서들에는 종양 영상에 대한 독립적 또는 중앙 집중식 검토에 관한 EMA 항암제 가이드라인이나 FDA 영상 종점 가이드라인의 내용이 포함 |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인은 인간에게 최초 투여 시 정맥투여를 권장하는 이유로, 생체이용률에 따른 변화를 배제할 수 있기 때문이라고 설명합니다 [1].  |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 제공된 문서에는 식약처 항암제 가이드라인이 BICR 판독자를 최소 몇 명으로 구성해야 하는지에 대한 정보가 없습니다. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
