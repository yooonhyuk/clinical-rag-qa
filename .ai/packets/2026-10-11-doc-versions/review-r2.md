# Review r2 — 2026-10-11-doc-versions (fix1 재검토)

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: review-r1 R1~R3과 그 수정(report-implementer `## fix1`)
- 기준 coordinator 결정:
  - R1: 폴더를 family 키에 넣는다.
  - R2(a): 파일명 날짜는 판이 아니다. **date는 manifest끼리만 비교한다.**
  - R2(b): 단독 R은 판이 아니다. 괄호·Rev·식별자 접두만 인정하고, 앞자리 0은 제외한다.
  - container.py 1줄은 사후 승인, `test_dates_only` 의도 변경은 승인.
- 실행: `uv run --project backend python`으로 `resolve_version`·`latest_flags`를 직접 호출했다(스크립트는 scratchpad, 레포 밖).

## 판정: **REQUEST_CHANGES**

R1, R2(b), R3은 고쳐졌다. 재현 쌍은 모두 숨김이 없어졌다.
하지만 **R2(a)가 coordinator 결정과 다르게 구현됐다.** 파일명 날짜가 "같은 종류 번호가 동률"일 때 여전히 승부를 가린다.
그 결과 양식 판 번호가 같은 날짜별 문서(회의록·방문 보고서·주간 보고)가 서로를 숨긴다(R4, 차단).

## 반려 항목

### R4. 파일명 날짜가 동률 깨기로 남아 날짜별 다른 문서를 숨긴다 (차단)
- 위치:
  - `backend/app/services/doc_versions.py:255-261` (`compare_versions`): `dated and (common or both manifest)`.
    `common`(같은 종류 번호가 있음)이면 source=filename인 날짜도 비교한다.
  - `tests/unit/test_doc_versions.py:155-159` `test_version_first_then_date_on_a_tie`: `plan v2 20250101` 대 `plan v2 20250915`에서 앞쪽이 숨는 것을 **의도로 고정**한다.
  - 문서: ADR 0006 §2(18행)의 "파일명의 날짜는 이렇게 같은 종류의 번호가 동률일 때만"
- 직접 실행 결과 (같은 폴더·같은 corpus):

  | 파일명 쌍 | family | 결과 |
  |---|---|---|
  | `Minutes v1 20250101.pdf` / `Minutes v1 20250301.pdf` | `minutes` | **1월 회의록 숨김** |
  | `회의록_v1_20250101.docx` / `회의록_v1_20250301.docx` | `회의록` | **1월 회의록 숨김** |
  | `MVR_v1.0_2025-01-10.pdf` / `MVR_v1.0_2025-03-02.pdf` | `mvr` | **1월 방문 보고서 숨김** |
  | `weekly report v1 2025-01-06.pdf` / `…2025-01-13.pdf` | `weekly report` | **앞 주 보고 숨김** |
  | `Protocol v2 Amendment 1 20250101.pdf` / `…20250301.pdf` | `protocol` | 앞쪽 숨김 |
  | `plan v2 20250101.pdf` / `plan v2.0 20250915.pdf` | `plan` | 앞쪽 숨김 |

- 왜 문제인가:
  - 업무 문서는 양식 판(`v1`, `v1.0`)을 이름에 넣고 날짜로 회차를 나누는 경우가 흔하다. r1 R2가 막으려던 "날짜별 다른 문서 숨김"이 `v1` 하나만 붙으면 그대로 재발한다.
  - coordinator 결정("manifest date만 비교")과 다르다. fix1 report는 r1의 권고 (a) 원문("동률일 때 보조 비교")을 따른 것으로 보인다. 그러나 dispatch에 적힌 결정은 그보다 엄격하다.
  - 판 번호가 같다는 것은 "확신 없음"이다. 설계 원칙("의심되면 둘 다 최신")과도 어긋난다.
  - 문서가 사실과 다르다:
    - README 392행 "날짜만 다른 파일은 숨기지 않습니다"는 위 표의 경우에 틀린다.
    - ADR 0006 Consequences 34행 "날짜 계열을 같은 문서의 판으로 숨기려면 manifest로 명시해야 합니다"도 틀린다.
