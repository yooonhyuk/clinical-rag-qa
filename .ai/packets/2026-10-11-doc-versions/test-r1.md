# Tester 보고 r1 — 2026-10-11-doc-versions

판정: **PASS** (G1~G3 기대치 충족, G4는 판정 안 함)

## G1 — `make lint`
- exit code: **0**
- ruff check: `All checks passed!` / ruff format --check: `188 files already formatted`

## G2 — `uv run --project backend pytest --junitxml=.ai/packets/2026-10-11-doc-versions/evidence/junit-tester.xml`
- exit code: **0**
- 마지막 요약 줄: `======================= 564 passed, 1 warning in 58.50s ========================`
- junit (`evidence/junit-tester.xml`): tests=**564** failures=**0** errors=**0** skipped=**0**
- junit timestamp: `2026-10-11T17:28:15.109594+09:00` (= 08:28:15Z). 실행 시작 `date -u` 08:28:14Z, 종료 08:29:14Z 사이 → **이번 실행**
- 기대(failures=0 errors=0 skipped=0) 충족. integration(`test_doc_versions_db.py`)도 skip 없이 실행됨
- 경고 1건: testcontainers.postgres DeprecationWarning (테스트 결과와 무관)

## G3 — `eval/results/2026-10-11_public*` (존재·분모만, 해석 없음)

| 폴더 | summary.json | questions(분모) | answerable | unanswerable | errors |
|---|---|---|---|---|---|
| 2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff_8e014ae3 | 있음 | 99 | 79 | 20 | 0 |
| 2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff-run2_8e014ae3 | 있음 | 99 | 79 | 20 | 0 |
| 2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston_8e014ae3 | 있음 | 99 | 79 | 20 | 0 |
| 2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston-run2_8e014ae3 | 있음 | 99 | 79 | 20 | 0 |

분모(`overall.questions`) 4개 모두 > 0. 각 폴더에 config.json, questions.jsonl, report.md, summary.json 존재.

## G4 — 변경 파일 목록 (판정 안 함)

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
(이 보고서 `test-r1.md` 는 목록 채취 시점 이후에 생성되어 포함되지 않음. `evidence/` 는 목록에 나타나지 않음.)
```
.ai/packets/2026-10-11-doc-versions/packet.md
.ai/packets/2026-10-11-doc-versions/report-implementer.md
backend/alembic/versions/0007_document_versions.py
backend/app/services/doc_versions.py
docs/decisions/0006-document-versions.md
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff-run2_8e014ae3/config.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff-run2_8e014ae3/questions.jsonl
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff-run2_8e014ae3/report.md
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff-run2_8e014ae3/summary.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff_8e014ae3/config.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff_8e014ae3/questions.jsonl
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff_8e014ae3/report.md
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latestoff_8e014ae3/summary.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston-run2_8e014ae3/config.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston-run2_8e014ae3/questions.jsonl
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston-run2_8e014ae3/report.md
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston-run2_8e014ae3/summary.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston_8e014ae3/config.json
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston_8e014ae3/questions.jsonl
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston_8e014ae3/report.md
eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-lateston_8e014ae3/summary.json
tests/integration/test_doc_versions_db.py
tests/unit/test_doc_version_search.py
tests/unit/test_doc_versions.py
```

## 비고
- 소스 수정·git 조작 없음. 생성한 파일은 `evidence/junit-tester.xml` 과 이 보고서뿐 (evidence 디렉터리는 mkdir -p 로 보장).
- G3 JSON 은 읽기 전용으로 파싱했다(`python3 -I`). 평가 결과 해석은 Reviewer 몫.
