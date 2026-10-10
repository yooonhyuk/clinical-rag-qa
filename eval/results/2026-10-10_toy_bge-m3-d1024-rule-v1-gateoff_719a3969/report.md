# RAG Eval Report — toy / bge-m3-d1024-rule-v1-gateoff (2026-10-10T20:00:17)

## Config

- run_at: `2026-10-10T20:00:17`
- label: `bge-m3-d1024-rule-v1-gateoff`
- corpus: `toy`
- corpus_root: `samples/documents`
- corpus_classification: `synthetic-sample`
- corpus_sha256: `719a3969baacdd3013ca04f0646bef35de2180cf9bc092b3b3896eb022031417`
- questions_file: `questions.yaml`
- questions_sha256: `19e9dfb63fcf82cf5ddc9204c3ab225575fc719d04014630d463538db8720ada`
- git_commit: `3342ce5`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `none`
- partial_answers: `True`
- rag_prompt_variant: `default`
- eval_process_max_rss_mb: `140`
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
- min_relevance_score: `-1.0`
- scope_classifier: `embedding`
- scope_margin: `0.056`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 100.0% |
| Section/page hit@k | 100.0% |
| Citation accuracy (cited files ⊆ gold) | 89.5% |
| Citation location (a cited chunk in gold section/page) | 100.0% |
| Keyword coverage | 94.7% |
| Refusal accuracy (must-refuse) | 100.0% |
| False refusal rate (answerable) | 0.0% |
| Partial answers with caveat (answerable) | 0.0% |
| False refusal if partial = refusal (MVP-1 policy) | 0.0% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 100.0% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 57 |
| Retrieval p95 (ms) | 84 |
| Generation p50 (ms) | 3,534 |
| Generation p95 (ms) | 7,330 |
| Total p50 (ms) | 3,379 |
| Total p95 (ms) | 7,178 |
| Input tokens (total) | 22,155 |
| Output tokens (total) | 2,215 |
| Questions (answerable / must-refuse) / errors | 25 (19 / 6) / 0 |
| Must-refuse questions answered partially | 0 |

Refusal reasons: {'ANSWERED': 19, 'MODEL_REFUSED': 3, 'OUT_OF_SCOPE': 3}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| factual | 25 | 100.0% | 100.0% | 89.5% | 94.7% | 100.0% | 0.0% | 0.0% | 3,379 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| ko | 25 | 100.0% | 100.0% | 89.5% | 94.7% | 100.0% | 0.0% | 0.0% | 3,379 |

## Failed questions

- **q01**: citation ['dicom-upload-guide.md', 'error-code-guide.md']
- **q13**: citation ['error-code-guide.md', 'qa-checklist.md']
- **q18**: keywords 0%

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| q01 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | DICOM 업로드 실패 시 운영자는 다음 항목들을 먼저 확인해야 합니다:  1. 파일 형식이 DICOM Part 10인지 확인해야 합니다 [1] |
| q02 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | 업로드 가능한 파일 형식은 DICOM Part 10 파일(.dcm)과 DICOM 파일을 묶은 ZIP 파일입니다. JPG, PNG, PDF와 같은 |
| q03 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | 모든 영상에는 StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID, Modality, Rows, Col |
| q04 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | CT와 MR 영상은 공간 정보 확인을 위해 PixelSpacing, SliceThickness, ImagePositionPatient, Imag |
| q05 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | 한 번에 업로드할 수 있는 최대 용량은 2GB입니다. 이 용량을 초과할 경우 Series 단위로 나누어 업로드해야 합니다. [1], [2] |
| q06 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | E103 오류는 'Subject ID not matched'를 의미하며, 이는 PatientID 값이 EDC Subject ID와 불일치할 때  |
| q07 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | E201 발생 시 개발자는 메시지 큐 적체 여부와 저장소(Object Storage) 응답 지연을 확인해야 합니다 [1]. |
| q08 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | 로그 레벨 WARN은 업로드는 되었으나 QC 확인이 필요한 경우(예: 권장 태그 누락)에 사용됩니다 [1]. |
| q09 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | PatientBirthDate 태그는 삭제하는 것이 원칙이며, 연령 정보가 필요한 경우에만 PatientAge를 유지할 수 있습니다 [1]. |
| q10 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | StudyDate는 직접 식별자는 아니지만, 다른 정보와 결합할 경우 재식별 위험이 있어 민감 정보 가능 항목으로 관리합니다 [1]. |
| q11 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | 비식별화되지 않은 영상(PHI 포함)이 업로드된 것을 발견했을 경우, 다음 순서로 대응해야 합니다: 1. 즉시 해당 업로드를 격리(quarant |
| q12 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | 영상 픽셀에 이름 등이 새겨진(burned-in) 경우, 태그 비식별화로는 제거되지 않으므로, BurnedInAnnotation 태그가 YES이 |
| q13 | factual | ko | ANSWERED | Y | Y | error-code-guide.md, qa-checklist.md | QC 결과에서 WARNING과 FAIL은 다음과 같이 다릅니다:  *   **WARNING**: 권장 태그가 누락되었거나 경미한 프로토콜 이탈이 |
| q14 | factual | ko | ANSWERED | Y | Y | qa-checklist.md | QC에서 WARNING 또는 FAIL이 발생하여 사이트에 Query가 발행된 경우, 사이트는 영업일 기준 3일 이내에 응답해야 합니다 [1]. |
| q15 | factual | ko | ANSWERED | Y | Y | operator-faq.txt | 헬프데스크는 평일 09:00부터 18:00(KST)까지 운영하며, 긴급 장애(전체 업로드 불가)의 경우 24시간 당직 번호로 연락해야 합니다 [ |
| q16 | factual | ko | ANSWERED | Y | Y | operator-faq.txt | 업로드 중 네트워크가 끊겼을 경우, 업로드는 Series 단위로 이어받기(resume)를 지원하므로 이를 사용해야 합니다. 같은 Series를  |
| q17 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, qa-checklist.md | CT의 경우, 권장 촬영 조건은 SliceThickness가 5mm 이하이며, 구체적으로는 1.25mm~2.5mm가 권장됩니다 [1]. 또한,  |
| q18 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, dicom-upload-guide.md | 영상 촬영 시점과 허용되는 방문 창(visit window)은 다음과 같습니다:  1. **방문 명칭 및 시점:**     *   **Scree |
| q19 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, dicom-upload-guide.md | 사이트는 촬영일로부터 영업일 기준 5일 이내에 영상을 업로드해야 합니다 [1], [2]. |
| q20 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q21 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q22 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q23 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| q24 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| q25 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