- 방향:
  - `compare_versions`에서 날짜는 **양쪽 source가 모두 manifest일 때만** 비교한다. 파일명 날짜는 `VersionInfo.date`(표시용)에만 남긴다. 번호가 동률이면 0을 돌려 둘 다 최신으로 둔다.
  - `test_version_first_then_date_on_a_tie`의 첫 assert를 "둘 다 최신"으로 바꾼다. 이 의도 변경을 report에 적는다. 두 번째 assert(v3 > v2, 날짜 무관)는 유지한다.
  - 위 표의 `Minutes v1`·`MVR_v1.0`·`회의록_v1` 쌍을 `test_identifiers_and_date_series_are_not_editions`에 추가한다.
  - 판 번호 동률 + manifest date 비교 테스트(`test_manifest_dates_compare_when_stated` 계열)는 그대로 둔다.
  - ADR §2와 README 문장을 새 규칙에 맞춘다. ADR §2의 비문 "비교할 수 없으면 그래도 가릴 수 없으면"도 함께 고친다.
  - public 영향은 없다. public에 날짜가 든 파일명이 없고, 02·05는 manifest에 date가 없다. 재측정은 필요 없다.

## 확인한 항목

### 1) r1 재현 — 숨김이 없어졌다 (R1·R2 해소)
- R1 폴더:
  - `studyA/Protocol_v2.0` 대 `studyB/Protocol_v3.0` → family `studya/protocol` / `studyb/protocol`, 둘 다 최신.
  - 같은 폴더(`studyA/…v2.0` 대 `studyA/…v3.0`)는 경쟁한다(v2.0 숨김). 루트 대 `studyB/` 하위는 경쟁하지 않는다.
  - 파이프라인은 `f.path.relative_to(root).as_posix()`를 넘긴다(`indexing_pipeline.py:120-122`). 상대 경로가 맞다.
- r1 R2 표 11쌍을 모두 재실행했다.
  - NIH R01/R21, Site R1/R2, COVID-19 R0/R1, 회의록 날짜, Monitoring Visit Report 날짜, Lot 날짜 → 모두 family None, 숨김 없음.
  - Table/Phase/연도/mm → 여전히 숨김 없음.
  - `ICH_E6R2`/`E6R3` → 의도대로 R2 숨김.
- 단위 테스트 2파일을 재실행했다: 52 passed.

### 2) 새 오탐 탐색 — 합성 파일명 약 80쌍
판단 기준: 숨김이 일어나는 쌍이 같은 문서의 판인가.

**같은 문서의 판일 때만 숨김 (양호):**
- `ICF_Korean_v3`/`v4`, `SAP_v1.0_draft`/`SAP_v2.0_draft`, `CRF_v2 Appendix 3`/`CRF_v3 Appendix 3`
- `Study-123_Protocol_v2`/`v3`, `Protocol Amendment 2`/`3`, `E6(R2) 번역본`/`E6(R3) 번역본`, `ICH E6(R2)`/`ICH E6R3`
- `guide Version 2`/`ver.3`, `지침 제2차 개정`/`제3차 개정`, `지침_개정2`/`개정3`, `IB Rev5`/`Rev6`
- `Protocol v2.0 Amendment 1`/`2`, `model v1.2.3`/`v1.10`, `v2 Protocol`/`v3 Protocol`, `Protocol_v2_KR`/`v3_KR`

**다른 문서는 숨기지 않음 (양호):**
- `Protocol v2.0 (R1 site)` 대 `(R2 site)`(v2.0/v3.0 모두), `ICF_Korean_v3` 대 `ICF_English_v4`
- `SAP_v1.0_draft` 대 `_final`, `CRF_v2 Appendix 3` 대 `Appendix 4`·`CRF_v3`
- `Study-123` 대 `Study-456`, `Amendment 2 summary` 대 `Protocol Amendment 3`, `E6(R2) 번역본` 대 `E6(R3)`
- `SOP-001 v2` 대 `SOP-002 v3`, `Cohort A`/`B`, `Arm 1`/`2`, `Section 5`/`6`, `Part A`/`B`, `Volume 1 rev 2`/`Volume 2 rev 3`
- `Annex1`/`Annex2`, `Table 4 v1`/`Table 5 v2`, `GL v2 2024`/`GL v3 2025`, `IND 12345`/`67890 Amendment`
- `Protocol_v2` 대 `Protocol_v2 (1)`, `Protocol_v2 copy` 대 `Protocol_v3`, `HER2 R1`/`R2`, `Q1R1`/`Q2R1`, `(R01)`/`(R02)`, `E6R01`/`E6R02`
- 동률 `guide v1` 대 `guide V1.0` → 둘 다 최신(양호)

