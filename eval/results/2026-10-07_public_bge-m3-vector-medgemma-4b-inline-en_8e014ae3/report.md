# RAG Eval Report — public / bge-m3-vector-medgemma-4b-inline-en (2026-10-07T09:25:01)

## Config

- run_at: `2026-10-07T09:25:01`
- label: `bge-m3-vector-medgemma-4b-inline-en`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `05ebae8`
- provider: `ollama`
- generator_model: `medgemma:4b`
- reranker: `none`
- partial_answers: `True`
- rag_prompt_variant: `inline-en`
- eval_process_max_rss_mb: `153`
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
| Citation accuracy (cited files ⊆ gold) | 76.6% |
| Citation location (a cited chunk in gold section/page) | 70.1% |
| Keyword coverage | 88.3% |
| Refusal accuracy (must-refuse) | 90.0% |
| False refusal rate (answerable) | 2.5% |
| Partial answers with caveat (answerable) | 0.0% |
| False refusal if partial = refusal (MVP-1 policy) | 2.5% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 90.0% |
| Answers in Korean (answered) | 62.3% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 122 |
| Retrieval p95 (ms) | 178 |
| Generation p50 (ms) | 6,150 |
| Generation p95 (ms) | 20,504 |
| Total p50 (ms) | 5,997 |
| Total p95 (ms) | 19,764 |
| Input tokens (total) | 178,134 |
| Output tokens (total) | 7,051 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 0 |

