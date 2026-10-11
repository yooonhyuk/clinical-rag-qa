# Review r3 — 2026-10-11-versions-draft (fix2 확인, 좁은 범위)

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: review-r2의 R2-b와 N1이 fix2로 고쳐졌는지만 본다. 새 탐색은 하지 않았다. 기준은 working tree(base `HEAD` = 55e8894) + untracked

## 판정: APPROVE

R2-b와 N1 모두 고쳐졌다. 초안 도구를 직접 실행했다. 출력에서 문서 안내대로 `# ` 두 글자만 지우면 날짜가 적용된다. 지우기 전에는 날짜로 숨겨지는 파일이 0건이다. 명시 태그 두 경우도 경고를 남기고 추정으로 대체된다.

## 확인 항목

### 1) 문서대로 `# `만 지우면 날짜가 적용되는가: **예 (R2-b 고쳐짐)**
합성 코퍼스(scratchpad, 6건: `a/Visit 1 minutes 20250105/20250405.docx`, `a/Site 01 monitoring report 20250101/20250301.pdf`, `a/Protocol v2.1/v2.2.pdf`)로 `uv run --project backend python scripts/draft_versions.py <dir> --out draft.yaml`을 실행했다. stderr는 `files 6 · families 1 · candidate bundles 2 · needs confirmation 6 (date candidates 4)`이다. 항목은 block mapping(`  - match:` / `    family:` / `    version:`)으로 나온다. 날짜 후보는 `    # date: 2025-01-05  # 확인 후 '# ' 두 글자만 지운다` 형태로, mapping 안에 들어 있다.

출력을 `<dir>/.versions.yaml`에 둔 뒤 `indexing_pipeline._read_manifest` → `resolve_version` → `latest_flags` 순서로 직접 실행했다:

| 운영자 동작 | entries | manifest 날짜 | 숨김 |
|---|---|---|---|
| 그대로 적용 | 6 | 없음 | `Protocol v2.1`만 (**날짜로 숨김 0**) ✅ |
| `^\s*# date: `에서 `# `만 지움(바뀐 줄 4개, 들여쓰기 그대로) | 6 | 4개 적용 | `Protocol v2.1`, `Site 01 … 20250101`, `Visit 1 … 20250105` ✅ |
| 회의록 쌍 2줄만 지움 | 6 | 2개 | `Protocol v2.1`, `Visit 1 … 20250105`만 ✅ |

r2에서 ParserError가 나던 경로(entries 0)가 이제 유효한 YAML이다. 새 단위 테스트 `test_removing_the_hash_and_space_of_a_date_candidate_hides_the_older_file`(`tests/unit/test_draft_versions.py:123`)는 문서 절차 그대로 `    # date: ` 줄의 첫 `# `만 지운다. 지우기 전 `[True, True]`, 바뀐 줄 2개, 지운 뒤 date 적용과 `[False, True]`를 모두 단언한다.

### 2) 출력 전체가 parse_manifest로 읽히는가: **예**
위 초안을 `yaml.safe_load` → `parse_manifest`로 읽으면 entries 6이고 예외가 없다. `uv run --project backend pytest -q tests/unit/test_draft_versions.py tests/unit/test_doc_versions.py` → 73 passed. 게이트 판정은 Tester가 한다.

### 3) `!!timestamp nope` / `!!bool maybe`: **경고 + 추정 대체 (N1 고쳐짐)**
`_read_versions_file`의 except가 `Exception`으로 넓어졌다(`indexing_pipeline.py:84`). 초안의 한 날짜 줄을 각 태그 값으로 바꿔 실행했다:
- `!!timestamp nope` → `WARNING … ignored (not readable YAML: 'NoneType' object has no attribute 'groupdict')`, entries 0, 파일명 추정(Protocol v2.1만 숨김)
- `!!bool maybe` → `WARNING … ignored (not readable YAML: 'maybe')`, entries 0, 같은 결과

통합 테스트 broken-file parametrize에 두 경우가 추가되어 있다(`tests/integration/test_doc_versions_db.py:344-345`).

### 4) 문구-코드 일치: **맞음**
- 초안 머리말: "그대로 적용하면 … 날짜로는 아무것도 숨기지 않는다"와 "그 줄의 '# ' 두 글자만 지워라(들여쓰기는 그대로)"는 1)의 결과와 맞는다. 항목 줄 주석도 같다.
- README: "그 줄의 `# ` 두 글자만 지우세요"와 "깨져 있으면(없는 날짜 `2025-02-30`, 잘못된 `!!` 태그 포함) 경고만 남기고 추정으로 대체"는 코드와 맞는다.
- ADR 0006 addendum: "`# ` 두 글자만 지우면(들여쓰기 그대로) 그 항목의 `date:` 키가 되어 manifest 날짜로 비교에 쓰인다", "(c) … 주석 줄 `# date: ...`로 낸다(살아 있는 `date:` 값이 아니다)"는 코드와 맞는다.
- 비차단 사소: `scripts/draft_versions.py` 모듈 docstring 규칙 (c)의 "offered as `date`. It takes effect only after the operator confirms it"에는 주석 줄이라는 말이 없다. 틀린 말은 아니고 출력 머리말에는 정확히 적혀 있어 지적만 남긴다.

### 5) 위생
| 항목 | 결과 |
|---|---|
| `git stash list` | 0 ✅ |
| 변경 범위 | tracked 6개(README, doc_versions.py, indexing_pipeline.py, ADR 0006, 통합/단위 테스트, `+206/-2`) + untracked(scripts/draft_versions.py, tests/unit/test_draft_versions.py, packet 디렉터리). r2와 같은 파일 집합이고 fix2 지시 범위(render, except, 테스트, 문구) 안이다 ✅ |
| assert 완화 | tracked 테스트 diff의 삭제 줄 0. 새 해제 테스트는 r2가 요구한 문서 그대로의 조작으로 바꾼 것이다. 지우기 전 숨김 0과 바뀐 줄 수까지 단언하므로 더 강하다 ✅ |
| denylist | `git diff HEAD` + untracked 소스/테스트 + packet md를 `grep -inEf ~/clinical-rag-private/commit-denylist.txt`(7패턴)로 검사 → **0건** ✅ |

## 후속
- 없음(차단 항목 없음). 원하면 모듈 docstring (c)에 "as a comment line"을 덧붙인다(선택).
