# RAG Eval Report — private / bge-m3-vector-exact-gemma4-e4b (2026-10-09T14:28:24)

## Config

- run_at: `2026-10-09T14:28:24`
- label: `bge-m3-vector-exact-gemma4-e4b`
- corpus: `private`
- corpus_root: `local`
- corpus_classification: `licensed-local-only`
- corpus_sha256: `8487c910ed8d347f0a8bdd2e843ee41785cc49b824c26907790d5a5709ac1f1e`
- questions_file: `protocol_questions.yaml`
- questions_sha256: `16394c4a90f3f53ef357f24d993a8ebb195902c981b5f2eea245216496891853`
- git_commit: `1365549`
- provider: `ollama`
- generator_model: `gemma4:e4b`
- reranker: `none`
- partial_answers: `True`
- rag_prompt_variant: `default`
- eval_process_max_rss_mb: `173`
- embedding_model: `bge-m3`
- embedding_dim: `1024`
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
| Citation accuracy (cited files ⊆ gold) | 50.0% |
| Citation location (a cited chunk in gold section/page) | 45.2% |
| Keyword coverage | 63.1% |
| Refusal accuracy (must-refuse) | 86.7% |
| False refusal rate (answerable) | 34.4% |
| Partial answers with caveat (answerable) | 10.9% |
| False refusal if partial = refusal (MVP-1 policy) | 45.3% |
| Refusal accuracy if partial = refusal (MVP-1 policy) | 100.0% |
| Answers in Korean (answered) | 97.6% |
| JSON schema-valid generations | 100.0% |
| Retrieval p50 (ms) | 225 |
| Retrieval p95 (ms) | 1,478 |
| Generation p50 (ms) | 20,464 |
| Generation p95 (ms) | 37,740 |
| Total p50 (ms) | 19,888 |
| Total p95 (ms) | 38,742 |
| Input tokens (total) | 109,558 |
| Output tokens (total) | 7,577 |
| Questions (answerable / must-refuse) / errors | 79 (64 / 15) / 0 |
| Must-refuse questions answered partially | 2 |

Refusal reasons: {'ANSWERED': 35, 'ANSWERED_PARTIAL': 9, 'MODEL_REFUSED': 20, 'NO_EVIDENCE': 2, 'OUT_OF_SCOPE': 13}

## By question type

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| bicr_process | 10 | 80.0% | 60.0% | 42.9% | 28.6% | - | 30.0% | 30.0% | 24,734 |
| cross_doc | 5 | 80.0% | 40.0% | 66.7% | 16.7% | - | 40.0% | 0.0% | 19,888 |
| cross_trial | 5 | 80.0% | 40.0% | 66.7% | 66.7% | - | 40.0% | 40.0% | 19,958 |
| diagnosis_request | 5 | - | - | - | - | 100.0% | - | - | 0 |
| eligibility_imaging | 11 | 72.7% | 27.3% | 50.0% | 66.7% | - | 45.5% | 9.1% | 19,450 |
| imaging_schedule | 11 | 54.5% | 36.4% | 60.0% | 90.0% | - | 54.5% | 0.0% | 25,042 |
| no_answer | 7 | - | - | - | - | 85.7% | - | - | 17,850 |
| out_of_scope | 3 | - | - | - | - | 66.7% | - | - | 229 |
| response_criteria | 13 | 76.9% | 38.5% | 50.0% | 75.0% | - | 23.1% | 0.0% | 34,064 |
| sap_endpoint | 9 | 88.9% | 77.8% | 37.5% | 75.0% | - | 11.1% | 11.1% | 20,466 |

## By language

| group | n | hit_at_k | section_hit_at_k | citation_correctness | keyword_coverage | refusal_correctness | false_refusal_rate | partial_answer_rate | total_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|
| en | 30 | 79.2% | 45.8% | 40.0% | 46.7% | 83.3% | 37.5% | 4.2% | 19,682 |
| ko | 49 | 72.5% | 45.0% | 55.6% | 72.2% | 88.9% | 32.5% | 15.0% | 20,466 |

## Failed questions

