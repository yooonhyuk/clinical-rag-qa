# Review r1 — 2026-10-11-doc-versions

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: worktree `doc-versions`, working tree diff vs `origin/main` (`8d1ae8f`) + untracked. Phase 4는 대상 아님.

## 판정: **REQUEST_CHANGES**

검색 필터, 0007, API, 측정은 대체로 건전하다. 하지만 **파일명 추정이 서로 다른 문서를 한 family로 묶어 하나를 숨기는 경로**가 합성 파일명으로 재현된다(R1·R2).
또 **p32 한계**(옛 판 문서를 이름으로 지목한 질문을 최신판 기본값이 막음)가 문서화되지 않았다(R3).

## 반려 항목

### R1. family 키가 디렉터리를 무시한다 → 다른 폴더의 동명 문서가 서로를 숨김 (차단)
- 위치: `backend/app/services/doc_versions.py:204-218` (`resolve_version`→`infer_from_filename(file_name)`), `indexing_pipeline.py:120-122`
- 재현 (직접 실행):
  `resolve_version("Protocol_v2.0.pdf", "studyA/Protocol_v2.0.pdf")`와 `resolve_version("Protocol_v3.0.pdf", "studyB/Protocol_v3.0.pdf")`
  → 둘 다 family `protocol`. `latest_flags` 결과 `[False, True]`라 **studyA의 프로토콜이 숨겨진다.**
- 왜 문제인가: 업무 코퍼스는 시험별 폴더에 같은 파일명 템플릿(`Protocol_vX.Y`, `SAP_vX`, `ICF_vX`)을 쓰는 경우가 흔하다. "확신 없으면 숨기지 않음"을 정면으로 어긴다.
  ADR 0006 Consequences의 "나머지 이름이 같을 때뿐이라 드물다"는 이 경우에 맞지 않는다.
- 방향: 추정(source=filename)일 때 family 키에 상대 디렉터리(`relative_path`의 parent)를 포함한다. manifest는 지금처럼 명시 family를 그대로 쓴다.
  단위 테스트(다른 폴더, 같은 이름, 다른 판 → 둘 다 최신)와 통합 테스트 1건을 추가한다.

### R2. 판이 아닌 식별자·날짜 계열을 판으로 잡아 숨김 (차단)
직접 실행 결과 (`infer_from_filename` + `latest_flags`, 같은 corpus):

| 파일명 쌍 | family | 결과 |
|---|---|---|
| `Table 4 summary` / `Table 5 summary`, `Phase 3 protocol` / `Phase 2 protocol`, `Annual report 2024` / `2025`, `needle 2.5 mm` / `3.0 mm`, `ICH_E6R2` / `ICH_E6R3` | 없음 | ok (숨김 없음) |
| `NIH_R01_application` / `NIH_R21_application` | `nih application` | **R01 숨김** |
| `Site R1 log` / `Site R2 log` | `site log` | **R1 숨김** |
| `COVID-19 R0 model` / `COVID-19 R1 model` | `covid 19 model` | **R0 숨김** |
| `회의록_20250101` / `회의록_20250301` | `회의록` | **1월 회의록 숨김** |
| `Monitoring Visit Report 2025-01-10` / `2025-03-02` | `monitoring visit report` | **1월 방문 보고서 숨김** |
| `Lot 20250101` / `Lot 20250102` | `lot` | **숨김** |

- 'Table 4', 'Phase 3', 연도만, '2.5 mm'는 판으로 잡지 않는다(양호).
- 문제 1: 단독 `R\d+` 패턴(`doc_versions.py:49`)이 R01(연구비 종류), 사이트·지역 번호, R0 같은 식별자를 revision으로 읽는다.
- 문제 2: **날짜만 있는 이름은 "같은 문서의 판"이 아니라 "날짜별로 다른 문서"(회의록, 방문 보고서, 주간 보고, 로트 기록)인 경우가 많다.** 이것이 업무 문서에서 가장 흔한 패턴이다.
  packet 설계가 8자리 날짜를 토큰으로 지정했으므로 설계 단계의 위험이다. 그래도 결과는 "다른 문서를 숨김"이므로 차단으로 본다.
