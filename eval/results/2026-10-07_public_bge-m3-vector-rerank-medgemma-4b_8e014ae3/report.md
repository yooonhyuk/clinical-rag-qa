# RAG Eval Report — public / bge-m3-vector-rerank-medgemma-4b (2026-10-07T02:42:45)

## Config

- run_at: `2026-10-07T02:42:45`
- label: `bge-m3-vector-rerank-medgemma-4b`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `b96c482`
- provider: `ollama`
- generator_model: `medgemma:4b`
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
| Citation accuracy (cited files ⊆ gold) | 84.8% |
| Citation location (a cited chunk in gold section/page) | 84.8% |
| Keyword coverage | 91.1% |
| Refusal accuracy (must-refuse) | 75.0% |
| False refusal rate (answerable) | 0.0% |
| Partial answers with caveat (answerable) | 0.0% |
| False refusal if partial = refusal (MVP-1 policy) | 0.0% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 75.0% |
| Answers in Korean (answered) | 69.6% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 2,645 |
| Retrieval p95 (ms) | 3,271 |
| Generation p50 (ms) | 5,854 |
| Generation p95 (ms) | 16,081 |
| Total p50 (ms) | 8,257 |
| Total p95 (ms) | 15,466 |
| Input tokens (total) | 158,991 |
| Output tokens (total) | 9,168 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 0 |

