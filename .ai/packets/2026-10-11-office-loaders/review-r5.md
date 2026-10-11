# Review R5 — 2026-10-11-office-loaders (fix4 최종 확인)

- Reviewer: Claude Opus 5.5 (read-only, r5)
- 대상: `review-r4.md` B1~B6·N1 ↔ `report-implementer.md` `## fix4`. working tree(base `origin/main` = `8ebf1fe`) + untracked
- 범위: r4 차단 항목이 실제로 막혔는지만 본다. 새로 찾은 증폭 경로는 '후속(이슈 후보)'에만 적고 판정에 넣지 않는다.
- **판정: APPROVE**
  - B1·B2·B3·B5·B6·N1은 r4 재현 파일을 실제 상한으로 돌렸을 때 모두 막혔다. 상한 바로 아래 변형으로도 확인했다.
  - B4는 r4 재현 4건이 모두 파싱 전에 거부된다. 다만 coordinator가 정한 (b) 압축률 상한만으로는 남는 몫이 있다. 압축률 98.9배 파일 653 KB가 1.7 GB를 쓴다(아래 3)). 이것은 (a) iterparse를 하지 않기로 한 결정의 알려진 잔여라서 차단에 넣지 않았다. coordinator가 판단할 몫이다.
  - 회귀는 없다. 정상 docx '300쪽 상당' 합성 문서가 압축률 상한(189배)에 걸려 거부된다. 이 사실은 fix4 report에 이미 적혀 있다.

## 재현 방법

- r4의 생성기·측정기(`gen.py`, `run.py`)를 이번 세션 scratchpad `r5/`로 복사해 그대로 썼다. 레포 밖이고 커밋 대상이 아니다.
- 추가 변형은 `r5/gen2.py`, `r5/gen3.py`, `r5/lie.py`로 만들었다. 무압축(STORED) 변형, 압축률 상한 바로 아래 변형, 헤더 위조 변형이다.
- 실행: `BACKEND=backend uv run --project backend python -I run.py <file> <type>`
  - `text_extractor.extract`를 그대로 부른다. **monkeypatch는 없다.** 실제 상한은 `MIN_TEXT_BYTES` 8 MB, `TEXT_RATIO` 2, `MAX_PART_RATIO` 100, `MAX_DEPTH` 100, `MAX_GRID_COLUMNS` 1,000이다.
  - maxrss는 `getrusage`로 잰다. import 후 기준선은 약 37 MB다. 워치독은 RSS 8 GB에서 죽인다.

## 1) r4 차단 항목 재실행 (실제 상한)

