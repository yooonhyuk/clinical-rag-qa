# RAG Eval Report — public / bge-m3-vector-gemma4-e4b-inline-en (2026-10-07T09:48:12)

## Config

- run_at: `2026-10-07T09:48:12`
- label: `bge-m3-vector-gemma4-e4b-inline-en`
- corpus: `public`
- corpus_root: `corpus/public`
- corpus_sha256: `8e014ae39a5d011e2c7e258a32f4ad09d28ce44771861f427879cd66c13d7588`
- questions_file: `public_questions.yaml`
- questions_sha256: `bd52923c6bd9535e904040a0cb611ed6e2a5496c9201b10baffc00ea1e3c08a8`
- git_commit: `05ebae8`
- provider: `ollama`
- generator_model: `gemma4:e4b`
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
| Citation accuracy (cited files ⊆ gold) | 95.5% |
| Citation location (a cited chunk in gold section/page) | 92.5% |
| Keyword coverage | 94.0% |
| Refusal accuracy (must-refuse) | 95.0% |
| False refusal rate (answerable) | 15.2% |
| Partial answers with caveat (answerable) | 0.0% |
| False refusal if partial = refusal (MVP-1 policy) | 15.2% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 95.0% |
| Answers in Korean (answered) | 92.5% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 123 |
| Retrieval p95 (ms) | 161 |
| Generation p50 (ms) | 5,744 |
| Generation p95 (ms) | 8,775 |
| Total p50 (ms) | 5,562 |
| Total p95 (ms) | 8,874 |
| Input tokens (total) | 178,830 |
| Output tokens (total) | 5,575 |
| Questions (answerable / must-refuse) / errors | 99 (79 / 20) / 0 |
| Must-refuse questions answered partially | 0 |

Refusal reasons: {'ANSWERED': 68, 'MODEL_REFUSED': 19, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 10}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| cross_doc | 7 | 100.0% | 85.7% | 100.0% | 100.0% | - | 42.9% | 0.0% | 6,975 |
| cross_language | 25 | 88.0% | 80.0% | 95.2% | 100.0% | - | 16.0% | 0.0% | 5,578 |
| diagnosis_request | 9 | - | - | - | - | 100.0% | - | - | 0 |
| factual | 36 | 100.0% | 94.4% | 93.9% | 87.9% | - | 8.3% | 0.0% | 6,024 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 4,596 |
| out_of_scope | 4 | - | - | - | - | 100.0% | - | - | 108 |
| table_lookup | 11 | 100.0% | 81.8% | 100.0% | 100.0% | - | 18.2% | 0.0% | 6,771 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 96.3% | 81.5% | 89.5% | 84.2% | 100.0% | 29.6% | 0.0% | 5,149 |
| ko | 65 | 96.2% | 90.4% | 97.9% | 97.9% | 92.3% | 7.7% | 0.0% | 6,114 |

## Failed questions

