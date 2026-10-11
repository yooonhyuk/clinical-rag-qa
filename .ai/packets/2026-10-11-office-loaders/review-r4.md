# Review R4 — 2026-10-11-office-loaders (fix3 재리뷰 + 증폭 경로 일괄 점검, 최종)

- Reviewer: Claude Opus 5.5 (read-only, r4)
- 대상: `review-r3.md` R4 ↔ `report-implementer.md` `## fix3`. working tree(base `origin/main` = `8ebf1fe`) + untracked
- 이번 라운드의 기준(dispatch): 실무에서 나올 수 없는 입력이라도 **입력 ~1 MB가 메모리 수백 MB 이상**이 되면 차단 항목이다.
- **판정: REQUEST_CHANGES**
  - R4(공유 문자열 × 셀, 머리글 × 행)는 xlsx에서 고쳐졌다. 실제 상한(64M자, monkeypatch 없음)에서 피크 RSS 약 115~125 MB로 끝난다.
  - 하지만 일괄 점검에서 차단 항목 6건이 나왔다.
    - docx 3건: 표 머리글 × 행, 셀 안 중첩 문단, gridSpan.
    - 공통 1건: XML 트리 파싱 피크.
    - xlsx 1건: 상한 자체가 너무 크다.
    - docx 1건(CPU): 스타일 basedOn 처리가 제곱 시간이다.
  - 가장 심한 것은 docx다. docx에는 텍스트 상한이 아예 없다. 5 KB 파일이 RSS 6 GB와 20억 자 섹션을 만들고 **성공**한다.

## 재현 방법

- 합성 생성기와 측정기는 scratchpad에 있다(`r4/gen.py`, `r4/run.py`). 레포 밖이고 커밋 대상이 아니다.
- 실행: `uv run --project backend python -I run.py <file> <type>`
  - `app.services.text_extractor.extract`를 그대로 부른다. 상한 monkeypatch는 하지 않는다.
  - maxrss는 `getrusage`로 잰다. 기준선은 import 후 txt 1자 추출로 36 MB다.
  - 워치독이 RSS 8 GB를 넘으면 프로세스를 죽인다(KILLED). 측정 머신 메모리는 32 GB다.
- 아래 표의 "파일"은 zip 크기, "XML"은 압축 해제한 part 크기다.

## 1) r3 재현을 실제 상한으로 ✅ (R4 해소)

| 케이스 | 파일 | 결과 | 시간 | maxrss | tracemalloc 피크 |
|---|---|---|---|---|---|
| 100 KB 공유 문자열 × 5,000셀 | 26 KB | `CORRUPTED_FILE: XLSX text is too large to index` | 0.2 s | **115 MB** | 70 MB |
| 100 KB 머리글 셀 + 4,999행 | 65 KB | 같음 | 0.0 s | **112 MB** | 67 MB |

- r3에서는 같은 공유 문자열 케이스가 3,056 MB였다. 이제 상한(64M자) 근처에서 끊긴다.
- 코드 확인:
  - `_sheet_rows`가 정규화 사본을 만들기 **전에** 원본 길이로 남은 예산을 본다(`xlsx_extractor.py:178`).
  - `_sheet_lines`는 `_render_lines` 제너레이터에서 줄을 하나씩 받아 예산을 쓴다(`:195-200`).
  - 두 예산은 시트 사이에서도 이어진다(`:270-271`).
- 새 테스트 2개를 확인했다.
  - 상한을 8 MB로 낮추고, tracemalloc 피크가 32 MB 미만이며 `CORRUPTED_FILE`이 나는지 단언한다.
  - r3이 제안한 형태 그대로다.

## 2) 큰 머리글 × 많은 행 — xlsx ✅, docx ❌(B1)
- xlsx: 위 표와 같다. 끊긴다.
- docx: 상한이 없다. 아래 B1에 적었다.

## 3) 증폭 경로 일괄 점검

### 차단 항목

