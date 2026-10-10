# Cosine gate tuning (MIN_RELEVANCE_SCORE)

Runs: `2026-10-10_toy_embeddinggemma-2-270m-d256-gateoff_719a3969`, `2026-10-10_public_embeddinggemma-2-270m-d256-gateoff_8e014ae3`
Dev: 77 questions. Held-out half (47) not read.

Objective v1 (pre-registered): refusal accuracy - false refusal rate -> value 0.9167, tied interval -1.0..0.71 -> **-0.145**

| gate | refusal accuracy | false refusal |
|---|---|---|
| none (-1) | 17/17 | 5/60 |
| -0.145 | 17/17 | 5/60 |
