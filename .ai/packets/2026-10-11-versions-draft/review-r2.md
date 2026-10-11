# Review r2 — 2026-10-11-versions-draft (fix1 확인, 좁은 범위)

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: review-r1 R1·R2가 fix1로 고쳐졌는지만 본다. 새 탐색은 하지 않았다. 기준은 working tree(base `HEAD` = 55e8894) + untracked
- coordinator 결정: R2는 권장안(date 후보를 주석 줄로 낸다)

## 판정: REQUEST_CHANGES (R2-b 1건)

R1은 고쳐졌다. R2의 "그대로 적용하면 날짜로 숨기지 않는다"도 고쳐졌다. 남은 문제는 하나다. 머리말·README·ADR이 안내하는 **"주석을 풀어라"를 글자 그대로 따르면 YAML이 깨진다.** 그러면 `.versions.yaml` 전체가 경고와 함께 무시된다. 주석 해제로 날짜를 비교에 넣는 경로가 문서대로는 동작하지 않는다.

### R2-b [차단, 작은 수정] 주석 줄 `# date:`를 풀면 파일 전체가 무시된다
- 위치: `scripts/draft_versions.py` `render()` — 항목은 flow mapping 한 줄(`  - {match: …, family: …}`)이고, 그 아래에 `  # date: 2025-01-01  # 확인 후 주석 해제`가 들여쓰기 2로 붙는다
- 직접 실행 결과(합성 6건: 회의록 2, 방문 보고서 2, Protocol v2.1/v2.2). `_read_manifest`를 거친 결과다:

| 운영자 동작 | 결과 |
|---|---|
| 그대로 적용 | entries 6, 날짜 숨김 0, Protocol v2.1만 숨김 ✅ |
| `# `만 지움(→ `  date: 2025-01-01  # …`) | **ParserError → 경고 + 파일 전체 무시(entries 0)**. 모든 항목이 파일명 추정으로 돌아간다 |
| 지우고 들여쓰기 4 | 같음(entries 0) |
| 한 줄만 해제 | 같음(entries 0) |
| 날짜를 `{…}` 안으로 옮김(테스트 `test_uncommenting_a_date_candidate_hides_the_older_file`의 방식) | entries 6, 옛 날짜 숨김 ✅ |

- 왜 차단인가: dispatch 확인 항목 2("주석 해제 시에만 비교되는지, 헤더·README·ADR 문구가 코드와 맞는지")에서 실패한다. 문서가 "주석을 풀어라 / 풀어야 manifest 날짜로 비교에 쓰인다"(초안 머리말 4~5행, README, ADR addendum)라고 안내하지만, 실제로 주석을 풀면 날짜가 비교에 쓰이지 않는다. 그 파일의 family·version 항목까지 모두 사라진다. 실패 방향은 숨김이 아니라 추정으로 돌아가는 쪽이고, R1 수정 덕에 색인도 멈추지 않는다. 다만 경고는 색인 로그에만 남아서, 운영자가 고친 내용이 통째로 무시된 것을 알아차리기 어렵다. 테스트는 이 문제를 잡지 못한다. 줄을 중괄호 안으로 합치는 방식이라 문서의 절차와 다르기 때문이다.
- 수정 방향(권장): 항목을 block mapping으로 낸다. 그러면 `# date:` 줄이 mapping 안에 들어가서 `# `만 지워도 유효한 YAML이 된다.
  ```yaml
    - match: "a/Visit 1 minutes 20250105.docx"
      family: "a visit 1 minutes"
      # date: 2025-01-05  # 확인 후 주석 해제
  ```
  테스트 `test_uncommenting_a_date_candidate_hides_the_older_file`는 "`  # date:` 줄에서 첫 `# `만 지운다"는 문서 그대로의 조작으로 바꾼다. 그대로 적용 / parse_manifest 왕복 테스트는 지금처럼 통과해야 한다.
  (대안: 문구를 "중괄호 안으로 옮겨라"로 바꾼다. 운영자에게 덜 자연스러워 권하지 않는다.)

## 확인 항목

### 1) R1 — 날짜·값 오류에서 색인이 경고 + 추정 대체로 끝나는가: **고쳐짐**
`_read_versions_file`의 except에 이제 `ValueError`가 있다(`indexing_pipeline.py:84`). 임시 디렉터리에 `.versions.yaml`을 만들어 `_read_manifest`를 직접 실행했다:

