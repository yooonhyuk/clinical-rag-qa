# RAG Eval Report — private / embeddinggemma-2-270m-d512-exact-gemma4-e4b (2026-10-10T17:24:45)

## Config

- run_at: `2026-10-10T17:24:45`
- label: `embeddinggemma-2-270m-d512-exact-gemma4-e4b`
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
- eval_process_max_rss_mb: `161`
- ollama_version: `0.40.2`
- embedding_model: `embeddinggemma-2:270m`
- embedding_dim: `512`
- embedding_truncate_dim: `512`
- embedding_query_prefix: `task: search result | query: `
- embedding_document_prefix: `title: none | text: `
- hybrid_search: `False`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `-0.148`
- scope_classifier: `embedding`
- scope_margin: `0.0369`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 75.0% |
| Section/page hit@k | 34.4% |
| Citation accuracy (cited files ⊆ gold) | 58.5% |
| Citation location (a cited chunk in gold section/page) | 35.8% |
| Keyword coverage | 59.4% |
| Refusal accuracy (must-refuse) | 86.7% |
| False refusal rate (answerable) | 17.2% |
| Partial answers with caveat (answerable) | 28.1% |
| False refusal if partial = refusal (MVP-1 policy) | 45.3% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 93.3% |
| Answers in Korean (answered) | 100.0% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 85 |
| Retrieval p95 (ms) | 138 |
| Generation p50 (ms) | 5,235 |
| Generation p95 (ms) | 10,017 |
| Total p50 (ms) | 5,005 |
| Total p95 (ms) | 9,481 |
| Input tokens (total) | 102,202 |
| Output tokens (total) | 9,173 |
| Questions (answerable / must-refuse) / errors | 79 (64 / 15) / 0 |
| Must-refuse questions answered partially | 1 |

Refusal reasons: {'ANSWERED': 36, 'ANSWERED_PARTIAL': 19, 'MODEL_REFUSED': 11, 'OUT_OF_SCOPE': 13}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| bicr_process | 10 | 70.0% | 50.0% | 66.7% | 44.4% | - | 10.0% | 40.0% | 5,504 |
| cross_doc | 5 | 80.0% | 40.0% | 50.0% | 25.0% | - | 20.0% | 40.0% | 6,382 |
| cross_trial | 5 | 80.0% | 40.0% | 0.0% | 62.5% | - | 20.0% | 80.0% | 4,789 |
| diagnosis_request | 5 | - | - | - | - | 100.0% | - | - | 0 |
| eligibility_imaging | 11 | 63.6% | 27.3% | 66.7% | 68.5% | - | 18.2% | 18.2% | 6,204 |
| imaging_schedule | 11 | 54.5% | 27.3% | 85.7% | 69.0% | - | 36.4% | 9.1% | 4,631 |
| no_answer | 7 | - | - | - | - | 71.4% | - | - | 3,517 |
| out_of_scope | 3 | - | - | - | - | 100.0% | - | - | 1,923 |
| response_criteria | 13 | 92.3% | 23.1% | 63.6% | 68.2% | - | 15.4% | 15.4% | 5,759 |
| sap_endpoint | 9 | 88.9% | 44.4% | 44.4% | 61.1% | - | 0.0% | 33.3% | 5,614 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 30 | 79.2% | 33.3% | 52.4% | 34.1% | 83.3% | 12.5% | 25.0% | 4,884 |
| ko | 49 | 72.5% | 35.0% | 62.5% | 76.0% | 88.9% | 20.0% | 30.0% | 5,178 |

## Failed questions

