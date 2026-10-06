# RAG Eval Report — toy / bge-m3-hybrid-gemma4-e4b (2026-10-07T00:38:43)

## Config

- run_at: `2026-10-07T00:38:43`
- label: `bge-m3-hybrid-gemma4-e4b`
- corpus: `toy`
- corpus_root: `samples/documents`
- corpus_sha256: `719a3969baacdd3013ca04f0646bef35de2180cf9bc092b3b3896eb022031417`
- questions_file: `questions.yaml`
- questions_sha256: `19e9dfb63fcf82cf5ddc9204c3ab225575fc719d04014630d463538db8720ada`
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
| Retrieval hit@k (file) | 100.0% |
| Section/page hit@k | 100.0% |
| Citation accuracy (cited files ⊆ gold) | 84.2% |
| Citation location (a cited chunk in gold section/page) | 100.0% |
| Keyword coverage | 100.0% |
| Refusal accuracy (must-refuse) | 100.0% |
| False refusal rate (answerable) | 0.0% |
| Retrieval p50 (ms) | 118 |
| Retrieval p95 (ms) | 137 |
| Generation p50 (ms) | 4,302 |
| Generation p95 (ms) | 9,900 |
| Total p50 (ms) | 4,285 |
| Total p95 (ms) | 10,005 |
| Input tokens (total) | 19,581 |
| Output tokens (total) | 2,382 |
| Questions (answerable / must-refuse) / errors | 25 (19 / 6) / 0 |

Refusal reasons: {'ANSWERED': 19, 'MODEL_REFUSED': 2, 'NO_EVIDENCE': 1, 'OUT_OF_SCOPE': 3}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | refusal_correctness | false_refusal_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|
| factual | 25 | 100.0% | 100.0% | 84.2% | 100.0% | 0.0% | 4,285 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | refusal_correctness | false_refusal_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|
| ko | 25 | 100.0% | 100.0% | 84.2% | 100.0% | 0.0% | 4,285 |

## Failed questions

- **q01**: citation ['dicom-upload-guide.md', 'error-code-guide.md']
- **q06**: citation ['dicom-upload-guide.md', 'error-code-guide.md']
- **q17**: citation ['clinical-trial-protocol-sample.pdf', 'dicom-upload-guide.md', 'qa-checklist.md']

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| q01 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | DICOM 업로드 실패 시 운영자는 다음 항목들을 먼저 확인해야 합니다:   1. 파일 형식이 DICOM Part 10인지 [1], [2] 2. |
| q02 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | 업로드 가능한 파일 형식은 DICOM Part 10 파일(.dcm)과 DICOM 파일을 묶은 ZIP 파일입니다 [1]. JPG, PNG, PDF |
| q03 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | 모든 영상에는 StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID, Modality, Rows, Col |
| q04 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | CT와 MR 영상은 공간 정보 확인을 위해 PixelSpacing, SliceThickness, ImagePositionPatient, Imag |
| q05 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | 한 번에 업로드할 수 있는 최대 용량은 2GB입니다 [2], [1]. |
| q06 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | E103 오류는 'Subject ID not matched'를 의미하며, 이는 PatientID 값이 EDC Subject ID와 불일치할 때  |
| q07 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | E201 오류가 발생했을 경우, 개발자는 메시지 큐 적체 여부와 저장소(Object Storage) 응답 지연을 확인해야 합니다 [1]. |
| q08 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | 로그 레벨 WARN은 업로드는 되었지만 QC 확인이 필요한 경우(예: 권장 태그 누락)에 사용합니다. [1] |
| q09 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | PatientBirthDate 태그는 삭제하는 것이 원칙이며, 연령 정보가 필요한 경우에만 PatientAge를 유지합니다 [1]. |
| q10 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | StudyDate는 직접적인 식별자는 아니지만, 다른 정보와 결합될 경우 재식별 위험이 있어 민감 정보 가능 항목으로 관리합니다. [1] |
| q11 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | 비식별화되지 않은 영상(PHI 포함)이 업로드된 것을 발견했을 경우, 다음 순서로 대응해야 합니다. 첫째, 해당 업로드를 즉시 격리(quaran |
| q12 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | 영상 픽셀에 이름 등이 새겨진(burned-in) 경우, 태그 비식별화로는 제거되지 않습니다 [1]. 따라서 BurnedInAnnotation  |
| q13 | factual | ko | ANSWERED | Y | Y | qa-checklist.md | QC 결과가 WARNING인 경우, 권장 태그 누락 또는 경미한 프로토콜 이탈로 인해 사이트에 확인 요청(Query)이 발행되며 판독 대기열에  |
| q14 | factual | ko | ANSWERED | Y | Y | qa-checklist.md | 사이트는 Query를 발행받은 후 영업일 기준 3일 이내에 응답해야 합니다. [1] |
| q15 | factual | ko | ANSWERED | Y | Y | operator-faq.txt | 헬프데스크는 평일 09:00부터 18:00(KST)까지 운영합니다. 다만, 전체 업로드가 불가능한 긴급 장애 상황에서는 24시간 당직 번호로 연 |
| q16 | factual | ko | ANSWERED | Y | Y | operator-faq.txt | 업로드 중 네트워크가 끊겼을 경우, 업로드는 Series 단위로 이어받기(resume)를 지원하므로 이어받기를 사용해야 합니다 [1]. |
| q17 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, dicom-upload-guide.md, qa-checklist.md | CT 촬영 시 SliceThickness는 5mm 이하가 권장되며 [2], [1], [3], [2], [1] 등, 흉부 CT 영상의 경우 5mm |
| q18 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, dicom-upload-guide.md | 영상 촬영 시점과 허용되는 방문 창(visit window)은 다음과 같습니다. 첫 투여 전 28일 이내에 'Screening' 영상이 촬영되어 |
| q19 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, dicom-upload-guide.md | 영상 업로드 기한은 촬영일로부터 영업일 기준 5일 이내입니다 [1], [4]. |
| q20 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q21 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q22 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q23 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| q24 | factual | ko | NO_EVIDENCE | - | - | - | 문서에서 확인할 수 없습니다. |
| q25 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
