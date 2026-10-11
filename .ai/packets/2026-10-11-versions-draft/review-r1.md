# Review r1 — 2026-10-11-versions-draft

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: working tree diff (base `HEAD` = 55e8894) + untracked
- 참고: `origin/main`은 리뷰 시점에 e395717로 한 커밋 앞서 있다(`docs(ai)`: `.ai/README.md`, `.ai/rules/project.md`만). 이번 diff와 겹치는 파일이 없다. 그래서 `git diff origin/main`에 보이는 `.ai/*` 2건은 이번 변경이 아니다. PR 전에 rebase가 필요하지만 충돌은 예상되지 않는다.

## 판정: REQUEST_CHANGES (R1, R2)

### R1 [차단] `.versions.yaml`에 없는 날짜가 하나만 있어도 색인 전체가 멈춘다
- 위치: `backend/app/services/indexing_pipeline.py:82-88` (`_read_versions_file`)
- 문제: `yaml.safe_load`는 `date: 2025-02-30`이나 `date: 2025-13-01`처럼 따옴표 없는 날짜를 timestamp로 만들다가 `ValueError`를 던진다. 이것은 `yaml.YAMLError`가 아니다.
  except가 `(yaml.YAMLError, UnicodeDecodeError, OSError)`만 잡으므로 예외가 `IndexingPipeline.run()` 맨 앞(`:128`, IndexJob을 만들기 전)까지 올라가 색인이 중단된다.
- 직접 실행 결과:
  - `yaml.safe_load("date: 2025-02-30")` → `ValueError day is out of range for month` (`isinstance(e, yaml.YAMLError)` = False)
  - `_read_manifest(<tmp>, ".corpus.yaml")`에 `versions:\n  - {match: a.md, family: x, date: 2025-13-01}` → traceback
- 왜 차단인가: packet Phase 2-2("형식이 틀리면 색인을 멈추지 않고 경고만")와 ADR addendum의 서술("색인은 멈추지 않고 경고만")을 위반한다. 게다가 이번에 만든 흐름의 핵심이 **운영자가 초안의 `date`를 손으로 고치는 것**이라, 날짜 오타가 가장 흔한 형식 오류다.
- 수정 방향:
  - `_read_versions_file`의 except에 `ValueError`를 더한다. 또는 `safe_load` 단계의 예외를 넓게 잡아 경고 후 무시한다.
  - `test_broken_versions_yaml_warns_and_falls_back_to_filenames`의 parametrize에 `"versions:\n  - {match: 'sample guide v1.md', family: g, date: 2025-02-30}\n"`를 추가한다.
  - (참고) `.corpus.yaml`의 `read_marker`(`llm_guardrail.py:52-55`)에도 같은 구멍이 있다. 이것은 기존 코드이고 이번 Edit 목록 밖(Read)이라 후속 과제로 둔다.

### R2 [차단, 문구 수정 수준] 초안 머리말의 "확인 전에는 효력 없음"이 실제 동작과 다르다. 날짜만 다른 정기 문서가 그대로 적용하면 숨겨진다
- 위치: `scripts/draft_versions.py:227` (render 머리말 `(c) … (확인 전에는 효력 없음)`), `:207-213`(date 후보), `:183-185`(묶음 근거)
- 문제: 초안은 `date:`를 실제 YAML 값으로 쓴다. 운영자가 그대로 저장하면(README 예시가 `cp`다) 그 날짜는 곧바로 manifest 날짜가 되어 비교에 쓰인다.
  Implementer의 테스트 `test_applying_the_draft_orders_editions_and_hides_nothing_unconfirmed`도 그대로 적용하면 옛 날짜가 숨겨진다고 단언한다. 테스트 이름("hides nothing unconfirmed")도 단언 내용과 반대다.
  특히 **판 토큰 없이 날짜만 다른 이름**에 문제가 있다. 회의록·방문 보고서처럼 ADR 0006이 "날짜는 판이 아님"의 예로 든 문서들이다.
  규칙 (b)는 날짜를 뺀 core가 같다는 이유로 이들을 후보 묶음으로 만들고, 규칙 (c)가 날짜를 넣는다. 그래서 그대로 적용하면 최신 회의록 하나만 남고 나머지는 숨겨진다.
  근거 주석은 "판이 같거나 비교 불가 -> 파일명 날짜를 date 후보로 둠"뿐이라, 이 날짜 묶음이 서로 다른 문서일 수 있다는 경고가 없다.
