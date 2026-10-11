# Review R3 — 2026-10-11-office-loaders (fix2 재리뷰)

- Reviewer: Claude Opus 5.5 (read-only, r3)
- 대상: `review-r2.md` R1′ ↔ `report-implementer.md` `## fix2`. working tree(base `origin/main` = `8ebf1fe`) + untracked
- **판정: REQUEST_CHANGES**
  - R1′(같은 part를 가리키는 시트 반복)은 고쳐졌다. 경로 정규화 우회도 찾지 못했다.
  - 하지만 fix2가 추가한 텍스트 총량 상한은 텍스트를 다 만든 **뒤에** 검사한다.
  - 그래서 공유 문자열(sharedStrings)을 반복 참조하는 시트 하나로 같은 종류의 증폭이 남는다. 12 KB 파일로 RSS 3 GB를 만들었고, 셀 수에 비례해 커진다(R4).

## 반려 항목

### R4. 텍스트 상한이 사후 검사라 메모리 증폭을 막지 못한다 — `xlsx_extractor.py:258-261`(검사), `:160-177` `_sheet_rows`, `:141` `strings[int(raw)]`
- **문제:**
  - 셀 `<c t="s"><v>0</v></c>`(약 25 B)는 공유 문자열 0번을 통째로 가져온다.
  - `_sheet_rows`는 셀마다 `" ".join(value.split())`로 **새 사본**을 만든다. 그 뒤 `_sheet_lines`, `"\n".join`, `normalize_text`가 사본을 몇 번 더 만든다.
  - `text_bytes > _MAX_TEXT_BYTES` 검사는 시트 하나의 텍스트를 이미 다 만든 뒤에야 돈다.
  - 그래서 결국 `CORRUPTED_FILE`로 끝나더라도, 그 전에 셀 수 × 문자열 크기만큼 메모리를 쓴다.
  - 해제 바이트 예산(`MAX_TOTAL_BYTES`)은 압축 해제한 XML만 센다. 참조로 늘어나는 텍스트는 세지 않는다.
- **재현(scratchpad 합성, `uv run --project backend python -I`):** 시트 1개, 공유 문자열 1개(100 KB), 그 문자열을 참조하는 셀 N개

  | 셀 수 | 파일 | 결과 | 시간 | maxrss |
  |---|---|---|---|---|
  | 2,000 | 6 KB | `CORRUPTED_FILE: XLSX text is too large to index` | 0.3 s | 1,247 MB |
  | 3,000 | 8 KB | 같음 | 0.5 s | 1,850 MB |
  | 5,000 | 12 KB | 같음 | 0.9 s | **3,056 MB** |

  - 셀당 약 0.6 MB로 선형 증가한다.
  - 상한 안에서 만들 수 있는 최대치: 시트 part는 64 MB까지 허용되므로 셀 약 2백만 개, 공유 문자열은 64 MB까지 가능하다. 이것만으로 OOM이 난다.
  - 결과가 오류로 끝나는 것 자체는 맞다. 문제는 거기까지 가는 동안 쓰는 메모리다.
- **방향:**
  - 상한을 **만드는 중에** 건다. `_sheet_rows`(또는 `_cell_value` 호출부)에 남은 예산을 넘긴다. 셀 값 길이를 누적하다가 `_MAX_TEXT_BYTES`를 넘는 순간 `CORRUPTED_FILE`로 끊는다.
  - 예산은 시트 사이에도 이어지게 한다. 지금 `text_bytes` 누적을 그쪽으로 옮기면 된다.
  - `h: v` 라벨링은 값 길이를 약 2배로 늘린다. 그러니 셀 값 누적 예산을 기준으로 삼거나, 상한에 여유 계수를 둔다.
  - 회귀 테스트 예: `_MAX_TEXT_BYTES`를 작게 monkeypatch한다. 공유 문자열 1개를 참조하는 셀을 많이 둔 시트 1개로 `CORRUPTED_FILE`이 나오는지 본다.
    - 가능하면 "상한을 넘은 셀 이후는 처리하지 않음"도 함께 단언한다. 예: `_cell_value` 호출 횟수, 또는 tracemalloc 피크가 상한의 몇 배 이내인지.
  - 기존 `test_total_section_text_is_capped`는 그대로 둬도 된다(완화 아님).

## 확인 결과

### 1) r2 재현 재실행 ✅ (R1′ 해소)
worksheet part 1개(2.0 MB XML, 텍스트 0.93 MB)와 그 part를 가리키는 `<sheet>` N개

| 시트 수 | 파일 | 결과 | 섹션 텍스트 | 시간 | maxrss |
|---|---|---|---|---|---|
| 200 | 111 KB | OK, **섹션 1개**, 진단 199건 | 0.93 MB | 0.0 s | 78 MB |
| 256 | 111 KB | OK, **섹션 1개**, 진단 255건 | 0.93 MB | 0.0 s | 78 MB |
| 257 | 111 KB | `CORRUPTED_FILE` (시트 상한) | – | 0.0 s | – |