| 입력 | 결과 |
|---|---|
| `date: 2025-02-30` | WARNING + entries 0 ✅ |
| `date: 2025-13-01` | WARNING + entries 0 ✅ |
| `date: 2025-00-10` | WARNING ✅ |
| `date: 2025-02-29T25:00:00` | WARNING ✅ |
| `!!python/object:os.system` 태그 | WARNING(ConstructorError) ✅ |
| 정의되지 않은 alias `*b` | WARNING ✅ |
| 깨진 바이트 `\xff\xfe` | WARNING(UnicodeDecodeError ⊂ ValueError) ✅ |
| 탭 들여쓰기 | WARNING ✅ |
| `match: 5, family: [x], date: 2025, version: {a: 1}` | 예외 없이 항목 건너뜀 ✅ |

통합 테스트 `test_broken_versions_yaml_warns_and_falls_back_to_filenames`의 parametrize에 `2025-02-30`과 `2025-13-01`이 추가되어 있다.

- 비차단 N1: **명시 태그**를 쓰면 아직 잡히지 않는 예외가 있다. `date: !!timestamp nope` → `AttributeError`, `!!bool maybe` → `KeyError`가 색인 밖으로 올라간다(`!!int abc`, `!!float x`는 ValueError라 잡힌다). 운영자가 손으로 `!!` 태그를 쓸 일은 드물어 차단하지 않는다. report의 "잔여 예외 경로는 모두 같은 처리"는 이 두 경우에는 맞지 않는다. R2-b를 고치는 김에 `except Exception`으로 넓히면 끝난다(`safe_load`는 임의 코드를 실행하지 않으므로 넓게 잡아도 위험이 없다).

### 2) R2 — 그대로 적용하면 날짜로 아무것도 숨기지 않는가: **고쳐짐** / 주석 해제 경로: **R2-b**
- r1의 날짜 쌍(`Visit 1 minutes 20250105/20250405`, `Site 01 monitoring report 20250101/20250301`)으로 직접 실행했다. 그대로 적용하면 4건 모두 LATEST이고 `date=None`이다. 같은 초안의 Protocol v2.1/v2.2는 판 번호로 v2.1만 숨겨진다.
- 근거 주석에 "(날짜만 다른 이름이면 별개 문서일 수 있음)"이 붙는다 ✅
- 날짜를 중괄호 안으로 옮겨야만 비교된다. 글자 그대로 주석을 풀면 R2-b가 생긴다.
- 문구-코드 일치: 머리말 1~3행("그대로 적용하면 판 번호로만… 날짜로는 아무것도 숨기지 않는다"), README의 같은 문장, ADR addendum "(c) … 주석 줄 `# date: ...`로 낸다(살아 있는 `date:` 값이 아니다)"는 코드와 맞는다. **"주석을 풀어라 / 푸세요 / 풀어야 비교에 쓰인다"는 맞지 않는다(R2-b).**
- ADR addendum의 "읽히지 않거나(YAML 오류, …)"에는 없는 날짜가 따로 적혀 있지 않다. README에는 `2025-02-30`이 명시되어 있다. 사소하므로 지적하지 않는다.

### 3) 초안 출력이 parse_manifest로 읽히는가: **예**
위 6건 초안을 `yaml.safe_load` → `parse_manifest`로 읽으면 entries 6, 예외 없음. 단위 테스트(초안 → parse_manifest 왕복, `superseded` 키 없음)도 통과한다. `uv run pytest tests/unit/test_draft_versions.py tests/unit/test_doc_versions.py` → 73 passed (게이트 판정은 Tester 몫)

### 4) 위생
| 항목 | 결과 |
|---|---|
| `git stash list` | 비어 있음(0) ✅ |
| 변경 범위 | tracked 6개(README, doc_versions.py, indexing_pipeline.py, ADR 0006, 통합/단위 테스트) + untracked(scripts/draft_versions.py, tests/unit/test_draft_versions.py, packet 디렉터리). r1 때와 같은 파일 집합이고 fix1 지시 범위(pipeline except, draft render, 테스트, README·ADR 문구) 안이다 ✅ |
| assert 완화 | tracked 테스트 diff는 `+81/-0`, `+49/-0`이다(삭제 0줄). `test_draft_versions.py`에서 이름·단언이 바뀐 테스트(`…hides_nothing_unconfirmed` → `test_filename_dates_are_comments_so_the_draft_hides_nothing_by_date` 등)는 coordinator가 R2 권장안을 골라 의도가 바뀐 것이고, 숨김이 0이라는 더 강한 단언이다. 완화가 아니다 ✅ |
| denylist | `git diff HEAD` + untracked 전체를 `grep -inEf ~/clinical-rag-private/commit-denylist.txt`(7패턴)로 검사 → **0건** ✅ |

## 후속
- R2-b 수정 후 r3는 다음만 확인하면 된다: block mapping 출력, 문서 그대로(`# `만 지움)의 해제 테스트, 그대로 적용 시 날짜 숨김 0, parse_manifest 왕복
- N1(명시 태그 예외)은 같은 커밋에서 `except Exception`으로 처리하기를 권한다(선택)