- 합성 재현(아래 실험 B): `a/Visit 1 minutes 20250105.docx` / `20250405`, `a/Site 01 monitoring report 20250101.docx` / `20250301`. 그대로 적용하면 앞의 것이 둘 다 숨겨진다. 파일명 추정만 쓸 때는 둘 다 최신이었다.
- 왜 차단인가: 모든 항목에 `# 확인 필요`가 붙어 있으므로 coordinator 기준으로는 오묶음 자체는 비차단이다. 하지만 초안이 운영자에게 **사실과 반대되는 안내**("확인 전에는 효력 없음")를 한다. 그 결과 ADR 0006의 핵심 원칙(파일명 날짜로는 숨기지 않음)이 운영자도 모르는 사이 뒤집힌다.
  체크 7(문서-코드 일치)에서도 실패한다.
- 수정 방향 (최소 → 권장):
  1. 최소: 머리말 문구를 "date 를 남긴 채 저장하면 옛 날짜 문서가 숨겨진다"로 고친다. 묶음 안의 **모든** 멤버가 판 토큰 없이 날짜만 다른 경우에는 근거에 "날짜만 다른 이름 — 별개 정기 문서(회의록·보고서)일 수 있음"을 덧붙인다.
  2. 권장(packet 설계 (c) "운영자가 확인해야 효력"과 일치): date 후보를 주석 줄(`# date: 2025-01-05`)로 낸다. 운영자가 주석을 풀어야 효력이 생기므로, 그대로 적용해도 날짜로는 아무것도 숨기지 않는다.
     이 방식은 Phase 4의 "초안을 그대로 적용" 지표 뜻을 바꾸므로 coordinator가 고른다. 고르면 위 테스트의 단언과 이름을 함께 고쳐야 한다(Implementer 테스트이므로 assert 완화 규칙 대상이 아니다. 의도가 바뀌는 것이니 coordinator 결정으로 처리한다).

## 체크리스트

### 1) scope.md 위반 검출 1~6
| # | 결과 |
|---|---|
| 1 Edit 목록 | `git diff HEAD --name-only` = README.md, doc_versions.py, indexing_pipeline.py, ADR 0006, tests/integration/test_doc_versions_db.py, tests/unit/test_doc_versions.py. untracked = scripts/draft_versions.py, tests/unit/test_draft_versions.py, packet.md, report-implementer.md. 모두 Edit 목록 안이다(packet.md는 coordinator 파일). evidence/는 gitignore 대상 |
| 2 Protect | ADR 0006: 기존 결정 1~6은 그대로이고 addendum 절만 추가했다(packet이 "절 추가·정정" 허용). corpus/public, eval, 임계값, pyproject/uv.lock, compose, journey는 diff에 없다 |
| 3 assert 완화 | 테스트 파일 diff는 추가만 있고 삭제 0줄이다. 전체 삭제 2줄은 doc_versions docstring 1줄과 pipeline manifest 호출 1줄 |
| 4 denylist | `git diff HEAD` + untracked 전체(+junit.xml) 대상 `grep -inEf commit-denylist.txt`(7패턴) → **0건** |
| 5 외부 호출 | 새 HTTP·LLM SDK·API 키 없음. `import yaml`은 기존 의존성(`pyyaml>=6.0`)이고 기존 모듈 3곳이 이미 쓴다 |
| 6 로컬 전용 자료 | 테스트·실험 파일명은 모두 합성이다. ADR 수치(87/71/10/34/26/1)는 packet 배경의 집계와 같다 |

stash 건: `git stash list` = 0. `git diff HEAD`가 report 서술(Phase 1~3 + docs)과 정확히 일치하고, 서술에 없는 잔여 변경이나 누락은 없다.

### 2) 테스트 의도 보존
기존 테스트 수정 없음. 새 테스트만 있다. 위 R2의 테스트 이름-단언 불일치는 새 테스트 안의 문제다.

### 3) 오탐 수정 — 합성 파일명 직접 실행 (HEAD 버전 vs 현재, `infer_from_filename` + `latest_flags`)
| 입력 | HEAD | 현재 |
|---|---|---|
| Protocol v2.1 / v2.2 | v2.1 숨김 | 동일 |
| ICH E6(R2) / E6(R3), Guideline (R2)/(R3) | R2 숨김 | 동일 |
| SAP Rev5 / Rev6 | Rev5 숨김 | 동일 |
| Protocol Amendment 2 / 3 | Amd 2 숨김 | 동일 |
| Protocol v2.0 Amd 2 / v2.0 Amd 3 / v2.0 / v3.0 | v3.0만 최신 | 동일 |
| SAP v1.0 Rev 2 / v1.0 Rev 3, CRF 개정 2 v1.0 / 개정 3 v1.0 | 뒤의 것만 최신 | 동일 |
| Change table v2.1 v2.2 / v2.2 v3.0 | **앞의 것 숨김(오탐)** | 둘 다 단독·최신 |
| Plan Rev5->Rev6 / Rev6->Rev7 / Rev7 | Rev7만 최신 | 셋 다 최신(변경 문서는 단독) |
| Manual ver 2 v3 / Manual v3 | 앞의 것 숨김 | 둘 다 최신 |
| ICH E6R3 Guideline Rev 2 / Rev 3 (id형 R + Rev) | family는 같지만 첫 rev(R3)끼리 비교해 둘 다 최신 | 단독, 둘 다 최신 — 숨김 결과 차이 없음 |