- **r01**: section/page miss
- **r02**: false refusal (MODEL_REFUSED)
- **r03**: section/page miss; keywords 33%
- **r04**: section/page miss; keywords 50%
- **r07**: retrieval miss (got ['NCT03568461_Prot_002.pdf', 'NCT03820986_Prot_SAP_001.pdf', 'NCT04236141_SAP_001.pdf']); citation ['NCT04236141_SAP_001.pdf']; keywords 0%
- **r08**: false refusal (OUT_OF_SCOPE)
- **r09**: false refusal (OUT_OF_SCOPE)
- **r11**: false refusal (MODEL_REFUSED)
- **r12**: section/page miss; citation ['NCT02987543_SAP_015.pdf', 'NCT04494425_SAP_003.pdf']; keywords 0%
- **r13**: retrieval miss (got ['NCT03375320_Prot_SAP_000.pdf']); citation ['NCT03375320_Prot_SAP_000.pdf']; keywords 0%
- **r17**: section/page miss
- **r18**: retrieval miss (got ['NCT02667587_SAP_001.pdf', 'NCT02987543_Prot_005.pdf', 'NCT03785964_SAP_002.pdf', 'NCT04427072_SAP_001.pdf', 'NCT04494425_SAP_003.pdf']); citation ['NCT02987543_Prot_005.pdf', 'NCT04494425_SAP_003.pdf']; keywords 0%
- **r19**: keywords 0%
- **r20**: false refusal (OUT_OF_SCOPE)
- **r21**: keywords 0%
- **r22**: section/page miss
- **r23**: section/page miss
- **r24**: section/page miss; citation ['NCT03568461_Prot_002.pdf', 'NCT04427072_Prot_000.pdf']
- **r25**: false refusal (MODEL_REFUSED)
- **r26**: section/page miss; citation ['NCT04698187_SAP_001.pdf']; keywords 0%
- **r27**: section/page miss; citation ['NCT04236141_Prot_000.pdf', 'NCT04236141_SAP_001.pdf']; keywords 0%
- **r29**: section/page miss
- **r30**: false refusal (OUT_OF_SCOPE)
- **r31**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r32**: keywords 0%
- **r33**: section/page miss
- **r34**: section/page miss; keywords 50%
- **r35**: section/page miss; citation ['NCT02987543_Prot_005.pdf', 'NCT04494425_Prot_002.pdf']
- **r36**: keywords 0%
- **r38**: retrieval miss (got ['NCT03345095_Prot_000.pdf', 'NCT03568461_Prot_002.pdf', 'NCT03785964_Prot_000.pdf', 'NCT04494425_Prot_002.pdf']); citation ['NCT03345095_Prot_000.pdf', 'NCT03568461_Prot_002.pdf', 'NCT03785964_Prot_000.pdf']
- **r39**: retrieval miss (got ['NCT02667587_Prot_000.pdf', 'NCT04494425_Prot_002.pdf', 'protocol_NCT04489771.pdf']); citation ['NCT04494425_Prot_002.pdf', 'protocol_NCT04489771.pdf']; keywords 0%
- **r40**: keywords 50%
- **r41**: section/page miss
- **r42**: section/page miss
- **r43**: false refusal (OUT_OF_SCOPE)
- **r44**: false refusal (OUT_OF_SCOPE)
- **r45**: section/page miss; keywords 67%
- **r49**: section/page miss; citation ['NCT03517137_Prot_SAP_000.pdf']; keywords 0%
- **r50**: section/page miss; citation ['NCT04236141_Prot_000.pdf', 'NCT04236141_SAP_001.pdf']; keywords 50%
- **r51**: section/page miss; citation ['NCT04494425_SAP_003.pdf']; keywords 0%
- **r52**: retrieval miss (got ['NCT01712490_Prot_000.pdf', 'NCT01712490_SAP_001.pdf', 'NCT03785964_SAP_001.pdf']); citation ['NCT01712490_Prot_000.pdf', 'NCT01712490_SAP_001.pdf', 'NCT03785964_SAP_001.pdf']; keywords 0%
- **r53**: section/page miss; citation ['NCT03739684_Prot_000.pdf']
- **r55**: section/page miss; citation ['NCT04494425_SAP_003.pdf']
- **r56**: section/page miss; citation ['NCT02667587_Prot_000.pdf', 'NCT02667587_SAP_001.pdf', 'NCT03345095_Prot_000.pdf', 'NCT04427072_Prot_000.pdf']; keywords 0%
- **r57**: false refusal (MODEL_REFUSED)
- **r58**: citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']
- **r59**: citation ['NCT02987543_Prot_005.pdf', 'NCT04427072_Prot_000.pdf']; keywords 50%
- **r60**: false refusal (MODEL_REFUSED)
- **r61**: section/page miss; keywords 0%
- **r62**: section/page miss; keywords 0%
- **r63**: citation ['NCT01712490_SAP_001.pdf', 'NCT03517137_Prot_SAP_000.pdf']
- **r64**: citation ['NCT02667587_Prot_000.pdf', 'NCT02987543_SAP_015.pdf', 'NCT04494425_SAP_003.pdf']; keywords 0%
- **r66**: should refuse but answered
- **r69**: should refuse but a partial answer

Per-question answers are kept with the local-only corpus, not here.
