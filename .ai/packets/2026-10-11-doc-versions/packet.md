# Task Packet: 판본 메타데이터 + 최신판 기본 필터 + 인용에 버전

- **ID:** 2026-10-11-doc-versions
- **날짜:** 2026-10-11
- **Planner:** coordinator (Claude Opus 5.5, 기본 workspace)
- **Implementer:** Claude Sonnet 5.5 (`worker-start --agent claude --model claude-sonnet-5-5`)
- **Reviewer:** Claude Opus 5.5 (read-only) / **Tester:** Claude Sonnet 5.5 (게이트 실행·증빙만)
- **관련:** 이슈 005(GitHub #6), 회사 문서 테스트 결론 ②, base `8d1ae8f`
- **Workspace:** 새 top-level worktree `doc-versions` / base = `origin/main`
- **통합 대상:** 기본 workspace → `main` — PR (rebase merge)

## 배경 (왜 하는가)
- 같은 문서의 여러 판이 한 코퍼스에 있으면 옛 판이 검색되고, 옛 판 내용이 사실처럼 답으로 나간다.
  - **공개 코퍼스(#6):** ICH E6(R3) 질문 7개 중 6개에서 top-5 대부분을 E6(R2) 안내서(`05_mfds_ich_gcp_ko.pdf`)가 차지했다.
    p10은 R2에만 있는 예외 조항을 "E6(R3)에 따르면"이라며 답했다.
  - **업무 문서:** 판이 여러 개인 문서가 많다(87건 중 최신판 16건). 지난 테스트에서 위험 1순위가 판본 혼동이었다.
    최신판만 넣었을 때 정답이 17/42에서 20/42로 올랐다(같은 변환본, 재정렬 없음).
- 현재 코드:
  - `Document`에 판 정보가 없다(corpus·classification만 있음).
  - 검색 필터는 file_type·corpus·classification이다.
  - `SourceOut`에는 파일명·쪽·섹션만 있다.
  - `.corpus.yaml`은 `name`·`classification`·`include`만 읽는다(`llm_guardrail.read_marker`).
- 덤으로 고칠 것: `AskRequest.file_type` 패턴이 `^(md|txt|pdf|xml|html)$`라서 #17에서 추가한 docx·xlsx로 거를 수 없다.

## 설계 (coordinator 결정)
1. **판 정보의 출처는 두 가지다. 명시가 추정보다 우선한다.**
   - (a) **명시:** `.corpus.yaml`의 `versions:` 목록. 항목마다 `match`(glob), `family`, `version`, `date`(선택), `superseded`(선택, bool)를 둔다.
   - (b) **추정:** 파일명에서 판 토큰(`v2.1`, `ver 3`, `Rev6`, `R3`, `Amendment 2`, `_20250915` 같은 8자리 날짜, `개정`, `최종`)을 찾는다.
     토큰을 뺀 나머지를 정규화해 `family` 키로 쓴다.
   - 추정에 실패한 문서는 family 없음(단독 문서)으로 둔다. **확신이 없으면 숨기지 않는다.**
2. **최신판 판정:** 같은 corpus·family 안에서 version을 비교한다(숫자 비교, R/Rev/Amendment 번호). 그다음 date를 비교한다.
   - 비교할 수 없거나 동률이면 둘 다 최신으로 둔다.
   - `superseded: true`를 명시하면 그 판은 최신이 아니다.
   - 색인이 끝날 때 corpus 단위로 다시 계산한다. 문서가 추가·삭제돼도 맞아야 한다.
3. **DB:** `documents`에 열을 추가한다(Alembic 0007).
   - `doc_family`, `version_label`, `version_date`, `version_source`(`manifest`|`filename`|`none`), `is_latest`(bool, 기본 true)
   - 마이그레이션 자체는 재색인 없이 기존 행을 기본값으로 채운다.
4. **검색:** 기본값은 **최신판만**이다(`is_latest = true`).
   - `/api/ask`·`/api/retrieve`에 `include_superseded: bool = false`를 추가한다.
   - UI에 "옛 판 포함" 체크박스를 추가한다.
   - 설정 `SEARCH_LATEST_ONLY`(기본 true)로 전체 기본값을 끌 수 있다.
5. **인용·프롬프트:**
   - `SourceOut`에 `versionLabel`·`versionDate`·`isLatest`를 추가한다.
   - 생성 프롬프트의 근거 블록 머리에 `[파일명 · 판]`을 넣는다(embedding·chunk 텍스트는 바꾸지 않는다 → 재색인 불필요).
   - UI 출처 표시에 판을 붙인다.
   - 옛 판을 포함해 검색했고 옛 판이 인용되면 답 아래에 "옛 판(…) 내용 포함" 경고를 붙인다.
6. **이번 범위가 아닌 것:**
   - chunk 머리말에 문서·판·시험 식별자 넣기(재색인 필요, 3c #13과 함께)
   - 변경대비표의 "변경 전" 문구 처리(⑤)
   - 질문 속 판 이름("R3")으로 거르기

## 할 일
### Phase 1 — 판 정보 추출과 최신판 판정
1. `backend/app/services/doc_versions.py`를 새로 만든다.
   - 파일명 판 토큰 파서, family 키 정규화, manifest 매칭, 최신판 판정(순수 함수)
   - 한국어·영어 파일명, 확장자 제거, 대소문자, 구분자(`_`, `-`, 공백, 괄호)를 처리한다.
2. 단위 테스트를 공개·합성 파일명으로 만든다(회사 파일명 금지).
   - 숫자 판 비교: v2.10 > v2.9
   - R2 대 R3, 날짜만 있는 판
   - 판과 날짜가 섞인 경우
   - 동률·비교 불가 → 둘 다 최신
   - superseded 명시
   - family가 다른 문서끼리 섞이지 않음
   - 판 토큰이 없는 단독 문서

### Phase 2 — 저장·검색·API
3. Alembic 0007과 모델 필드를 추가한다. `indexing_pipeline`이 등록할 때 판 정보를 채운다.
   색인이 끝나면 corpus 단위로 `is_latest`를 다시 계산한다. 중복·재색인 경로도 포함한다.
4. `vector_search_service.search_chunks`에 최신판 필터를 추가한다. 하이브리드(pg_trgm) 채널에도 같은 필터를 적용한다. 이 필터를 `rag_service`·API 스키마로 연결한다.
5. `AskRequest.file_type` 패턴에 docx·xlsx를 추가한다.
6. `SourceOut`과 프롬프트 근거 블록에 판 정보를 넣는다. Streamlit에 체크박스와 출처 판 표시를 넣는다.
7. 통합 테스트(실제 PostgreSQL)를 만든다.
   - 같은 family의 두 판을 색인하면 기본 검색에서 옛 판이 빠진다.
   - `include_superseded=true`면 옛 판이 나온다.
   - 새 판을 추가 색인하면 이전 최신판의 `is_latest`가 바뀐다.
   - 0007 업·다운그레이드
   - API 응답의 판 필드

### Phase 3 — 측정
8. **공개 코퍼스:** `corpus/public/.corpus.yaml`에 `versions:`를 추가한다(아래 Edit 예외).
   - ICH E6 family: `02_ich_e6r3_2025.pdf` = R3, `05_mfds_ich_gcp_ko.pdf` = R2, `superseded: true`
   - 다른 문서는 family 없음
   - **임계값·규칙은 바꾸지 않는다.**
9. public을 exact로 2회 돌린다(gemma4:e4b, `think:false`). 기준선은 같은 날 같은 색인의 `SEARCH_LATEST_ONLY=false` 2회다.
   - 보고: 전체 지표, ICH E6(R3) 7문항(p10~p16)의 top-5 구성과 결과, 05를 근거로 쓰던 다른 문항이 잃은 것이 있는지
   - **편향 주의:** 이 7문항은 실패를 본 뒤 고친 것이라 개선 수치는 "실패 재확인"으로만 쓴다. report와 문서에 그렇게 적는다.
10. 결과 폴더는 `eval/results/2026-10-11_public_*`에 둔다. README와 journey에는 측정 사실만 적는다.

### Phase 4 — 업무 문서 재측정 (coordinator가 머지 후 로컬에서, 집계만)
11. 최신판 **추정**의 정확도를 잰다. 파일명 추정만으로 정한 `is_latest`를 수동 최신판 목록(16건)과 비교한 일치·불일치 수를 낸다.
12. 87건 전체를 색인한 뒤 42문항으로 비교한다.
    - 비교 조건: 최신판 필터 끔 대 켬(추정만)
    - 지표: 정답 파일 top-5, top-5 중 옛 판 chunk 비율
13. journey 새 절과 README 한 줄에 집계만 쓴다.

## Scope
### Read (참고만)
- `docs/issues/005-*.md`, `eval/**`(아래 Edit 제외), `backend/app/services/llm_guardrail.py`(marker 읽기 재사용)
### Edit
- 신규: `backend/app/services/doc_versions.py`, `backend/alembic/versions/0007_*.py`
- 수정:
  - `backend/app/models/document.py`
  - `backend/app/services/{indexing_pipeline,vector_search_service,rag_service,prompt_builder}.py`
  - `backend/app/schemas/rag.py`, `backend/app/api/**`(필드 연결만)
  - `backend/app/config.py`(`SEARCH_LATEST_ONLY`만), `frontend/streamlit_app.py`
- `tests/unit/**`, `tests/integration/**`(새 테스트 추가, 기존 assert 완화 금지)
- **Protect 예외:** `corpus/public/.corpus.yaml`에 `versions:` 블록 추가만. 문서 파일·`corpus/SHA256SUMS`는 그대로 둔다.
- `eval/results/<새 폴더>/**`
- `eval/run_eval.py`: 설정(`SEARCH_LATEST_ONLY`)과 판 필터 상태를 config.json에 기록하는 데 필요할 때만
- `docs/decisions/0006-document-versions.md`(새 ADR), `docs/journey.md`, `docs/issues/005-*.md`(상태 갱신), `README.md`, `.env.example`
- `.ai/packets/2026-10-11-doc-versions/report-implementer.md`, `…/evidence/`
### Protect (scope.md 상시 목록에 더해)
- chunker·chunk 텍스트·embedding 입력(재색인이 필요한 변경 금지)
- `prompt_builder`의 지시문 본문(근거 블록 머리 형식만 바꾼다)
- 임계값(`min_relevance_score`, `scope_margin`)과 평가셋

## 완료 조건
- Tester: `make lint`, `make test` exit 0. junit의 tests·failures=0·errors=0·skipped=0·timestamp를 인용한다.
- Reviewer:
  - scope.md 평가 규칙과 위반 검출 1~6
  - 최신판 판정의 경계 사례가 테스트로 덮였는지
  - "확신 없으면 숨기지 않음"이 지켜지는지
  - 하이브리드 채널에도 필터가 걸리는지
  - 0007 다운그레이드
  - public 측정이 같은 색인·exact·같은 Ollama인지, 편향 주의 문구가 있는지
  - `git diff --name-only` ⊆ Edit 목록
  - denylist 0건

## 제약
- git commit/push/브랜치/checkout/stash 금지(커밋은 coordinator가 한다)
- 패키지·모델 다운로드 금지, 외부 LLM API 금지
- 로컬 전용 업무 문서(scope.md의 로컬 전용 자료)는 Implementer가 열지 않는다. Phase 4는 coordinator 몫이다
- 긴 실행은 `caffeinate -i`로 감싼다
- Edit 목록 밖을 고쳐야 하면 `ask`로 묻는다. 완료는 `worker_done`으로 1회 보낸다
