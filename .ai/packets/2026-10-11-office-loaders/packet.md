# Task Packet: docx / xlsx 로더 + 서명본(암호화) PDF 열기

- **ID:** 2026-10-11-office-loaders
- **날짜:** 2026-10-11
- **Planner:** coordinator (Claude Opus 5.5, 기본 workspace)
- **Implementer:** Claude Sonnet 5.5 (`orca orchestration worker-start --agent claude --model claude-sonnet-5-5`)
- **Reviewer:** Claude Opus 5.5 (read-only) / **Tester:** Claude Sonnet 5.5 (게이트 실행·증빙만)
- **관련:** 회사 문서 테스트 결론 ①(ONBOARDING §2), ADR 0001(PDF 라이브러리), base `8ebf1fe`
- **Workspace:** 새 top-level worktree `office-loaders` / base = `origin/main`
- **통합 대상:** 기본 workspace → `main` — PR (rebase merge)

## 배경 (왜 하는가)
- 실제 업무 문서 87건을 넣어 보니 **그대로는 26건(PDF)만 읽혔다.** docx 25·xlsx 35·doc 1은 미지원이고,
  서명본 PDF 일부는 암호화(열기 암호 없음, 권한 암호만)라 `ENCRYPTED_PDF`로 빠졌다.
- 그때는 레포 밖 변환 스크립트(python-docx·openpyxl·textutil → Markdown)로 우회했다.
  변환하자 정답이 6/42에서 20/42로 올랐다(최신판만, 재정렬 없음). **이 우회를 제품 기능으로 옮기는 것이 목표다.**
- 현재 코드:
  - `document_loader.SUPPORTED_EXTENSIONS`: md, txt, pdf, xml(JATS), html
  - `text_extractor.extract()`가 형식별 추출기로 보낸다. 결과는 `Section(text, page_number, section_title, page_spans)` 목록
  - 표는 `table_rows.rows_to_lines()`가 "열이름: 값; …" 줄로 바꾼다(HTML·JATS가 이미 사용)
  - `pdf_extractor.read_pdf_pages()`는 빈 암호로 여는 것을 이미 시도한다. 실패하는 이유는 AES 복호화에 필요한
    `cryptography` 패키지가 없어서다.
  - DB `file_type`은 Text 열이라 마이그레이션이 필요 없다.
- JATS·HTML 추출기는 **표준 라이브러리만** 쓴다(선례). docx·xlsx도 zip + XML(OOXML)이라 같은 방식으로 읽을 수 있다.

## 할 일
### Phase 1 — docx 추출기 (`backend/app/services/docx_extractor.py`, 표준 라이브러리만)
1. `word/document.xml` 본문을 순서대로 읽는다:
   - 문단: 스타일이 제목(`Heading N`·`제목 N`, 또는 `outlineLvl`)이면 섹션 제목 경로로 쓴다
   - 나머지 문단은 본문으로 쓴다
2. 표는 `rows_to_lines()`로 렌더링한다.
   - 가로 병합(`gridSpan`)과 세로 병합(`vMerge`)은 값을 반복하지 않는다.
   - 첫 행을 머리글로 쓴다. 단, 모든 셀이 비어 있지 않을 때만이다(HTML 규칙과 같게).
3. 머리말·꼬리말·각주·변경 추적 삭제분(`w:del`)은 넣지 않는다. 삽입분(`w:ins`)은 넣는다.
4. 페이지 번호는 없다(`page_number=None`). 인용은 섹션 제목으로 한다.
5. 손상된 zip·XML은 `CORRUPTED_FILE`로, 암호가 걸린 docx(OLE 컨테이너)는 `ENCRYPTED_FILE`로 처리한다.

### Phase 2 — xlsx 추출기 (`backend/app/services/xlsx_extractor.py`, 표준 라이브러리만)
6. 시트 하나를 섹션 하나로 만든다(`section_title = 시트 이름`).
   - 값은 공유 문자열·인라인 문자열·수식의 캐시값(`<v>`)을 쓴다.
   - 날짜 서식(기본 numFmt 14~22와 y·m·d를 포함한 사용자 서식)은 ISO 날짜로 바꾼다.
7. 머리글 행은 앞 15행 중 비어 있지 않은 셀이 4개 이상인 첫 행으로 정한다(변환 스크립트에서 쓴 규칙).
   - 그 위의 행은 "a | b" 줄로 둔다.
   - 그 아래 행은 `rows_to_lines()`로 렌더링하고, 줄 앞에 `[시트명]`을 붙인다.
8. 숨김 시트는 넣는다. 다만 시트 상태를 결과 진단에 기록한다.
9. 손상 파일과 암호화 파일은 Phase 1과 같은 오류 형식으로 처리한다.

### Phase 3 — 서명본 PDF와 doc
10. `cryptography`를 **기본 의존성**에 추가한다(**사용자 승인 완료 2026-10-11**: cryptography 50.0.2·cffi 2.1.1·pycparser 3.11, PyPI). `uv add --project backend cryptography`로 추가한다.
    - 열기 암호가 없는 AES PDF는 열린다.
    - 열기 암호가 있는 PDF는 지금처럼 `ENCRYPTED_PDF`로 처리한다.
    - `pdf_extractor`의 주석을 고친다.
