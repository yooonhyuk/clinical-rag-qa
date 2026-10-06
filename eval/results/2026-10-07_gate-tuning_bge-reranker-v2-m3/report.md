# Reranker gate tuning (RERANK_MIN_SCORE)

Runs: `2026-10-07_toy_bge-m3-vector-rerank-nogate-gemma4-e4b_719a3969`, `2026-10-07_public_bge-m3-vector-rerank-nogate-gemma4-e4b_8e014ae3`

Dev: 77 questions (toy all + public even positions per type). Test (held out): 47 public questions (odd positions per type).

Objective v1 (pre-registered) -> **0.0** (adopted). Objective v2 (post-hoc, dev only) -> **0.56** (tied interval 0.5307..0.59). See the module docstring.

| split / gate | threshold | refusal accuracy | false refusal | refused by the gate |
|---|---|---|---|---|
| dev · no gate | 0.0 | 17/17 (100.0%) | 1/60 (1.7%) | - |
| dev · v2 | 0.56 | 17/17 (100.0%) | 2/60 (3.3%) | p80 |
| test · no gate | 0.0 | 8/9 (88.9%) | 3/38 (7.9%) | - |
| test · v2 | 0.56 | 8/9 (88.9%) | 6/38 (15.8%) | p40, p72, p86 |

## Dev curve (every 0.05)

| threshold | refusal accuracy | false refusal |
|---|---|---|
| 0.0 | 100.0% | 1.7% |
| 0.0001 | 100.0% | 1.7% |
| 0.0003 | 100.0% | 1.7% |
| 0.0004 | 100.0% | 1.7% |
| 0.0011 | 100.0% | 1.7% |
| 0.05 | 100.0% | 1.7% |
| 0.1 | 100.0% | 1.7% |
| 0.1009 | 100.0% | 1.7% |
| 0.15 | 100.0% | 1.7% |
| 0.2 | 100.0% | 1.7% |
| 0.25 | 100.0% | 3.3% |
| 0.3 | 100.0% | 3.3% |
| 0.35 | 100.0% | 3.3% |
| 0.4 | 100.0% | 3.3% |
| 0.45 | 100.0% | 3.3% |
| 0.5 | 100.0% | 3.3% |
| 0.55 | 100.0% | 3.3% |
| 0.56 | 100.0% | 3.3% |
| 0.6 | 100.0% | 5.0% |
| 0.65 | 100.0% | 5.0% |
| 0.7 | 100.0% | 6.7% |
| 0.75 | 100.0% | 6.7% |
| 0.8 | 100.0% | 6.7% |
| 0.8026 | 100.0% | 6.7% |
| 0.8481 | 100.0% | 13.3% |
| 0.85 | 100.0% | 15.0% |
| 0.9 | 100.0% | 20.0% |
| 0.95 | 100.0% | 25.0% |
