# Tester 보고 r1 — versions-draft

판정: **PASS** (G1, G2 통과. G3는 판정 안 함)

## G1: `make lint`
- exit code: **0**
- `ruff check`: All checks passed!
- `ruff format --check`: 190 files already formatted

## G2: `uv run --project backend pytest --junitxml=.ai/packets/2026-10-11-versions-draft/evidence/junit-tester.xml`
- exit code: **0**
- 마지막 요약 줄: `======================= 608 passed, 1 warning in 57.06s ========================`
- junit (`evidence/junit-tester.xml`): tests=**608** failures=**0** errors=**0** skipped=**0**
- junit timestamp: `2026-10-11T18:10:39.918344+09:00` (= 09:10:39Z). 실행 시작(09:10:39Z)~종료(09:11:37Z) 범위 안이므로 이번 실행 결과다.
- skipped=0 이라 integration이 조용히 skip되지 않았다 (`tests/integration/test_doc_versions_db.py` 가 junit에 포함됨).
- warning 1건: testcontainers.postgres DeprecationWarning (`tests/integration/conftest.py:47`). 실패와 무관.

## G3: 참고 목록 (판정 안 함)

### `git stash list`
(비어 있음)

### `git diff --name-only origin/main`
```
.ai/README.md
.ai/rules/project.md
README.md
backend/app/services/doc_versions.py
backend/app/services/indexing_pipeline.py
docs/decisions/0006-document-versions.md
tests/integration/test_doc_versions_db.py
tests/unit/test_doc_versions.py
```

### `git ls-files --others --exclude-standard`
```
.ai/packets/2026-10-11-versions-draft/packet.md
.ai/packets/2026-10-11-versions-draft/report-implementer.md
scripts/draft_versions.py
tests/unit/test_draft_versions.py
```
