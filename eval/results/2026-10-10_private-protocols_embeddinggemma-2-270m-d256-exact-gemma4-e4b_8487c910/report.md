# RAG Eval Report — private / embeddinggemma-2-270m-d256-exact-gemma4-e4b (2026-10-10T19:54:26)

## Config

- run_at: `2026-10-10T19:54:26`
- label: `embeddinggemma-2-270m-d256-exact-gemma4-e4b`
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
- embedding_dim: `256`
- embedding_truncate_dim: `256`
- embedding_query_prefix: `task: search result | query: `
- embedding_document_prefix: `title: none | text: `
- hybrid_search: `False`
- top_k: `5`
- chunk_size: `1000`
- chunk_overlap: `150`
- min_relevance_score: `-0.145`
- scope_classifier: `embedding`
- scope_margin: `0.0191`
- vector_search: `exact`
- hnsw_iterative_scan: `off`
- db_state: `{'chunks_by_corpus': {'private': 8447, 'public': 2029, 'toy': 32}, 'hnsw_index': 'CREATE INDEX chunks_embedding_hnsw ON public.chunks USING hnsw (embedding vector_cosine_ops)', 'hnsw_ef_search': '40', 'hnsw_iterative_scan_default': 'off', 'pgvector': '0.8.0'}`

## Metrics

| Metric | Value |
|---|---|
| Retrieval hit@k (file) | 70.3% |
| Section/page hit@k | 31.2% |
| Citation accuracy (cited files ⊆ gold) | 52.2% |
| Citation location (a cited chunk in gold section/page) | 34.8% |
| Keyword coverage | 62.0% |
| Refusal accuracy (must-refuse) | 86.7% |
| False refusal rate (answerable) | 28.1% |
| Partial answers with caveat (answerable) | 29.7% |
| False refusal if partial = refusal (MVP-1 policy) | 57.8% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 97.8% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 59 |
| Retrieval p95 (ms) | 113 |
| Generation p50 (ms) | 5,026 |
| Generation p95 (ms) | 8,593 |
| Total p50 (ms) | 4,372 |
| Total p95 (ms) | 8,390 |
| Input tokens (total) | 97,493 |
| Output tokens (total) | 8,334 |
| Questions (answerable / must-refuse) / errors | 79 (64 / 15) / 0 |
| Must-refuse questions answered partially | 2 |

Refusal reasons: {'ANSWERED': 27, 'ANSWERED_PARTIAL': 21, 'MODEL_REFUSED': 16, 'OUT_OF_SCOPE': 15}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| bicr_process | 10 | 70.0% | 50.0% | 62.5% | 56.2% | - | 20.0% | 30.0% | 4,993 |
| cross_doc | 5 | 60.0% | 0.0% | 25.0% | 62.5% | - | 20.0% | 80.0% | 6,569 |
| cross_trial | 5 | 100.0% | 60.0% | 0.0% | 50.0% | - | 40.0% | 20.0% | 3,986 |
| diagnosis_request | 5 | - | - | - | - | 100.0% | - | - | 0 |
| eligibility_imaging | 11 | 54.5% | 27.3% | 83.3% | 66.7% | - | 45.5% | 18.2% | 4,372 |
| imaging_schedule | 11 | 36.4% | 18.2% | 60.0% | 40.0% | - | 54.5% | 0.0% | 3,443 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 3,250 |
| out_of_scope | 3 | - | - | - | - | 66.7% | - | - | 1,705 |
| response_criteria | 13 | 92.3% | 23.1% | 45.5% | 63.6% | - | 15.4% | 30.8% | 5,622 |
| sap_endpoint | 9 | 88.9% | 44.4% | 55.6% | 77.8% | - | 0.0% | 55.6% | 7,268 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 30 | 75.0% | 29.2% | 50.0% | 41.7% | 83.3% | 25.0% | 16.7% | 4,316 |
| ko | 49 | 67.5% | 32.5% | 53.6% | 75.0% | 88.9% | 30.0% | 37.5% | 4,486 |

## Failed questions