Refusal reasons: {'ANSWERED': 79, 'MODEL_REFUSED': 8, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | 100.0% | - | 0.0% | 0.0% | 7,753 |
| cross_language | 25 | 88.0% | 80.0% | 60.0% | 88.0% | - | 0.0% | 0.0% | 5,962 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 100.0% | 94.4% | 77.1% | 91.4% | - | 2.8% | 0.0% | 6,558 |
| no_answer | 7 | - | - | - | - | 71.4% | - | - | 4,892 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 126 |
| table_lookup | 11 | 100.0% | 81.8% | 100.0% | 70.0% | - | 9.1% | 0.0% | 6,767 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 80.0% | 84.0% | 100.0% | 7.4% | 0.0% | 5,486 |
| ko | 65 | 96.2% | 90.4% | 75.0% | 90.4% | 84.6% | 0.0% | 0.0% | 6,482 |

## Failed questions

- **p01**: citation ['01_fda_imaging_endpoint_2018.pdf', '05_mfds_ich_gcp_ko.pdf', '06_mfds_ai_device_lung_ko.pdf']
- **p03**: citation ['01_fda_imaging_endpoint_2018.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p05**: citation ['05_mfds_ich_gcp_ko.pdf']
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p11**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p14**: citation ['05_mfds_ich_gcp_ko.pdf']
- **p15**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p16**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p19**: citation ['04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p20**: citation ['04_mfds_anticancer_guideline_ko.pdf']
- **p22**: citation ['03_ema_anticancer_rev6.pdf']
- **p24**: keywords 0%
- **p29**: citation ['03_ema_anticancer_rev6.pdf']
- **p33**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p34**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p35**: section/page miss; keywords 0%
- **p40**: retrieval miss (got ['01_fda_imaging_endpoint_2018.pdf', '03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf', '08_recil_vs_lugano_2019.xml', '11_dicom_ps3.15_annexE_2026d.html']); citation ['04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p41**: should refuse but answered
- **p50**: citation ['07_irecist_how_to_2020.xml', '09_rano2_review_2025.xml']
- **p55**: section/page miss; keywords 0%
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: section/page miss; keywords 0%
- **p72**: section/page miss; citation ['11_dicom_ps3.15_annexE_2026d.html']; keywords 0%
- **p76**: keywords 0%
- **p79**: keywords 0%
- **p86**: section/page miss
- **p95**: should refuse but answered

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf, 05_mfds_ich_gcp_ko.pdf, 06_mfds_ai_device_lung_ko.pdf | FDA 영상 평가변수 가이드라인에 따르면 영상과 판독 결과 같은 원본 기록은 최소 2년 동안 보관해야 합니다 [1, 2, 3, 4]. |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | The charter should specify the size of the batches and justify it to minimize re |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf, 04_mfds_anticancer_guideline_ko.pdf | 판독자 간 불일치 조정 비율이 중요하다고 판단되면, 시험 프로토콜과 통계 분석 계획(statistical analysis plan)에 대해 미리 |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | The FDA imaging charter guidance describes image presentation to readers, includ |
| p05 | cross_language | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | FDA는 무작위배정 대조 임상시험에서 1차 평가변수 영상 판독자가 시험군과 대조군의 치료 배정 정보를 알지 못하도록 눈가림되어야 한다고 기대합니 |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | The FDA says existing medical-practice imaging standards may be reasonable for a |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 때, FDA는 charter에 reader fatigue를 고려하여 reader fatigue로 인한 이미지 해 |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | Data locking means that no further modification of image assessment is allowed.  |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면 시험자는 시험대상자에게 즉각적인 위험요소를 제거하거나 시험 진행 및 행정상 단순 변경이 필요한 경우에만 임상시험계획 |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | According to ICH E6(R3), the investigator/institution should retain the essentia |
| p12 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에서 시험기관 모니터링 활동의 빈도는 시험대상자 보호와 데이터 완전성의 위험요소에 맞춰진 모니터링 계획을 개발하여야 합니다.  |
| p13 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | According to ICH E6(R3), the investigator should supervise any individual or par |
| p14 | factual | en | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | Centralized monitoring processes provide additional monitoring capabilities that |
| p15 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 임상시험이 조기 종료되거나 중지되면 시험자/시험기관은 의뢰자, 규제 당국, IRB/IEC에 즉시 보고하고, 그 사유를 문서 형태로 상세히 설명해 |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에서 IRB/IEC는 최소 5명의 위원으로 구성되어야 합니다 [1, 2]. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | ORR should be documented according to international standards (e.g. RECIST, Volu |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에서는 일반적으로 6명의 시험 대상자 중 적어도 2명에서 용량 제한 독성이 나타나는 용량으로 정의하며, 그 이상의 용량  |
| p19 | factual | en | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 인간에게 최초 투여 시 타당한 비임상 자료를 근거하여 투여 경로, 투여 용법을 선정한다. 대부분의 경우 정맥투여는 생체이용률에 따른 변화를 배제 |
| p20 | cross_language | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EMA 가이드라인에서 이전 치료의 TTP와 시험약의 PFS를 비교하는 환자 내 외부 대조 분석을 더 설득력 있게 만드는 방법은, 시험요법 직전에 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | The scientific support for the notion that BSA scaled dosing generally reduces i |
| p22 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 수용할 만한 독성이 나타난 후 재투여할 때는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직하다 [4]. |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 1상 단독요법 용량·용법 결정 시험의 주요 목적은 정해진 투여 일정과 투여 방법에 따라 최대내약용량(maximal tolerated dose,  |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 독성에 영향을 주는 인자들(장기 기능 장애, 병용요법)도 적절하게 평가되어야 하고, 이러한 인자들은 이후 2상/3상 임상시험에서 더 상세히 설명 |
| p25 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 3 상 임상시험 이전에 음식-약물 간 상호작용 시험이 수행되어야 한다 [3]. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR과 LDR은 현지 시험자 평가와 BICR 간의 불일치 측면에서 조사될 수 있으며, 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진 |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR을 수행하는 것은 중요한 시험자 비뚤림이 예상되거나 통과의 치료효과가 기대되는 경우에 권고됩니다 [1]. |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험의 1차 평가변수는 일반적으로 전체 반응률(Overall Response Rate, ORR)으로 설정하며, 개별 환자군에서의 효 |
| p29 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 우산형(umbrella) 임상시험에서 시험약물끼리 유효성을 비교하는 것은 권장되지 않습니다 [3]. |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | PFS 1차 분석에서 진행일은 진행이 확인된 시점으로 해야 합니다 [4]. |
| p31 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인과 EMA 가이드라인은 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대해 명확하게 규정하지 않습니다. 하 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 근거자료는 출처를 알 수 있고(attributable), 읽기 쉬우며(legible), 동시성을 입증할 수 있고(contemporaneous), |
| p33 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 의뢰자가 확인된 위험요소를 평가할 때 고려해야 하는 세 가지는 오류 발생 가능도, 해당 오류를 감지할 수 있는 정도, 해당 오류가 시험대상자 보 |
| p34 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(quality tolerance limit)에서 일탈이 감지되면 조치 필요성 여부를 결정하기 위하여 평가를 실시해야 |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 본 임상시험은 인공지능을 이용하여 폐CT 영상에서 폐암을 검출, 의사의 폐암·폐결절 진단을 보조하는 폐CT 영상 기반 폐암·폐결절 진단 보조소프 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터는 1:2의 비율로 강화 배정(enrichment allocation)을 시행합니다 [1, |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전, 후를 비교할 경우 판독자는 3명이며, 디지털의료기기의 보조 없이 표준적인 진료환경을 제공하고 개별 판독 후 참조표준을  |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다 [5]. |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 디지털의료기기의 개발 과정동안 사용된 학습 데이터와의 독립성이 유지되어야 한다 [2]. |
| p40 | cross_language | en | ANSWERED | N | N | 04_mfds_anticancer_guideline_ko.pdf | 별로 최소 30명, 최대 50명의 환자를 평가할 계획임 [1]. |
| p41 | no_answer | ko | ANSWERED | - | - | 06_mfds_ai_device_lung_ko.pdf | CT 영상으로서 다음의 조건을 충족하여야 한다. - OOmm 이하의 CT slice 간격 [4]. |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD가 나온 뒤 가성진행 여부를 재평가하는 추적검사는 4-8주 후에 하나요 [5]. |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD(미확정 진행)로 판정하는 조건은, TL(Tumor Load)의 합이 최소 20% 이상 증가(최소 5mm)하거나, Non-TL의 확실한  |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD is confirmed as iCPD at the next follow-up if further progress of the targe |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 정기적인 반응평가 추적검사 간격으로 권장되는 기간은 6~12주입니다 [1]. |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 환자당 최대 5개, 장기당 최대 2개 [1, 3]. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 5 mm [4]. |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD will not override a subsequent best overall response of iSD, iPR, or iCR [1 |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 논문은 면역항암제 투여 후 hyperprogression을 ≥ 2-fold increase in tumor growth kinet |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml, 09_rano2_review_2025.xml | Hodi et al. demonstrated that patients with advanced malignant melanoma showed a |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1~3점이면 완전관해(CR)로 판정합니다 [3]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Deauville 4~5점이지만 기저 대비 FDG 섭취가 감소했다면 Lugano 기준에서 partial remission (PR)으로 분류합니다 |
| p55 | cross_language | ko | ANSWERED | Y | N | 08_recil_vs_lugano_2019.xml | RECIL의 minor response(MiR) 기준은 아직 확립되지 않았으며, 임상적 가치가 입증되지 않았습니다. MiR은 주로 중간 재검사에 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL recommends uni-dimensional measurements of just up to three target lesions |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | At EOT, agreement between RECIL and Lugano was 90.7% (49/54 patients; κ = 0.79,  |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 1명과 2명의 판독자는 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었고, Lugano의 경우 각각 1.8 ± 0.3분과  |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 기저(baseline) 스캔은 방사선 치료 종료 후 21~35일(4주) 후에 촬영합니다 [5]. |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD(예비 진행)는 SPPD(Standardized Uptake Value)가 25% 이상 증가하거나  |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 2D; CR: No lesion; PR: More than 50% reduction; MR: Less than 50% but more than  |
| p65 | table_lookup | en | ANSWERED | Y | N | 09_rano2_review_2025.xml | According to Table 3 of the RANO 2.0 review, a more than 25% increase in SPPD de |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능 병변의 최소 단축 직경은 10mm이며, 2D 영상에서 최소 두 개의 슬라이스에 걸쳐 확장되어야 합니다 [1]. |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | Enhancing or non-enhancing tumors should have a minimum of two and a maximum of  |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 3D T1 강조영상의 슬라이스 두께 기준은 ≦ 1.5 mm [4]. |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종에서 RANO 2.0 기저 스캔은 치료 시작 전 14일 이내에 촬영해야 합니다 [2]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | ANSWERED | Y | N | 11_dicom_ps3.15_annexE_2026d.html | MIDI 보고서는 DICOM 영상 비식별화 시 Application Level Confidentiality Profile (E.1.1)를 기준으 |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | No arbitrary finite number or specified subset of indirect identifiers is consid |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | CT projection views, MR k-space data, PET list mode or sinogram data [1.20 Modal |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf, 11_dicom_ps3.15_annexE_2026d.html | MIDI 보고서는 DICOM PS3.15 E.1을 유지하는 것이 중요하며, 필요한 데이터 요소와 값을 유지하여 DICOM 표준에 부합하도록 해야 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Name (0010,0010) 속성은 In Std. Comp. IOD (from PS3.3): Y로 표시됩니다 [2]. |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Basic Prof.: U; Rtn. UIDs Opt.: K [3]. |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)는 Basic Profile에서는 Z로 처리되고, Retain Longitudinal Temporal I |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | The Attribute Name: Institution Name (0008,0080) is contained in Standard IODs [ |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | X는 속성을 제거하고, 속성이 시퀀스인 경우 시퀀스 항목과 그에 포함된 속성을 모두 제거합니다 [1]. |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)는 Basic Profile에서 Z로 처리하고, Retain Patient Characteristi |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | X [4] |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔은 각각 4주 또는 8주 후, 그리고 12주 후입니다 [3, 4]. |
| p85 | cross_doc | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 has retained the "minor response" category, which is similar to the REC |
| p86 | cross_doc | en | ANSWERED | Y | N | 01_fda_imaging_endpoint_2018.pdf, 03_ema_anticancer_rev6.pdf | The EMA anticancer guideline and the FDA imaging endpoint guidance do not mentio |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처(EMA) 가이드라인은 첫 인체 투여 시 타당한 비임상 자료를 근거하여 투여 경로, 투여 용법을 선정하도록 권장합니다. 대부분의 경우 정맥 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | ANSWERED | - | - | 02_ich_e6r3_2025.pdf | 식약처 항암제 가이드라인은 BICR 판독자를 최소 5명으로 구성하라고 권장합니다 [5]. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