- r2 수치는 200개 133 MB / 6.7 s, 256개 171 MB / 8.6 s였다. 이제 시트 수와 상관없이 섹션 1개다.
- 진단 형식: `sheet 'N2': duplicate part xl/worksheets/sheet1.xml, skipped`

### 2) 경로 정규화 우회 ✅ (찾지 못함)
- 기준 `worksheets/sheet1.xml`과 변형 1개를 쌍으로 넣어 각각 실행했다.
- **같은 part로 정규화돼 중복으로 건너뛴 것(6종):**
  - `/xl/worksheets/sheet1.xml`
  - `//xl/worksheets/sheet1.xml`
  - `../xl/worksheets/./sheet1.xml`
  - `./worksheets//sheet1.xml`
  - `worksheets/../worksheets/sheet1.xml`
  - `/xl/worksheets/sheet1.xml/.`
- **다른 이름으로 남아 `CORRUPTED_FILE: Missing part`로 거부된 것(6종):**
  - `Worksheets/Sheet1.xml`
  - `worksheets/SHEET1.XML`
  - `worksheets\sheet1.xml`
  - `…#x`
  - `…%2Exml`
- **우회가 안 되는 이유:**
  - 중복 판정 키, `read_member` 캐시 키, `ZipFile.getinfo` 조회 이름이 모두 같은 정규화 문자열이다.
  - `getinfo`는 대소문자를 구분하는 정확 일치다. macOS에서 `os.sep == "/"`이므로 `\`도 변환되지 않는다.
  - 그래서 키가 다르면 zip 안의 다른 member를 읽는다. 그 member는 압축을 따로 풀고 `bytes_read`(256 MB)에 따로 잡힌다.
  - 대소문자만 다른 member를 실제로 여러 개 넣는 것도 결국 이 해제 예산 안으로 묶인다.

### 3) 텍스트 총량 상한 ⚠️ → R4
- 동작: 시트마다 `normalize_text` 후 UTF-8 바이트를 누적한다. 누적이 `_MAX_TEXT_BYTES`(= `MAX_TOTAL_BYTES`, 256 MB)를 넘으면 `CORRUPTED_FILE`이다.
  - 위 재현에서 결과는 실제로 이 오류였다. 결과는 맞고 문제는 메모리 피크다(R4).
- 테스트 `test_total_section_text_is_capped`:
  - 상한을 250으로 monkeypatch한다. 3개 시트(각 약 101 B)는 기본 상한에서 3섹션 → 상한 250에서 `CORRUPTED_FILE`. 의도대로 검증한다.
  - 다만 시트 사이 누적만 다루고, 시트 하나 안의 증폭은 다루지 않는다.

### 4) 변경 범위와 테스트 의도 ✅
- r2 작성 시각(12:27:06) 이후 바뀐 파일은 셋뿐이다(diff 대상 + untracked의 mtime 기준). `make format`이 다른 파일을 건드리지 않았다.
  - `xlsx_extractor.py` 12:27:50
  - `test_xlsx_extractor.py` 12:28:50
  - `report-implementer.md` 12:29:45
- `git diff --name-only origin/main`은 r2와 같은 10개다.
- 테스트 이름 비교(`junit-fix1.xml` 502 → `junit-fix2.xml` 503):
  - `test_repeated_sheet_part_is_read_once_and_sheet_count_is_capped` → `…_is_one_section_and_…`으로 교체됐다. r2가 지시했고 fix1에서 새로 생긴 테스트다.
  - `test_total_section_text_is_capped`가 추가됐다.
  - 삭제된 테스트는 없다.
- 교체한 테스트는 오히려 강해졌다.
  - 캐시 단언(`bytes_read` 불변)과 257시트 → `CORRUPTED_FILE`은 그대로 남았다.
  - 단언이 섹션 `["N1"]`, 진단 49건, 첫 진단 문자열로 더 엄격해졌다.
- 다른 기존 assert는 완화되지 않았다.
- 단위 테스트 재실행(xlsx·docx·document_loader·text_extractor): **42 passed**

### 5) denylist ✅ 0건
- `~/clinical-rag-private/commit-denylist.txt`의 7패턴, `grep -iEf`로 검사했다.
  - `git diff origin/main` 0
  - untracked 텍스트 파일 0
  - `.ai/packets/2026-10-11-office-loaders/`(evidence 포함) 0
  - samples/office: docx·xlsx는 압축을 푼 XML, pdf는 raw 바이트로 검사했다. 둘 다 0

## 비차단
- N7(r2): 시트 하나의 64 MB 파싱 피크는 그대로다(follow-up, `iterparse`).
- 시트 대상 경로를 찾을 수 없으면 건너뛰지 않고 `CORRUPTED_FILE`로 끝난다(`read_member` 기본값 `required=True`). fix2 이전부터 그랬고, 실패를 숨기지 않는 쪽이라 유지해도 된다.

## 후속
- R4만 고치면 된다. 수정 범위는 `xlsx_extractor.py`와 테스트 1개다.
- r4에서는 위 공유 문자열 재현(5,000셀)을 다시 돌린다. maxrss가 상한의 작은 배수 이내인지, 오류가 나는지 확인한다.
