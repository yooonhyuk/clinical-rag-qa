# RAG Eval Report — public / bge-m3-hybrid-gemma4-e4b (2026-10-07T00:53:47)

## Config

- run_at: `2026-10-07T00:53:47`
- label: `bge-m3-hybrid-gemma4-e4b`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `688b7e2`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `none`
- embedding_model: `bge-m3`
- embedding_dim: `1024`
- hybrid_search: `True`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `0.45`
- scope_classifier: `embedding`
- scope_margin: `0.056`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 92.4% |
| Section/page hit@k | 81.0% |
| Citation accuracy (cited files ⊆ gold) | 88.1% |
| Citation location (a cited chunk in gold section/page) | 89.8% |
| Keyword coverage | 94.9% |
| Refusal accuracy (must-refuse) | 100.0% |
| False refusal rate (answerable) | 25.3% |
| Retrieval p50 (ms) | 458 |
| Retrieval p95 (ms) | 622 |
| Generation p50 (ms) | 6,749 |
| Generation p95 (ms) | 10,920 |
| Total p50 (ms) | 7,058 |
| Total p95 (ms) | 11,287 |
| Input tokens (total) | 153,434 |
| Output tokens (total) | 9,133 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |

Refusal reasons: {'ANSWERED': 59, 'MODEL_REFUSED': 28, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | refusal_correctness | false_refusal_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | - | 71.4% | 10,042 |
| cross_language | 25 | 76.0% | 68.0% | 87.5% | - | 36.0% | 6,890 |
| diagnosis_request | 9 | - | - | - | 100.0% | - | 0 |
| factual | 36 | 100.0% | 91.7% | 88.2% | - | 5.6% | 7,535 |
| no_answer | 7 | - | - | - | 100.0% | - | 4,795 |
| out_of_scope | 4 | - | - | - | 100.0% | - | 456 |
| table_lookup | 11 | 100.0% | 72.7% | 85.7% | - | 36.4% | 7,858 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | refusal_correctness | false_refusal_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 90.5% | 100.0% | 22.2% | 6,979 |
| ko | 65 | 90.4% | 80.8% | 86.8% | 100.0% | 26.9% | 7,105 |

## Failed questions

- **p01**: citation ['01_fda_imaging_endpoint_2018.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p02**: keywords 0%
- **p05**: false refusal (MODEL_REFUSED)
- **p06**: keywords 0%
- **p10**: false refusal (MODEL_REFUSED)
- **p12**: false refusal (MODEL_REFUSED)
- **p13**: citation ['05_mfds_ich_gcp_ko.pdf']
- **p14**: citation ['05_mfds_ich_gcp_ko.pdf']
- **p15**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p16**: false refusal (MODEL_REFUSED)
- **p18**: false refusal (MODEL_REFUSED)
- **p20**: false refusal (MODEL_REFUSED)
- **p24**: false refusal (MODEL_REFUSED)
- **p25**: citation ['03_ema_anticancer_rev6.pdf', '04_mfds_anticancer_guideline_ko.pdf']
- **p31**: false refusal (MODEL_REFUSED)
- **p34**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p35**: section/page miss; keywords 0%
- **p40**: false refusal (MODEL_REFUSED)
- **p49**: false refusal (MODEL_REFUSED)
- **p55**: false refusal (MODEL_REFUSED)
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: false refusal (MODEL_REFUSED)
- **p72**: false refusal (MODEL_REFUSED)
- **p75**: false refusal (MODEL_REFUSED)
- **p77**: false refusal (MODEL_REFUSED)
- **p80**: false refusal (MODEL_REFUSED)
- **p81**: citation ['10_midi_deid_report_2023.pdf', '11_dicom_ps3.15_annexE_2026d.html']
- **p84**: false refusal (MODEL_REFUSED)
- **p85**: false refusal (MODEL_REFUSED)

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf, 05_mfds_ich_gcp_ko.pdf | 제공된 문서들 중 FDA 영상 평가 변수 가이드라인에 대한 직접적인 언급은 없으나, 임상시험 관련 원본 기록(판독 결과 포함)은 마케팅 신청 승 |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 독자들이 이미지를 배치(batches)로 해석하는 경우, 임상시험 문서(charter)는 배치 크기를 명시하고 해당 배치 크기가 필요한 이유를  |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 간 불일치 조정(adjudication) 비율이 중요하다고 판단될 경우, 임상시험 문서(프로토콜 및 통계 분석 계획)에 이 비율 결정 과 |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 이미징 헌장 지침은 독자에게 이미지를 제시하는 방식에 대해 다음과 같은 내용을 설명합니다. 첫째, 이미지를 배치(batches)로 제시할 |
| p05 | cross_language | ko | MODEL_REFUSED | N | N | - | 제공된 문서에는 무작위배정 대조 임상시험에서 1차 평가변수 영상 판독자가 무엇에 대해 눈가림되어야 하는지에 대한 FDA의 기대 사항은 명시되어  |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA는 기존 의료 관행 이미징 표준이 적절할 수 있는 임상시험 종점의 경우, 임상 사이트 간에 중요하게 변하지 않는 잘 받아들여지고 널리 구현 |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 경우, 개발자는 세션에서 판독할 수 있는 최대 이미지 수를 명시할지 고려해야 합니다 [3]. |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 데이터 잠금(locking data)이란, 이미지 검토 과정 중 미리 정해진 시점에 독자(reader)가 생성한 이미지 해석 데이터(사례 보고서 |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | MODEL_REFUSED | N | N | - | 제공된 문서에는 ICH E6(R3)에 따른 시험자가 임상시험계획서에서 벗어날 수 있는 경우에 대한 정보가 없습니다. |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | 임상시험 책임자/기관은 해당 규정에서 요구하는 보존 기간 동안 또는 스폰서가 해당 기록이 더 이상 필요하지 않다고 통보할 때까지 중 더 긴 기간 |
| p12 | cross_language | ko | MODEL_REFUSED | N | N | - | 문서에서 확인할 수 없습니다. |
| p13 | factual | en | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 모니터링을 수행하는 사람은 의뢰자의 모니터링 계획과 적용 가능한 모니터링 절차를 따라야 합니다 [3]. |
| p14 | factual | en | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링은 임상시험이 진행되는 현장(site) 모니터링을 보완하고 그 범위 및/또는 빈도를 줄일 수 있는 추가적인 모니터링 역량을 제공하며 |
| p15 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | 임상시험이 조기 종료되거나 중지된 경우, 시험자/시험기관은 다음과 같은 조치를 취해야 합니다:  1. **시험대상자 보호 및 후속 조치:** 시 |
| p16 | cross_language | ko | MODEL_REFUSED | Y | N | - | ICH E6(R3)에 대한 정보는 제공된 문서에서 확인할 수 없습니다. 다만, 다른 문서에 따르면 IRB/IEC는 최소 5명으로 구성되는 것이  |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 세포독성 화합물(cytotoxic compounds)의 임상 2상 단일제 치료 탐색적 연구에서 ORR(Overall Response Rate)은 |
| p18 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에는 MTD(최대내약용량)의 전통적인 정의가 식약처 가이드라인과 EMA 가이드라인에서 각각 어떻게 다른지 비교하여 설명하는 내용은 포 |
| p19 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 최초 인간 대상 연구(first use in man studies)에서 정맥 투여(intravenous administration)가 권장되는  |
| p20 | cross_language | ko | MODEL_REFUSED | N | N | - | 제공된 문서에는 EMA 가이드라인에서 이전 치료의 TTP와 시험약의 PFS를 비교하는 환자 내 외부 대조 분석을 더 설득력 있게 만드는 구체적인 |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA(Body Surface Area) 기반 용량 설정에 대한 과학적 근거는 약하며, 이는 높은 BSA를 가진 환자에게는 과소 노출, 낮은 B |
| p22 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생하여 재투여하는 경우, 환자가 회복될 때까지 기다린 후에는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다.  |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 세포독성 물질의 1상 단독요법 용량 및 용법 결정 시험의 주요 목적은 다음과 같습니다. 첫째, 정해진 투여 일정과 투여 방법에 따라 최대내약용량 |
| p24 | factual | ko | MODEL_REFUSED | Y | N | - | 제공된 문서에서는 1상 임상시험의 독성 등급을 매기는 구체적인 기준에 대해서는 언급하고 있지 않습니다. 다만, 1상 임상시험의 주요 목적은 용량 |
| p25 | factual | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 항암제의 음식-약물 상호작용 시험은 3상 임상시험 이전에 수행되어야 합니다 [1], [5]. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR(초기 불일치율)과 LDR(후기 불일치율)은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1] |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR은 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1], [2]. |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 바구니형 임상시험의 1차 평가변수는 일반적으로 전체 반응률(Overall Response Rate, ORR)로 설정합니다 [1]. |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 아니요, 우산형 임상시험에서 시험약물 간의 유효성 비교는 권장되지 않습니다. [1] |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 예정된 평가 시점과 관계없이, 계획되지 않은 평가에서 진행이 확인된 경우, 1차 분석 목적에서는 진행일은 평가가 예정된 시점이 아니라 진행이 실 |
| p31 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에서 1상 시험에서 수용 가능한 독성 후 재투여할 때의 최소 투여 주기에 대한 식약처 가이드라인과 EMA 가이드라인을 각각 명확하게  |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | ICH GCP 안내서에 따르면, 시험책임자/임상시험실시기관은 각 시험대상자에 대해 모든 관련 관찰사항을 포함하는 적절하고 정확한 근거문서와 임상 |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자가 확인된 위험요소를 평가할 때 고려해야 하는 세 가지 사항은 다음과 같습니다: 1. 오류 발생 가능도 [1], [2] 2. 해당 오류를  |
| p34 | factual | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(predefined quality tolerance limit)에서 일탈(deviation)이 감지되면, 조치(ac |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 폐CT 영상 기반 폐암·폐결절 진단보조 소프트웨어의 안전성 및 유효성을 평가하기 위한 임상시험은 다기관, 후향적, 우월성 확증 임상시험으로 설계 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐결절이 있는 것으로 확인된 상당수의 증례(3000증례 이상) 중에서 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터를 1:2의 비율로  |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 디지털의료기기 사용 전 판독은 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 수행하며 [1], 개별 판독 후 참 |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | AI 의료기기 임상시험에서 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성되어야 합니다. [1] |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋을 선정·배정할 때는 디지털의료기기의 개발 과정에서 사용된 학습 데이터와 독립성을 유지해야 합니다 [1]. |
| p40 | cross_language | en | MODEL_REFUSED | N | N | - | 제공된 문서에서는 MFDS AI 폐 결절 프로토콜 예시에 참여하는 판독자의 수나 판독 기간에 대한 정보를 확인할 수 없습니다. |
| p41 | no_answer | ko | MODEL_REFUSED | - | - | - | 제공된 임상시험 가이드라인 예시에서는 CT slice 간격에 대한 구체적인 최대 수치(예: OOmm 이하)를 명시하고 있으나, 정확한 수치는 [ |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 iUPD가 확인된 후, 4~8주 후에 별도의 추적 검사를 통해 재평가할 수 있습니다 [4]. |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 미확정 진행(iUPD)으로 판정하는 조건은 다음과 같습니다. 첫째, 모든 표적 병변(TL)의 합이 가장 낮은 TL 합(Nadi |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD가 확인된 후 다음 추적 관찰 시 iCPD로 확정되는 경우는, 표적 부위(target sum)가 5mm 이상 추가로 진행되거나, 비표적  |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST의 정기적인 추적 반응 평가(follow-up response assessment)는 6~12주 간격으로 권장됩니다 [1]. |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서 표적 병변(target lesions)은 환자당 최대 5개까지, 그리고 장기당 최대 2개까지 정의할 수 있습니다 [1]. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 추적 관찰 시 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우, 기본값으로 5 mm를 사용할 수 있습니다. [1] |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD는 iRECIST에서 후속 최적 전체 반응(iSD, iPR, 또는 iCR)을 무효화할 수 없습니다. [1] |
| p49 | cross_language | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에서는 iRECIST가 면역항암제 투여 후 hyperprogression을 구체적으로 설명하는 내용은 확인할 수 없습니다. 다만, 면 |
| p50 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | Hodi 등은 펨브롤리주맙(Pembrolizumab)을 사용한 진행성 흑색종 환자에서 총 7%의 가성 진행률을 보고했습니다 [1]. |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1–3점은 완전 관해(CR)로 판정됩니다 [1]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 기준에서 Deauville 4–5점이지만 기저 대비 FDG 섭취가 감소했다면 부분 관해(PR)로 분류됩니다 [3]. |
| p55 | cross_language | ko | MODEL_REFUSED | Y | N | - | 제공된 문서에는 RECIL의 minor response(MiR)에 대한 구체적인 기준은 명시되어 있지 않습니다. 다만, MiR은 RECIL의 임 |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대해 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR을 PR로 재코딩했을 때, 치료 종료 시점(EOT)의 RECIL과 Lugano 간의 일치도는 49/54 환자에서 90.7%였으며, Cohe |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었으며, Lugano의 경우 평균 판독 시 |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서는 방사선 치료 종료 후 약 4주(21–35일)에 후방사선 치료 MRI를 기저 스캔으로 설정하여 PsP(가성 진행)의 영향을  |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 preliminary PD는 다음 두 가지 조건 중 하나로 정의될 수 있습니다: 12주 초기 치료 기간 동안 SPPD(Sho |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0의 2D 측정 기준에서 부분반응(PR)의 임계값은 50% 초과 감소입니다. [1] |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 제공된 문서에는 RANO 2.0 검토의 표 3(Table 3)에 대한 정보가 포함되어 있지 않아, 진행성 질환(PD)을 정의하는 3D 부피 변화 |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 측정 가능한 병변은 기본적으로 최소 단축 직경 10 mm를 가지며, 2D 영상에서는 최소 2개 슬라이스에 걸쳐 확장되어야 합 |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0에서 조영 증강 종양 또는 비조영 증강 종양을 평가할 때는 최소 2개에서 최대 3개의 병변을 선택해야 합니다 [1]. 혼합 종양의 |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0 리뷰의 최소 3T MRI 프로토콜 표(Table 2)에 따르면, 3D-T1w Pre의 슬라이스 두께(Slice Thickness |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 치료 시작 전 표준화된 시간 간격(14일 이내)으로 사전 스캔을 기저 스캔으로 사용해야 합니다 [2]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에서 MIDI 보고서가 DICOM 영상 비식별화 시 특정 표준 프로파일을 기준으로 삼으라고 권고하는 내용은 확인할 수 없습니다. |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | 아니요, 위험 분석 없이 고정된 수의 간접 식별자를 유지하는 것은 허용되지 않습니다. 위험 분석이 없는 경우, 임의의 유한한 수 또는 지정된 하 |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MIDI 보고서에서 범위 밖(out of scope)으로 둔 원시 데이터의 예로는 MR k-space, CT 투영(projections), PE |
| p75 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | MIDI 보고서에 따르면, DICOM IOD는 특정 방식으로 처리되기 위해 '인식'될 필요가 없으며, 예를 들어 Raw Data 객체는 모든 환 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM PS3.15 Basic Profile에서 Patient's Name (0010,0010) 속성은 표준 구성 IOD(Std. Comp. |
| p77 | table_lookup | en | MODEL_REFUSED | Y | Y | - | Study Instance UID (0020,000D)의 Basic Profile은 'U'로 지정되어 있습니다 [1]. 이 태그는 표준 구성 I |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Date (0008,0020)의 Basic Profile은 'Z'로 설정되어 있으며 [1], 'Retain Long. Full Dat |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | DICOM Basic Application Level Confidentiality Profile에 따라 Institution Name (0008 |
| p80 | table_lookup | ko | MODEL_REFUSED | Y | N | - | 제공된 문서에서는 'DICOM 비식별화 조치 코드 X'에 대한 구체적인 정의를 확인할 수 없습니다. |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf, 11_dicom_ps3.15_annexE_2026d.html | Patient's Age (0010,1010)의 Basic Profile 처리 여부는 'X'이며, Retain Patient Characteri |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (0018,1000)의 De-identification Action은 X/Z/D입니다. [1] |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에는 iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔 시기에 대한 정보가 없습니다. 다만, RANO 2.0의 경우 |
| p85 | cross_doc | en | MODEL_REFUSED | Y | N | - | 제공된 문서에는 RECIL과 RANO 2.0이 '경미한 반응(minor response)'을 어떻게 정의하는지에 대한 직접적인 비교 정보가 포함 |
| p86 | cross_doc | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf, 03_ema_anticancer_rev6.pdf | EMA의 항암제 가이드라인은 특정 내용을 직접적으로 언급하고 있지는 않으나, 전이성 질환의 경우 1차 평가 변수 선택과 관계없이 ORR, DoR |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인은 인간에게 최초 투여 시 정맥투여를 권장하는 이유로, 생체이용률에 따른 변화를 배제할 수 있기 때문이라고 설명합니다 [1].  |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 제공된 문서에는 EMA 항암제 가이드라인이 맹검된 독립적 중앙평가(BICR)에 필요한 최소 판독자 간 카파(kappa) 값에 대한 정보가 포함되 |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 제공된 문서들은 임상시험 문서 및 의료영상 업로드 운영 문서에 관한 내용이며, 파이썬 버블 정렬 코드 작성에 대한 정보는 포함하고 있지 않습니다 |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
