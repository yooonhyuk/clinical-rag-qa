# Implementer report — 2026-10-11-versions-draft

- Phase 1: `infer_from_filename` leaves a name with two tokens of one kind (`v2.1 v2.2`, `Rev5->Rev6`) standalone (date kept). New `name_core()` helper (None for such names).
- Phase 2: `indexing_pipeline._read_manifest` = `.corpus.yaml` entries, then `.versions.yaml` (first match wins). Unreadable/ill-shaped `.versions.yaml` -> warning, ignored (inference). Integration tests: dates hide the older doc; deleting the file restores both; `.corpus.yaml` wins; 3 broken shapes warn + fall back; file not indexed.
- Phase 3: `scripts/draft_versions.py` (+ `tests/unit/test_draft_versions.py`, synthetic names). No `superseded`; filename dates only as `date` candidates; each entry has `# 근거:` / `# 확인 필요`.
- Docs: ADR 0006 addendum, README usage.
- Gate: `make lint` exit 0; `make test` 608 passed (integration ran via testcontainers). junit: `evidence/junit.xml` tests=608 failures=0 errors=0 skipped=0 timestamp=2026-10-11T18:08:33+09:00.
- Public corpus: `resolve_version` output for all 11 files identical before (HEAD) and after.
- Process slip: I ran `git stash push` once (to compare old code), and restored it right away via apply+drop (same SHA); tree intact. Should have used `git show`.

## fix1

review-r1 R1·R2 반영. git 조작 없음.

- R1: `_read_versions_file` 가 `ValueError` 도 잡는다(`date: 2025-02-30`, `2025-13-01`, 깨진 바이트). 경고 후 파일명 추정으로 대체. broken-file 통합 테스트에 날짜 오류 2건 추가. 같은 함수의 `parse_manifest` 는 타입이 이상한 값(`match: 5`, `family: [x]`, 문자열 날짜, 정수 날짜, dict version)을 예외 없이 건너뛴다 — 단위 테스트 `test_parse_manifest_ignores_odd_value_types_without_raising` 로 확인. 잔여 예외 경로는 `safe_load` 뿐이고 이제 모두 같은 처리.
- R2 (coordinator 결정: 권고안): 파일명 날짜는 살아 있는 `date:` 가 아니라 `  # date: 2025-03-02  # 확인 후 주석 해제` 주석 줄로 낸다. 머리말을 사실에 맞게 고치고 근거에 "날짜만 다른 이름이면 별개 문서일 수 있음"을 덧붙였다. 테스트: 날짜만 다른 회의록·방문 보고서 형태 2쌍은 그대로 적용하면 모두 최신, 주석을 풀면 옛 날짜가 숨겨짐. 기존 테스트 `..._hides_nothing_unconfirmed` 는 의도 변경(coordinator 결정)으로 이름·단언을 바꿨다.
- 문구: README, ADR 0006 addendum.
- 게이트: `make lint` exit 0, `uv run --project backend pytest` exit 0 — 613 passed, junit `.ai/packets/2026-10-11-versions-draft/evidence/junit-fix1.xml` (tests=613 failures=0 errors=0).

## fix2

review-r2 R2-b·N1 반영. git 조작 없음.

- R2-b: `render()` 가 항목을 block mapping(`- match:` / `    family:` / `    version:`)으로 낸다. 날짜 후보 줄은 `    # date: 2025-01-05  # 확인 후 '# ' 두 글자만 지운다` 로, 거기서 `# ` 만 지우면 들여쓰기 4의 유효한 `date:` 키가 된다. 머리말·README·ADR 0006 문구를 "`# ` 두 글자만 지운다"로 맞췄다.
- 테스트: `test_removing_the_hash_and_space_of_a_date_candidate_hides_the_older_file` — 지우기 전에는 둘 다 최신(숨김 0), 문서 안내 그대로 `# ` 만 지우면(바뀐 줄 2개) parse_manifest 로 date 가 적용되고 옛 날짜가 숨겨짐. 그대로 적용·왕복 테스트는 그대로 통과.
- N1: `_read_versions_file` 의 except 를 `Exception` 으로 넓혔다. 통합 테스트 broken-file parametrize 에 `!!timestamp nope`, `!!bool maybe` 추가(경고 + 추정 대체).
- 게이트: `make lint` exit 0, `uv run --project backend pytest` exit 0 — 615 passed, junit `.ai/packets/2026-10-11-versions-draft/evidence/junit-fix2.xml` (tests=615 failures=0 errors=0 skipped=0, timestamp=2026-10-11T18:20:36+09:00).