| 항목 | 케이스 | 파일 | 결과 | 시간 | maxrss | r4 |
|---|---|---|---|---|---|---|
| (r3) | 100 KB 공유 문자열 × 5,000셀 | 26 KB | `CORRUPTED_FILE` text too large | 0.0 s | 51 MB | 115 MB |
| (r3) | 100 KB 머리글 + 4,999행 | 65 KB | `CORRUPTED_FILE` text too large | 0.0 s | 50 MB | 112 MB |
| B1 | docx 머리글 4×100 KB + 200행 | 1 KB | `CORRUPTED_FILE` text too large | 0.0 s | 48 MB | OK, 278 MB |
| B1 | 같음, 1,000행 | 2 KB | `CORRUPTED_FILE` text too large | 0.0 s | 50 MB | OK, 1,267 MB |
| B1 | 같음, 5,000행 | 5 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 38 MB | OK, 5,999 MB |
| B1 | 같음, 5,000행, **STORED**(압축률 1배) | 1,382 KB | `CORRUPTED_FILE` text too large | 0.0 s | 59 MB | – |
| B2 | 셀 안 `w:p` 100단계 + 1 MB | 2 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 38 MB | 1,433 MB |
| B2 | 같음, 500단계 | 2 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 38 MB | 7,006 MB |
| B2 | 같음, 900단계 | 2 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 38 MB | KILLED |
| B2 | 90단계 + 1 MB, 머리글 + 본문 행, **STORED** | 1,025 KB | OK, 1,048,577자(**한 번만**) | 0.0 s | 53 MB | – |
| B2 | 같음, 95단계 | 1,025 KB | OK, 1,048,577자 | 0.0 s | 53 MB | – |
| B2 | 같음, 101단계 | 1,025 KB | `CORRUPTED_FILE` nesting > 100 | 0.0 s | 39 MB | – |
| B3 | gridSpan 200 × 100 / 행, XML 8 MB | 26 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 52 MB | 397 MB |
| B3 | 같음, 32 MB | 103 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 100 MB | 1,497 MB |
| B3 | 같음, 63 MB | 201 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 162 MB | (~3 GB 추정) |
| B3 | gridSpan 200 × 5 / 행(1,000열, 상한 안), **STORED** 8 MB | 8,192 KB | `EMPTY_DOCUMENT` | 0.8 s | 153 MB | – |
| B4 | xlsx 숫자 셀 16 MB | 34 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 68 MB | 461 MB |
| B4 | xlsx 숫자 셀 63 MB | 132 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 162 MB | 1,724 MB |
| B4 | xlsx sharedStrings 1자 항목 63 MB | 149 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 155 MB | 1,036 MB |
| B4 | docx `vMerge` 63 MB | 204 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 162 MB | 854 MB |
| B4 | 숫자 셀 63 MB, 중앙 디렉터리 `compress_size` 위조(2 MB) | 132 KB | `CORRUPTED_FILE` Overlapped entries | 0.0 s | 37 MB | – |
| B5 | 공유 문자열 1M자 × 63셀, ASCII | 2 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 38 MB | OK, 229 MB |
| B5 | 같음, 한글 `가` | 4 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 42 MB | OK, 423 MB |
| B5 | 같음, 이모지 | 5 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 44 MB | OK, 803 MB |
| B6 | basedOn 체인 5,000 | 26 KB | OK | 0.0 s | 41 MB | 0.5 s |
| B6 | 체인 20,000 | 102 KB | OK | 0.0 s | 58 MB | 9.7 s |
| B6 | 순환 20,000 | 102 KB | OK | 0.0 s | 58 MB | 21.3 s |
| N1 | 최상위 `w:sdt` 2,000단계 | <1 KB | `CORRUPTED_FILE` nesting > 100 | 0.0 s | 38 MB | `RecursionError` |
| N1 | 문단 안 `w:r` 2,000단계 | <1 KB | `CORRUPTED_FILE` nesting > 100 | 0.0 s | 37 MB | `RecursionError` |
| N1 | 같음, 100,000단계 | 2 KB | `CORRUPTED_FILE` 압축률 | 0.0 s | 38 MB | `RecursionError` |

- **B1 ✅** 압축률에 걸리는 5,000행 외에, 압축률을 피한 1,000행과 STORED 5,000행도 텍스트 예산(8 MB)에서 끊긴다. 코드: `_table_lines`가 행마다 렌더링 **전에** `머리글 바이트 + Σ(값 + 4)`를 쓴다(`docx_extractor.py:325-344`). `rows_to_lines`는 행마다 독립이라 출력은 같다(`table_rows.py:30-33`, 미수정).
- **B2 ✅** r4 재현은 압축률에 먼저 걸린다. 그래서 STORED 변형으로 증폭 자체를 따로 봤다. 깊이 90·95에서 1 MB 텍스트가 정확히 한 번만 나온다(r4 방식이면 90배). `_cell_text`가 직계 자식만 본다(`:264-284`).
- **B3 ✅** 상한 안(1,000열) 최대 폭 행으로 8 MB를 채워도 153 MB다(입력 8 MB 대비 약 19배, part 바이트·트리 몫 포함). 1,000열 초과는 `_widen`이 거부한다(`:297-300`).
- **B4 ✅(r4 재현 기준), 잔여 있음** — 아래 3)을 본다. 위조한 `compress_size`로 압축률 검사를 피하는 경로는 표준 라이브러리 `zipfile`의 overlapped-entry 검사가 막는다(마지막 항목에서도).
- **B5 ✅** r4 재현은 압축률에 걸린다. 텍스트 예산은 UTF-8 바이트로 센다(`utf8_size`). 예산 하한(8 MB)에서 끊기는 것은 B1 STORED, r3 두 케이스, fix4의 `test_text_budget_counts_utf8_bytes_at_the_real_floor`로 확인했다.
- **B6 ✅** 20,000 체인·순환 모두 0.0 s다. `_style_levels`가 스타일마다 한 번만 해석한다(`:200-217`).
- **N1 ✅** `RecursionError`가 더 나지 않는다. 모두 `CORRUPTED_FILE`이다.