**다른 문서를 숨김:**
- 날짜 동률 깨기 6쌍 → **R4 (차단)**
- coordinator 결정 범위 안의 잔여 위험 (비차단, 문서화 권고):
  - (i) 방문 번호 `V1`/`V2`: `Visit V1 CRF`/`V2`, `Patient V1 report`/`V2`, `Lab_Results_V1`/`V2` → 앞쪽 숨김.
    임상시험에서 V1은 흔히 Visit 1이다. 그러나 `v\d`는 packet이 지정한 핵심 토큰이라 이름만으로는 가를 수 없다.
  - (ii) 식별자 접두 R: `IL1R1 assay`/`IL1R2 assay`(실재하는 서로 다른 유전자), `CD4R1`/`CD4R2`, `A1R1 site`/`A1R2 site` → 앞쪽 숨김. coordinator가 승인한 "식별자 접두" 규칙의 부작용이다.
  - (iii) 괄호 R이 식별자인 경우: `Region (R2) plan`/`(R3)`, `Subject (R1) narrative`/`(R2)` → 앞쪽 숨김. 괄호 인정 결정의 부작용이다.
  - 권고: ADR 0006 Consequences에 (i)~(iii)을 한 문장으로 적는다(이름만으로 가를 수 없음 → manifest 또는 `SEARCH_LATEST_ONLY=false`). Phase 4 추정 정확도 측정에 "판이 아닌데 묶인 쌍 수"를 넣는다(r1 후속 제안과 같음).
- 진짜 판을 놓치는 경우 (비차단): `지침_제2판`/`제3판`(판 토큰 없음), `E6(R2) 번역본` 대 `E6(R3)`(나머지 이름이 다름), `Amendment 2_v1.0`(나머지가 비어 family None). 모두 숨기지 않는 쪽이라 안전하다.
- 경미: 폴더 정규화가 대소문자·구분자를 합친다. 그래서 디스크상 다른 폴더 `Study A/`와 `study_a/`가 같은 family가 된다. 실무에서 드물어 비차단이다.

### 3) 의도 변경 테스트 2건 — 정당하다
- `test_names_without_a_token_are_standalone`에서 `02_ich_e6r3_2025.pdf`를 뺐다.
  - 새 규칙(식별자 접두 `E6R3`)에서는 이 이름이 판 `r3`로 잡힌다. 단독 문서 목록에 남길 수 없다.
  - 대신 `test_ich_style_editions…`가 `label == "r3"`을 assert한다. 검증이 지워진 게 아니라 옮겨졌다.
  - public에서는 manifest가 우선하므로 동작 영향이 없다(아래 4).
- `sample gcp R2/R3` → `(R2)/(R3)`: 결정 R2(b)(단독 R 불인정)에 맞춘 변경이다.
  - 같은 테스트가 여전히 R2 숨김·R3 최신을 assert한다.
  - 단독 R 쌍은 `test_identifiers_and_date_series_are_not_editions`로 반대 방향이 고정됐다. 완화가 아니다.
- `test_dates_only` → `test_dates_only_never_hide_anything`: 승인된 의도 변경이다.

### 4) public 매니페스트 결과 — 현재 값이 report와 일치한다
- 현재 코드로 `corpus/public` 11개 파일에 `resolve_version(name, name, manifest)`를 직접 실행했다.
  - 02: manifest `ich e6 gcp`/R3, 최신
  - 05: manifest `ich e6 gcp`/R2, superseded, **숨김**
  - 03: filename `rev6`/family `03 ema anticancer`, 최신(단독)
  - 나머지 8개: source=none
  - report 서술과 같다.
