# 013. 스폰서 PDF 추출: 기호 손실로 숫자가 바뀌고, 가로 회전된 일정표는 행 구조를 잃음

- 상태: 열림 (NUL 바이트로 인한 인덱싱 실패는 수정함)
- GitHub: https://github.com/yooonhyuk/clinical-rag-qa/issues/14
- 발견: 2026-10-09, 실제 프로토콜 코퍼스(로컬 전용 31개 PDF, 20~238쪽) 인덱싱·평가
- 영향 범위: `backend/app/services/pdf_extractor.py`(pypdf), 수치가 들어간 답변, Schedule of Assessments 질문
- 관련: [ADR 0001](../decisions/0001-pdf-library.md)(pypdf, 레이아웃 정보 없음)

## 증상

1. **기호가 사라지거나 다른 글자로 바뀜** (pypdf `extract_text`, 폰트 인코딩 문제)
   - RECIST 1.1 원문(저널 PDF): `≥`가 `P`로 추출됩니다("short axis of P15 mm"). 생성 모델은 이를 그대로 옮겨 "단축이 P15 mm 이상"이라고 답했고, 키워드 채점(`15`)은 정답으로 셌습니다.
   - 림프종 시험 프로토콜: 범위의 en dash가 사라져 "6–8 weeks"가 "68 weeks"로 추출됩니다. 1차 평가변수 시점이 10배 이상 다른 숫자가 됩니다.
   - 호지킨 림프종 SAP: "Deauville score of ≥ 3"에서 `≥`가 공백이 되어 "Deauville score of 3"으로 읽힙니다.
   - QIBA FDG-PET 프로파일(줄 번호가 있는 초안 형식): 줄 번호가 본문 끝에 붙어 "Profile Details189", "(typically 60 min)201"처럼 숫자가 섞입니다.
2. **NUL 바이트로 인덱싱 실패**: 한 SAP(105쪽)의 텍스트 레이어에 `\x00`이 있어 PostgreSQL이 `invalid byte sequence for encoding "UTF8": 0x00`로 거부했습니다(`DB_ERROR`). → `normalize_text`에서 NUL을 지우도록 **수정**했고 회귀 테스트를 넣었습니다.
3. **가로(landscape) 회전된 Schedule of Assessments 표**: pypdf의 일반 추출은 셀을 위→아래 순서로 늘어놓아 "행 = 평가 항목, 열 = 방문"의 대응이 사라집니다. `extraction_mode="layout"`은 회전 페이지에서 "Rotated text discovered. Output will be incomplete."를 내고 일부를 버립니다. 그래서 일정표를 "항목: 방문=X" 행으로 펼치는(flatten) 처리는 구현하지 못했습니다.

## 이번에 한 것

- 표 캡션(`Table 4 Schedule of Assessments ...`)을 가장 깊은 수준의 헤딩으로 인식해, 표 본문 chunk가 캡션 아래 섹션으로 묶이게 했습니다(`headings.TABLE_LEVEL`). 회전 표의 행 구조는 복원하지 못하지만, 최소한 "어느 표의 내용인지"는 chunk 머리말에 남습니다.
- 번호 헤딩을 "일관된 번호 사슬"로만 인정(`headings.consistent_headings`)해, 개정 이력 표의 섹션 번호 인용(예: "5.2 Exclusion Criteria | Updated wording...")이 이후 모든 chunk의 섹션 경로를 오염시키던 문제를 고쳤습니다(DESTINY-Breast06 프로토콜: 수정 전에는 본문 대부분이 "Appendix G > ..." 아래로 들어감).

## 수정 방향

- 글리프 손실: 추출 후 검증 규칙(예: 숫자 앞의 단독 대문자 `P`, `\d{2}\s?weeks`처럼 범위가 붙은 패턴)을 경고로 기록하고, 인덱싱 보고서에 문서별 의심 건수를 남깁니다. 근본 해결은 폰트 ToUnicode를 더 잘 다루는 추출기 비교가 필요합니다(PyMuPDF는 AGPL이라 런타임에 쓰지 않음, ADR 0001).
- 회전 표: pypdf의 `visitor_text`로 글자 좌표를 받아 회전 행렬을 되돌린 뒤 행·열을 군집하는 방식을 시험해 볼 수 있습니다. 측정 기준: SoA 질문의 섹션 hit와 키워드.
- 답변 측: 수치가 들어간 답변 문장은 인용 chunk의 원문 수치와 대조하는 후처리를 검토합니다(이슈 010의 "인용 없는 수치 제거"와 같은 방향).