- **종류가 다른 토큰 2개**(`Protocol v2.0 Amendment 3`): kinds = {ver, amd}가 중복이 아니므로 판으로 읽는다. 종류별로 비교된다(ver가 같으면 amd로, 한쪽에만 amd가 있으면 0 → 둘 다 최신). 진짜 판에서는 안전하다.
- 잔여 위험(비차단, 기존 동작 그대로): 종류가 섞인 **변경 문서**는 여전히 판으로 읽힌다. 예: `Protocol v2.0 Amendment 2 summary` / `… Amendment 3 summary`는 한 family가 되어 Amd 2 요약이 숨겨진다. 원래 오탐과 같은 성격이지만 이번 설계 범위("같은 종류 2개 이상") 밖이다. 후속 후보다.

### 4) `.versions.yaml`
- 우선순위: `_read_manifest` = `.corpus.yaml` 항목 + `.versions.yaml` 항목 순서이고, `resolve_version`은 첫 일치를 쓴다. 통합 테스트 `test_corpus_yaml_entry_wins_over_versions_yaml`가 확인한다. OK
- 형식 오류: YAML 문법 오류, 최상위 리스트, `versions:` 스칼라 → 경고 + 무시(통합 테스트 3종). **없는 날짜(`2025-02-30`)는 색인 중단 → R1**
- 조용한 무시(비차단): 최상위 매핑에 `versions` 키가 없는 경우(`version:` 오타), 빈 파일 → 경고 없이 빈 목록. 개별 항목 형식 오류도 기존처럼 조용히 건너뛴다. 운영자가 고친 파일이 안 먹는 것을 알아차리기 어려우므로 경고 추가를 권한다
- 색인 제외: `test_versions_yaml_is_not_indexed_as_a_document`(total == 1). OK
- 삭제 후 재색인 복귀: 통합 테스트로 확인. OK
- 경로 탈출: `match`는 `fnmatchcase`로 코퍼스 상대 경로와 파일명 **문자열**에만 대조하고 파일시스템에는 접근하지 않는다. `../outside/*`, `/etc/*`를 넣어 직접 실행해도 매칭 0이다(source=none). 파일은 `<root>/.versions.yaml` 하나만 읽고 `safe_load`를 쓴다. 영향 없음

### 5) 초안 도구
- `superseded`는 키로 쓰지 않는다(테스트 + 코드 확인). 파일명 날짜는 `date`로 쓰고 근거 주석을 단다. 다만 "후보"라는 표시가 실제로는 효력이 있다 → R2
- 출력 → `parse_manifest` 왕복: 단위 테스트, 그리고 아래 실험 B(38건, 30 entries, 오류 없음)에서 확인. glob 문자는 `glob.escape`, 문자열은 JSON 인용이다. OK
- 다른 폴더: `a/Imaging charter v1.0` · `v2.0 draft`는 묶이고 `b/Imaging charter v3.0`은 묶이지 않는다. OK. 다른 형식 계열도 묶지 않는다(테스트)
- `corpus/public`에 실행 → `versions: []`, 오류 없음

**실험 B — 합성 파일명 38개(한 폴더 37 + 다른 폴더 1)로 오묶음 찾기**

결과: 후보 묶음 13개 + family 1개, 30 entries, date 후보 4개. 모든 entry에 `# 근거:`와 `# 확인 필요`가 붙어 있다.