- **r01**: section/page miss
- **r02**: false refusal (MODEL_REFUSED)
- **r03**: false refusal (MODEL_REFUSED)
- **r04**: section/page miss; citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']; keywords 0%
- **r06**: false refusal (MODEL_REFUSED)
- **r07**: retrieval miss (got ['NCT03568461_Prot_002.pdf', 'NCT04236141_SAP_001.pdf', 'protocol_NCT03761056.pdf']); citation ['NCT04236141_SAP_001.pdf']; keywords 0%
- **r08**: false refusal (OUT_OF_SCOPE)
- **r09**: false refusal (OUT_OF_SCOPE)
- **r10**: keywords 0%
- **r11**: false refusal (MODEL_REFUSED)
- **r12**: section/page miss; citation ['NCT02987543_SAP_015.pdf', 'NCT04494425_SAP_003.pdf']; keywords 0%
- **r16**: keywords 0%
- **r17**: section/page miss; citation ['NCT02987543_Prot_005.pdf', 'NCT04698187_Prot_000.pdf']
- **r18**: retrieval miss (got ['NCT02667587_SAP_001.pdf', 'NCT02987543_Prot_005.pdf', 'NCT03785964_SAP_002.pdf', 'NCT04427072_Prot_000.pdf', 'NCT04427072_SAP_001.pdf']); citation ['NCT02987543_Prot_005.pdf']; keywords 50%
- **r19**: keywords 0%
- **r20**: false refusal (OUT_OF_SCOPE)
- **r21**: false refusal (MODEL_REFUSED)
- **r22**: false refusal (MODEL_REFUSED)
- **r23**: section/page miss
- **r24**: section/page miss; citation ['NCT03785964_Prot_000.pdf', 'NCT04427072_Prot_000.pdf']
- **r25**: section/page miss; citation ['NCT04494425_Prot_002.pdf', 'protocol_NCT04489771.pdf']; keywords 50%
- **r26**: section/page miss; citation ['NCT04698187_SAP_001.pdf']; keywords 0%
- **r27**: section/page miss; citation ['NCT04236141_Prot_000.pdf', 'NCT04236141_SAP_001.pdf']
- **r29**: section/page miss; keywords 0%
- **r30**: false refusal (OUT_OF_SCOPE)
- **r31**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r32**: keywords 0%
- **r33**: section/page miss
- **r34**: section/page miss; citation ['NCT03785964_Prot_000.pdf']; keywords 50%
- **r35**: false refusal (MODEL_REFUSED)
- **r36**: keywords 0%
- **r38**: retrieval miss (got ['NCT03345095_Prot_000.pdf', 'NCT03785964_Prot_000.pdf', 'NCT04698187_Prot_000.pdf', 'protocol_NCT03761056.pdf']); citation ['NCT03345095_Prot_000.pdf', 'NCT03785964_Prot_000.pdf']; keywords 0%
- **r39**: false refusal (OUT_OF_SCOPE)
- **r40**: false refusal (OUT_OF_SCOPE)
- **r41**: section/page miss
- **r42**: section/page miss
- **r43**: false refusal (OUT_OF_SCOPE)
- **r44**: false refusal (OUT_OF_SCOPE)
- **r46**: citation ['NCT03785964_Prot_000.pdf', 'NCT03785964_SAP_001.pdf']
- **r49**: section/page miss; keywords 0%
- **r50**: section/page miss; citation ['NCT04236141_SAP_001.pdf']
- **r51**: section/page miss; keywords 0%
- **r52**: retrieval miss (got ['NCT01712490_Prot_000.pdf', 'NCT01712490_SAP_001.pdf', 'NCT03375320_Prot_SAP_000.pdf', 'NCT03785964_SAP_001.pdf']); citation ['NCT01712490_Prot_000.pdf', 'NCT03375320_Prot_SAP_000.pdf']
- **r53**: section/page miss; citation ['NCT03739684_Prot_000.pdf', 'NCT03739684_SAP_001.pdf']
- **r55**: false refusal (MODEL_REFUSED)
- **r56**: false refusal (MODEL_REFUSED)
- **r57**: citation ['NCT04427072_Prot_000.pdf', 'protocol_NCT03761056.pdf']; keywords 0%
- **r58**: citation ['NCT04698187_SAP_001.pdf', 'protocol_NCT04489771.pdf']
- **r59**: citation ['NCT02987543_Prot_005.pdf', 'NCT04698187_SAP_001.pdf']; keywords 50%
- **r60**: false refusal (MODEL_REFUSED)
- **r61**: section/page miss
- **r62**: section/page miss; citation ['NCT02667587_SAP_001.pdf', 'NCT02987543_Prot_005.pdf']; keywords 0%
- **r63**: retrieval miss (got ['NCT02987543_SAP_015.pdf', 'NCT03517137_Prot_SAP_000.pdf', 'NCT03739684_Prot_000.pdf', 'qiba_fdg_pet_ct_v1.14_2023.pdf']); citation ['NCT03517137_Prot_SAP_000.pdf']; keywords 50%
- **r64**: section/page miss; citation ['NCT03375320_Prot_SAP_000.pdf']
- **r69**: should refuse but a partial answer
- **r79**: should refuse but a partial answer

Per-question answers are kept with the local-only corpus, not here.
