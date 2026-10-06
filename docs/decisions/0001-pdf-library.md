# ADR 0001. PDF 텍스트 추출 라이브러리: pypdf (런타임), PyMuPDF는 dev 전용

- 상태: 채택 (2026-10-07)
- 관련 코드: `backend/app/services/pdf_extractor.py`, `backend/pyproject.toml`

## 배경

MVP-1은 PyMuPDF(`pymupdf`)로 PDF를 읽었습니다. 공개 코퍼스(B5)를 넣으면서 PDF 7종(영문 4, 한국어 3)을 실제로 인덱싱해야 했고, 이 저장소는 공개 포트폴리오이자 폐쇄망 번들로 배포됩니다.

- PyMuPDF는 **AGPL-3.0**(또는 Artifex 상용 라이선스)입니다. api 이미지와 오프라인 번들에 넣어 배포하면 AGPL 조건(네트워크 서비스 소스 공개 포함)이 따라옵니다.
- pypdf는 **BSD-3-Clause**, 순수 Python이며 의존성이 없습니다.

## 측정 (2026-10-07, macOS arm64, pypdf 6.19.0 / PyMuPDF 1.28.2)

| 파일 | pypdf | PyMuPDF | 한글 음절 수 (pypdf / PyMuPDF) |
|---|---|---|---|
| 01 FDA (31p) | 0.2s | 0.1s | - |
| 02 ICH E6(R3) (86p) | 0.8s | 0.2s | - |
| 03 EMA Rev.6 (43p) | 0.8s | 0.2s | - |
| 04 식약처 항암제 (70p) | 1.1s | 0.1s | 49,675 / 49,675 |
| 05 식약처 ICH GCP (158p) | 2.1s | 0.3s | 47,335 / 47,335 |
| 06 식약처 AI 폐결절 (21p) | 0.5s | 0.0s | 16,294 / 16,294 |
| 10 MIDI 보고서 (138p) | 1.9s | 0.3s | - |

- 텍스트 품질: 두 라이브러리의 한글 음절 수가 같고, 영문 문자 수 차이는 0.1% 이내(공백·줄바꿈 차이)입니다.
- 속도: pypdf가 5~10배 느리지만 코퍼스 전체가 약 7.5초이고, 인덱싱 시간은 embedding(수 분)이 지배합니다. 추출은 `asyncio.to_thread`에서 돌기 때문에 이벤트 루프를 막지 않습니다.
- 차이점 1: 식약처 PDF는 아래아(U+119E `ᆞ`)를 가운뎃점으로 씁니다. 두 라이브러리 모두 그대로 내보내므로 `normalize_text`에서 `·`로 바꿉니다(NFC 정규화 포함).
- 차이점 2: pypdf 6.19는 Korea1 Unicode CMap(`/UniKS-UTF16-H`)을 모릅니다. PyMuPDF로 만든 toy PDF(비임베디드 `korea` 폰트)가 깨져 나왔습니다. 이 CMap은 문자 코드가 곧 UTF-16BE이므로(UniCNS/UniJIS-UTF16과 같은 방식) 시작 시 pypdf의 CMap 표에 등록합니다(`_register_korean_unicode_cmaps`). 비공개 API(`pypdf._cmap._predefined_cmap`)라서 pypdf 버전을 올릴 때 `test_pdf_korean_cid_font_is_decoded`가 회귀를 잡습니다.
- 차이점 3: AES 암호화 PDF는 pypdf에 `cryptography`가 있어야 열립니다. 추가하지 않고, 열지 못하면 `ENCRYPTED_PDF`로 보고합니다(이전과 같은 오류 코드).

## 결정

- 런타임(api 이미지, 오프라인 번들의 api)은 **pypdf**만 씁니다.
- PyMuPDF는 `dev` 의존성 그룹으로 옮겨, 테스트용 PDF 생성(`tests/unit/test_text_extractor.py`)과 toy PDF 생성기(`scripts/generate_sample_pdf.py`)에서만 씁니다. `Dockerfile`은 `--no-dev`로 설치하므로 api 이미지에 들어가지 않습니다.
- 페이지 머리말·꼬리말 제거, 목차 페이지 제거, 헤딩 인식은 라이브러리와 무관하게 `pdf_extractor`/`headings`에서 합니다(PyMuPDF의 폰트 크기 정보 같은 레이아웃 기능을 쓰지 않음).

## 결과와 한계

- 레이아웃 정보(폰트 크기·굵기)가 없으므로 헤딩은 번호 패턴(`I.`, `A.`, `4.2.1`, `Ⅳ.`, `1.1.1.`, `제3장`, `가.`)으로만 찾습니다. 번호 없는 굵은 소제목(FDA Appendix A의 "• Readers and their background qualifications." 등)은 섹션으로 나뉘지 않고, 이 경우 인용은 페이지 번호에 의존합니다.
- PDF 표는 구조 없이 텍스트로 나옵니다(예: 식약처 AI 가이드라인의 관찰항목 표). 구조가 있는 표는 JATS XML과 DICOM HTML에서만 행 단위로 처리합니다.
- 오프라인 번들의 `wheels/`(개발·테스트용, `--all-groups`)에는 여전히 PyMuPDF wheel이 들어갑니다. 테스트를 폐쇄망에서 돌릴 때만 필요하며 api 런타임에는 쓰지 않습니다.
