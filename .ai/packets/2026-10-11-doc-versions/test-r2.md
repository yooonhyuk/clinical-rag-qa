# Tester 보고 r2 (최종) — doc-versions

판정: **PASS**

## G1 — `make lint`
- exit code: **0**
- ruff check: `All checks passed!`
- ruff format --check: `188 files already formatted`

## G2 — `uv run --project backend pytest --junitxml=.ai/packets/2026-10-11-doc-versions/evidence/junit-tester-r2.xml`
- exit code: **0**
- 마지막 요약 줄: `======================= 585 passed, 1 warning in 56.59s ========================`
- junit (`evidence/junit-tester-r2.xml`): `tests="585" failures="0" errors="0" skipped="0"`, `timestamp="2026-10-11T17:42:58.449187+09:00"`
- timestamp 확인: 실행 직전 UTC `2026-10-11T08:42:58` = KST 17:42:58, 실행 종료 UTC 08:43:55 → **이번 실행** (잔존물 아님)
- 기대값(failures=0 errors=0 skipped=0) 충족. integration 테스트(`tests/integration/test_doc_versions_db.py`)도 skip 없이 실행됨.
- warning 1건: `testcontainers.postgres is deprecated` (DeprecationWarning, tests/integration/conftest.py:47) — 실패 아님.

## G3 — 변경 파일 목록 (판정 안 함)

### `git diff --name-only origin/main`
```
.env.example
README.md
backend/app/api/rag.py
backend/app/config.py
backend/app/container.py
backend/app/models/document.py
backend/app/schemas/rag.py
backend/app/services/indexing_pipeline.py
backend/app/services/prompt_builder.py
backend/app/services/rag_service.py
backend/app/services/vector_search_service.py
corpus/public/.corpus.yaml
docs/issues/005-ich-version-confusion-cross-language.md
docs/journey.md
eval/run_eval.py
frontend/streamlit_app.py
```

### `git ls-files --others --exclude-standard`
```
.ai/packets/2026-10-11-doc-versions/packet.md
.ai/packets/2026-10-11-doc-versions/report-implementer.md
.ai/packets/2026-10-11-doc-versions/review-r1.md
.ai/packets/2026-10-11-doc-versions/review-r2.md
.ai/packets/2026-10-11-doc-versions/review-r3.md
.ai/packets/2026-10-11-doc-versions/test-r1.md
backend/alembic/versions/0007_document_versions.py
backend/app/services/doc_versions.py
docs/decisions/0006-document-versions.md
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff-run2_8e014ae3/{config.json,questions.jsonl,report.md,summary.json}
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff_8e014ae3/{config.json,questions.jsonl,report.md,summary.json}
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston-run2_8e014ae3/{config.json,questions.jsonl,report.md,summary.json}
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston_8e014ae3/{config.json,questions.jsonl,report.md,summary.json}
tests/integration/test_doc_versions_db.py
tests/unit/test_doc_version_search.py
tests/unit/test_doc_versions.py
```
(eval/results 항목은 원 출력의 파일 16줄을 폴더별로 `{}` 로 축약 표기)

참고: 이 보고서(`test-r2.md`)와 `evidence/junit-tester-r2.xml` 은 위 목록 캡처 이후에 생성되었다. 소스 수정·git 조작 없음.
