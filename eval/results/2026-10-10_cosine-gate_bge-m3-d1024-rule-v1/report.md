# Cosine gate tuning (MIN_RELEVANCE_SCORE)

Runs: `2026-10-10_toy_bge-m3-d1024-rule-v1-gateoff_719a3969`, `2026-10-10_public_bge-m3-d1024-rule-v1-gateoff_8e014ae3`
Dev: 77 questions. Held-out half (47) not read.

Objective v1 (pre-registered): refusal accuracy - false refusal rate -> value 0.9078, tied interval -1.0..0.53 -> **-0.235**

| gate | refusal accuracy | false refusal |
|---|---|---|
| none (-1) | 16/17 | 2/60 |
| -0.235 | 16/17 | 2/60 |
