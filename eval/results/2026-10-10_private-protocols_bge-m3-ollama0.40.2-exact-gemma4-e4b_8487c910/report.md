# RAG Eval Report — private / bge-m3-ollama0.40.2-exact-gemma4-e4b (2026-10-10T16:17:53)

## Config

- run_at: `2026-10-10T16:17:53`
- label: `bge-m3-ollama0.40.2-exact-gemma4-e4b`
- corpus: `private`
- corpus_root: `local`
- corpus_classification: `licensed-local-only`
- corpus_sha256: `8487c910ed8d347f0a8bdd2e843ee41785cc49b824c26907790d5a5709ac1f1e`
- questions_file: `protocol_questions.yaml`
- questions_sha256: `16394c4a90f3f53ef357f24d993a8ebb195902c981b5f2eea245216496891853`
- git_commit: `3342ce5`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `none`
- partial_answers: `True`
- rag_prompt_variant: `default`
- eval_process_max_rss_mb: `160`
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
- min_relevance_score: `0.45`
- scope_classifier: `embedding`
- scope_margin: `0.056`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 75.0% |
| Section/page hit@k | 45.3% |
| Citation accuracy (cited files ⊆ gold) | 45.7% |
| Citation location (a cited chunk in gold section/page) | 45.7% |
| Keyword coverage | 59.4% |
| Refusal accuracy (must-refuse) | 86.7% |
| False refusal rate (answerable) | 28.1% |
| Partial answers with caveat (answerable) | 23.4% |
| False refusal if partial = refusal (MVP-1 policy) | 51.6% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 93.3% |
| Answers in Korean (answered) | 100.0% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 100 |
| Retrieval p95 (ms) | 127 |
| Generation p50 (ms) | 5,587 |
| Generation p95 (ms) | 10,309 |
| Total p50 (ms) | 4,966 |
| Total p95 (ms) | 9,567 |
| Input tokens (total) | 109,476 |
| Output tokens (total) | 9,331 |
| Questions (answerable / must-refuse) / errors | 79 (64 / 15) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 32, 'ANSWERED_PARTIAL': 16, 'MODEL_REFUSED': 16, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 13}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| bicr_process | 10 | 80.0% | 60.0% | 44.4% | 33.3% | - | 10.0% | 60.0% | 6,281 |
| cross_doc | 5 | 80.0% | 40.0% | 50.0% | 12.5% | - | 20.0% | 20.0% | 7,030 |
| cross_trial | 5 | 80.0% | 40.0% | 50.0% | 62.5% | - | 20.0% | 60.0% | 7,489 |
| diagnosis_request | 5 | - | - | - | - | 100.0% | - | - | 0 |
| eligibility_imaging | 11 | 72.7% | 27.3% | 40.0% | 60.0% | - | 54.5% | 9.1% | 4,141 |
| imaging_schedule | 11 | 54.5% | 36.4% | 66.7% | 80.6% | - | 45.5% | 9.1% | 4,396 |
| no_answer | 7 | - | - | - | - | 71.4% | - | - | 3,525 |
| out_of_scope | 3 | - | - | - | - | 100.0% | - | - | 81 |
| response_criteria | 13 | 76.9% | 38.5% | 55.6% | 72.2% | - | 30.8% | 0.0% | 4,471 |
| sap_endpoint | 9 | 88.9% | 77.8% | 22.2% | 77.8% | - | 0.0% | 33.3% | 5,639 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 30 | 79.2% | 45.8% | 41.2% | 41.2% | 83.3% | 29.2% | 16.7% | 4,867 |
| ko | 49 | 72.5% | 45.0% | 48.3% | 70.1% | 88.9% | 27.5% | 27.5% | 4,966 |

## Failed questions

