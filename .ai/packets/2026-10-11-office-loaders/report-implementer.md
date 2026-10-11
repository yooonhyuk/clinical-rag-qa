# Implementer 보고 — 2026-10-11-office-loaders

## 구현
- `docx_extractor.py`: 제목 스타일(`Heading N`/`제목 N`/`outlineLvl`) → 섹션 경로, 표 → `rows_to_lines`(gridSpan·vMerge 값 반복 없음, 첫 행은 전 셀이 찰 때만 머리글), `w:del`·`w:moveFrom`·머리말·꼬리말·각주 제외, `w:ins` 포함, `page_number=None`.
- `xlsx_extractor.py`: 시트 = 섹션, 공유/인라인 문자열·수식 캐시값, 날짜 서식(14~22, y/m/d 사용자 서식, 1904 체계) → ISO, 머리글 = 앞 15행 중 비지 않은 셀 ≥4인 첫 행, 위 행은 `a | b`, 아래 행은 `[시트명] 열: 값`. 숨김 시트는 포함하고 `extract_xlsx_with_diagnostics()`가 `sheet 'X': hidden`을 반환(+로그). 진단을 DB까지 싣는 경로는 pipeline이 Read 범위라 건드리지 않음.
- OOXML 공용 안전 장치는 `docx_extractor`의 `open_ooxml/read_member/parse_xml`(xlsx가 import): DTD·ENTITY 거부, 항목 5,000개·부분 64MB·전체 256MB 상한, OLE(암호) → `ENCRYPTED_FILE`, 손상 → `CORRUPTED_FILE`.
- `.doc`: `SUPPORTED_EXTENSIONS`에 `doc`을 넣어 extract까지 보내고 "docx로 저장 후 다시 넣으세요" 안내와 `UNSUPPORTED_FILE_TYPE`. (pipeline의 `supported` 검사가 먼저 걸러 메시지를 못 바꾸므로 이 방식을 택함. `DiscoveredFile.supported`는 `.doc`에서 True.)
- `cryptography` 50.0.2 / cffi 2.1.1 / pycparser 3.11만 lock에 추가(다른 패키지·버전 변화 없음). pdf_extractor 주석 수정. ADR 0001에 절 추가, README 한 줄 + 형식 설명.
- `scripts/generate_sample_office.py` + `samples/office/`(docx·xlsx·AES-128 권한암호 PDF). 암호화 PDF 생성은 pymupdf(dev 의존성, 기존 PDF 생성기와 동일).

## 기존 테스트 변경 (확인 필요)
`.docx`를 "미지원 형식" 예시로 쓰던 3곳이 이제 지원 형식이라 깨졌다. assert는 그대로 두고 확장자만 `.pptx`로 바꿨다:
`tests/unit/test_document_loader.py`, `tests/unit/test_text_extractor.py::test_unsupported_type`, `tests/integration/test_pipeline_db.py`(notes.docx → notes.pptx).

## 게이트
- `make lint` exit 0.
- `pytest -q --junitxml=evidence/junit.xml`: 491 passed, skipped=0, failures=0, errors=0, timestamp 2026-10-11T12:10:47+09:00 (integration 포함, Docker 사용).
- 회사 문서는 열지 않았고 외부 다운로드는 승인된 3개 패키지뿐.

## 남은 것
Phase 5(회사 문서 재측정·journey·README 수치)는 coordinator 몫. journey.md는 수정하지 않음.

## fix1
Reviewer R1 판정(`review-r1.md`) 반영. Edit 범위·의존성 변경 없음(표준 라이브러리만).