- 방향 (coordinator 결정 필요, 권고 순서):
  - (a) 파일명 추정에서는 **날짜만으로 숨기지 않는다.** 날짜는 같은 종류의 판 번호가 동률일 때의 보조 비교로만 쓰고, 날짜만 있는 family는 manifest로 명시해야 숨긴다.
  - (b) 단독 `R\d+`는 괄호 `(R3)` 또는 이름 끝 위치일 때만 판으로 인정하거나, 앞자리 0이 있는 `R01` 형태는 제외한다.
  - (c) (a)·(b)를 받지 않으면 최소한 ADR 0006 Consequences에 날짜 계열·R 식별자 오탐을 명시한다. Phase 4 추정 정확도 측정에 "날짜만으로 숨겨진 문서 수"를 별도 항목으로 넣는다.
  - 어느 쪽이든 위 표의 쌍을 단위 테스트로 고정한다.
  - 현재 `test_dates_only`(`weekly 2025…`)는 날짜 계열을 숨기는 동작을 **의도로 고정**하고 있다. (a)를 택하면 이 테스트의 의도 변경을 packet에 명시해야 한다.

### R3. p32 한계 미문서화: 옛 판 문서를 이름으로 지목한 질문을 기본값이 막음 (차단)
- p32는 "**ICH GCP 안내서**에 따르면 …"으로 05번(R2 안내서)을 이름으로 지목한다. 켬 2회에서 05는 top-5에 0개였고, 답은 R3 chunk로 나왔다.
- journey §16은 이 감소를 "상당 부분은 '정답 파일이 옛 판'이라는 평가셋의 정의 때문"이라고 쓴다.
  p32에는 이 설명이 맞지 않는다. **사용자가 명시적으로 그 문서를 요청했는데 기본값이 그 요청을 막은 것이다.**
  README·issue 005·ADR 0006 어디에도 이 한계가 없다. ADR Consequences의 "옛 판 포함을 켭니다"는 일반론이고, 질문이 옛 문서를 이름으로 부를 때의 실패 모드를 말하지 않는다.
- 방향: ADR 0006 Consequences와 journey §16 "잃은 것"에 한 문장씩 추가한다.
  - p32는 질문이 옛 판 문서(ICH GCP 안내서)를 이름으로 지목한 경우다.
  - 최신판 기본값은 이런 명시적 요청도 막는다(평가셋 정의 문제가 아니라 기능의 한계).
  - 대응은 "옛 판 포함" 또는 Not decided의 "질문 속 판·문서 이름으로 거르기"다.
  - p33·p34(문서를 지목하지 않음)는 평가셋 정의 문제로 따로 적는다.

## 확인한 항목

### 1) scope.md 위반 검출 1~6
- denylist: `git diff origin/main` + untracked 전체 내용을 `grep -inEf ~/clinical-rag-private/commit-denylist.txt`(7줄)로 검사했다. **0건**.
- 외부 호출: 새 HTTP 클라이언트·LLM SDK·API 키 없음. `httpx`는 통합 테스트의 `ASGITransport`(in-process)뿐이다.
- 로컬 전용 자료: diff에 업무 문서·질문 원문 없음. 결과 폴더의 `questions.jsonl`은 이미 레포에 있는 공개 평가셋 문항이다. 테스트 파일명은 합성·공개 이름만 쓴다.
- Protect: `corpus/public/.corpus.yaml`은 packet 예외(`versions:` 추가만)대로 바뀌었다. 문서 파일·SHA256SUMS 변경 없음. 평가셋·임계값·기존 ADR·기존 결과 폴더 변경 없음. 의존성 변경 없음.
- assert 완화: 기존 테스트 파일 수정 없음(새 테스트 3개만 추가).

