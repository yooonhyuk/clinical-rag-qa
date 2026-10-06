# RAG Eval Report — public / bge-m3-vector-medgemma-4b-run2 (2026-10-07T03:04:53)

## Config

- run_at: `2026-10-07T03:04:53`
- label: `bge-m3-vector-medgemma-4b-run2`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `b96c482`
- provider: `ollama`
- generator_model: `medgemma:4b`
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
| Citation accuracy (cited files ⊆ gold) | 78.2% |
| Citation location (a cited chunk in gold section/page) | 85.9% |
| Keyword coverage | 87.2% |
| Refusal accuracy (must-refuse) | 85.0% |
| False refusal rate (answerable) | 1.3% |
| Partial answers with caveat (answerable) | 0.0% |
| False refusal if partial = refusal (MVP-1 policy) | 1.3% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 90.0% |
| Answers in Korean (answered) | 67.9% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 113 |
| Retrieval p95 (ms) | 125 |
| Generation p50 (ms) | 5,704 |
| Generation p95 (ms) | 9,560 |
| Total p50 (ms) | 5,731 |
| Total p95 (ms) | 9,163 |
| Input tokens (total) | 151,341 |
| Output tokens (total) | 8,678 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 80, 'ANSWERED_PARTIAL': 1, 'MODEL_REFUSED': 6, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | 100.0% | - | 0.0% | 0.0% | 8,038 |
| cross_language | 25 | 88.0% | 80.0% | 68.0% | 88.0% | - | 0.0% | 0.0% | 5,807 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 100.0% | 94.4% | 75.0% | 88.9% | - | 0.0% | 0.0% | 5,846 |
| no_answer | 7 | - | - | - | - | 57.1% | - | - | 4,234 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 109 |
| table_lookup | 11 | 100.0% | 81.8% | 100.0% | 70.0% | - | 9.1% | 0.0% | 6,302 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 80.8% | 76.9% | 100.0% | 3.7% | 0.0% | 5,332 |
| ko | 65 | 96.2% | 90.4% | 76.9% | 92.3% | 76.9% | 0.0% | 0.0% | 5,815 |

## Failed questions