- **"fix 전" 코드는 git에 없다**(`doc_versions.py`가 untracked 새 파일이다). 그래서 전후 diff를 내가 다시 돌리지는 못했다. 대신 변경 3가지가 public 이름에 닿는지 확인했다.
  - (a) 폴더 접두: 11개 모두 루트라 접두 없음
  - (b) 날짜만 → family 없음: 8자리 날짜가 든 이름이 없음(연도 4자리만)
  - (c) 단독 R 제외: 단독 R 토큰이 없음. `rev6`은 Rev 규칙이다.
  - 셋 다 영향이 없다. 02는 manifest 없이 추정하면 이제 family `02 ich e6 2025`가 되지만, manifest가 우선하므로 무관하다.
  - 결론: "public 결과 동일 → 재측정 불필요"는 **타당하다.** R4 수정도 public 이름에 날짜가 없어 영향이 없다.

### 5) p32 한계 문장 — 정확하다
- `eval/public_questions.yaml` p32: "ICH GCP 안내서에 따르면…". expected는 `05_mfds_ich_gcp_ko.pdf` p.12다. 옛 판 문서를 이름으로 지목한다는 서술이 맞다.
- 결과 폴더 top-5:
  - 끔 2회: 05 ×5, hit True
  - 켬 2회: 02 ×4 + 04 ×1, hit False, 거절 아님
  - "05가 top-5에 0개, 답은 R3 chunk"와 일치한다.
- ADR 0006 Consequences 35행, journey §16 140행, issue 005 70행, README 392행이 같은 내용이다.
  - 기능의 한계 대 평가셋 정의(p33·p34)의 구분이 있다.
  - 대응("옛 판 포함" / Not decided의 이름 필터)도 적혀 있다.
- 경미: 켬 top-5에 04 chunk 1개가 섞여 있다. "R3 chunk로 나왔다"는 답(인용)에 대한 서술로 읽으면 맞으므로 수정 불필요.

### 6) 변경 범위 · assert · denylist
- `git diff --name-only origin/main`: 16개로 r1과 같다. 목록 밖은 container.py뿐이고 사후 승인됐다.
- untracked 파일:
  - 새 파일: 0007, doc_versions, ADR 0006, 테스트 3개, 결과 폴더 4개
  - 기존 결과 폴더·평가셋·SHA256SUMS 변경 없음
- assert 완화:
  - 기존(tracked) 테스트 파일 diff가 없다.
  - 새 테스트 파일 안의 변경은 위 3)의 의도 변경 3건뿐이다. 모두 승인됐거나 결정에 따른 것이다. 검증을 지운 것은 없다.
  - **단, R4의 `test_version_first_then_date_on_a_tie`는 결정과 반대 동작을 고정하고 있다.**
- denylist: `git diff origin/main` 전체 + untracked 파일 내용(결과 폴더 포함)을 `grep -inEf ~/clinical-rag-private/commit-denylist.txt`로 검사했다. **0건**.
- 외부 호출·의존성 변경 없음.
- 게이트 증빙: `evidence/junit-fix1.xml` tests=578, failures=0. 리뷰 중 단위 테스트를 재실행해 52 passed.

## 발견 리스크 (심각도순)
1. **R4** 파일명 날짜 동률 깨기 → 양식 판이 같은 날짜별 문서 숨김. coordinator 결정 불일치, README·ADR 문장도 틀림 (높음, 차단)
2. V1/V2 방문 번호, 식별자 접두 R(IL1R1), 괄호 R 식별자 → 이름만으로 못 가르는 잔여 오탐 (중간, 결정 범위 내, 문서화 권고)
3. 폴더 정규화가 대소문자·구분자만 다른 폴더를 합침 (낮음)
4. fix 전 코드가 보존되지 않아 "전후 동일" 덤프를 제3자가 재현할 수 없음 (낮음, 절차. 분석상 결론은 맞음)

## 후속 제안
- R4를 고친 뒤 재검토는 다음 3가지만 보면 된다: `compare_versions` 한 곳, 테스트 1건의 의도 변경과 추가 쌍, ADR §2·34행·README 문장.
- r1 후속 제안(삭제된 파일 행의 경쟁, checksum 중복 시 판 덮어쓰기)은 여전히 후속 이슈로 남는다.
