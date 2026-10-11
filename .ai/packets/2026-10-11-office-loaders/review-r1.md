# Review R1 — 2026-10-11-office-loaders

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: working tree diff (base `origin/main` = HEAD = `8ebf1fe`) + untracked 파일. Phase 5는 리뷰하지 않았다.
- **판정: REQUEST_CHANGES** (R1~R3. 셋 다 packet 완료 조건 "XML 파싱 안전 / zip 폭탄 상한"에 걸린다.
  기능·범위·의존성·문서는 통과)

## 반려 항목

### R1. 압축 해제 총량 상한이 실제로 읽는 양을 막지 못한다 — `xlsx_extractor.py:219-225`, `docx_extractor.py:61-64`
- **문제:** `MAX_TOTAL_BYTES`는 open 시점에 zip 헤더 `file_size`의 합만 본다. xlsx는 `<sheet>`마다 `read_member`를 부르는데,
  여러 `<sheet>`가 같은 rId·같은 part를 가리키면 같은 part를 몇 번이든 다시 풀고 다시 파싱한다. 시트 수에도 상한이 없다.
- **재현(scratchpad 합성 파일):** 154 KB xlsx. 시트 200개가 1.47 MB part 하나를 가리킨다.
  → 압축을 실제로 푼 양은 약 293 MB, 섹션 텍스트는 51.6 MB, 10초가 걸렸다.
  시트 수와 part 크기(최대 64 MB)를 늘리면 256 MB 상한과 상관없이 계속 커진다.
- **방향:** archive 단위로 실제로 읽은 바이트를 누적해 `MAX_TOTAL_BYTES`를 넘으면 `CORRUPTED_FILE`로 끊는다
  (`read_member`에 카운터를 두거나 같은 part는 한 번만 읽는다). 시트 수 상한도 둔다. 둘 다 회귀 테스트를 붙인다.

### R2. 희소한 먼 열 하나가 메모리를 크게 부풀린다 — `xlsx_extractor.py:158, 165-166`
- **문제:** 행마다 `range(max(cells)+1)`로 리스트를 만들고, `_sheet_lines`가 모든 행을 시트 최대 폭까지 채운다.
  셀 하나가 `XFD`(16,384열)에 있으면 모든 행이 16,384칸이 된다.
- **재현:** 11 KB xlsx(A열 2,000행 + `XFD2001` 셀 1개) → tracemalloc 최대 **536 MB**, 5.4초.
  행 수가 늘면 그대로 비례한다(64 MB 시트 = 수십만 행이면 OOM). 실무 xlsx에도 먼 열에 값이 남는 일이 흔하다.
- **방향:** 행을 dict(열→값)로 두고 실제 값이 있는 열만으로 렌더링한다. 또는 헤더 폭을 기준으로 맞추고 폭에
  상한(예: 마지막으로 값이 있는 열)을 둔다. 지금 출력 형식은 유지한다. "먼 열 1셀" 회귀 테스트를 붙인다.

### R3. DTD/ENTITY 거부를 UTF-16 인코딩으로 우회할 수 있다 — `docx_extractor.py:87-94`
- **문제:** `<!DOCTYPE`/`<!ENTITY` 검사가 바이트 문자열을 비교한다. UTF-16 XML(expat이 지원)에서는 이 바이트가
  나타나지 않는다.
- **재현:** `encoding="UTF-16"`인 `word/document.xml`에 `<!ENTITY a "PWN">`을 넣으면 거부되지 않는다.
  추출 결과가 `['PWN']`이다(내부 엔티티 전개).
  외부 엔티티는 ElementTree가 원래 가져오지 않고, 이 환경의 expat 2.6.3은 billion-laughs 증폭 방어가 있다.
  그래서 실제 피해는 낮다. 다만 docstring과 README가 약속한 "no DTD/entities"는 사실이 아니다.