#### B1. docx 표 머리글 × 행: 텍스트 상한이 없다 — `docx_extractor.py:227-252` `_table_lines`, `:279-280` `buffer.extend`, 렌더링은 `table_rows.rows_to_lines`
- **문제:**
  - 머리글은 첫 행의 모든 칸이 비어 있지 않을 때만 정해진다. 그러면 본문 각 행이 `"h: v; ..."`로 렌더링된다.
  - 따라서 본문 한 줄은 최소한 머리글 전체 길이를 가진다.
  - docx 경로에는 xlsx의 `_Budget` 같은 상한이 없다.
- **재현:** 머리글 4칸(각 100 KB `"word "` 반복) + 본문 `v` 4칸 × N행

  | N | 파일 | 결과 | 시간 | maxrss |
  |---|---|---|---|---|
  | 200 | 1 KB | **OK**, 81,922,999자 | 0.1 s | 278 MB |
  | 1,000 | 2 KB | **OK**, 409,614,999자 | 0.3 s | 1,267 MB |
  | 5,000 | 5 KB | **OK**, 2,048,074,999자 | 1.4 s | **5,999 MB** |

  - 행 수에 선형으로 커진다.
  - `document.xml`은 64 MB까지 허용된다. 그 안에 행 약 30만 개를 넣을 수 있으니 OOM이 확실하다.
  - 오류로 끝나지도 않는다. 20억 자 섹션이 청킹·임베딩 단계로 넘어간다.

#### B2. docx 셀 안 중첩 문단: 깊이 × 텍스트 — `docx_extractor.py:213-215` `_cell_text`, `:178-190` `_text`
- **문제:**
  - `_cell_text`는 `tc.iter(W:p)`로 **모든 자손** 문단을 돈다.
  - 그런데 각 문단의 `_paragraph_text`(`_text`의 재귀)는 다시 그 아래 자손 텍스트를 다 모은다.
  - 그래서 `<w:p>`가 d단계로 중첩되면(실무에서는 `w:txbxContent` 같은 경로로 생김) 맨 아래 텍스트가 d번 복사된다.
  - 복사할 때마다 `split()`이 단어 리스트를 새로 만든다.
- **재현:** 셀 1개, `<w:p>`를 d단계 중첩, 맨 아래에 1 MB 텍스트

  | d | 파일 | 결과 | 시간 | maxrss |
  |---|---|---|---|---|
  | 100 | 2 KB | `EMPTY_DOCUMENT` | 0.7 s | 1,433 MB |
  | 500 | 2 KB | `EMPTY_DOCUMENT` | 3.7 s | **7,006 MB** |
  | 900 | 2 KB | **KILLED** (RSS ≥ 10.3 GB, 5 s) | – | – |

  - 결과가 `EMPTY_DOCUMENT`인 이유: 행이 하나뿐이라 머리글로 소비됐다. 본문 행을 하나 더 두면 출력 텍스트도 d배가 된다.
- **본문(body) 수준에서는 증폭이 없다.** `walk`가 최상위 `w:p`만 보고, 그 문단 텍스트는 한 번만 만든다.

#### B3. docx `gridSpan`: 셀 하나(약 55 B)가 리스트 칸 200개 — `docx_extractor.py:235-245`
- **문제:**
  - `gridSpan`은 200으로 잘리지만, 셀마다 `[""] * 199`가 늘어난다.
  - 행 길이에는 상한이 없다(`gridBefore`/`gridAfter`도 각각 200까지).
  - 머리글이 없어도 `_clean`과 `rows_to_lines`가 행 리스트 사본을 또 만든다.
- **재현:** `<w:tc><w:tcPr><w:gridSpan w:val="200"/></w:tcPr></w:tc>` × 100 / 행

  | XML | 파일 | 결과 | 시간 | maxrss |
  |---|---|---|---|---|
  | 8 MB | 26 KB | `EMPTY_DOCUMENT` | 0.8 s | 397 MB |
  | 32 MB | 103 KB | `EMPTY_DOCUMENT` | 3.2 s | **1,497 MB** |

  - 64 MB면 약 3 GB로 추정한다.
  - 같은 크기의 `vMerge` 케이스(32 MB, 104 KB 파일)는 451 MB였다. 이 값은 아래 B4의 파싱 기준선이다. 차이인 약 1 GB가 gridSpan 리스트 몫이다.