11. `.doc`(구형 바이너리)은 지원하지 않는다. 대신 `UNSUPPORTED_FILE_TYPE`과 함께 "docx로 저장 후 다시 넣으세요"
    안내를 낸다. 지금은 확장자가 없는 것처럼 조용히 무시된다.

### Phase 4 — 시험 데이터와 테스트 (공개·합성만)
12. `scripts/generate_sample_office.py`를 추가한다. 표준 라이브러리로 **합성** 문서를 만든다:
    - docx 1개: 영상 판독 차터 형식으로, 제목 계층, 병합 셀 표, 변경 추적 포함
    - xlsx 1개: 영상 촬영 일정표 형식으로, 머리글 위 안내 행, 날짜·수식, 시트 2개
    - 암호화 PDF 1개: 권한 암호만, AES-128
    - 출력 위치는 `samples/office/`다. **toy 코퍼스(`samples/documents`)에는 넣지 않는다.** toy 평가 수치를 바꾸지 않기 위해서다.
13. 단위 테스트(`tests/unit/test_docx_extractor.py`, `test_xlsx_extractor.py`, PDF 테스트 추가):
    - 제목 경로, 병합 셀, 변경 추적
    - 날짜 변환, 머리글 탐지, 시트 섹션
    - 손상·암호 오류 형식
    - `.doc` 안내
14. 통합 테스트를 하나 추가한다. `samples/office/`를 색인했을 때 세 파일이 모두 `indexed`가 되고, chunk의
    `file_type`·`section_title`이 맞는지 본다.
15. 기존 toy·public 평가는 **다시 돌리지 않는다.** PDF·MD 경로를 건드리지 않으므로 필요 없다.
    `make test`가 회귀를 막는다.

### Phase 5 — 회사 문서 재측정 (coordinator가 로컬에서, 집계만)
16. 머지 후 coordinator가 레포 밖 로컬 전용 폴더에서 실행한다:
    - **읽힘:** 87건 중 `indexed` 수(전에는 26)와 실패 유형별 수
    - **변환 대비 추출 일치도:** 파일별로, 변환 Markdown의 토큰이 새 추출 결과에 얼마나 들어 있는지(재현율) 계산하고
      중앙값·최솟값만 낸다
    - **검색:** 42문항에서 출처 파일이 top-5에 드는지 본다. 설정은 최신판만·재정렬 없음으로, "변환본"과 "원본 그대로(새 로더)"를
      같은 조건에서 비교한다
    - 에이전트는 문서 내용과 답변을 출력하거나 읽지 않는다. 스크립트는 숫자만 출력한다
17. 결과는 `docs/journey.md` 새 절과 README 한 줄에 **집계만** 쓴다.
    - 예: "실제 업무 문서 87건 중 N건 바로 색인(전 26건)"
    - 정답률 재채점은 이번 범위가 아니다("측정 안 함")

## Scope
### Read (참고만)
- `backend/app/services/{html_extractor,jats_extractor,headings,chunker,indexing_pipeline}.py`, `docs/decisions/0001-pdf-library.md`
### Edit
- 신규: `backend/app/services/docx_extractor.py`, `backend/app/services/xlsx_extractor.py`, `scripts/generate_sample_office.py`, `samples/office/**`
- 수정: `backend/app/services/{document_loader,text_extractor,pdf_extractor,document_types}.py`
- `tests/unit/**`, `tests/integration/**`(새 테스트 추가만, 기존 assert 완화 금지)
- `backend/pyproject.toml`·`backend/uv.lock`: **`cryptography` 한 줄만**(승인됨)
- `docs/decisions/0001-pdf-library.md`(절 추가: 암호화 PDF), `docs/journey.md`, `README.md`(지원 형식 표)
- `.ai/packets/2026-10-11-office-loaders/report-implementer.md`, `…/evidence/`
### Protect (scope.md 상시 목록에 더해)
- toy·public 코퍼스와 평가셋, 기존 `eval/results/**`
- PDF·Markdown·JATS·HTML 추출 동작(공용 헬퍼를 고쳐야 하면 먼저 `ask`로 묻는다)
- `offline-bundle/**`(재빌드하면 lock에서 cryptography wheel이 자동으로 들어가므로 수정하지 않는다)

## 완료 조건
- Tester: `make lint`, `make test` exit 0. junit의 tests·failures=0·errors=0·timestamp를 인용한다. integration skip 0.
- Reviewer:
  - 위 Phase 1~4가 테스트로 덮였는지
  - 표준 라이브러리 외 추가 의존성이 `cryptography`(와 그 의존성)뿐인지
  - XML 파싱이 안전한지: 외부 엔티티 없음, zip 폭탄 상한(압축 해제 크기·항목 수)
  - `git diff --name-only` ⊆ Edit 목록
  - denylist 검사
- Phase 5 수치는 coordinator가 집계만 커밋한다.

## 제약
- git commit/push/브랜치/checkout/stash 금지(커밋은 coordinator가 한다)
- **패키지 다운로드는 승인된 `cryptography`(+cffi, pycparser)만 한다.** 다른 패키지나 다른 버전이 lock에 끌려오면 멈추고 `ask`로 묻는다. 그 밖의 다운로드와 외부 LLM API는 금지
- 로컬 전용 업무 문서(scope.md의 로컬 전용 자료)는 Implementer가 열지 않는다. 개발은 합성 문서로만 한다
- Edit 목록 밖을 고쳐야 하면 `ask`로 묻는다. 완료는 `worker_done`으로 1회 보낸다