- **방향:** 바이트 검사 대신 파서 수준에서 막는다. 예: `ET.XMLParser()`를 만들고
  `parser.parser.StartDoctypeDeclHandler`(또는 `EntityDeclHandler`)에서 예외를 던져 `CORRUPTED_FILE`로 바꾼다.
  UTF-16 DTD 회귀 테스트를 추가한다.

## 비차단 (같이 고치면 좋음)
- N1. `xlsx_extractor.py:85,130`: `int(xf.get("numFmtId"))`, `int(c.get("s"))`, `int(n.get("numFmtId"))`가 숫자가 아니면
  `ValueError`가 잡히지 않는다. 그러면 파이프라인에서 `UNEXPECTED_ERROR`가 된다(재현됨). `CORRUPTED_FILE`이나 기본값으로 처리하면 일관된다.
- N2. `_is_date_format("[h]:mm:ss")`가 True다. 대괄호를 지운 뒤 `mm`이 남기 때문이다. 경과 시간 ≥1일이면 `1900-01-01 12:00`처럼
  날짜로 바뀐다. 드문 경우라 follow-up으로 둬도 된다.
- N3. docx의 `basedOn` 상속 제목 스타일(사용자 스타일 ← Heading 1)과 `w:gridBefore`(행 앞 빈 칸)는 처리하지 않는다.
  폭이 다른 행은 `a | b` 형식으로 떨어지므로 데이터는 잃지 않는다. 회사 문서 재측정(Phase 5)에서 일치도가 낮으면 확인할 후보다.
- N4. OLE 매직이 있으면 모두 `ENCRYPTED_FILE`이다. `.doc`의 확장자만 `.docx`로 바꾼 파일도 "암호"로 보고된다.
  OneDrive 폴더에 흔한 `~$*.docx` 잠금 파일은 `CORRUPTED_FILE`이 된다. Phase 5에서 실패 유형을 셀 때 이 점을 감안한다.
- N5. 숨김 시트 진단(packet 8)은 `extract_xlsx_with_diagnostics()`의 반환값과 로그에만 남는다. DB와 job details에는 실리지 않는다
  (pipeline은 Read 범위다). coordinator가 이걸로 충분한지 정한다.
- N6. **(coordinator 몫)** `packet.md`가 denylist 패턴 #6·#7에 3건 걸린다(회사 문서 경로 표기). Implementer 산출물에는
  걸리는 것이 없다. packet을 커밋할 거면 해당 경로 표기를 먼저 일반화한다.

## 체크리스트 결과

1. **scope.md 위반 검출**
   - (1)(2) diff 파일 10개와 untracked 파일이 모두 Edit 목록 안이다.
   - 상시 Protect 해당: `pyproject.toml`/`uv.lock`(packet에서 승인), ADR 0001(기존 결정은 그대로 두고 "추가" 절만 붙임).
   - `document_types.py`는 바뀌지 않았다.
   - (3) assert 완화는 없다(아래 2).
   - (4) denylist 검사: `git diff origin/main` + untracked 텍스트 파일 + docx/xlsx 압축을 푼 XML + PDF 바이트 → Implementer 산출물 0건. packet만 걸린다(N6).
   - (5) 새 HTTP 클라이언트나 LLM SDK는 없다. `anthropic`은 원래 있던 의존성이다.
   - (6) 샘플 3개는 "가상 샘플"·"DEMO-ONC-01"·"fictional"로 표시된 합성 문서다. 원문·개인정보 없음.
2. **Edit 밖 변경**
   - 기존 테스트 3곳에서 `.docx`를 `.pptx`로 바꿨다.
   - assert의 대상(미지원 확장자 → `supported=False` / `UNSUPPORTED_FILE_TYPE`)과 강도가 같다. `.docx`가 지원 형식이 됐으니 바꾸는 게 맞다.
   - `test_pipeline_db.py`도 같은 치환만 했다. 약화 없음.
3. **의존성:** `uv.lock`에 `+`만 있고 `-`는 없다. 새 패키지는 cryptography 50.0.2, cffi 2.1.1, pycparser 3.11 셋뿐이다.
   pyproject에는 `cryptography>=50.0.2` 한 줄만 추가됐다.