- **R1** `docx_extractor.py`: `OoxmlArchive`(ZipFile 하위 클래스)가 실제 압축 해제 바이트(`bytes_read`)와 part 캐시를 가진다. `read_member`는 같은 part를 한 번만 풀고, 남은 예산(`MAX_TOTAL_BYTES - bytes_read`)을 넘으면 `CORRUPTED_FILE`. `xlsx_extractor.py`: 시트 수 상한 `_MAX_SHEETS=256`. docx·xlsx가 같은 헬퍼 사용. 테스트: `test_total_decompressed_bytes_are_capped`, `test_part_is_read_once_and_counted`(docx), `test_repeated_sheet_part_is_read_once_and_sheet_count_is_capped`(xlsx).
- **R2** `xlsx_extractor.py`: 행 = `dict[열, 값]`(값 있는 열만), 렌더링도 값 있는 열만(출력 형식 유지: `[시트] 열이름: 값; ...`, 헤더 이름 없는 열은 값만). 테스트 `test_far_column_cell_does_not_blow_up_memory`(3,000행 + `XFD` 1셀, tracemalloc 피크 < 20MB, 5초 미만; 수정 전 ~500MB).
- **R3** `parse_xml`: 바이트 검사 제거, `ET.XMLParser(target=TreeBuilder 하위 클래스)`의 `doctype()`에서 예외 → `CORRUPTED_FILE`(parser 수준, 인코딩 무관). xlsx 모든 XML 파싱이 같은 `parse_xml`. 테스트 `test_utf16_doctype_entity_is_rejected`(docx), `test_utf16_doctype_in_xlsx_part_is_rejected`(xlsx), 기존 `test_entities_and_oversized_parts_are_rejected`. (참고: `XMLParser.parser` 속성은 C 구현에 없어 target 훅을 썼다. Python 3.12.13에서 `-W error`로도 경고 없음.)
- **N1** `_to_int`(실패 시 기본값)로 `numFmtId`·`s`·`r` 파싱. 테스트 `test_non_numeric_style_and_numfmt_ids_do_not_crash`.
- **N2** `_ELAPSED_RE`로 `[h]`·`[mm]`·`[ss]` 서식은 날짜 아님. 테스트 `test_elapsed_time_format_is_not_a_date`.
- **N3** `_style_levels`가 `basedOn` 체인(순환 방지)으로 제목 수준 상속, `_row_grid`가 `w:gridBefore/gridAfter` 처리. 테스트 `test_style_inheritance_and_grid_before_after`.
- **N4** `document_loader.scan_documents`가 `~$` 시작 파일을 건너뜀(`test_scan_skips_office_lock_files`). OLE 매직 오류 메시지 → "…: 암호화되었거나 구형(doc/xls) 파일입니다"(`ENCRYPTED_FILE` 유지, `test_ole_docx_message_mentions_legacy`).
- N5 현 상태 유지, N6 미접촉(packet.md 안 건드림).

### 샘플 결정성
`generate_sample_office.py`를 두 번 실행해 sha256 비교: docx `48e6fc15…0db30e25`, xlsx `c21131ce…8d5b058b` 두 번 모두 동일(그리고 이전 생성분과도 동일 → 바이트 결정적). PDF는 AES IV가 무작위라 해시가 매번 다르다(`05135564…` → `939464d3…`); 텍스트 추출은 통합 테스트(`tests/integration/test_office_samples.py`)가 통과해 동일.

### 게이트
- `make lint` exit 0.
- `uv run --project backend pytest -q --junitxml=.ai/packets/2026-10-11-office-loaders/evidence/junit-fix1.xml` exit 0: tests=502 failures=0 errors=0 skipped=0 timestamp=2026-10-11T12:22:04.206659+09:00.

## fix2
Reviewer R2 판정(`review-r2.md`)의 R1′만 반영. Edit 범위는 `xlsx_extractor.py`, `test_xlsx_extractor.py`, 이 보고서뿐이다. 출력 형식·다른 동작 변경 없음.

- **R1′** `xlsx_extractor.py`: 이미 읽은 part(정규화된 경로)를 가리키는 두 번째 이후 `<sheet>`는 건너뛴다. 섹션은 처음 한 번만 만들고, 건너뛴 시트마다 진단/로그에 `sheet 'X': duplicate part <path>, skipped`를 남긴다. 추출한 섹션 텍스트 총량에도 상한(`_MAX_TEXT_BYTES = MAX_TOTAL_BYTES`)을 둬서 넘으면 `CORRUPTED_FILE`.
- 테스트: 기존 "50섹션 정상" 단언을 "섹션 1개 + 진단 49건"으로 교체(`test_repeated_sheet_part_is_one_section_and_sheet_count_is_capped`, 시트 257개 → `CORRUPTED_FILE`는 유지). 추가: `test_total_section_text_is_capped`(상한 monkeypatch, 3개 시트 정상 → 상한 초과 시 `CORRUPTED_FILE`).
- 참고: 테스트 파일 줄 길이 때문에 `make format`을 한 번 돌렸고 lint 수정 후 재확인했다. 다른 파일 diff 변화는 없다.

