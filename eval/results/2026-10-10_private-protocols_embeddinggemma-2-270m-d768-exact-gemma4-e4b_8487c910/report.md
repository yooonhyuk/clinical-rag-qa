# RAG Eval Report — private / embeddinggemma-2-270m-d768-exact-gemma4-e4b (2026-10-10T16:52:40)

## Config

- run_at: `2026-10-10T16:52:40`
- label: `embeddinggemma-2-270m-d768-exact-gemma4-e4b`
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
| Retrieval hit@k (file) | 68.8% |
| Section/page hit@k | 34.4% |
| Citation accuracy (cited files ⊆ gold) | 54.8% |
| Citation location (a cited chunk in gold section/page) | 38.1% |
| Keyword coverage | 65.5% |
| Refusal accuracy (must-refuse) | 80.0% |
| False refusal rate (answerable) | 34.4% |
| Partial answers with caveat (answerable) | 18.8% |
| False refusal if partial = refusal (MVP-1 policy) | 53.1% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 93.3% |
| Answers in Korean (answered) | 100.0% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 95 |
| Retrieval p95 (ms) | 161 |
| Generation p50 (ms) | 4,927 |
| Generation p95 (ms) | 8,226 |
| Total p50 (ms) | 4,512 |
| Total p95 (ms) | 8,170 |
| Input tokens (total) | 92,436 |
| Output tokens (total) | 7,654 |
| Questions (answerable / must-refuse) / errors | 79 (64 / 15) / 0 |
| Must-refuse questions answered partially | 2 |

Refusal reasons: {'ANSWERED': 31, 'ANSWERED_PARTIAL': 14, 'MODEL_REFUSED': 15, 'OUT_OF_SCOPE': 19}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| bicr_process | 10 | 70.0% | 50.0% | 83.3% | 58.3% | - | 40.0% | 10.0% | 4,880 |
| cross_doc | 5 | 80.0% | 40.0% | 25.0% | 12.5% | - | 20.0% | 40.0% | 5,468 |
| cross_trial | 5 | 80.0% | 60.0% | 33.3% | 66.7% | - | 40.0% | 60.0% | 5,016 |
| diagnosis_request | 5 | - | - | - | - | 100.0% | - | - | 0 |
| eligibility_imaging | 11 | 45.5% | 18.2% | 60.0% | 73.3% | - | 54.5% | 27.3% | 3,361 |
| imaging_schedule | 11 | 54.5% | 27.3% | 66.7% | 80.6% | - | 45.5% | 9.1% | 4,008 |
| no_answer | 7 | - | - | - | - | 71.4% | - | - | 3,758 |
| out_of_scope | 3 | - | - | - | - | 66.7% | - | - | 2,006 |
| response_criteria | 13 | 76.9% | 23.1% | 66.7% | 72.2% | - | 30.8% | 7.7% | 4,843 |
| sap_endpoint | 9 | 88.9% | 44.4% | 33.3% | 72.2% | - | 0.0% | 11.1% | 5,182 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 30 | 75.0% | 33.3% | 52.9% | 42.2% | 83.3% | 29.2% | 16.7% | 4,605 |
| ko | 49 | 65.0% | 35.0% | 56.0% | 81.3% | 77.8% | 37.5% | 20.0% | 4,459 |

## Failed questions

- **r01**: section/page miss
- **r02**: false refusal (MODEL_REFUSED)
- **r03**: section/page miss; keywords 33%
- **r04**: section/page miss; citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']; keywords 50%
- **r05**: citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']
- **r07**: false refusal (OUT_OF_SCOPE)
- **r08**: false refusal (OUT_OF_SCOPE)
- **r09**: false refusal (OUT_OF_SCOPE)
- **r11**: false refusal (MODEL_REFUSED)
- **r12**: section/page miss; keywords 0%
- **r13**: false refusal (MODEL_REFUSED)
- **r17**: false refusal (MODEL_REFUSED)
- **r18**: retrieval miss (got ['NCT02667587_SAP_001.pdf', 'NCT02987543_Prot_005.pdf', 'NCT03785964_SAP_002.pdf', 'NCT04427072_SAP_001.pdf', 'NCT04494425_SAP_003.pdf']); citation ['NCT02987543_Prot_005.pdf', 'NCT04494425_SAP_003.pdf']; keywords 50%
- **r19**: keywords 0%
- **r20**: false refusal (OUT_OF_SCOPE)
- **r21**: false refusal (MODEL_REFUSED)
- **r22**: section/page miss
- **r23**: section/page miss
- **r24**: section/page miss; citation ['NCT03568461_Prot_002.pdf', 'NCT04427072_Prot_000.pdf']
- **r25**: false refusal (MODEL_REFUSED)
- **r26**: section/page miss; citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']; keywords 0%
- **r27**: false refusal (OUT_OF_SCOPE)
- **r29**: false refusal (OUT_OF_SCOPE)
- **r30**: false refusal (OUT_OF_SCOPE)
- **r31**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r32**: keywords 0%
- **r33**: section/page miss
- **r34**: section/page miss; keywords 50%
- **r35**: false refusal (OUT_OF_SCOPE)
- **r36**: false refusal (MODEL_REFUSED)
- **r38**: retrieval miss (got ['NCT03345095_Prot_000.pdf', 'NCT03785964_Prot_000.pdf', 'NCT04494425_Prot_002.pdf', 'protocol_NCT03761056.pdf']); citation ['NCT03345095_Prot_000.pdf', 'NCT03785964_Prot_000.pdf']; keywords 0%
- **r39**: false refusal (OUT_OF_SCOPE)
- **r40**: false refusal (OUT_OF_SCOPE)
- **r41**: section/page miss; citation ['NCT03517137_Prot_SAP_000.pdf', 'NCT03739684_Prot_000.pdf', 'qiba_fdg_pet_ct_v1.14_2023.pdf']
- **r42**: section/page miss
- **r43**: false refusal (OUT_OF_SCOPE)
- **r44**: false refusal (OUT_OF_SCOPE)
- **r45**: section/page miss; keywords 67%
- **r47**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r49**: section/page miss; citation ['NCT03517137_Prot_SAP_000.pdf']; keywords 0%
- **r50**: section/page miss; citation ['NCT04236141_SAP_001.pdf']; keywords 50%
- **r51**: section/page miss; citation ['NCT03568461_SAP_001.pdf']; keywords 0%
- **r52**: retrieval miss (got ['NCT01712490_Prot_000.pdf', 'NCT01712490_SAP_001.pdf', 'NCT03785964_SAP_001.pdf']); citation ['NCT01712490_Prot_000.pdf']
- **r53**: section/page miss; citation ['NCT03739684_Prot_000.pdf', 'NCT03739684_SAP_001.pdf']
- **r55**: false refusal (MODEL_REFUSED)
- **r56**: citation ['NCT02667587_SAP_001.pdf']; keywords 50%
- **r57**: false refusal (MODEL_REFUSED)
- **r58**: citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']
- **r59**: keywords 50%
- **r60**: false refusal (MODEL_REFUSED)
- **r61**: section/page miss; citation ['NCT02667587_SAP_001.pdf']; keywords 0%
- **r62**: section/page miss; citation ['protocol_NCT03761056.pdf']; keywords 0%
- **r63**: citation ['NCT03517137_Prot_SAP_000.pdf']; keywords 50%
- **r64**: keywords 0%
- **r66**: should refuse but answered
- **r69**: should refuse but a partial answer
- **r79**: should refuse but a partial answer

Per-question answers are kept with the local-only corpus, not here.