- **p02**: keywords 0%
- **p06**: keywords 0%
- **p10**: retrieval miss (got ['05_mfds_ich_gcp_ko.pdf']); citation ['05_mfds_ich_gcp_ko.pdf']
- **p12**: false refusal (MODEL_REFUSED)
- **p13**: false refusal (MODEL_REFUSED)
- **p14**: citation ['02_ich_e6r3_2025.pdf', '05_mfds_ich_gcp_ko.pdf']
- **p19**: citation ['04_mfds_anticancer_guideline_ko.pdf']; keywords 0%
- **p35**: section/page miss; keywords 0%
- **p40**: false refusal (MODEL_REFUSED)
- **p41**: should refuse but answered
- **p50**: false refusal (MODEL_REFUSED)
- **p55**: false refusal (MODEL_REFUSED)
- **p59**: false refusal (MODEL_REFUSED)
- **p60**: false refusal (MODEL_REFUSED)
- **p65**: false refusal (MODEL_REFUSED)
- **p72**: false refusal (MODEL_REFUSED)
- **p84**: false refusal (MODEL_REFUSED)
- **p85**: false refusal (MODEL_REFUSED)
- **p86**: false refusal (MODEL_REFUSED)

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| p01 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 원본 기록은 마케팅 신청 승인 또는 임상시험용 의약품의 출하 및 전달 중단 후 최소 2년 동안 보관해야 합니다 [1]. |
| p02 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 독심률을 최소화하기 위해 배치 크기를 명시하고 배치 크기를 정당화해야 하며, 배치 세션 간의 허용 가능한 시간 간격도 미리 정의해야 합니다 [1 |
| p03 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 이미지 판독 조정률이 중요한 고려 사항으로 간주되는 경우, 임상 시험 문서(프로토콜 및 통계 분석 계획)에 이 비율 결정 과정을 사전에 명시해야 |
| p04 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | FDA 이미징 헌장은 모달리티별 기술 세부 사항, 이미지 해석, 이미지 보관 절차를 포함하여 임상 시험 이미징 방법론을 설명해야 합니다 [1]. |
| p05 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 무작위 배정 임상시험에서 영상 판독자는 피험자의 치료 배정 정보에 대해 눈가림되어야 한다고 예상합니다 [4]. |
| p06 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 기존 의료 관행 영상 프로세스 표준은 장골 골절 또는 두개내 출혈 감지에 초점을 맞춘 종말점에는 합리적일 수 있습니다 [1]. |
| p07 | cross_language | ko | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 판독자 피로가 중요한 고려사항일 경우, 세션에서 판독할 수 있는 최대 이미지 수를 명시할지 고려해야 합니다 [3]. |
| p08 | factual | en | ANSWERED | Y | Y | 01_fda_imaging_endpoint_2018.pdf | 데이터 잠금(locking data)은 이미지 평가에 대한 추가적인 수정이 허용되지 않음을 의미합니다 [1]. |
| p09 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p10 | cross_language | ko | ANSWERED | N | N | 05_mfds_ich_gcp_ko.pdf | 시험자는 임상시험 대상자에게 즉각적인 위험요소를 제거하는 것이 필요하거나, 모니터 변경이나 전화번호 변경과 같이 행정적인 측면만 관련된 경우를  |
| p11 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | 적용 가능한 규제 요건에 따라 또는 스폰서가 해당 기록이 더 이상 필요하지 않다고 통보할 때까지, 그 중 더 긴 기간 동안 보관해야 합니다 [1 |
| p12 | cross_language | ko | MODEL_REFUSED | N | N | - | 문서에서 확인할 수 없습니다. |
| p13 | factual | en | MODEL_REFUSED | Y | Y | - | 문서에서 확인할 수 없습니다. |
| p14 | factual | en | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf, 05_mfds_ich_gcp_ko.pdf | 중앙 모니터링 과정은 현장 모니터링의 정도 및/또는 빈도를 보완하고 감소시킬 수 있는 추가적인 모니터링 역량을 제공하며, 신뢰할 수 있는 자료와 |
| p15 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | 임상시험이 조기 종료되거나 중지되면, 시험자/시험기관은 관련 규정에 따라 IRB/IEC 및 규제 당국에 신속하게 통지하고 적절한 설명을 제공해야 |
| p16 | cross_language | ko | ANSWERED | Y | Y | 02_ich_e6r3_2025.pdf | IRB/IEC는 최소 5명의 위원으로 구성되어야 합니다 [2]. |
| p17 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | ORR은 국제 표준(예: RECIST, Volumetric RECIST 또는 WHO 기준)에 따라 문서화되어야 하며, 이러한 기준의 수정은 특정 |
| p18 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 항암제 가이드라인에서는 최대내약용량(MTD)을 일반적으로 6명의 시험대상자 중 적어도 2명에서 용량제한독성(DLT)이 나타나는 용량으로  |
| p19 | factual | en | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 인간에게 최초 투여 시 정맥투여를 권장하는 이유는 생체이용률에 따른 변화를 배제할 수 있기 때문입니다 [4]. |
| p20 | cross_language | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | 이전 치료와 시험 치료 모두에서 질병 진행에 대한 평가가 독립적으로 이루어지면 분석이 더 설득력이 있습니다 [1]. |
| p21 | factual | en | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf | BSA 스케일링 투여가 노출의 환자 간 변동성을 줄인다는 개념에 대한 과학적 근거는 약하며, 높은 BSA를 가진 환자에게는 과다 노출, 낮은 B |
| p22 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 수용할 만한 독성이 발생한 경우, 환자가 회복될 때까지 기다린 후 재투여할 때는 동일 용량으로 최소 2주기 이상 투여하는 것이 바람직합니다 [1 |
| p23 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 최대내약용량(MTD), 용량제한독성(DLT) 및 2상 권장용량(RP2D)을 확인하고, 용량 및 용법에 따른 빈번한 부작용과 표적 장기 독성을 규 |
| p24 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 독성은 일반적으로 인정되는 시스템(예, 미국 국립암연구소[National Cancer Institute]의 이상반응에 대한 일반용어기준[Comm |
| p25 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 항암제 임상시험 이전에 음식-약물 상호작용 시험이 수행되어야 합니다 [1]. |
| p26 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | EDR과 LDR은 각각 현지 평가에서 BICR에 비해 조기 또는 후기에 진행을 선언하는 빈도에 근거합니다 [1]. |
| p27 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 완전한 BICR을 수행하는 것은 중요한 시험자 비뚤림이 예상되거나 보통의 치료효과가 기대되는 경우에 권고됩니다 [1] [3]. |
| p28 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 일반적으로 1차 평가변수는 전체 반응률(Overall Response Rate, ORR)로 설정하며, 개별 환자군에서의 효과를 별도로 관찰합니다 |
| p29 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 아니요, 시험약물 간의 비교는 권장되지 않습니다 [1]. |
| p30 | factual | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | PFS의 1차 분석을 위해 진행일은 평가가 예정된 시점이 아니라 진행이 확인된 시점을 근거로 해야 합니다 [3]. |
| p31 | cross_doc | ko | ANSWERED | Y | Y | 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인에서는 수용 가능한 독성이 발생한 경우 환자가 회복될 때까지 기다린 후 재투여가 가능하며, 이때는 동일 용량으로 최소 2주기 이 |
| p32 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 근거자료는 출처를 알 수 있고(attributable), 읽기 쉬우며(legible), 동시성을 입증할 수 있고(contemporaneous), |
| p33 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 의뢰자는 확인된 위험요소를 평가할 때 다음 세 가지를 고려해야 합니다: 오류 발생 가능도 [1], 해당 오류를 감지할 수 있는 정도 [1], 그 |
| p34 | factual | ko | ANSWERED | Y | Y | 05_mfds_ich_gcp_ko.pdf | 사전에 설정된 품질 허용한계(predefined quality tolerance limit)로부터 일탈(deviation)이 감지되면, 조치(a |
| p35 | factual | ko | ANSWERED | Y | N | 06_mfds_ai_device_lung_ko.pdf | 본 임상시험은 인공지능을 이용하여 폐CT 영상에서 폐암을 검출하고, 의사의 폐암·폐결절 진단을 보조하는 폐CT 영상 기반 폐암·폐결절 진단보조소 |
| p36 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 폐암 확진 환자 데이터와 양성 폐결절 확진 환자 데이터는 1:2의 비율로 강화 배정합니다 [1]. |
| p37 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 사용 전에는 선정된 표본 영상을 사전에 기준에 합당하게 선정된 참여 임상의(판독자) 3명이 판독을 수행하며, 개별 판독 후 참조표준을 이용하여  |
| p38 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 판독자는 참조표준을 구축하는 임상의와 독립적으로 구성해야 합니다 [2]. |
| p39 | factual | ko | ANSWERED | Y | Y | 06_mfds_ai_device_lung_ko.pdf | 시험 데이터셋은 디지털의료기기의 개발 과정동안 사용된 학습 데이터와의 독립성을 유지해야 합니다 [2]. |
| p40 | cross_language | en | MODEL_REFUSED | N | N | - | 문서에서 확인할 수 없습니다. |
| p41 | no_answer | ko | ANSWERED | - | - | 06_mfds_ai_device_lung_ko.pdf | CT slice 간격은 OOmm 이하이어야 합니다 [1]. |
| p42 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD의 경우, 가성진행 여부 재평가를 위한 추적검사는 일반적으로 권장되는 6–12주 간격과 달리 4–8주 후에 수행해야 합니다 [2]. |
| p43 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD는 모든 TL의 합이 가장 낮은 TL 합(Nadir)에 비해 최소 ≥20% (최소 ≥5 mm) 증가했거나, Non-TL의 명백한 진행이  |
| p44 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iCPD는 목표 합계의 추가 진행(≥ 5 mm), 또는 Non-TL의 추가 진행, 그리고/또는 수나 크기 면에서 새로운 측정 가능 및 비측정 가 |
| p45 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST의 정기적인 추적 반응 평가(follow-up response assessment)는 6~12주 간격으로 권장됩니다 [1]. |
| p46 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST에서는 환자당 최대 5개의 병변까지, 그리고 장기당 최대 2개의 병변을 표적 병변으로 정의할 수 있습니다 [1]. |
| p47 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | 측정하기에는 너무 작지만 여전히 보이는 표적 병변의 경우, 기본값 5 mm를 사용할 수 있습니다 [1]. |
| p48 | factual | en | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iUPD는 iSD, iPR 또는 iCR의 후속 최적 전체 반응을 무효화하지 않습니다 [1]. |
| p49 | cross_language | ko | ANSWERED | Y | Y | 07_irecist_how_to_2020.xml | iRECIST 논문은 면역항암제 투여 후 hyperprogression을 치료 전 상태 대비 ≥ 2배 증가한 종양 성장 동역학으로 설명했습니다  |
| p50 | factual | en | MODEL_REFUSED | Y | Y | - | 문서에서 확인할 수 없습니다. |
| p51 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p52 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p53 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | Lugano 분류에서 Deauville 1–3점은 완전 관해(CR)로 판정합니다 [2]. |
| p54 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | 부분 관해(PR)로 분류합니다 [2]. |
| p55 | cross_language | ko | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p56 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL은 최대 세 개의 표적 병변에 대한 단일 차원 측정(uni-dimensional measurements)을 권장하는 반면, Lugano |
| p57 | factual | en | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | MiR을 PR로 재코딩했을 때, 치료 종료 시점(EOT)의 RECIL과 Lugano 간의 일치도는 90.7%였습니다 [2]. |
| p58 | cross_language | ko | ANSWERED | Y | Y | 08_recil_vs_lugano_2019.xml | RECIL의 경우, 평가자 1과 2의 평균 판독 시간은 각각 3.4 ± 0.7분과 3.8 ± 0.6분이었고, Lugano의 경우 평균 판독 시간 |
| p59 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p60 | factual | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p61 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p62 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | RANO 2.0은 방사선 치료 종료 후 약 4주(21–35일)에 기저 스캔을 설정하여 PsP의 영향을 최소화합니다 [1]. |
| p63 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | Preliminary PD는 SPPD가 25% 이상 증가했거나 초기 치료 기간 12주 동안 새로운 조영 증강 병변이 발견된 경우로 정의됩니다 [ |
| p64 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 2D 측정 기준에서 부분반응(PR)의 임계값은 50% 초과 감소입니다 [1]. |
| p65 | table_lookup | en | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p66 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 측정 가능한 병변은 최소 단축 직경이 10mm이고 2D 영상에서 최소 두 개의 슬라이스에 걸쳐 확장되는 명확하게 경계가 구분된 병변으로 정의됩니 |
| p67 | factual | en | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 증강 또는 비증강 종양을 평가할 때는 최소 2개에서 최대 3개의 병변을 선택해야 하며 [1], 혼합 종양의 경우 증강 병변과 비증강 병변 각각에 |
| p68 | table_lookup | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 3D-T1w Pre의 슬라이스 두께는 1.5 mm 이하입니다 [1]. 3D-T1w Post의 슬라이스 두께도 1.5 mm 이하입니다 [1]. |
| p69 | cross_language | ko | ANSWERED | Y | Y | 09_rano2_review_2025.xml | 재발성 교모세포종의 경우, 치료 시작 전 표준화된 시간 간격(14일 이내)으로 기저 스캔을 사용해야 합니다 [2]. |
| p70 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p71 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p72 | cross_language | ko | MODEL_REFUSED | Y | N | - | 문서에서 확인할 수 없습니다. |
| p73 | factual | en | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | 아닙니다. 위험 분석 없이 임의의 유한한 수의 간접 식별자를 유지하는 것은 허용되지 않습니다 [5]. |
| p74 | cross_language | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf | MR k-space, CT projection, PET list mode 데이터가 원시 데이터의 예시이며, 이는 보고서의 범위 밖에 있습니다 [ |
| p75 | cross_doc | ko | ANSWERED | Y | Y | 10_midi_deid_report_2023.pdf, 11_dicom_ps3.15_annexE_2026d.html | MIDI 보고서는 어떤 접근 방식(규칙 기반 또는 통계적)을 사용하든, 인코딩된 DICOM 이미지가 DICOM 표준의 적합성을 유지하는 것이 중 |
| p76 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Patient's Name (0010,0010) 속성은 Std. Comp. IOD (from PS3.3)에 포함되며 Basic Prof.은 Z입 |
| p77 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Study Instance UID (0020,000D)의 Basic Profile은 U이며, Retain UIDs Option은 K입니다 [2] |
| p78 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Basic Profile은 Z이며, Retain Long. Full Dates Opt.는 K입니다 [2]. |
| p79 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Institution Name (0008,0080)의 Basic Prof.은 X/Z/D입니다 [1]. |
| p80 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | X는 속성(Attribute)을 제거하며, 해당 속성이 시퀀스(Sequence)인 경우 모든 시퀀스 항목과 포함된 속성을 제거합니다 [1]. |
| p81 | table_lookup | ko | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Basic Profile에서는 X로 처리되며, Retain Patient Characters 옵션은 K입니다 [1]. |
| p82 | table_lookup | en | ANSWERED | Y | Y | 11_dicom_ps3.15_annexE_2026d.html | Device Serial Number (0018,1000)의 기본 프로파일은 X/Z/D입니다 [2]. |
| p83 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p84 | cross_doc | ko | MODEL_REFUSED | Y | Y | - | 제공된 문서에는 iRECIST와 RANO 2.0에서 진행을 확인하기 위한 추가 스캔 시기에 대한 정보가 없습니다. |
| p85 | cross_doc | en | MODEL_REFUSED | Y | Y | - | RECIL은 'minor response'를 정의하는 방식에 대한 정보가 제공되지 않았습니다. RANO 2.0의 2D 기준에서 'minor re |
| p86 | cross_doc | en | MODEL_REFUSED | Y | N | - | 제공된 문서에는 종양 영상의 독립적 또는 중앙 집중식 검토에 대한 EMA 항암제 가이드라인과 FDA 영상 종점 가이드라인의 내용이 나와 있지 않 |
| p87 | cross_doc | ko | ANSWERED | Y | Y | 03_ema_anticancer_rev6.pdf, 04_mfds_anticancer_guideline_ko.pdf | 식약처 가이드라인은 인간에게 최초 투여 시 정맥투여를 권장하는 이유는 생체이용률에 따른 변화를 배제할 수 있기 때문입니다 [1]. EMA 가이드 |
| p88 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p89 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p90 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p91 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p92 | diagnosis_request | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p93 | diagnosis_request | en | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p94 | no_answer | en | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p95 | no_answer | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p96 | out_of_scope | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| p97 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| p98 | out_of_scope | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| p99 | out_of_scope | en | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