4. **보안**
   - 표준 `xml.etree.ElementTree`만 쓴다. 외부 엔티티는 가져오지 않는다.
   - DOCTYPE 거부는 UTF-8에서만 동작한다 → R3.
   - 항목 수 5,000, 단일 part 64 MB(실제 읽은 양으로 재확인), 헤더 합계 256 MB가 있다. 반복 읽기와 메모리 증폭은 막지 못한다 → R1, R2.
   - 경로: zip 멤버 이름은 zip 안에서만 찾는다. 파일시스템에 쓰거나 풀지 않는다. 경로 탐색 위험은 없다.
5. **동작과 테스트 커버리지**
   - docx 제목 경로(영문·한글·outlineLvl): ✅ test
   - gridSpan·vMerge: ✅ test
   - w:del 제외 / w:ins 포함: ✅ test
   - 머리말·각주 제외: ✅. 애초에 `document.xml`만 읽는다. test와 integration이 있지만 구조상 항상 참이다.
   - 첫 행 머리글 규칙: ✅ test
   - xlsx 공유·인라인 문자열, 수식 캐시값, 기본·사용자 날짜 서식, 머리글 탐지와 그 위 행, 시트 섹션: ✅ test
   - 숨김 시트: ✅ test
   - 1904 체계: 구현만 있고 테스트 없음(경미).
   - 암호 docx/xlsx(OLE) → `ENCRYPTED_FILE`: ✅ test(매직 바이트 합성)
   - 열기 암호 PDF → `ENCRYPTED_PDF`: ✅ 기존 `test_encrypted_pdf_fails`(AES-256, user_pw). 이제 cryptography가 있으므로 `FileNotDecryptedError` 경로를 실제로 탄다.
   - 권한 암호만 있는 AES PDF가 열림: ✅ unit test와 sample. sample은 pypdf로 `/V 4 /R 4`(AES-128)임을 확인했다.
   - `.doc` 안내: ✅ test
   - 샘플 3개 실제 추출 결과를 눈으로 확인: 제목 경로, 병합 셀, "5영업일"(7일 제외), ISO 날짜, 수식값 -2/2, 숨김 시트 "메모"가 모두 맞다.
   - `tests/unit`을 다시 돌렸다: **479 passed**(53s). 전체·integration 게이트는 Tester 몫이다.
6. **기존 경로**
   - PDF/MD/JATS/HTML 코드는 바뀌지 않았다. `pdf_extractor`는 주석만 바뀌었다. 동작 변화는 의도한 AES PDF 열림뿐이다.
   - `samples/documents`와 `corpus/public`에는 `/Encrypt` PDF도 Office 파일도 없다. 기존 색인과 평가 수치는 그대로다.
   - `samples/documents`는 git status 기준 변경 없음.
7. **문서**
   - README 지원 형식과 Office 문단은 구현과 맞다(R3를 고치면 그대로 사실이 된다).
   - ADR 0001 추가 절의 테스트 이름과 sample 경로는 실제로 있다. 측정 수치를 주장하지 않는다.
   - "번들 스크립트는 바꾸지 않는다"는 `build-bundle.sh`가 `uv export --frozen`으로 lock을 쓰는 것과 맞다. 다만 번들 재빌드는 하지 않았다.
     이것은 측정이 아니라 메커니즘 서술이라 괜찮다. 원하면 "번들 재빌드 측정 안 함"을 한 줄 덧붙이길 권장한다.
   - 위쪽 "차이점 3"(추가하지 않는다)은 추가 절과 반대된다. 이 점은 추가 절이 설명하고 있다. 원하면 차이점 3 끝에 "→ 2026-10-11 추가 절" 포인터를 단다.

## 후속 제안
- R1~R3를 고친 뒤 R2(Reviewer) 재리뷰 범위: `docx_extractor.py`의 OOXML 헬퍼, `xlsx_extractor.py`, 새 회귀 테스트 3개.
