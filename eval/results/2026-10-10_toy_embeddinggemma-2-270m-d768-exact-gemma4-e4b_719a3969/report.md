# RAG Eval Report — toy / embeddinggemma-2-270m-d768-exact-gemma4-e4b (2026-10-10T16:41:38)

## Config

- run_at: `2026-10-10T16:41:38`
- label: `embeddinggemma-2-270m-d768-exact-gemma4-e4b`
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
| Retrieval hit@k (file) | 89.5% |
| Section/page hit@k | 89.5% |
| Citation accuracy (cited files ⊆ gold) | 88.2% |
| Citation location (a cited chunk in gold section/page) | 88.2% |
| Keyword coverage | 94.1% |
| Refusal accuracy (must-refuse) | 100.0% |
| False refusal rate (answerable) | 10.5% |
| Partial answers with caveat (answerable) | 0.0% |
| False refusal if partial = refusal (MVP-1 policy) | 10.5% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 100.0% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 52 |
| Retrieval p95 (ms) | 59 |
| Generation p50 (ms) | 2,720 |
| Generation p95 (ms) | 5,292 |
| Total p50 (ms) | 2,158 |
| Total p95 (ms) | 5,153 |
| Input tokens (total) | 18,315 |
| Output tokens (total) | 1,957 |
| Questions (answerable / must-refuse) / errors | 25 (19 / 6) / 0 |
| Must-refuse questions answered partially | 0 |

Refusal reasons: {'ANSWERED': 17, 'MODEL_REFUSED': 3, 'OUT_OF_SCOPE': 5}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| factual | 25 | 89.5% | 89.5% | 88.2% | 94.1% | 100.0% | 10.5% | 0.0% | 2,158 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| ko | 25 | 89.5% | 89.5% | 88.2% | 94.1% | 100.0% | 10.5% | 0.0% | 2,158 |

## Failed questions

- **q01**: citation ['dicom-upload-guide.md', 'error-code-guide.md']
- **q04**: false refusal (OUT_OF_SCOPE)
- **q13**: citation ['error-code-guide.md', 'qa-checklist.md']
- **q17**: false refusal (OUT_OF_SCOPE)
- **q18**: keywords 0%

## Per-question

| id | type | lang | result | hit | sec | cited | answer |
|---|---|---|---|---|---|---|---|
| q01 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | DICOM 업로드 실패 시 운영자는 다음 항목들을 먼저 확인해야 합니다:  1. 파일 형식이 DICOM Part 10인지 확인해야 합니다 [1] |
| q02 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | 업로드 가능한 파일 형식은 DICOM Part 10 파일(.dcm)과 DICOM 파일을 묶은 ZIP 파일입니다. JPG, PNG, PDF와 같은 |
| q03 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md | 모든 영상은 StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID, Modality, Rows, Colu |
| q04 | factual | ko | OUT_OF_SCOPE | N | N | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q05 | factual | ko | ANSWERED | Y | Y | dicom-upload-guide.md, error-code-guide.md | 한 번에 업로드할 수 있는 최대 용량은 2GB입니다. 이 용량을 초과할 경우 Series 단위로 나누어 업로드해야 합니다. [1], [2] |
| q06 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | E103 오류는 'Subject ID not matched'를 의미하며, 이는 PatientID 값이 EDC Subject ID와 불일치할 때  |
| q07 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | E201 발생 시 개발자는 메시지 큐 적체 여부와 저장소(Object Storage) 응답 지연을 확인해야 합니다 [1]. |
| q08 | factual | ko | ANSWERED | Y | Y | error-code-guide.md | 로그 레벨 WARN은 업로드는 되었으나 QC 확인이 필요한 경우(예: 권장 태그 누락)에 사용됩니다 [1]. |
| q09 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | PatientBirthDate 태그는 삭제하는 것을 원칙으로 하며, 연령 정보가 필요한 경우에만 PatientAge만 유지합니다 [1]. |
| q10 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | StudyDate는 직접 식별자는 아니지만, 다른 정보와 결합될 경우 재식별 위험이 있어 민감 정보 가능 항목으로 관리합니다 [1]. |
| q11 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | 비식별화되지 않은 영상(PHI 포함)이 업로드된 것을 발견하면 다음 순서로 대응해야 합니다: 첫째, 해당 업로드를 즉시 격리(quarantine |
| q12 | factual | ko | ANSWERED | Y | Y | privacy-sop-sample.md | 영상 픽셀에 이름 등이 새겨진(burned-in) 경우, 태그 비식별화로는 제거되지 않습니다 [1]. 따라서 BurnedInAnnotation  |
| q13 | factual | ko | ANSWERED | Y | Y | error-code-guide.md, qa-checklist.md | QC 결과에서 WARNING과 FAIL은 다음과 같이 다릅니다:  *   **WARNING**: 권장 태그가 누락되었거나 경미한 프로토콜 이탈이 |
| q14 | factual | ko | ANSWERED | Y | Y | qa-checklist.md | QC에서 WARNING 또는 FAIL이 발생하여 사이트에 Query가 발행된 경우, 사이트는 영업일 기준 3일 이내에 응답해야 합니다 [1]. |
| q15 | factual | ko | ANSWERED | Y | Y | operator-faq.txt | 헬프데스크는 평일 09:00부터 18:00(KST)까지 운영하며, 긴급 장애(전체 업로드 불가)의 경우 24시간 당직 번호로 연락해야 합니다 [ |
| q16 | factual | ko | ANSWERED | Y | Y | operator-faq.txt | 업로드 중 네트워크가 끊겼을 경우, 업로드는 Series 단위로 이어받기(resume)를 지원하므로 이를 사용하는 것이 좋습니다. 만약 같은 S |
| q17 | factual | ko | OUT_OF_SCOPE | N | N | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q18 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf | 영상 촬영 시점은 Screening(첫 투여 전 28일 이내), Week 6 및 Week 12(이후 12주 간격으로 반복), End of Tre |
| q19 | factual | ko | ANSWERED | Y | Y | clinical-trial-protocol-sample.pdf, dicom-upload-guide.md | 사이트는 촬영일로부터 영업일 기준 5일 이내에 영상을 업로드해야 합니다 [1], [2]. |
| q20 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q21 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q22 | factual | ko | OUT_OF_SCOPE | - | - | - | 이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. 문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다. |
| q23 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| q24 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
| q25 | factual | ko | MODEL_REFUSED | - | - | - | 문서에서 확인할 수 없습니다. |