- `vMerge` 자체는 셀당 `""` 하나라서 증폭이 없다(B4 기준선만 남는다).

#### B4. XML 전체 트리 파싱 피크(xlsx·docx 공통) — `docx_extractor.py:121-132` `parse_xml`; 상한 `MAX_MEMBER_BYTES` 64 MB / `MAX_TOTAL_BYTES` 256 MB
- **문제:**
  - `ET.XMLParser`가 part 전체를 트리로 만든다. 작은 원소가 많으면 XML 1바이트당 약 13~27 B를 쓴다.
  - 해제 상한은 **파일 크기와 상관없이** 64 MB/part다.
  - 그래서 반복이 심한 XML은 100~200 KB zip으로 1 GB를 넘긴다.
  - r2·r3에서는 N7(비차단, follow-up)로 뒀다. 이번 기준(입력 1 MB → 수백 MB = 차단)으로 올린다.
- **재현:**

  | 케이스 | XML | 파일 | 결과 | 시간 | maxrss |
  |---|---|---|---|---|---|
  | xlsx 숫자 셀 `<c><v>1</v></c>` | 16 MB | 34 KB | OK, 6.7M자 | 0.9 s | 461 MB |
  | 같음 | 63 MB | 132 KB | **OK**, 26.4M자 | 4.0 s | **1,724 MB** |
  | xlsx sharedStrings 1자 항목 | 63 MB | 149 KB | OK | 1.8 s | **1,036 MB** |
  | docx `vMerge` 셀 | 63 MB | 204 KB | `EMPTY_DOCUMENT` | 2.3 s | **854 MB** |

  - 정상 문서에서도 같은 비율이 나온다. 아래 4)의 xlsx 50,000행 × 3시트(7.4 MB, XML 82.5 MB)가 753 MB였다.

#### B5. xlsx 텍스트 상한(64M**자**)이 입력 크기에 비해 너무 크다 — `xlsx_extractor.py:50` `_MAX_TEXT_BYTES`
- **문제:**
  - 상한을 넘지 않으면 작은 파일이 상한 근처 크기의 섹션을 만들고 **성공**한다.
  - 상한은 문자 수로 센다. 그런데 CPython 문자열은 문자 하나에 1/2/4 B를 쓴다. 그래서 같은 상한에서도 메모리가 4배까지 달라진다.
  - 피크는 행 사본, 줄, `"\n".join`, `translate`가 겹친 값이다.
- **재현:** 공유 문자열 1개(1,048,576자) × 셀 63개(상한 바로 아래)

  | 문자 | 파일 | 결과 | 시간 | maxrss |
  |---|---|---|---|---|
  | ASCII `a` | 2 KB | **OK**, 66,060,665자 | 0.1 s | 229 MB |
  | 한글 `가` | 4 KB | **OK**, 같음 | 2.5 s | 423 MB |
  | 이모지 U+1F600 | 5 KB | **OK**, 같음 | 2.8 s | **803 MB** |

  - 5 KB 파일이 섹션 1개(Python 메모리 264 MB)를 만든다. 이 섹션은 청킹·임베딩 단계로 그대로 넘어간다.

#### B6. docx 스타일 `basedOn` 처리가 제곱 시간(CPU) — `docx_extractor.py:161-169`
- **문제:**
  - 순환은 `seen`으로 막혀서 무한 루프는 없다. 깊이 제한도 없지만 메모리는 O(N)이다.
  - 그러나 스타일마다 체인을 처음부터 다시 따라가서 O(N²)이다.
- **재현:** `s0→s1→…→sN`(끝은 `heading 1`) 체인, 그리고 N개짜리 순환

  | 케이스 | 파일 | 시간 | maxrss |
  |---|---|---|---|
  | 체인 5,000 | 26 KB | 0.5 s | 40 MB |
  | 체인 20,000 | 102 KB | **9.7 s** | 56 MB |
  | 순환 20,000 | 102 KB | **21.3 s** | 58 MB |

  - 4배 입력에 약 20배 시간이 걸린다(제곱).
  - `styles.xml`은 64 MB까지 허용된다(스타일 약 80만 개). 이를 외삽하면 수 시간이다.
  - 메모리 기준은 아니지만 같은 종류의 증폭(입력 100 KB → 분 단위 CPU)이라 함께 막는다.

