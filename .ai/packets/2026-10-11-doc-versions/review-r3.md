# Review r3 — 2026-10-11-doc-versions (fix2 재검토, R4만)

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: review-r2 R4와 그 수정(report-implementer `## fix2`). 새 오탐 탐색은 하지 않았다(r2에서 끝남).
- 실행: `uv run --project backend python`으로 `resolve_version`·`latest_flags`·`compare_versions`를 직접 호출했다. 스크립트는 scratchpad에 두었다(레포 밖).

## 판정: **APPROVE**

R4가 고쳐졌다. 파일명 날짜는 이제 숨김 판단에 쓰이지 않는다. 날짜는 양쪽 모두 manifest에서 온 경우에만 비교한다. 테스트·문서·범위 모두 fix2 지시와 일치한다.

## 확인한 항목

### 1) r2 재현 쌍 — 모두 둘 다 최신
`resolve_version(name, relative_path)` → `latest_flags`. 같은 폴더, 같은 그룹 기준이다.

| 파일명 쌍 | family / label / source | flags |
|---|---|---|
| `Minutes v1 20250101.pdf` / `…20250301.pdf` | `minutes` / v1 / filename | [True, True] |
| `회의록_v1_20250101.docx` / `…20250301.docx` | `회의록` / v1 / filename | [True, True] |
| `MVR_v1.0_2025-01-10.pdf` / `…2025-03-02.pdf` | `mvr` / v1.0 / filename | [True, True] |
| `weekly report v1 2025-01-06.pdf` / `…01-13.pdf` | `weekly report` / v1 | [True, True] |
| `Protocol v2 Amendment 1 20250101.pdf` / `…20250301.pdf` | `protocol` | [True, True] |
| `plan v2 20250101.pdf` / `plan v2.0 20250915.pdf` | `plan` | [True, True] |
| `sub/Minutes v1 …0101` / `sub/Minutes v1 …0301` (폴더 안) | `sub/minutes` | [True, True] |
| 대조: `plan v2 20250915.pdf` / `plan v3 20250101.pdf` | `plan` | [False, True] (번호 우선, 정상) |

**파일명 날짜가 숨김에 쓰이는 다른 경로는 없다.** 확인한 사용처는 다음과 같다.
- `doc_versions.py`:
  - 날짜 비교는 `compare_versions` 252–255행 한 곳뿐이다. 조건은 `a.source == b.source == "manifest"`다.
  - `latest_flags`는 `compare_versions`와 `superseded`만 쓴다.
  - `infer_from_filename`은 날짜만 있는 이름에 family를 주지 않는다(173행).
- `indexing_pipeline.py`:
  - `_apply_version`이 `version_source`를 DB에 저장한다.
  - `recompute_latest`(296–325행)는 DB 행에서 `source=d.version_source`로 `VersionInfo`를 다시 만든다. 그래서 재계산 때도 source가 보존되고, manifest끼리만 비교하는 조건이 유지된다.
- 그 밖의 `version_date` 사용처는 모두 표시·전달용이다. 숨김 판단에는 쓰이지 않는다.
  - `api/rag.py` 28·92, `rag_service.py` 485, `prompt_builder.py` 20, `vector_search_service.py` 53–128, `schemas/rag.py` 29
  - 검색 필터는 `is_latest`만 본다(`vector_search_service.py:149`).

### 2) manifest 날짜 동률 깨기
직접 호출한 결과:
- manifest v1(2025-01-01)과 manifest v1(2025-03-01): `compare=1`, flags [False, True]. 앞쪽이 숨는다(유지).
- manifest v1(01-01)과 filename v1(03-01): `compare=0`, flags [True, True]. 비교하지 않는다.
- manifest 날짜가 같을 때: 0이다.

테스트:
- `test_manifest_dates_break_a_version_tie`(175–190행)를 새로 넣었다. 두 가지를 고정한다.
  - 동률 + manifest 날짜 → 앞쪽 숨김
  - manifest 날짜 대 파일명 날짜 → 둘 다 최신
