# Tester r2 — office-loaders

판정: **PASS**

실행 시각(UTC): 시작 2026-10-11T03:55:50Z, 종료 03:56:49Z. 소스 수정·git 조작·스크립트 실행(generate_sample_office.py 포함) 없음.

## G1 — `make lint`
- exit code: **0**
- ruff check: `All checks passed!` / ruff format: `179 files already formatted`

## G2 — `uv run --project backend pytest --junitxml=.ai/packets/2026-10-11-office-loaders/evidence/junit-tester-r2.xml`
- exit code: **0**
- 마지막 요약 줄: `======================= 517 passed, 1 warning in 54.67s ========================`
- junit(`evidence/junit-tester-r2.xml`): tests=517 failures=0 errors=0 skipped=0
- junit timestamp: `2026-10-11T12:55:54.350105+09:00` (= 03:55:54Z) → 이번 실행 구간(03:55:50Z~03:56:49Z) 안. 이전 실행 잔존물 아님.
- skipped=0 이므로 integration 이 조용히 skip 되지 않음.
- 경고 1건: testcontainers 관련 import 경고(DeprecationWarning 추정, 실패 아님).

## G3 — samples/office 불변성 (실행 전 == 후, diff 일치)
`git status --short samples/office` (전/후 동일):
```
?? samples/office/
```
`shasum samples/office/*` (전/후 동일):
```
a10c6085b7bc40efd681ad7f740c8fb0ab8b80c0  samples/office/demo-imaging-charter.docx
5a6a2bb104757ba09e494811d71783cc172dcb71  samples/office/demo-imaging-schedule.xlsx
b214e086b223475927034d4b2fac7104eb933f58  samples/office/demo-signed-protocol.pdf
```
결과: **변하지 않음**.

## G4 — 목록 (판정 안 함)
`git diff --name-only origin/main`:
```
README.md
backend/app/services/document_loader.py
backend/app/services/pdf_extractor.py
backend/app/services/text_extractor.py
backend/pyproject.toml
backend/uv.lock
docs/decisions/0001-pdf-library.md
tests/integration/test_pipeline_db.py
tests/unit/test_document_loader.py
tests/unit/test_text_extractor.py
```
`git ls-files --others --exclude-standard`:
```
.ai/packets/2026-10-11-office-loaders/packet.md
.ai/packets/2026-10-11-office-loaders/report-implementer.md
.ai/packets/2026-10-11-office-loaders/review-r1.md
.ai/packets/2026-10-11-office-loaders/review-r2.md
.ai/packets/2026-10-11-office-loaders/review-r3.md
.ai/packets/2026-10-11-office-loaders/review-r4.md
.ai/packets/2026-10-11-office-loaders/review-r5.md
.ai/packets/2026-10-11-office-loaders/test-r1.md
backend/app/services/docx_extractor.py
backend/app/services/xlsx_extractor.py
samples/office/demo-imaging-charter.docx
samples/office/demo-imaging-schedule.xlsx
samples/office/demo-signed-protocol.pdf
scripts/generate_sample_office.py
tests/integration/test_office_samples.py
tests/unit/test_docx_extractor.py
tests/unit/test_xlsx_extractor.py
```
(참고: `evidence/junit-tester-r2.xml` 은 이번 실행으로 생성됐으나 위 untracked 목록에는 나타나지 않음 — evidence 경로가 ignore 되는 것으로 보임. 이 보고서 `test-r2.md` 도 목록 수집 이후 작성되어 목록에 없음.)