### 2) Edit 목록 대조
- `git diff --name-only`는 16개다. 목록 밖은 **`backend/app/container.py` 1개**다.
  - `latest_only=settings.search_latest_only` 한 줄 배선이다. `SEARCH_LATEST_ONLY`를 동작시키려면 필요하고 최소다. **정당하다고 판단한다.**
  - 다만 packet은 목록 밖 수정 시 `ask`를 요구한다. report의 "최종 diff는 Edit 목록 안"이라는 서술도 사실과 다르다(경미). coordinator가 사후 승인으로 처리하면 된다.
- `version_superseded` 열: 0007은 Edit 목록 안이다. manifest 없이 corpus 재계산을 하려면 필요하고, ADR 0006 §4에 이유가 적혀 있다. **정당하고 최소다.**

### 3) 경계 사례 테스트 (`tests/unit/test_doc_versions.py`, 33건)
- 덮인 것:
  - v2.10 > v2.9, 2.0 == 2 동률
  - R2/R3, Rev 5/6, Amendment 동률 깨기
  - 날짜만, 판 우선 후 날짜
  - 동률·비교 불가(v 대 R, v 대 날짜, 최종 대 개정) → 둘 다 최신
  - superseded 명시, family 전체가 superseded면 숨기지 않음
  - family·corpus 혼선 없음, 토큰 없는 단독, 잘못된 날짜, manifest 우선·glob
- "확신 없으면 숨기지 않음"을 코드에서 확인했다:
  - `compare_versions`는 공통 종류가 없고 날짜도 하나라도 없으면 `None`을 돌려준다. `latest_flags`는 `== 1`일 때만 숨긴다.
  - 추정 실패(토큰 없음, 빈 family)는 `family=None` → 항상 최신이다.
  - 실패·미완 문서(INDEXED 아님)는 재계산에 참여하지 않는다.
- **비교 경로 자체는 지켜진다. 문제는 묶는 단계(family 키)에서 생긴다 → R1·R2.**

### 4) 필터 적용 범위
- 벡터·pg_trgm 두 채널이 같은 `stmt`(필터 포함)에서 정렬만 달리한다(`vector_search_service.py:148-160`). 통합 테스트가 hybrid False/True를 모두 확인한다.
- reranker: 필터가 걸린 후보 집합을 재정렬하므로 옛 판이 섞이지 않는다.
- `include_superseded`·`SEARCH_LATEST_ONLY=false` → `latest_only` 옵션 미전달. 단위 테스트로 확인했다.
- `is_latest` 재계산:
  - 매 색인 후 corpus 단위로 INDEXED 전체를 다시 계산한다(크래시 시에도).
  - 중복(checksum 같음) 경로에서 판 열을 갱신한다. 새 판 추가 시 강등되는 것과 실패한 새 판이 옛 판을 숨기지 않는 것은 통합 테스트로 확인된다.
  - corpus 경계는 `(group, family)`로 지켜진다(통합 테스트 있음).
- 비차단 관찰:
  - **삭제**: 문서 삭제 API가 없고, 디스크에서 지운 파일의 행은 INDEXED로 남아 계속 경쟁한다(기존 동작). 옛 판이 남은 상태에서 새 판 파일만 지우면, 행이 남아 옛 판이 계속 숨겨진다. 후속 이슈로 기록할 것을 권고한다.
  - **같은 내용·다른 이름**: checksum이 같은 두 파일(`guide.pdf`, `guide_v2.pdf`)이면 나중에 처리된 쪽의 판 정보가 기존 행을 덮는다. 처리 순서는 `bounded` 병렬이라 비결정적이고, `file_name`은 처음 이름 그대로라 행의 이름과 판이 어긋날 수 있다.
  - corpus가 None이면 재계산을 생략한다(아무것도 숨기지 않음 — 안전한 쪽).
  - `eval/compare_search_modes.py`는 `latest_only`를 넘기지 않는다(진단 스크립트, 기본 False). 기록만 남긴다.