## 2) 실무 크기 정상 문서

| 케이스 | 파일 | 큰 part 압축률 | 결과 | 시간 | maxrss |
|---|---|---|---|---|---|
| xlsx 12열 × 5,000행 × 3시트 | 753 KB | 10.7배 | **통과**, 3시트, 3,335,901자 | 0.4 s | 107 MB |
| xlsx 12열 × 50,000행 × 3시트 | 7.4 MB | 11.1배 | **통과**, 3시트, 33,508,707자 | 5.5 s | 753 MB |
| docx 50쪽 상당 | 3 KB | 169.9배(XML 0.5 MB < 1 MB라 검사 제외) | **통과**, 50섹션, 152,150자 | 0.0 s | 41 MB |
| docx 300쪽 상당 | 16 KB | **189.0배**(XML 3.15 MB) | **거부** `CORRUPTED_FILE: Part is compressed suspiciously well: word/document.xml` | 0.0 s | 42 MB |

- xlsx 두 케이스는 r4와 같은 결과·같은 메모리다. 텍스트 예산(`2 × 해제 바이트`)에도 걸리지 않는다.
- docx 300쪽 상당은 r4에서 통과(67 MB)했으나 이제 압축률 상한으로 거부된다. 이 합성 문서는 같은 문단·표를 그대로 반복해 실제 Word 문서보다 훨씬 잘 압축된다(실측 189배). fix4 report '알려진 위험'에 적혀 있고, 실제 문서 영향은 Phase 5에서 `compressed suspiciously well` 오류 건수로 확인하기로 했다. 그래서 회귀로 보지 않았다.
- fix4의 `test_realistic_300_page_document_passes_the_caps`는 단어를 다양하게 바꿔 압축률을 낮춘 문서라 통과한다. 위 합성 문서와는 다르다.

## 3) B4 잔여: 압축률 상한 바로 아래 (coordinator 판단 필요, 차단 아님)

| 케이스 | 파일 | part 압축률 | 결과 | 시간 | maxrss |
|---|---|---|---|---|---|
| xlsx 숫자 셀 63 MB, 60셀마다 난수 1개 | 653 KB | 98.9배 | **OK**, 27,240,006자 | 4.7 s | **1,718 MB** |
| docx `vMerge` 63 MB, 16셀마다 주석 난수 | 814 KB | 79.3배 | `EMPTY_DOCUMENT` | 2.1 s | **828 MB** |

- (b)는 입력 대비 압축률만 묶는다. 트리 비용(XML 1 B당 13~27 B)은 그대로라 1 MB 미만 입력이 GB 단위를 쓸 수 있다. r4 B4 원 재현(132 KB → 1,724 MB)과 피크가 같고, 필요한 입력만 약 5배 커졌다.
- r4 기준("입력 ~1 MB → 수백 MB 이상")으로는 여전히 해당한다. 하지만 이것은 (a) iterparse를 하지 않기로 한 coordinator 결정의 알려진 잔여다(fix4 report '남은 것'). 그래서 차단에 넣지 않았다.
- 선택지: (a) 스트리밍 파싱을 후속 이슈로 둔다. 또는 `MAX_PART_RATIO`를 낮춘다. 다만 정상 xlsx가 11배이므로 예컨대 30배로 낮춰도 3배 여유는 있지만 위 '300쪽' 같은 반복형 정상 문서는 더 많이 거부된다.

