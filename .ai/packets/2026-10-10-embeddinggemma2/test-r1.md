# Tester 보고 r1 — PASS

실행 시각: 2026-10-10 (UTC 11:54, KST 20:54). 소스 수정·git 조작 없음.

## G1 — `make lint`
- exit code 0
- `All checks passed!` / `173 files already formatted` → **PASS**

## G2 — pytest
- `uv run --project backend pytest --junitxml=.ai/packets/2026-10-10-embeddinggemma2/evidence/junit-tester.xml` → exit code 0
- 마지막 요약 줄: `475 passed, 1 warning in 55.14s`
- junit: tests=475 failures=0 errors=0 skipped=0, timestamp=`2026-10-10T20:54:22+09:00` (이번 실행 시각과 일치, 잔존물 아님)
- skip 0 — integration도 조용히 skip되지 않고 실행됨 (`tests/integration/...` 통과 확인)
- 경고 1건: testcontainers.postgres DeprecationWarning (무해) → **PASS**

## G3 — eval/results/2026-10-10_* summary.json 존재·분모>0
(분모 키: eval=`overall.questions`, scope=`heldout.n`, cosine-gate=`dev_questions`. 수치 해석 안 함)

| 폴더 | summary.json | 분모 키 | 분모 | 판정 |
|---|---|---|---|---|
| 2026-10-10_cosine-gate_bge-m3-d1024-rule-v1 | yes | dev_questions | 77 | OK |
| 2026-10-10_cosine-gate_embeddinggemma-2-270m-d256 | yes | dev_questions | 77 | OK |
| 2026-10-10_cosine-gate_embeddinggemma-2-270m-d512 | yes | dev_questions | 77 | OK |
| 2026-10-10_cosine-gate_embeddinggemma-2-270m-d768 | yes | dev_questions | 77 | OK |
| 2026-10-10_private-protocols_bge-m3-d1024-rule-v1-exact-gemma4-e4b_8487c910 | yes | overall.questions | 79 | OK |
| 2026-10-10_private-protocols_bge-m3-ollama0.40.2-exact-gemma4-e4b_8487c910 | yes | overall.questions | 79 | OK |
| 2026-10-10_private-protocols_embeddinggemma-2-270m-d256-exact-gemma4-e4b_8487c910 | yes | overall.questions | 79 | OK |
| 2026-10-10_private-protocols_embeddinggemma-2-270m-d512-exact-gemma4-e4b_8487c910 | yes | overall.questions | 79 | OK |
| 2026-10-10_private-protocols_embeddinggemma-2-270m-d768-exact-gemma4-e4b_8487c910 | yes | overall.questions | 79 | OK |
| 2026-10-10_public_bge-m3-d1024-rule-v1-exact-gemma4-e4b-run2_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_bge-m3-d1024-rule-v1-exact-gemma4-e4b_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_bge-m3-d1024-rule-v1-gateoff_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_bge-m3-ollama0.40.2-exact-gemma4-e4b-run2_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_bge-m3-ollama0.40.2-exact-gemma4-e4b_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d256-exact-gemma4-e4b-run2_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d256-exact-gemma4-e4b_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d256-gateoff_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d512-exact-gemma4-e4b-run2_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d512-exact-gemma4-e4b_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d512-gateoff_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d768-exact-gemma4-e4b-run2_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d768-exact-gemma4-e4b_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_public_embeddinggemma-2-270m-d768-gateoff_8e014ae3 | yes | overall.questions | 99 | OK |
| 2026-10-10_scope-b6_bge-m3_9caf3158b734 | yes | heldout.n | 61 | OK |
| 2026-10-10_scope-b6_embeddinggemma-2-270m-256d_9caf3158b734 | yes | heldout.n | 61 | OK |
| 2026-10-10_scope-b6_embeddinggemma-2-270m-512d_9caf3158b734 | yes | heldout.n | 61 | OK |
| 2026-10-10_scope-b6_embeddinggemma-2-270m_9caf3158b734 | yes | heldout.n | 61 | OK |
| 2026-10-10_toy_bge-m3-d1024-rule-v1-exact-gemma4-e4b_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_bge-m3-d1024-rule-v1-gateoff_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_bge-m3-ollama0.40.2-exact-gemma4-e4b_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_embeddinggemma-2-270m-d256-exact-gemma4-e4b_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_embeddinggemma-2-270m-d256-gateoff_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_embeddinggemma-2-270m-d512-exact-gemma4-e4b_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_embeddinggemma-2-270m-d512-gateoff_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_embeddinggemma-2-270m-d768-exact-gemma4-e4b_719a3969 | yes | overall.questions | 25 | OK |
| 2026-10-10_toy_embeddinggemma-2-270m-d768-gateoff_719a3969 | yes | overall.questions | 25 | OK |