### 게이트
- `make lint` exit 0.
- `uv run --project backend pytest -q --junitxml=.ai/packets/2026-10-11-office-loaders/evidence/junit-fix2.xml` exit 0: tests=503 failures=0 errors=0 skipped=0 timestamp=2026-10-11T12:28:50.365297+09:00.

## fix3
Reviewer R4(`review-r3.md`) 반영. Edit 범위는 `xlsx_extractor.py`, `test_xlsx_extractor.py`, 이 보고서뿐이다. 출력 형식·다른 동작 변경 없음.

- **R4** `xlsx_extractor.py`: 텍스트 상한을 사후 검사에서 생성 중 검사로 바꿨다. `_Budget.spend`가 누적하다 `_MAX_TEXT_BYTES`를 넘는 순간 `CORRUPTED_FILE`.
  - 셀 단계: `_sheet_rows`가 셀 값 길이를 누적한다. 정규화 사본을 만들기 전에 남은 예산보다 긴 원본이면 바로 끊는다.
  - 렌더링 단계: `_sheet_lines`가 `_render_lines` 제너레이터에서 줄을 하나씩 받아 길이를 누적한다. 머리글이 행마다 반복되는 증폭도 같은 상한에서 끊긴다.
  - 두 예산(셀, 줄)은 시트 사이에서도 이어진다. 상한은 추출 텍스트 기준 `_MAX_TEXT_BYTES = 64 MB`(압축 해제 상한 `MAX_TOTAL_BYTES`와 분리, 문자 수 기준). 사후 `text_bytes` 검사는 제거했다.
- 테스트(상한을 8 MB로 monkeypatch, tracemalloc 피크 < 상한×4 = 32 MB, `CORRUPTED_FILE`):
  - `test_shared_string_amplification_is_cut_while_building`: 100 KB 공유 문자열 1개를 셀 5,000개가 참조.
  - `test_repeated_large_header_is_cut_while_rendering`: 100 KB 머리글 셀 + 4,999행.
  - 기존 `test_total_section_text_is_capped`(상한 250)는 그대로 통과.

### 게이트
- `make lint` exit 0.
- `uv run --project backend pytest -q --junitxml=.ai/packets/2026-10-11-office-loaders/evidence/junit-fix3.xml` exit 0: tests=505 failures=0 errors=0 skipped=0 timestamp=2026-10-11T12:33:25.228149+09:00.

## fix4
Reviewer R4(`review-r4.md`) 차단 B1~B6과 비차단 N1을 반영했다. 리뷰의 '수정 방향' 1~6과 coordinator 결정을 따랐다. Edit 범위는 `docx_extractor.py`, `xlsx_extractor.py`, 두 테스트 파일, 이 보고서뿐이다. `table_rows.py`(Protect)는 손대지 않았다. 새 의존성은 없다. 출력 형식과 기존 assert는 그대로다.