| 묶음 | 판정 |
|---|---|
| Data management plan + Safety management plan | **오묶음**(유사도) |
| Informed consent form adult + adult final + child | **child 오묶음** |
| Lab manual Part A v1.0 + Part B v1.0 | **오묶음** |
| eCRF specification arm A + arm B | **오묶음** |
| Subject A narrative + Subject B narrative | **오묶음** |
| Vendor contact + Vendor contract | **오묶음** |
| Visit 1 minutes 20250105 + 20250405 | **오묶음**(날짜만 다른 별개 회의록) + date 후보 |
| Site 01 monitoring report 20250101 + 20250301 | **오묶음**(별개 방문 보고서) + date 후보 |
| Protocol v2.0 Amd 2 summary + Amd 3 summary + Amd 3 summary 수정 | 일부 오묶음(Amd 2/3 요약은 별개). 파일명 추정만 써도 이미 같은 결과 |
| Imaging charter v1.0 + v2.0 draft, Query log + copy, 계획서 요약 + 수정본, CRF completion guideline(s) | 타당 |
| 묶지 않음: Site 02 report(숫자 다름), Data transfer plan, Safety monitoring plan, Delegation/Training log, b/ 폴더 | 타당 |

**그대로 적용했을 때 다른 문서를 숨기기가 얼마나 쉬운가**
- 판 토큰도 날짜도 없는 오묶음(Part A/B, arm A/B, Subject A/B, contact/contract, adult/child)은 판·날짜가 없거나 같다. 그래서 비교 불가 → 둘 다 최신이고 **숨김 0**이다. 이 경우 오묶음은 무해하다.
- **날짜만 다른 같은 이름**(회의록·방문 보고서·주간 보고)은 그대로 적용하면 **최신 1건만 남기고 전부 숨긴다**. 이 실험에서는 2쌍이었다. 조건은 같은 폴더 + 같은 형식 + 이름에서 날짜만 다름이다. 정기 문서가 폴더 하나에 모인 실제 코퍼스에서는 흔할 것으로 본다. 파일명 추정만 쓸 때는 0건이었다(측정 안 함: 실제 87건에서의 빈도).
- 판 토큰이 같은 오묶음(Part A v1.0 / Part B v1.0)에 파일명 날짜가 붙어 있으면, 같은 방식으로 날짜가 늦은 쪽이 다른 문서를 숨긴다. 이 실험의 Part A/B에는 날짜가 없어 숨김이 없었다.
- 결론: 오묶음 자체(유사도 0.85)는 흔하다(13 중 7~8). 다만 숨김으로 이어지는 경로는 사실상 **date 후보**뿐이다. 그래서 R2의 권장안(date를 주석으로)을 쓰면 "그대로 적용"해도 판 번호로만 숨기게 되어 위험이 크게 준다.

### 6) public 11개 `resolve_version` 전후
HEAD의 `doc_versions.py`(`git show`로 scratchpad에 복사) + `.corpus.yaml` manifest와, 현재 코드 + `_read_manifest`를 비교했다. 11개 모두 (family, label, date, source, superseded)가 같다. `latest_flags`도 같다(05만 False).

### 7) 문서-코드 일치
- README 사용법(명령, `--out`, stderr 요약, `.corpus.yaml` 우선, 깨지면 경고, 지우면 복귀): 코드와 일치한다. 단 "깨져 있으면 경고만"은 R1 때문에 날짜 오류에서는 거짓이다. "파일명 날짜는 `date` 후보"는 R2 참조
- ADR addendum: 규칙 (a)(b)(c), 우선순위, 숨김 파일 제외가 코드와 일치한다. "형식이 틀리면 색인은 멈추지 않고"는 R1 때문에 불일치한다
- 초안 머리말 "(확인 전에는 효력 없음)"은 불일치한다 → R2

## 기타 비차단 제안
- N1: `draft_versions`는 기존 `.corpus.yaml` `versions:`나 기존 `.versions.yaml`을 보지 않는다. `--out <corpus>/.versions.yaml`로 다시 실행하면 운영자가 고친 내용을 덮어쓴다. README에 "기존 파일에 직접 쓰지 말 것"을 한 줄 넣거나, 대상이 이미 있으면 거부하기를 권한다.
- N2: `draft_versions.py:178-181`에서 `draft.bundles += 1` 뒤에 `continue`할 수 있어 개수가 어긋날 수 있다(실제로 core None이 나오는 경로는 찾지 못함).
- N3: 묶음 family는 `normalize_family("a/core")` → `"a core"`(슬래시가 공백이 됨)이고 추정 family는 `"a/core"`다. 표기가 달라 폴더 `a b`/`c`와 `a`/`b c`가 충돌할 수 있다(실용상 무시 가능). 표기를 맞추면 초안 가독성이 좋아진다.
- N4: 종류가 섞인 변경 문서(`… Amendment 2 summary` 등)의 오탐은 후속 이슈 후보다(위 3).
- 게이트(lint·test)는 Tester 몫이라 여기서 판정하지 않는다. 참고로 단위 테스트 2파일을 실행했고 70 passed다.