## 4) 후속(이슈 후보) — 판정 외

- **F1. docx 섹션 제목의 긴 제목 반복.** `extract_docx.title()`은 최근 제목 3개를 `" > "`로 이어 **섹션마다 새 문자열**로 만든다. 제목 텍스트는 예산에 한 번만 잡히고, 섹션 제목은 예산에 잡히지 않는다(`docx_extractor.py:362-368`, 제목 적재 `:384-387`).
  - 재현: `outlineLvl` 0·1·2 제목 각 *H* KB + (`outlineLvl` 3 제목 "h" + 본문 "y") × *N*. document.xml을 1 MB 미만으로 두면 압축률 검사도 받지 않는다.

    | H × 3, N | 파일 | 결과 | 시간 | maxrss |
    |---|---|---|---|---|
    | 300 KB × 3, 800 | 2 KB | **OK**, 800섹션 | 0.0 s | 518 MB |
    | 170 KB × 3, 3,400 | 3 KB | **OK**, 3,400섹션 | 0.1 s | **1,216 MB** |

  - 3 KB 파일이 1.2 GB를 쓰고 **성공**한다. 결과 섹션의 `section_title` 합계가 약 1.7 GB 문자다. 이 값은 청킹 단계에서 청크마다 복제될 수 있다.
  - 수정 방향 예: 제목 하나의 길이를 자른다(예: 200자). 또는 `title()` 결과를 예산에 넣는다. xlsx는 시트 이름이 각 줄의 `[name]` 접두어로 반복되지만 그 줄은 줄 예산에 들어가므로 해당하지 않는다.

## 5) 추가 확인

- **변경 범위 ✅** r4 작성(12:41:11) 이후 바뀐 파일은 여섯 개다(`find -newer review-r4.md`). 모두 fix4 Edit 범위 안이다.
  - `backend/app/services/docx_extractor.py`, `backend/app/services/xlsx_extractor.py`
  - `tests/unit/test_docx_extractor.py`, `tests/unit/test_xlsx_extractor.py`
  - `report-implementer.md`, `evidence/junit-fix4.xml`
  - `git diff --name-only origin/main`은 r4와 같은 10개다. `table_rows.py`는 바뀌지 않았다(Protect 유지).
- **기존 assert 완화 없음 ✅**
  - junit fix3(505) → fix4(517): 삭제 0, 추가 12(fix4 report 목록과 일치).
  - xlsx 기존 테스트 3개는 monkeypatch 대상만 `_cap_text`(`MIN_TEXT_BYTES = cap`, `TEXT_RATIO = 0`)로 바뀌었다. `TextBudget.remaining`이 실행 시 모듈 전역을 읽으므로 상한이 실제로 적용된다. assert는 그대로다(`< cap * 4`, `CORRUPTED_FILE`, 상한 250·3섹션). `_peak_of_rejected_extract`에는 `"text is too large"` 단언이 **추가**됐다(강화).
- **출력 형식 불변 ✅** `test_office_samples` 통과(섹션 제목 `2. 판독 절차 > 2.1 판독자 구성`, 시트 제목 `{촬영 일정, 메모}`, `page_number`, `DO-NOT-INDEX` 제외 단언 그대로).
- **테스트 재실행:** unit xlsx·docx·document_loader·text_extractor + integration `test_office_samples` = **57 passed**(r4의 45 + 12). `tests/unit` 전체 **505 passed**.
- **denylist ✅** `commit-denylist.txt` 7패턴, `grep -iEf`로 모두 0건이다.
  - `git diff origin/main`
  - untracked 텍스트 파일(samples 제외)
  - `.ai/packets/2026-10-11-office-loaders/` 전체(evidence 포함)
  - samples/office: docx·xlsx는 압축을 푼 XML, pdf는 raw 바이트
