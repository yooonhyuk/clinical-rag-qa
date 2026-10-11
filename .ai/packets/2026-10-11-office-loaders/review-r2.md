# Review R2 — 2026-10-11-office-loaders (fix1 재리뷰)

- Reviewer: Claude Opus 5.5 (read-only, r2)
- 대상: working tree(base `origin/main` = HEAD = `8ebf1fe`) + untracked. 기준: `review-r1.md` R1~R3, N1~N4(채택), N5(미채택), N6(coordinator)
- **판정: REQUEST_CHANGES** — R1이 반만 고쳐졌다(압축 해제는 1회로 줄었지만, 같은 part를 가리키는 시트 반복 → 출력·CPU 증폭은 그대로).
  R2·R3·N1~N4·N6과 scope 검사는 통과.

## 반려 항목

### R1′. 같은 part를 가리키는 시트 반복 증폭이 그대로다 — `xlsx_extractor.py:234-243`, `_sheet_parts` `:209-218`
- **문제:** fix1은 `read_member` 캐시로 압축 해제 바이트를 1회만 센다. 하지만 `extract_xlsx_with_diagnostics`는 시트마다
  캐시된 같은 바이트를 다시 `parse_xml`하고, 다시 행과 줄을 만들고, 섹션을 하나씩 더 붙인다. 시트 상한 256은 r1 재현(200개)보다 크다.
  그래서 r1이 지적한 "작은 파일 → 거대한 섹션 텍스트·CPU" 증폭이 남아 있다. 새 테스트
  `test_repeated_sheet_part_is_read_once_and_sheet_count_is_capped`도 50개 섹션(`len(...) == 50`)이 나오는 동작을 정상으로 고정한다.
- **재현(scratchpad 합성, 직접 실행):** 1.57 MB worksheet part 1개 + 그 part를 가리키는 `<sheet>` N개
  | 시트 수 | 파일 | 결과 | 섹션 텍스트 | 시간 | maxrss |
  |---|---|---|---|---|---|
  | 200 (r1 재현) | 125 KB | **OK, 200 섹션** | **133 MB** | 6.7 s | 215 MB |
  | 256 | 125 KB | **OK, 256 섹션** | **171 MB** | 8.6 s | 393 MB |
  | 257 | 125 KB | `CORRUPTED_FILE` (시트 상한) | – | 0 s | – |
  part는 64 MB까지 허용되므로 증폭은 part 크기에 비례해 더 커진다(최악 256 × 64 MB 파싱). 이 텍스트가 그대로 chunker와 임베딩으로 간다.
- **방향(둘 중 하나 이상):**
  1. `_sheet_parts`(또는 루프)에서 이미 나온 part를 가리키는 시트는 건너뛰고 진단에 남기거나(`sheet 'X': duplicate part`), `CORRUPTED_FILE`로 끊는다.
     정상 xlsx는 시트끼리 part를 공유하지 않는다.
  2. 그리고/또는 "소비한 바이트" 예산을 둔다. 캐시 적중도 `MAX_TOTAL_BYTES`에 더해서, 파싱에 넘긴 총량이 상한을 넘으면 끊는다.
  - 회귀 테스트는 "같은 part 시트 N개 → 섹션 1개(또는 오류)"로 바꾼다. 지금 테스트는 fix1에서 새로 생겼으므로, 이것을 바꾸는 것은 assert 완화가 아니다.

## 확인 결과 (통과)

### 1) r1 재현 3건 재실행 (scratchpad, `uv run --project backend python -I`)
- **R1:** 압축 해제 누적·캐시는 동작한다(같은 part의 반복 read는 `bytes_read` 불변). 시트 257개 → `CORRUPTED_FILE`. **증폭은 남음 → R1′**
- **R2 ✅:** A열 2,000행 + `XFD2001` 1셀(16 KB) → 0.0 s, tracemalloc 피크 3 MB(수정 전 536 MB)
- **R3 ✅:** UTF-16 `word/document.xml` + `<!ENTITY a "PWN">` → `CORRUPTED_FILE: DTD/entity declarations not allowed`
  - 변형 3개도 모두 거부됐다: styles.xml UTF-16 DTD, BOM 없는 UTF-16LE, UTF-8 `<!DOCTYPE … SYSTEM>`