### 비차단

- **N1. 깊은 중첩에서 타입 없는 `RecursionError`가 난다.**
  - 재현: 최상위 `w:sdt/w:sdtContent` 2,000단계 중첩(`walk`), 문단 안 `w:r` 2,000단계와 100,000단계 중첩(`_text`). 모두 1 KB 미만 파일이다.
  - 결과는 `RecursionError`이고 0.0 s, 66 MB 이하로 끝난다. 메모리 문제는 없다.
  - 파이프라인에서는 `_classify`가 이를 `UNEXPECTED_ERROR`로 남긴다(`indexing_pipeline.py:251`).
  - 다른 손상 입력과 같은 `CORRUPTED_FILE`로 타입을 붙이면 좋다. B2를 고칠 때 깊이를 제한하면 함께 해결된다.
- **증폭이 없음을 확인한 경로:**
  - numbering: `numbering.xml`을 읽지 않는다. 그래서 증폭 경로가 없다.
  - xlsx 숫자·날짜 서식: 날짜 문자열은 최대 16자다. 셀 XML은 15 B 이상이다. 비율이 1 미만이다.
  - 시트 수: 256개 상한, 중복 part 건너뛰기, 시트 사이로 이어지는 예산이 있다. 해제 예산(256 MB)도 있다. r3 결과를 유지한다.
  - xlsx `vMerge`/병합 셀: xlsx는 병합 셀을 펼치지 않는다. 그래서 해당 경로가 없다.

## 4) 실무 크기 정상 문서 ✅ (상한에 걸리지 않는다)

| 케이스 | 파일 | XML | 결과 | 시간 | maxrss |
|---|---|---|---|---|---|
| xlsx 12열 × 5,000행 × 3시트 | 753 KB | – | OK, 3시트, 3.3M자 | 0.4 s | 107 MB |
| xlsx 12열 × 50,000행 × 3시트 | 7.4 MB | 82.5 MB | OK, 3시트, 33.5M자 | 5.3 s | 753 MB |
| docx 50쪽 상당 | 3 KB | – | OK, 50섹션 | 0.0 s | 41 MB |
| docx 300쪽 상당 | 16 KB | 3 MB | OK, 300섹션 | 0.1 s | 67 MB |

- xlsx 행 구성: inline·shared 문자열, 날짜(`numFmtId` 14), bool, 소수, 한글 자유 서술이 섞여 있다.
  - 예시 줄: `[S0] SubjectID: SUBJ-00003; Visit: 3; Date: 2023-03-18; …; Comment: 자유 서술 코멘트 …`
- docx 쪽 구성: `outlineLvl` 제목 1개, 본문 문단 8개, 5열 × 21행 표 1개.
- 이 형태의 행으로 현재 64M자 상한에 닿으려면 약 29만 행이 필요하다. 그 전에 시트 part 64 MB 상한(시트당 약 12만 행)에 먼저 닿는다.
- **수정 방향 B5·B4를 정할 때 주의:** 15만 행 워크북이 33.5M자다. 그래서 고정 상한을 16M자로 낮추면 이 정상 워크북이 거부된다. 아래 방향처럼 **해제 바이트 대비 비율**로 상한을 두기를 권한다.

## 5) 변경 범위·테스트 의도·denylist ✅

- **변경 범위:** r3 작성(12:32:19) 이후 바뀐 파일은 넷뿐이다(`find -newer`). Edit 범위 안이다.
  - `xlsx_extractor.py`
  - `test_xlsx_extractor.py`
  - `report-implementer.md`
  - `evidence/junit-fix3.xml`
- `git diff --name-only origin/main`은 r3과 같은 10개다.
- **테스트 의도:** junit fix2(503건) → fix3(505건) 비교에서 삭제된 테스트는 0이다. 추가된 테스트는 아래 2개다.
  - `test_shared_string_amplification_is_cut_while_building`
  - `test_repeated_large_header_is_cut_while_rendering`