- **B1·B5 공용 텍스트 예산** `docx_extractor.TextBudget`(xlsx의 `_Budget`을 옮기고 이름을 바꿨다).
  - 상한은 `max(MIN_TEXT_BYTES = 8 MB, TEXT_RATIO = 2 × archive.bytes_read)`이다. UTF-8 바이트로 센다(`utf8_size`). `bytes_read`는 실제로 푼 바이트다. 그래서 xlsx처럼 시트를 나중에 읽으면 상한도 같이 커진다.
  - docx: `walk`가 문단 텍스트를 넣을 때 예산을 쓴다. `_table_lines`는 행을 하나씩 만든다. 머리글은 한 번만 낸다. 본문 행은 렌더링 **전에** 상한값 `머리글 바이트 + Σ(값 바이트 + 4)`만큼 예산을 쓰고, 그다음 `rows_to_lines(header, [row])`를 부른다. 이 방식의 출력은 표 전체를 한 번에 처리했을 때와 같다(행마다 독립적으로 렌더링된다).
  - xlsx: `_MAX_TEXT_BYTES`(64M자)와 `_Budget`를 없앴다. 셀 예산과 줄 예산이 각각 `TextBudget`이다. 정규화 전 검사는 `budget.check(len(raw))`로 한다(문자 수 ≤ UTF-8 바이트이므로 안전한 하한).
  - 기존 xlsx 테스트 3개는 monkeypatch 대상만 `_MAX_TEXT_BYTES`에서 `_cap_text`(`MIN_TEXT_BYTES = cap`, `TEXT_RATIO = 0`)로 바꿨다. assert는 그대로다. `_peak_of_rejected_extract`에는 메시지 단언(`text is too large`)을 **추가**했다. 다른 상한(비율)이 대신 걸려 통과하는 것을 막기 위해서다.
- **B2 + 정합성:** `_cell_text`는 셀의 직계 자식만 본다. `w:p`는 `_paragraph_text`로 한 번 처리한다. `w:sdt`·`w:sdtContent`·`w:ins`는 같은 함수로 재귀한다. 중첩 `w:tbl`은 행·셀 순서대로 평탄화해 공백으로 잇는다(종전 출력 순서와 같다).
  - 종전 `tc.iter(p)`는 셀 안 텍스트 상자(`w:txbxContent`)를 두 번 냈다. 바깥 문단 텍스트에 한 번, 안쪽 문단으로 또 한 번이다. 이 정합성 버그도 함께 고쳐졌다.
- **N1 깊이 상한:** `MAX_DEPTH = 100`이다. 깊이 하나를 `walk` → `_table_lines` → `_row_cells` → `_cell_text` → `_paragraph_text` → `_text`로 이어서 센다. 넘으면 `CORRUPTED_FILE: DOCX nesting is deeper than 100`이다. `RecursionError`는 더 나지 않는다.
- **B3:** `MAX_GRID_COLUMNS = 1,000`이다. `_widen`이 `gridBefore`·`gridSpan`·`gridAfter`를 더하기 전에 검사하고, 넘으면 `CORRUPTED_FILE`이다. 정확히 1,000열은 허용한다(테스트로 확인했다).
- **B4 (b) part별 압축률 상한:** `read_member`가 실제 해제 바이트를 본다. 1 MB를 넘고 `해제 / compress_size > MAX_PART_RATIO(100)`이면 **파싱 전에** `CORRUPTED_FILE: Part is compressed suspiciously well`이다. (a) iterparse는 하지 않았다(coordinator 결정).
  - 근거(review-r4 실측): 정상 xlsx 7.4 MB / 82.5 MB는 11배다. 공격 케이스는 480~500배였다. 실제 docx·xlsx는 보통 5~20배다. 이번 합성 테스트에서는 실무형 워크북 3.9배, 공격형 숫자 셀 시트 502배였다.
  - **알려진 위험:** 고정 템플릿을 반복한 문서는 정상이어도 100배를 넘을 수 있다. 실제로 review-r4의 합성 '300쪽' docx(16 KB zip / XML 3 MB, 약 190배)는 이제 거부된다. 실제 Word 문서에는 `rsid` 등 다양한 속성이 있어 이 정도로 압축되기 어렵다고 본다. 그래도 회사 문서 재측정(Phase 5)에서 `compressed suspiciously well` 오류가 나오는지 확인이 필요하다.
- **B6:** `_style_levels`가 스타일마다 한 번만 해석한다. 체인을 따라가다 이미 해석된 스타일을 만나면 멈추고, 지나온 체인 전체에 결과를 넣는다. 그래서 O(N)이다. 순환은 `on_chain`으로 끊는다(수준 없음).