- **r01**: section/page miss; citation ['NCT04494425_Prot_002.pdf', 'NCT04494425_SAP_003.pdf']
- **r02**: false refusal (MODEL_REFUSED)
- **r03**: false refusal (MODEL_REFUSED)
- **r04**: citation ['NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']; keywords 50%
- **r07**: false refusal (OUT_OF_SCOPE)
- **r08**: false refusal (OUT_OF_SCOPE)
- **r09**: false refusal (OUT_OF_SCOPE)
- **r11**: false refusal (OUT_OF_SCOPE)
- **r12**: false refusal (MODEL_REFUSED)
- **r13**: retrieval miss (got ['NCT03375320_Prot_SAP_000.pdf', 'NCT03785964_SAP_001.pdf', 'NCT04427072_Prot_000.pdf', 'NCT04494425_Prot_002.pdf']); citation ['NCT04427072_Prot_000.pdf']; keywords 0%
- **r14**: section/page miss; keywords 0%
- **r15**: false refusal (MODEL_REFUSED)
- **r17**: section/page miss; citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']; keywords 0%
- **r19**: citation ['NCT03739684_Prot_000.pdf', 'NCT03739684_SAP_001.pdf']; keywords 0%
- **r20**: false refusal (MODEL_REFUSED)
- **r21**: citation ['NCT03375320_Prot_SAP_000.pdf', 'NCT04494425_SAP_003.pdf']; keywords 0%
- **r22**: section/page miss
- **r23**: section/page miss
- **r24**: false refusal (MODEL_REFUSED)
- **r25**: false refusal (MODEL_REFUSED)
- **r26**: section/page miss; citation ['NCT04698187_SAP_001.pdf']; keywords 0%
- **r27**: citation ['NCT03568461_Prot_002.pdf']
- **r30**: false refusal (OUT_OF_SCOPE)
- **r31**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r32**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']; keywords 0%
- **r33**: section/page miss
- **r34**: section/page miss; citation ['NCT03785964_Prot_000.pdf']; keywords 50%
- **r36**: citation ['NCT03785964_Prot_000.pdf', 'NCT03785964_SAP_001.pdf']; keywords 0%
- **r37**: section/page miss
- **r38**: section/page miss; citation ['NCT03820986_Prot_SAP_001.pdf', 'NCT04494425_Prot_002.pdf', 'NCT04698187_Prot_000.pdf', 'protocol_NCT04489771.pdf']; keywords 0%
- **r39**: false refusal (OUT_OF_SCOPE)
- **r40**: false refusal (MODEL_REFUSED)
- **r41**: section/page miss; citation ['protocol_NCT03761056.pdf']
- **r42**: false refusal (MODEL_REFUSED)
- **r43**: false refusal (OUT_OF_SCOPE)
- **r44**: false refusal (MODEL_REFUSED)
- **r45**: section/page miss
- **r47**: false refusal (MODEL_REFUSED)
- **r48**: citation ['NCT02987543_Prot_005.pdf', 'NCT02987543_SAP_015.pdf']
- **r49**: citation ['NCT03517137_Prot_SAP_000.pdf']
- **r50**: retrieval miss (got ['NCT03785964_SAP_001.pdf', 'NCT04698187_Prot_000.pdf', 'NCT04698187_SAP_001.pdf']); citation ['NCT04698187_SAP_001.pdf']; keywords 0%
- **r51**: section/page miss; keywords 0%
- **r52**: citation ['NCT01712490_Prot_000.pdf', 'NCT01712490_SAP_001.pdf', 'NCT03517137_Prot_SAP_000.pdf']
- **r53**: citation ['NCT03739684_Prot_000.pdf', 'NCT03739684_SAP_001.pdf']
- **r55**: section/page miss; citation ['NCT03785964_Prot_000.pdf', 'NCT04494425_Prot_002.pdf', 'NCT04494425_SAP_003.pdf', 'protocol_NCT04489771.pdf']
- **r56**: section/page miss; keywords 0%
- **r57**: false refusal (MODEL_REFUSED)
- **r59**: false refusal (MODEL_REFUSED)
- **r60**: false refusal (MODEL_REFUSED)
- **r61**: keywords 0%
- **r62**: section/page miss; keywords 0%
- **r63**: section/page miss; citation ['NCT03517137_Prot_SAP_000.pdf']; keywords 50%
- **r64**: false refusal (MODEL_REFUSED)
- **r69**: should refuse but a partial answer
- **r79**: should refuse but a partial answer

Per-question answers are kept with the local-only corpus, not here.