- `test_total_section_text_is_capped`는 그대로다(상한 250, 3섹션 → `CORRUPTED_FILE`). 다른 assert도 완화되지 않았다.
- 재실행 결과: unit xlsx·docx·document_loader·text_extractor와 integration `test_office_samples`가 **45 passed**다.
- **denylist:** `commit-denylist.txt` 7패턴으로 검사했다(`grep -iEf`). 모두 0건이다.
  - `git diff origin/main`
  - untracked 텍스트 파일
  - `.ai/packets/2026-10-11-office-loaders/` 전체
  - samples/office: docx 1개·xlsx 1개는 압축을 푼 XML, pdf는 raw 바이트로 검사했다.

## 수정 방향 (한 번에 닫기 위한 제안)

모두 docx_extractor·xlsx_extractor와 그 테스트 안에서 할 수 있다. `table_rows.py`는 HTML과 공용이고 Protect 대상이다. 손대야 하면 먼저 `ask`로 묻는다.

1. **공용 텍스트 예산을 두고 docx에도 적용한다** (B1·B2·B5)
   - `_Budget`을 `docx_extractor.py`의 OOXML 헬퍼 쪽으로 옮긴다. xlsx는 이미 그 모듈에서 import한다.
   - 상한은 고정값과 비율 중 큰 쪽으로 정한다: `max(고정 하한 예: 8M자, k × archive.bytes_read)`, k는 예: 2.
   - 정상 xlsx의 텍스트/XML 비율은 0.4였다(33.5M자 / 82.5 MB). 증폭 케이스는 수백~수만 배다.
   - 바이트 단위로 셀 거면 `len(s)` 대신 최악 4 B/자를 가정하거나 UTF-8 길이로 센다.
   - docx는 `walk`에서 문단 텍스트를 넣을 때 쓴다. 표는 `_table_lines`가 행 하나씩 렌더링하면서 쓴다(예: 머리글을 정한 뒤 `rows_to_lines(header, [row])`를 행마다 부르고 예산을 쓴다).
2. **B2:** `_cell_text`에서 `tc.iter(p)` 대신 셀의 직계 자식만 본다(`w:p`, `w:sdt`, 중첩 `w:tbl`은 명시적으로 처리한다). 같은 텍스트를 두 번 모으지 않게 한다.
   - 재귀(`_text`, `walk`)에는 깊이 상한(예: 64~200)을 두고 넘으면 `CORRUPTED_FILE`로 끊는다(N1 함께 해결).
3. **B3:** 행 전체 grid 폭에 상한을 둔다. Word 표는 최대 63열이다. 넉넉히 예: 1,000으로 두고, 넘으면 `CORRUPTED_FILE`로 끊거나 그 행을 잘라낸다.
4. **B4:** 둘 중 하나, 또는 둘 다.
   - (a) 큰 part(`sheetN.xml`, `sharedStrings.xml`, `document.xml`)를 `iterparse` + `elem.clear()`로 스트리밍한다.
   - (b) part별 압축률 상한을 둔다. 예: 해제가 1 MB를 넘고 `해제 바이트 / compress_size > 100`이면 거부한다.
     - 실측 압축률: 정상 xlsx 11배, 공격 케이스 480~500배.
     - 실제 docx·xlsx는 보통 5~20배다. 그래도 고정 반복 템플릿 문서가 거부될 수 있으니 이 값을 근거와 함께 report에 남긴다.
   - (b)는 작고 바로 할 수 있다. (a)는 정상 대용량 시트(50,000행 → 753 MB)의 피크도 낮춘다.
5. **B6:** 레벨을 메모이제이션한다. 해석한 결과를 `levels`에 넣고, 체인을 따라가다 이미 해석된 스타일을 만나면 멈춘다. 그러면 O(N)이다.
6. **회귀 테스트:** 위 재현마다 하나씩 둔다. 상한을 작게 monkeypatch하고 tracemalloc 피크 < 상한 × 4와 `CORRUPTED_FILE`을 단언한다(fix3 패턴). B6은 체인 2만에서 1 s 미만을 단언한다.