### 2) 새 우회 탐색
- **해제 바이트 누적:** 모든 read가 `read_member` 하나를 거친다(`grep`). 이 함수가 `bytes_read`를 누적하고 남은 예산으로 `read(limit+1)` 한다.
  - docx: `word/document.xml`, `word/styles.xml`
  - xlsx: `sharedStrings`, `styles`, `workbook`(캐시 적중), `_rels/workbook.xml.rels`, 시트
  - docx는 `numbering.xml`을 읽지 않는다(경로 자체가 없음).
  - 그 밖의 `ZipFile.read`/`open` 호출은 없다.
- **파서 수준 거부:** 모든 XML 파싱이 `parse_xml`(`_NoDoctypeBuilder.doctype` 예외)을 쓴다.
  - xlsx part 5종(sharedStrings·styles·workbook·rels·sheet)에 UTF-16 DTD를 하나씩 넣어 모두 `CORRUPTED_FILE`을 직접 확인했다.
  - docx document·styles도 같다.
  - 두 추출기에 `ET.fromstring`/`ET.parse` 직접 호출은 없다(JATS는 기존 경로라 범위 밖).

### 3) 출력 형식
- 행 dict로 바꾼 렌더링(`_plain`/`_labelled`)을 fix1 전 방식과 비교했다. 전에는 행을 시트 폭까지 채운 뒤 `rows_to_lines`로 렌더링했다. 결과는 같다.
  - 머리글 있는 열은 `h: v`, 머리글 이름 없는 열은 값만 남는다.
  - 빈 셀은 건너뛰고, 빈 행은 버린다.
  - 머리글 위 행은 `a | b`, 머리글이 없으면 `[시트] a | b`다.
- 테스트 이름을 비교했다(`evidence/junit-tester.xml` 491 → `junit-fix1.xml` 502). 삭제는 0이고 추가만 11개다.
- tracked 테스트 diff는 `.docx`→`.pptx` 치환과 테스트 추가뿐이다. 이것은 r1에서 판정했다.
- 기존 xlsx/docx 테스트의 기대 문자열(`"[일정] 방문: V1; 날짜: 2026-10-05; 검사: CT; 비고: 3"` 등)은 그대로이고 통과한다.

### 4) N1~N4
- **N1 ✅** `_to_int`로 `numFmtId`·`s`·`r` 파싱. `test_non_numeric_style_and_numfmt_ids_do_not_crash`
- **N2 ✅** `_ELAPSED_RE`. `[h]:mm:ss` 1.5 → `"1.5"`. `test_elapsed_time_format_is_not_a_date`
- **N3 ✅** `basedOn` 체인(순환 방지 `seen`)과 `gridBefore/After`(0~200 클램프). `test_style_inheritance_and_grid_before_after`
- **N4 ✅** `scan_documents`가 `~$*`를 건너뛴다. OLE 메시지는 "암호화되었거나 구형(doc/xls)"이다(`ENCRYPTED_FILE` 유지).
  - 테스트: `test_scan_skips_office_lock_files`, `test_ole_docx_message_mentions_legacy`
- N5는 미채택이다. 현 상태 그대로임을 확인했다.
- 단위 테스트 재실행: docx·xlsx·document_loader·text_extractor **41 passed**

### 5) Scope·의존성·denylist
- `git diff --name-only origin/main` 10개와 untracked가 모두 packet Edit 목록 안이다.
  - `.ai/packets/…/{packet,review-r1,test-r1}.md`는 coordinator/리뷰 산출물이다.
  - `evidence/`는 `.gitignore`(`.ai/packets/**/evidence/`) 대상이다.
- **uv.lock:** mtime 12:06으로 fix1(12:19~12:23)보다 이르다. `origin/main` 대비 `-` 줄 0개, `+name`은 cffi·cryptography·pycparser뿐이다.
  pyproject는 `cryptography>=50.0.2` 한 줄이다. fix1 이후 변화 없음.
- **denylist(7패턴) 0건:**
  - `git diff origin/main`
  - untracked 텍스트 전부(**packet.md 포함 → N6 해소**)
  - packet 디렉터리 md와 evidence
  - samples/office 3개(raw 바이트, docx/xlsx는 압축을 푼 XML)

## 비차단
- N7. 시트 하나가 64 MB까지 허용되고 `ET` 전체 트리로 파싱된다. part 하나의 메모리 피크는 크다(측정 안 함).
  R1′를 고치면 이 비용이 시트 하나만큼으로 묶인다. 더 줄이려면 `iterparse`를 쓴다(follow-up).

## 후속
- R1′만 고치면 된다. 수정 범위는 `xlsx_extractor.py`와 해당 테스트 1개다. r3에서는 위 재현(200·256 시트)을 다시 돌려 섹션 수와 텍스트 크기를 확인한다.