- **r01**: section/page miss
- **r02**: false refusal (MODEL_REFUSED)
- **r03**: section/page miss; citation ['NCT01712490_Prot_000.pdf']; keywords 33%
- **r04**: citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']; keywords 50%
- **r07**: false refusal (OUT_OF_SCOPE)
- **r08**: false refusal (OUT_OF_SCOPE)
- **r09**: false refusal (OUT_OF_SCOPE)
- **r11**: false refusal (OUT_OF_SCOPE)
- **r12**: citation ['NCT02987543_Prot_005.pdf', 'NCT04494425_Prot_002.pdf']; keywords 0%
- **r13**: retrieval miss (got ['NCT03375320_Prot_SAP_000.pdf', 'NCT03785964_SAP_001.pdf', 'NCT04427072_Prot_000.pdf', 'NCT04494425_Prot_002.pdf']); citation ['NCT04427072_Prot_000.pdf']; keywords 0%
- **r14**: section/page miss; keywords 0%
- **r15**: false refusal (MODEL_REFUSED)
- **r17**: section/page miss; citation ['NCT02987543_Prot_005.pdf']; keywords 0%
- **r19**: keywords 0%
- **r20**: retrieval miss (got ['NCT03517137_Prot_SAP_000.pdf', 'NCT03568461_Prot_002.pdf', 'NCT03739684_SAP_001.pdf']); citation ['NCT03517137_Prot_SAP_000.pdf', 'NCT03568461_Prot_002.pdf']; keywords 0%
- **r21**: citation ['NCT03375320_Prot_SAP_000.pdf', 'NCT04494425_SAP_003.pdf']
- **r22**: section/page miss
- **r23**: section/page miss
- **r24**: false refusal (MODEL_REFUSED)
- **r25**: false refusal (MODEL_REFUSED)
- **r26**: section/page miss; citation ['NCT04698187_SAP_001.pdf']; keywords 0%
- **r27**: false refusal (MODEL_REFUSED)
- **r30**: false refusal (OUT_OF_SCOPE)
- **r31**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r32**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']; keywords 0%
- **r33**: section/page miss
- **r34**: section/page miss; citation ['NCT02987543_Prot_005.pdf', 'NCT03785964_Prot_000.pdf']; keywords 50%
- **r35**: false refusal (MODEL_REFUSED)
- **r36**: citation ['NCT03785964_Prot_000.pdf', 'NCT03785964_SAP_001.pdf']; keywords 0%
- **r37**: section/page miss
- **r38**: section/page miss; citation ['NCT04494425_Prot_002.pdf', 'NCT04698187_Prot_000.pdf', 'protocol_NCT04489771.pdf']; keywords 0%
- **r39**: false refusal (OUT_OF_SCOPE)
- **r40**: false refusal (MODEL_REFUSED)
- **r41**: section/page miss; citation ['protocol_NCT03761056.pdf']
- **r42**: false refusal (MODEL_REFUSED)
- **r43**: false refusal (OUT_OF_SCOPE)
- **r44**: false refusal (MODEL_REFUSED)
- **r45**: section/page miss
- **r46**: citation ['NCT02667587_SAP_001.pdf', 'NCT03785964_SAP_001.pdf']
- **r47**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r48**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r49**: citation ['NCT03517137_Prot_SAP_000.pdf']
- **r50**: retrieval miss (got ['NCT03785964_SAP_001.pdf', 'NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']); citation ['NCT04698187_SAP_001.pdf']; keywords 0%
- **r51**: section/page miss; keywords 0%
- **r52**: citation ['NCT01712490_Prot_000.pdf', 'NCT01712490_SAP_001.pdf', 'NCT03517137_Prot_SAP_000.pdf']
- **r53**: citation ['NCT03739684_Prot_000.pdf', 'NCT03739684_SAP_001.pdf']
- **r55**: section/page miss; citation ['NCT04494425_Prot_002.pdf', 'NCT04494425_SAP_003.pdf']
- **r56**: section/page miss; keywords 0%
- **r57**: false refusal (MODEL_REFUSED)
- **r59**: citation ['NCT03568461_Prot_002.pdf']; keywords 50%
- **r60**: false refusal (MODEL_REFUSED)
- **r61**: keywords 0%
- **r62**: section/page miss; keywords 0%
- **r63**: section/page miss; citation ['NCT03517137_Prot_SAP_000.pdf']; keywords 50%
- **r64**: citation ['NCT02987543_SAP_015.pdf', 'NCT04494425_Prot_002.pdf', 'NCT04494425_SAP_003.pdf']; keywords 0%
- **r66**: should refuse but answered
- **r69**: should refuse but a partial answer

Per-question answers are kept with the local-only corpus, not here.