### 5) Alembic 0007
- 업: nullable 3열 + `version_source` server_default `'none'`, `version_superseded` false, `is_latest` true → 기존 행은 아무것도 숨기지 않는다.
- 다운: 6열을 drop한다.
- 통합 테스트가 0006 다운 → 기존 행 삽입 → 업(기본값 확인) → 다시 다운(행 유지) → 업 순서로 확인한다. 양호.

### 6) 프롬프트·재색인
- `prompt_builder` 변경은 `format_source_label`에 ` · 판`을 붙이는 것뿐이다. 지시문 본문과 프롬프트 파일 변경 없음. 판이 없는 문서는 이전과 바이트 동일하다(테스트 있음).
- chunker·embedding 입력 변경 없음 → 재색인 불필요. 확인했다.

### 7) public 측정 (결과 폴더 4개를 직접 집계)
- 4회 모두: Ollama 0.40.2, exact, chunk 2,029, commit 8d1ae8f, gemma4:e4b, 99문항(answerable 79)이다. errors 0, 분모>0. `search_latest_only`가 off 2회와 on 2회로 기록돼 있다.
- **카나리아**: 전체 top-5에서 05 chunk 수가 끔 47·47 → 켬 0·0이다. 필터가 실제로 동작했다.
- 수치는 report·README·journey·issue 005와 일치한다.
  - hit 96.2 → 94.9, 섹션 87.3 → 84.8, Cit 86.7/85.3 → 90.7/90.7, KW 92.0, 거절 95.0
  - p10~p16: R2 27 → 0, R3 8 → 29, hit 5 → 7, cit 2 → 7
  - p32~p34는 켬에서 hit·섹션·인용 모두 miss, 거절 아님
- 편향 주의("실패 재확인"): report·README·journey·issue 005에 있다. ADR 0006은 측정을 journey로 넘겨서 직접 문구는 없다(허용).
- hit@5 하락과 p32~p34가 정답 파일 05라는 점은 정직하게 적혀 있다. **p32의 성격은 R3 참조.**
- 경미: `git_commit`이 dirty tree에서 `8d1ae8f`로 기록돼 코드 상태를 특정하지 못한다(기존 관행과 같음).

### 8) API
- `file_type` 패턴에 `docx|xlsx`를 추가했다(테스트 있음).
- `SourceOut.versionLabel/versionDate/isLatest`, `/retrieve` metadata에 같은 필드, `AskResponse.supersededWarning`을 추가했다.
  옛 판이 인용됐을 때만 경고가 붙고 최신판만 검색하면 붙지 않는다(단위 테스트로 확인). Streamlit 체크박스·판 표시·경고도 연결돼 있다.

### 게이트 증빙 (Tester 몫, 참고)
- `evidence/junit.xml`: tests=564, failures=0, errors=0, skipped=0, timestamp 2026-10-11T17:26:14+09:00.
- 리뷰 중 단위 테스트 2파일을 재실행했다: 39 passed.

## 발견 리스크 (심각도순)
1. R1 디렉터리 무시 family → 다른 시험의 동명 문서를 숨김 (높음, 업무 코퍼스에서 흔함)
2. R2 날짜 계열·R 식별자 오탐 → 다른 문서를 숨김 (높음, 회의록·방문 보고서)
3. R3 p32 한계 미문서화 (중간, 문서)
4. 삭제·이동된 파일의 행이 계속 경쟁 (중간, 기존 동작에서 비롯, 후속 이슈)
5. checksum 중복 시 판 정보 덮어쓰기 비결정성 (낮음)
6. container.py를 ask 없이 수정, report 서술 부정확 (낮음, 절차)

## 후속 제안
- R1·R2를 고친 뒤 Phase 4 추정 정확도 측정에 다음 집계를 더한다: "family로 묶였지만 수동 목록상 같은 문서가 아닌 쌍의 수", "날짜만으로 숨겨진 문서 수".
- 판이 있는 코퍼스의 평가셋 정답을 판 단위로 적는 작업(journey 교훈)은 새 파일로 한다. 기존 문항은 수정 금지다.
