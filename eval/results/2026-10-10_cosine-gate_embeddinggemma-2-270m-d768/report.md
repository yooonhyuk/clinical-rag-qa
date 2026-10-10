# Cosine gate tuning (MIN_RELEVANCE_SCORE)

Runs: `2026-10-10_toy_embeddinggemma-2-270m-d768-gateoff_719a3969`, `2026-10-10_public_embeddinggemma-2-270m-d768-gateoff_8e014ae3`
Dev: 77 questions. Held-out half (47) not read.

Objective v1 (pre-registered): refusal accuracy - false refusal rate -> value 0.8833, tied interval -1.0..0.7 -> **-0.15**

| gate | refusal accuracy | false refusal |
|---|---|---|
| none (-1) | 17/17 | 7/60 |
| -0.15 | 17/17 | 7/60 |