- `test_manifest_dates_compare_when_stated`(149행, 판 없이 manifest 날짜만 있는 경우)는 그대로 남아 있다.
- 단위 테스트 2파일을 재실행했다: **59 passed**(r2의 52 + 추가 7).
- `make lint` exit 0.
- 증빙 `evidence/junit-fix2.xml`: tests=585, failures=0, errors=0.

### 3) 문서 문장과 코드의 일치
- **ADR 0006 §2(18행)**: "같으면 날짜로 가리되, 날짜는 두 문서가 모두 manifest에 `date`를 적었을 때만 … 파일명에서 읽은 날짜는 어떤 경우에도 숨김 판단에 쓰지 않습니다"
  - 코드와 일치한다.
  - r2가 지적한 비문("비교할 수 없으면 그래도 가릴 수 없으면")은 고쳐졌다.
- **ADR Consequences(34행)**: "날짜 계열을 같은 문서의 판으로 숨기려면 manifest에 판·날짜를 명시해야"
  - 이제 사실이다.
  - 잔여 오탐(V1/V2, `IL1R1`, `Region (R2)`)과 대응(manifest family 또는 `SEARCH_LATEST_ONLY=false`)이 r2 권고대로 추가됐다.
- **README 392행**: "파일명 날짜는 숨김 판단에 쓰지 않습니다(날짜는 manifest에 적은 것끼리만 비교)". 일치한다.
- **journey §16(129행)**: "번호를 숫자로(날짜는 manifest에 적은 것끼리만) 비교". 일치한다.
- issue 005와 `doc_versions.py` 모듈 docstring(15–18행)도 일치한다.
- 경미, 비차단: 코드는 두 문서 모두 manifest 날짜가 있으면 번호가 없거나 종류가 달라도 날짜로 가린다(예: manifest v2 대 R3에 날짜가 있을 때).
  - ADR §2의 "같으면 날짜로"는 번호 동률만 말하는 것처럼 읽힐 수 있다.
  - 이는 fix 전부터 있던 동작이고, `test_manifest_dates_compare_when_stated`가 의도로 고정한 것이다. 명시 manifest만 해당하므로 수정할 필요는 없다.

### 4) 범위 · assert · denylist
- `git diff --name-only origin/main`: 16개로 r2와 같다. untracked 파일 목록도 r2와 같다(packet 문서·새 코드·테스트·결과 폴더 4개).
- 평가셋·기존 결과 폴더는 바뀌지 않았다. `corpus/public/.corpus.yaml`은 기존 변경 그대로다.
- fix2가 손댄 파일은 `doc_versions.py`, `test_doc_versions.py`, ADR 0006, README, journey, report다. 지시 범위 안이다.
- assert 변경:
  - `test_version_first_then_date_on_a_tie`의 첫 assert를 "둘 다 최신"으로 바꿨다. 승인된 의도 변경 1건이다.
  - 두 번째 assert(v3 > v2, 날짜 무관)는 유지했다.
  - 나머지는 추가만 있다(parametrize 6쌍, 새 테스트 1개). 완화나 삭제는 없다.
- denylist: `git diff origin/main` 전체와 untracked 파일 내용을 `grep -inEf ~/clinical-rag-private/commit-denylist.txt`로 검사했다. **0건**.
- public 영향: public 파일명에 8자리 날짜가 없다(r2 확인). 이번 변경은 public 결과에 닿지 않는다. 재측정은 필요 없다.

## 발견 리스크
- 차단 없음.
- 경미: ADR §2가 "manifest 날짜는 번호 비교가 안 될 때도 쓰인다"를 명시하지 않는다(위 3). 원하면 문장 하나를 보탠다.

## 후속 제안
- r1·r2의 후속 제안은 그대로 남는다.
  - 삭제된 파일 행의 경쟁
  - checksum 중복 시 판 덮어쓰기
  - Phase 4 추정 정확도 측정에 "판이 아닌데 묶인 쌍 수"를 넣는 것