- **p05**: citation ['04_mfds_anticancer_guideline_ko.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p06**: keywords 0%
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p11**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p12**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p15**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p16**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p19**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p20**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p22**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p29**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p33**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p34**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p35**: section/page miss; keywords 0%
- **p40**: retrieval miss (got ['01_fda_imaging_endpoint_2018.pdf', '03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf', '08_recil_vs_lugano_2019.xml', '11_dicom_ps3.15_annexE_2026d.html']); citation ['04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p41**: should refuse but answered
- **p50**: citation ['07_irecist_how_to_2020.xml', '09_rano2_review_2025.xml']
- **p52**: should refuse but a partial answer
- **p55**: section/page miss; keywords 0%
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: section/page miss; keywords 0%
- **p65**: section/page miss; keywords 0%
- **p72**: section/page miss; citation ['11_dicom_ps3.15_annexE_2026d.html']; keywords 0%
- **p76**: keywords 0%
- **p79**: keywords 0%
- **p86**: section/page miss
- **p95**: should refuse but answered

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 영상 평가변수 가이드라인에 따르면 영상과 판독 결과 같은 원본 기록은 최소 2년 동안 보관해야 합니다. |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | If readers interpret images in batches, the imaging charter should specify the s |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단되면, 시험계획서(protocol)와 통계 분석 계획(statistical |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | The FDA imaging charter guidance describes the image presentation to readers, in |
| p05 | cross_language | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf, 05_mfds_ich_gcp_ko.pdf | 무작위배정 대조 임상시험에서 1차 평가변수 영상 판독자는 시험의 무작위 배정 절차에 따라 눈가림되어야 하며, 시험계획서에 의해서만 눈가림이 해제 |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 관행의 영상 처리 기준이 적절한 경우, 뼈 골절이나 뇌출혈과 같은 명백한 결과에 초점을 맞춘 시험의 경우에만 적절하다고 말합 |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 때 FDA는 charter에 reader fatigue를 고려하여 reader fatigue로 인해 이미지 해석 |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 이미지 분석 데이터베이스를 형성하기 위해 스폰서로 이전된 경우, 일부 상황에서는 사례 보고서 양식이 표 형식으로 숫자(예: 병변 측정) 또는 범 |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면 시험자는 시험대상자에게 즉각적인 위험요소를 제거하거나 시험 진행 및 행정상 단순 변경이 필요한 경우에만 임상시험계획 |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | According to ICH E6(R3), the investigator/institution should retain the essentia |
| p12 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에서는 시험기관 모니터링 활동의 빈도는 시험의 특성, 위험요소, 그리고 모니터링 계획에 따라 결정되어야 합니다. 시험의 규모, |
| p13 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | According to ICH E6(R3), monitoring should be performed by persons who follow th |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | Centralized monitoring can complement and reduce the extent and/or frequency of  |
| p15 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 임상시험이 조기 종료되거나 중지되면 시험자/시험기관은 의뢰자, 규제 당국, IRB/IEC에 즉시 보고해야 하며, 조기 종료 또는 중지에 대한 상 |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | ICH E6(R3)에 따르면 IRB/IEC는 최소 5명의 위원으로 구성되어야 합니다. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | ORR should be documented according to international standards (e.g. RECIST, Volu |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에서는 일반적으로 6명의 시험 대상자 중 적어도 2명에서 용량 제한 독성(DLT)이 나타나는 용량으로 정의합니다. EMA |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | EMA 가이드라인은 최초 인간 연구에서 정맥 투여를 권장하는 이유는 생체이용률에 따른 변화를 배제할 수 있기 때문입니다. 이는 투여 경로를 선택 |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | EMA 가이드라인에서 이전 치료의 TTP와 시험약의 PFS를 비교하는 환자 내 외부 대조 분석을 더 설득력 있게 만드는 방법은, 이전 치료와 시 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | The EMA guideline states that the scientific support for BSA-scaled dosing is we |
| p22 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 나타난 후 재투여할 때는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다. |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 정해진 투여 일정과 투여 방법에 따라 최대내약용량(maximal tolerated dose |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에서 1상 시험의 독성 등급은 일반적으로 미국 국립암연구소(NCI)의 이상반응에 대한 일반용어기준(Common Termi |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 3 상 임상시험 이전에 음식-약물 간 상호작용 시험이 수행되어야 한다. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | BICR과 현지 시험자 평가의 불일치를 볼 때 쓰는 EDR(early discrepancy rate)과 LDR(late discrepancy r |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 모든 환자의 모든 관련 데이터에 대한 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 통과의 치료효과가 기대되는 경우에 권고됩니다. 사건의  |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험의 1차 평가변수는 일반적으로 전체 반응률(Overall Response Rate, ORR)으로 설정합니다. 개별 환자군에서의  |
| p29 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 우산형(umbrella) 임상시험에서 시험약물끼리 유효성을 비교하는 것은 권장되지 않습니다. 우산형 임상시험은 단일 질환의 맥락에서 다양한 시험 |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | PFS 1차 분석에서 진행일은 진행이 확인된 시점으로 해야 합니다. |
| p31 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인과 EMA 가이드라인은 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대해 명확하게 규정하지 않습니다. 하 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | ICH GCP 안내서에 따르면 시험책임자가 유지하는 근거자료(source data)는 출처를 알 수 있고(attributable), 읽기 쉬우며 |
| p33 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 의뢰자는 확인된 위험요소를 평가할 때 다음 세 가지를 고려해야 합니다. (a) 오류 발생 가능도 (b) 해당 오류를 감지할 수 있는 정도 (c) |
| p34 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(quality tolerance limit)에서 일탈이 감지되면, 조치(action)가 필요한지를 결정하기 위하여  |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 폐CT 기반 폐암·폐결절 진단보조 소프트웨어 임상시험계획서 예시는 귀환(帰還) 검정(帰帰検定)을 사용한 연구 설계입니다. 연구 가설은 다음과 같 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐암 확진 데이터와 양성 폐결절 확진 데이터는 1:2의 비율로 강화 배정(enrichment allocation)을 시행합니다. |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 3명의 판독자가 수행하며, 각 판독자의 AUC를 산출하여 3명의 평균을 기록합니다. [1] |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다. [1], [4], [5] 참조 |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 시험디자인을 고려하여 구체적이고 엄격한 선정기준과 제외기준을 제시하여야 하며, 시험 데이터셋은 시험디자인을 고려하여 구체적이고  |
| p40 | cross_language | en | ANSWERED | N | N | 04_mfds_anticancer_guideline_ko.pdf | 별로 최소 30명, 최대 50명의 환자를 평가할 계획임 ∎ (시험방법) 신물질 A 및 병용약물의 투여 방법은 가변적이며 공통 대조군(표준 치료요 |
| p41 | no_answer | ko | ANSWERED | - | - | 06_mfds_ai_device_lung_ko.pdf | CT 영상으로서 다음의 조건을 충족하여야 한다. - OOmm 이하의 CT slice 간격 |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD가 나온 뒤 가성진행 여부를 재평가하는 추적검사는 4-8주 후에 하나요. |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD(미확정 진행)로 판정하는 조건은 다음과 같습니다.  1.  TL(Tumor Load)의 합이 기존의 최소 TL 합보다 ≥20% 증가 ( |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD는 다음 후속 검사에서 iCPD로 확인됩니다. iCPD는 추가적인 목표 합계(≥ 5mm)의 진행, Non-TL의 추가적인 진행, 또는 새 |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 정기적인 반응평가 추적검사 간격으로 권장되는 기간은 6~12주입니다. [1] |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 환자당 최대 5개, 장기당 최대 2개까지 표적병변을 정의할 수 있습니다. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 5 mm |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | No, iUPD will not override a subsequent best overall response of iSD, iPR, or iC |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 논문은 면역항암제 투여 후 hyperprogression을 ≥ 2-fold increase in tumor growth kinet |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml, 09_rano2_review_2025.xml | Hodi et al. reported a total pseudoprogression rate of about 7% for pembrolizuma |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | ANSWERED_PARTIAL | - | - | 07_irecist_how_to_2020.xml | iRECIST how-to 논문에 보고된 판독자 간 급내상관계수(ICC) 값은 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1~3점은 완전관해(CR)로 판정됩니다. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4~5점이지만 기저 대비 FDG 섭취가 감소했다면 partial remission (PR)으로 분류합니다 |
| p55 | cross_language | ko | ANSWERED | Y | N | 08_recil_vs_lugano_2019.xml | RECIL의 minor response(MiR) 기준은 18F-FDG PET/CT 기반의 반응 평가 기준이며, RECIL-1: "response |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL recommends uni-dimensional measurements of up to three target lesions, whi |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL and Lugano agreement at end-of-treatment when MiR was recoded as PR was 90 |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 판독자 1과 2의 평균 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었고, Lugano의 경우 평균 시간은 1.8  |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | ANSWERED | Y | N | 08_recil_vs_lugano_2019.xml | The RECIL versus Lugano study used PET reconstruction settings with 2 iterations |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 기저(baseline) 스캔은 방사선 치료 종료 후 약 4주(21–35일) 후에 촬영합니다. |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD(예비 진행)는 SPPD(Standardized Uptake Value)가 25% 이상 증가하거나  |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 2D 측정 기준 부분반응(PR)의 임계값은 50% 이상 감소입니다. |
| p65 | table_lookup | en | ANSWERED | Y | N | 09_rano2_review_2025.xml | According to Table 3 of the RANO 2.0 review, a more than 25% increase in SPPD de |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능 병변의 최소 단축 직경은 10mm이며, 2D 영상에서 최소 두 개의 층에 걸쳐 확장되어야 합니다. [1], [2] |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 enhancing 또는 non-enhancing 종양에 대해 최소 2개에서 최대 3개의 target lesion을 선택해야 |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 3D-T1w Pre: ≦ 1.5 mm |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종에서 RANO 2.0 기저 스캔은 치료 시작 전 14일 이내에 촬영해야 합니다. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | ANSWERED | Y | N | 11_dicom_ps3.15_annexE_2026d.html | MIDI 보고서는 DICOM 영상 비식별화 시 Application Level Confidentiality Profile을 기준으로 삼으라고 권 |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | No, the MIDI report does not accept retaining a fixed number of indirect identif |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서가 범위 밖(out of scope)으로 둔 원시 데이터(raw data)의 예는 MR k-space, CT projections |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf, 11_dicom_ps3.15_annexE_2026d.html | MIDI 보고서는 비식별화 후 DICOM IOD 적합성을 유지하기 위해, 위험 요소가 있는 표준 데이터 요소에 대한 정보를 계속 유지해야 한다고 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Name (0010,0010) 속성은 Basic Profile에서 'Y'로 표시되어 있으며, Standard Complianc |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Basic Profile는 Study Instance UID (0020,000D)를 유지합니다. Retain UIDs 옵션이 활성화되면 Stud |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)는 Basic Profile에서는 Retain Longitudinal Temporal Informatio |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | The Institution Name (0008,0080) is a Basic Prof. attribute and is contained in  |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | X는 제거할 속성을 의미합니다. 속성이 시퀀스인 경우 시퀀스 항목과 그에 포함된 속성을 제거합니다. |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)는 Basic Profile에서 Z로 표시되고, Retain Patient Characteristi |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | X |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔은 각각 4주 또는 8주 후에 진행을 확인하기 위한 추가 스캔이 필요합니다.  |
| p85 | cross_doc | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml, 09_rano2_review_2025.xml | RANO 2.0은 2D 평가에서 "minor response" 범주를 도입했으며, 이는 RANO-LGG에서 도입된 범주입니다. RANO 2.0의 |
| p86 | cross_doc | en | ANSWERED | Y | N | 01_fda_imaging_endpoint_2018.pdf, 03_ema_anticancer_rev6.pdf | EMA anticancer guideline and the FDA imaging endpoint guidance do not explicitly |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처와 EMA 가이드라인 모두 첫 인체 투여 시 정맥투여를 권장하는 이유는 생체이용률에 따른 변화를 배제할 수 있기 때문입니다. [1], [2 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | ANSWERED | - | - | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 식약처 항암제 가이드라인은 IRB/IEC를 최소 5명으로 구성하라고 권장합니다. [4], [5]의 문서를 참조하십시오. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 파이썬으로 버블 정렬 코드를 작성해 달라는 요청은 의료 영상 업로드 운영 문서와 임상시험 문서와 관련이 없습니다. 따라서 답변할 수 없습니다. |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