Refusal reasons: {'ANSWERED': 84, 'MODEL_REFUSED': 3, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 71.4% | 100.0% | 100.0% | - | 0.0% | 0.0% | 10,495 |
| cross_language | 25 | 88.0% | 88.0% | 84.0% | 96.0% | - | 0.0% | 0.0% | 7,978 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 97.2% | 91.7% | 77.8% | 88.9% | - | 0.0% | 0.0% | 8,818 |
| no_answer | 7 | - | - | - | - | 42.9% | - | - | 7,441 |
| out_of_scope | 4 | - | - | - | - | 75.0% | - | - | 2,402 |
| table_lookup | 11 | 100.0% | 90.9% | 100.0% | 81.8% | - | 0.0% | 0.0% | 9,806 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 81.5% | 85.2% | 85.7% | 0.0% | 0.0% | 7,398 |
| ko | 65 | 94.2% | 92.3% | 86.5% | 94.2% | 69.2% | 0.0% | 0.0% | 9,120 |

## Failed questions

- **p06**: keywords 0%
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']
- **p11**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p13**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p15**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p16**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p17**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p19**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p22**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p29**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p35**: section/page miss; keywords 0%
- **p41**: should refuse but answered
- **p49**: keywords 0%
- **p52**: should refuse but answered
- **p60**: section/page miss; keywords 0%
- **p65**: section/page miss
- **p71**: should refuse but answered
- **p76**: keywords 0%
- **p79**: keywords 0%
- **p85**: section/page miss
- **p86**: section/page miss
- **p95**: should refuse but answered
- **p98**: should refuse but answered

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가변수 가이드라인에 따르면 영상과 판독 결과 같은 원본 기록은 최소 2년 동안 보관해야 합니다. [1] |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | If readers interpret images in batches, the imaging charter should specify the s |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단되면, 시험 프로토콜과 통계 분석 계획(statistical analysi |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA imaging charter guidance describes the randomization process of image presen |
| p05 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 무작위배정 대조 임상시험에서 1차 평가변수 영상 판독자는 치료 투여 여부에 대해 눈가림되어야 한다고 FDA는 기대한다. |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 실무 영상 표준이 적절한 경우, 긴 뼈 골절이나 뇌출혈과 같이 명백한 결과가 잘 받아들여지고 널리 구현된 영상 방법으로 쉽게 |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 때 FDA는 charter에 판독자가 검토해야 하는 이미지의 최대 수를 지정하도록 고려하라고 합니다. [2] |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 데이터 잠금은 이미징 데이터가 읽기 전에 수정되지 않도록 하는 프로세스입니다. 이는 이미징 데이터가 정확하고 일관되게 기록되도록 보장하는 데 중 |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf, 06_mfds_ai_device_lung_ko.pdf | ICH E6(R3)에 따르면 시험자는 시험대상자에게 즉각적인 위험요소를 제거하기 위해 계획서를 일탈하거나 변경할 수 있습니다. 또한, 시험 진행 |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | According to ICH E6(R3), the investigator/institution should retain the essentia |
| p12 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에서 시험기관 모니터링 활동의 빈도는 시험의 목적, 실시계획, 복잡성, 눈가림, 대상자 수 및 결과변수 등을 고려하여 정해야  |
| p13 | factual | en | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | According to ICH E6(R3), the sponsor should develop a monitoring plan that is ta |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | In ICH E6(R3), centralized monitoring can relate to site monitoring in several w |
| p15 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | 임상시험이 조기 종료되거나 중지되면 시험자/시험기관은 시험대상자에게 알리고 적절한 치료법을 제공하거나 후속조치를 실시해야 하며 규제 당국에도 그 |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에서 IRB/IEC는 최소 5명으로 구성되어야 한다. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | Objective response rate (ORR) should be documented according to international st |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인과 EMA 가이드라인에서 MTD(최대내약용량)는 전통적으로 다음과 같이 정의합니다.  식약처 항암제 가이드라인: 일반적으 |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | EMA 가이드라인은 최초 인간 투여 시 정맥 투여를 권장하는 이유는 생체 이용률에 따른 변화를 배제할 수 있기 때문입니다. [1], [2] |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | EMA 가이드라인에서 이전 치료의 TTP와 시험약의 PFS를 비교하는 환자 내 외부 대조 분석을 더 설득력 있게 만드는 방법은, 이전 치료와 시 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA-scaled dosing에 대한 과학적 지원은 약하며, BSA가 높은 환자에서는 약물의 과다 노출, BSA가 낮은 환자에서는 과소 노출을 |
| p22 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제 1상 시험에서 수용할 만한 독성이 나타난 후 재투여할 때는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. [1], [2] |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 1상 임상시험의 주요 목적은 용량제한독성 및 다음 단계의 임상시험을 위한 적정 용량을 결정하는 것이다. 또한, 정해진 투여 일정과 투여 방법에  |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에서 1상 시험의 독성 등급은 일반적으로 미국 국립암연구소(NCI)의 이상반응에 대한 일반용어기준(Common Termi |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 3 상 임상시험 이전에 음식-약물 간 상호작용 시험이 수행되어야 한다. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | BICR과 현지 시험자 평가의 불일치를 볼 때 쓰는 EDR(early discrepancy rate)과 LDR(late discrepancy r |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 모든 환자의 모든 관련 데이터에 대한 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 통상의 치료효과가 기대되는 경우에 권고됩니다. 사건의  |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형(basket) 임상시험의 1차 평가변수는 일반적으로 전체 반응률(Overall Response Rate, ORR)으로 설정합니다. 개별 |
| p29 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 아니오, 우산형 임상시험에서 시험약물 간의 유효성 비교는 권장되지 않습니다. 우산형 임상시험은 단일 질환의 맥락에서 다양한 시험약물을 연구하기  |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 사이의 계획되지 않은 평가에서 진행이 확인되면, PFS 1차 분석에서 진행일은 평가가 예정된 시점이 아니라 진행이 확인된 시점을 근 |
| p31 | cross_doc | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인과 EMA 가이드라인은 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대한 명확한 기준을 제시하지 않습니다 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | ICH GCP 안내서에 따르면 시험책임자가 유지하는 근거자료(source data)는 출처를 알 수 있고(attributable), 읽기 쉬우며 |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자가 확인된 위험요소를 평가할 때 고려해야 하는 세 가지는 다음과 같습니다. (a) 오류 발생 가능도 (b) 해당 오류를 감지할 수 있는 정 |
| p34 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(quality tolerance limit)에서 일탈이 감지되면, 시험의 통계적 설계 및 변수들의 의료 및 통계적  |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 본 임상시험은 인공지능을 이용하여 폐CT 영상에서 폐암을 검출, 의사의 폐암·폐결절 진단을 보조하는 폐CT 영상 기반 폐암·폐결절 진단 보조 소 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐암 확진 데이터와 양성 폐결절 확진 데이터는 1:2의 비율로 강화 배정(enrichment allocation)을 시행합니다. |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 3명의 판독자가 하고, 각 판독자의 AUC를 산출하여 평균을 기록합니다. [1] |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다. [1] |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 디지털의료기기의 개발 과정 동안 사용된 학습 데이터와의 독립성이 유지되어야 합니다. |
| p40 | cross_language | en | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | MFDS AI lung-nodule protocol example에서, 판독자들은 10일 동안 표본을 적절히 배분하고 판독하여 결과를 기록하도록 |
| p41 | no_answer | ko | ANSWERED | - | - | 06_mfds_ai_device_lung_ko.pdf | CT 영상으로서 다음의 조건을 충족하여야 한다. - OOmm 이하의 CT slice 간격 |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD가 나온 뒤 가성진행 여부를 재평가하는 추적검사는 4-8주 후에 하나요. |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD(미확정 진행)로 판정하는 조건은 다음과 같습니다.  1.  TL(Tumor Load)의 합이 이전 시간점(Nadir) |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD는 4-8주 후의 추적 관찰에서 iCPD로 확인됩니다. iCPD는 추가적인 목표 합(≥ 5mm)의 진행, Non-TL의 추가 진행, 또는 |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 정기적인 반응평가 추적검사 간격으로 권장되는 기간은 6~12주입니다. [1] |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 환자당 최대 5개, 장기당 최대 2개의 표적병변을 정의할 수 있습니다. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 5 mm |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | No, iUPD will not override a subsequent best overall response of iSD, iPR, or iC |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 논문은 면역항암제 투여 후 hyperprogression을 설명하지 않습니다. |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi et al. reported a total pseudoprogression rate of about 7% for pembrolizuma |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | ANSWERED | - | - | 07_irecist_how_to_2020.xml | iRECIST how-to 논문에 보고된 판독자 간 급내상관계수(ICC) 값은 0.86입니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1~3점은 완전관해(CR)로 판정됩니다. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4~5점이지만 기저 대비 FDG 섭취가 감소했다면 partial remission (PR)으로 분류합니다 |
| p55 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 minor response(MiR) 기준은 SLD(sum of the longest diameters of the target le |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL recommends uni-dimensional measurements of up to three target lesions, whi |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | At end-of-treatment, agreement between RECIL and Lugano was 90.7% (49/54 patient |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 판독자 1과 2의 평균 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었고, Lugano의 경우 평균 시간은 1.8  |
| p59 | table_lookup | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Diffuse Large B-Cell Lymphoma (DLBCL): 55.5 ± 17.5 |
| p60 | factual | en | ANSWERED | Y | N | 08_recil_vs_lugano_2019.xml | The RECIL versus Lugano study used 10 iterations and 10 subsets. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 기저(baseline) 스캔은 방사선 치료 종료 후 4주(21–35일) 후에 촬영합니다. |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD(예비 진행)는 12주간의 초기 치료 후, 기존 측정 가능한 병변 중 25% 이상 증가하거나 새로운 |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 2D 측정 기준 부분반응(PR)의 임계값은 50% 이상 감소 |
| p65 | table_lookup | en | ANSWERED | Y | N | 09_rano2_review_2025.xml | According to RANO 2.0, a 40% increase in 3D volume defines progressive disease. |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능 병변의 최소 단축 직경은 10mm이며, 최소 두 개의 2D 슬라이스에 걸쳐 확장되어야 합니다. [1] |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 2개에서 3개의 target lesion을 선택해야 합니다. mixed tumor의 경우, enhancing 및 non-e |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 3D T1 강조영상의 슬라이스 두께는 ≦ 1.5 mm이어야 합니다. |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종에서 RANO 2.0 기저 스캔은 치료 시작 전 14일 이내에 촬영해야 합니다. Ellingson et al.는 재발성 교모세포 |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | ANSWERED | - | - | 09_rano2_review_2025.xml | RANO 2.0에서는 새로운 측정 가능한 덩어리가 있는 경우, 25% 이상의 SPPD 증가 또는 40% 이상의 부피 증가를 기준으로 진행을 정의 |
| p72 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서는 DICOM 영상 비식별화 시 DICOM PS3.15 E.1 Application Level Confidentiality Pro |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | No, the MIDI report does not accept retaining a fixed number of indirect identif |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서가 범위 밖(out of scope)으로 둔 원시 데이터(raw data)의 예는 CT 프로젝션 뷰, MR k-space 데이터, |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서는 비식별화 후 DICOM IOD 적합성을 유지하기 위해, 데이터 요소의 제거, 대체 또는 제거를 포함한 다양한 옵션을 고려해야  |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Name (0010,0010) 속성은 Basic Profile에서 Retd. (from PS3.6): N으로 표시되어 있으며, |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Basic Profile는 Study Instance UID (0020,000D)를 유지 (Retain) 합니다. Retain UIDs Opti |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Basic Profile에서는 Study Date (0008,0020)가 Basic Prof.: Z로 처리됩니다. Retain Longitudi |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Institution Name (0008,0080) is not retired (Retd. (from PS3.6): N). |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM 비식별화 조치 코드 X는 속성을 제거하고, 속성이 시퀀스인 경우 시퀀스 항목과 그에 포함된 속성을 모두 제거합니다. X는 Type 3 |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)는 Basic Profile에서 유지되며, Retain Patient Characteristics  |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | K |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔은 각각 4주 후와 8주 후, 또는 12주 후입니다. RANO 2.0에서는 1 |
| p85 | cross_doc | en | ANSWERED | Y | N | 08_recil_vs_lugano_2019.xml, 09_rano2_review_2025.xml | RECIL-2: "response" (PR or CR) vs. "no or minor response" (MiR, SD, or PD); and  |
| p86 | cross_doc | en | ANSWERED | Y | N | 01_fda_imaging_endpoint_2018.pdf, 03_ema_anticancer_rev6.pdf | EMA anticancer guideline and FDA imaging endpoint guidance both emphasize the im |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처와 EMA 가이드라인은 첫 인체 투여 시 정맥투여를 권장하는 이유는 생체이용률에 따른 변화를 배제할 수 있기 때문이라고 설명합니다. 식약처 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | ANSWERED | - | - | 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인은 BICR 판독자를 최소 30명으로 구성하라고 명시하고 있습니다. [2] |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | ANSWERED | - | - | 11_dicom_ps3.15_annexE_2026d.html | 파이썬으로 버블 정렬 코드는 다음과 같습니다.  ```python def bubble_sort(arr):     n = len(arr)      |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