폴더 36개, 실패 0개

→ **PASS** (36/36 존재, 분모 전부 >0)

## G4 — Reviewer용 목록 (판정 없음)

### git diff --name-only origin/main
```
.env.example
README.md
backend/app/config.py
backend/app/container.py
backend/app/services/ollama_client.py
docs/decisions/0002-embedding-model.md
docs/journey.md
eval/run_eval.py
eval/run_scope_eval.py
tests/unit/test_embedding_config.py
tests/unit/test_embedding_service.py
tests/unit/test_ollama_client.py
```

### git ls-files --others --exclude-standard (비-eval/results 항목)
```
.ai/packets/2026-10-10-embeddinggemma2/packet.md
.ai/packets/2026-10-10-embeddinggemma2/report-implementer.md
.ai/packets/2026-10-10-embeddinggemma2/review-r1.md
.ai/packets/2026-10-10-embeddinggemma2/review-r2.md
eval/tune_cosine_gate.py
tests/integration/test_embedding_truncation_live.py
tests/unit/test_tune_cosine_gate.py
```

### 〃 eval/results 하위 (파일 수 / 폴더)
```
   2 eval/results/2026-10-10_cosine-gate_bge-m3-d1024-rule-v1
   2 eval/results/2026-10-10_cosine-gate_embeddinggemma-2-270m-d256
   2 eval/results/2026-10-10_cosine-gate_embeddinggemma-2-270m-d512
   2 eval/results/2026-10-10_cosine-gate_embeddinggemma-2-270m-d768
   4 eval/results/2026-10-10_private-protocols_bge-m3-d1024-rule-v1-exact-gemma4-e4b_8487c910
   4 eval/results/2026-10-10_private-protocols_bge-m3-ollama0.40.2-exact-gemma4-e4b_8487c910
   4 eval/results/2026-10-10_private-protocols_embeddinggemma-2-270m-d256-exact-gemma4-e4b_8487c910
   4 eval/results/2026-10-10_private-protocols_embeddinggemma-2-270m-d512-exact-gemma4-e4b_8487c910
   4 eval/results/2026-10-10_private-protocols_embeddinggemma-2-270m-d768-exact-gemma4-e4b_8487c910
   4 eval/results/2026-10-10_public_bge-m3-d1024-rule-v1-exact-gemma4-e4b_8e014ae3
   4 eval/results/2026-10-10_public_bge-m3-d1024-rule-v1-exact-gemma4-e4b-run2_8e014ae3
   4 eval/results/2026-10-10_public_bge-m3-d1024-rule-v1-gateoff_8e014ae3
   4 eval/results/2026-10-10_public_bge-m3-ollama0.40.2-exact-gemma4-e4b_8e014ae3
   4 eval/results/2026-10-10_public_bge-m3-ollama0.40.2-exact-gemma4-e4b-run2_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d256-exact-gemma4-e4b_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d256-exact-gemma4-e4b-run2_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d256-gateoff_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d512-exact-gemma4-e4b_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d512-exact-gemma4-e4b-run2_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d512-gateoff_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d768-exact-gemma4-e4b_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d768-exact-gemma4-e4b-run2_8e014ae3
   4 eval/results/2026-10-10_public_embeddinggemma-2-270m-d768-gateoff_8e014ae3
   2 eval/results/2026-10-10_scope-b6_bge-m3_9caf3158b734
   2 eval/results/2026-10-10_scope-b6_embeddinggemma-2-270m_9caf3158b734
   2 eval/results/2026-10-10_scope-b6_embeddinggemma-2-270m-256d_9caf3158b734
   2 eval/results/2026-10-10_scope-b6_embeddinggemma-2-270m-512d_9caf3158b734
   4 eval/results/2026-10-10_toy_bge-m3-d1024-rule-v1-exact-gemma4-e4b_719a3969
   4 eval/results/2026-10-10_toy_bge-m3-d1024-rule-v1-gateoff_719a3969
   4 eval/results/2026-10-10_toy_bge-m3-ollama0.40.2-exact-gemma4-e4b_719a3969
   4 eval/results/2026-10-10_toy_embeddinggemma-2-270m-d256-exact-gemma4-e4b_719a3969
   4 eval/results/2026-10-10_toy_embeddinggemma-2-270m-d256-gateoff_719a3969
   4 eval/results/2026-10-10_toy_embeddinggemma-2-270m-d512-exact-gemma4-e4b_719a3969
   4 eval/results/2026-10-10_toy_embeddinggemma-2-270m-d512-gateoff_719a3969
   4 eval/results/2026-10-10_toy_embeddinggemma-2-270m-d768-exact-gemma4-e4b_719a3969
   4 eval/results/2026-10-10_toy_embeddinggemma-2-270m-d768-gateoff_719a3969
```