### 실제 상한에서의 측정 (monkeypatch 없음, scratchpad 생성기, maxrss)
| 케이스(review-r4) | 파일 | 결과 | 시간 | maxrss |
|---|---|---|---|---|
| B1 머리글 4×100 KB + 5,000행 | 7 KB | `CORRUPTED_FILE` (압축률) | 0.0 s | 38 MB |
| B1 같음, 1,000행(part < 1 MB) | 2 KB | `CORRUPTED_FILE` (text too large) | 0.0 s | 49 MB |
| B2 `w:p` 500단계 중첩 + 1 MB | 1 KB | `CORRUPTED_FILE` (nesting) | 0.0 s | 38 MB |
| B2 90단계 중첩 + 750 KB, 본문 행 있음 | 1 KB | OK, 750,008자(한 번만) | 0.0 s | 47 MB |
| B3 gridSpan 200 × 100 / 행, 64 MB | 201 KB | `CORRUPTED_FILE` (압축률) | 0.0 s | 132 MB |
| B4 docx vMerge 64 MB | 184 KB | `CORRUPTED_FILE` (압축률) | 0.0 s | 152 MB |
| B4 xlsx 숫자 셀 60 MB | 114 KB | `CORRUPTED_FILE` (압축률) | 0.0 s | 149 MB |
| B5 이모지 1M자 × 63셀 | 5 KB | `CORRUPTED_FILE` (압축률) | 0.0 s | 43 MB |
| B5 `가` 300K자 × 63셀(part < 1 MB) | 2 KB | `CORRUPTED_FILE` (text too large) | 0.0 s | 38 MB |
| B6 순환 20,000 | 107 KB | OK | 0.0 s | 60 MB |

- 압축률 거부 케이스의 피크(130~150 MB)는 part 바이트(최대 64 MB)를 한 번 읽은 몫이다. 트리는 만들지 않는다.

### 새 테스트 (12개)
- **docx**
  - `test_long_header_repeated_on_many_rows_is_cut`: B1. 상한 8 MB, 피크 < 32 MB.
  - `test_paragraph_text_is_capped`: 문단 경로 예산.
  - `test_nested_paragraphs_in_a_cell_are_read_once`: B2. 90단계, 200 KB, 피크 < 32 MB, 단어 수가 정확히 1배.
  - `test_nested_table_and_text_box_text_is_not_duplicated`: 정상 중첩 표와 텍스트 상자의 출력 정합성.
  - `test_deep_nesting_is_corrupted_not_recursion_error`: N1. sdt 2,000단계, run 2,000단계, 셀 안 run, 중첩 표 300단계.
  - `test_row_wider_than_grid_cap_is_corrupted`: B3. 1,200열과 gridBefore는 거부, 1,000열은 허용.
  - `test_highly_compressed_document_part_is_refused_before_parsing`: B4.
  - `test_long_and_circular_based_on_chains_are_linear`: B6. 체인 20,000과 순환 20,000이 1 s 미만이고, 제목 수준이 상속된다.
  - `test_realistic_300_page_document_passes_the_caps`: 300블록(제목 1 + 문단 8 + 5×21 표), 다양한 단어 → 300섹션, 0.2 s.
- **xlsx**
  - `test_text_budget_counts_utf8_bytes_at_the_real_floor`: B5. 실제 8 MB 하한, UTF-8 바이트로 센다.
  - `test_highly_compressed_sheet_part_is_refused_before_parsing`: B4. 피크 < 4 × part.
  - `test_realistic_workbook_passes_the_caps`: 12열 × 5,000행 × 3시트, 0.9 s.
- samples/office 통합 테스트(`test_office_samples`)는 통과한다.

### 게이트
- `make lint` exit 0. 줄 길이 때문에 `make format`을 돌렸다. 바뀐 파일은 위 4개뿐이다(`find -newer review-r4.md`로 확인했다).
- `uv run --project backend pytest -q --junitxml=.ai/packets/2026-10-11-office-loaders/evidence/junit-fix4.xml` exit 0: tests=517 failures=0 errors=0 skipped=0 timestamp=2026-10-11T12:47:23.364851+09:00. fix3의 505건에 이번 12건이 더해졌고, 삭제된 테스트는 없다.

### 남은 것
- B4 (a) iterparse 스트리밍은 하지 않았다. 정상 대용량 시트(50,000행 → 753 MB)의 피크는 그대로다.
- 압축률 100배 상한이 실제 반복 템플릿 문서를 거부하는지는 Phase 5에서 확인해야 한다.
