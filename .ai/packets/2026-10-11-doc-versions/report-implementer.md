# Implementer report — 2026-10-11-doc-versions

## 한 일
- `backend/app/services/doc_versions.py`(판 토큰 파서·family 정규화·manifest 매칭·최신판 판정, 순수 함수), Alembic 0007, `Document` 열, `indexing_pipeline`(판 채움 + 색인 후 corpus 단위 `recompute_latest`, 중복·재색인 경로 포함).
- `search_chunks(latest_only=)`: 벡터·하이브리드 채널이 같은 `stmt`를 써서 둘 다 필터링. `RagService`/API에 `include_superseded`, 설정 `SEARCH_LATEST_ONLY`(기본 true), `QuestionRequest.file_type`에 docx·xlsx.
- `SourceOut` + 응답에 `versionLabel/versionDate/isLatest/supersededWarning`, 프롬프트 근거 머리 `[n] 출처: 파일명 · 판 / …`(판 없으면 이전과 동일, 지시문 불변), Streamlit 체크박스·출처 판 표시·경고.
- 테스트: 단위 33 + 6, 통합 7(실제 PostgreSQL). `make test` 564 passed (증빙: `evidence/junit.xml`, tests=564 failures=0 errors=0 skipped=0, timestamp 2026-10-11T17:26:14+09:00), `make lint` 통과.
- 공개 코퍼스 `versions:` 추가, public 측정 4회, ADR 0006, journey §16, README, 이슈 005, `.env.example`, eval config.json에 `search_latest_only`.

## 결정/주의 (packet과 다른 점)
- **`version_superseded` 열을 추가**했다(packet의 열 목록 외). manifest의 `superseded`를 남겨야 이후 색인 때 manifest 없이 재계산 가능.
- family 전체가 superseded이면 숨기지 않고 서로 비교(확신 없으면 숨기지 않음). 실패한 새 판은 옛 판을 숨기지 않음(INDEXED만 참여).
- 토큰 없는 원본(`foo.pdf`)과 `foo v2.pdf`는 묶지 않음(설계대로).
- 이미 색인된 행은 다음 색인 실행(중복 생략 경로)에서 판 열이 갱신된다. 마이그레이션만으로는 family 없음/최신으로 둔다.
- 사고: `ruff format`을 `--config` 없이 돌려 테스트 24개가 재포맷됐고 `git restore`로 되돌림. 최종 `git diff --name-only`는 Edit 목록 밖 `backend/app/container.py` 1개(`latest_only=settings.search_latest_only` 한 줄 배선)를 포함한다. `ask` 없이 수정했고 coordinator가 사후 승인했다(review-r1·fix1).

## 측정 (public 99문항, exact, bge-m3, gemma4:e4b, Ollama 0.40.2, 같은 색인 2,029 chunk, 일회용 컨테이너 `crqa-docver-eval`)
- 끔 2회 / 켬 2회, 폴더 `eval/results/2026-10-11_public_bge-m3-exact-gemma4-e4b-latest{off,on}[-run2]_8e014ae3`.
- hit@5 96.2 → 94.9%, 섹션 hit 87.3 → 84.8%, Citation 86.7/85.3 → 90.7/90.7%, Keyword 92.0 = 92.0%, 거절 95.0 = 95.0%.
- p10~p16 top-5: R2 27 → 0, R3 8 → 29 (두 번 동일). 파일 hit 5 → 7, 인용 정확 2 → 7. **편향 주의: 실패를 본 뒤 고친 문항이라 "실패 재확인"만.**
- 잃은 것: p32·p33·p34(정답 파일이 05) hit·섹션·인용 miss. 답은 R3로 나옴(거절 아님, 내용 채점은 안 함). 평가셋·임계값은 그대로.
- Reviewer 확인용: 같은 색인(chunk 2,029)·exact·같은 Ollama. 끔 대 켬 사이 다른 변경 없음(환경변수 `SEARCH_LATEST_ONLY`만).

## 남은 것
- Phase 4는 coordinator(로컬). 일회용 컨테이너 `crqa-docver-eval`은 측정 후 삭제.

## fix1 (review-r1 R1~R3)
- **R1** 파일명 추정(source=filename)의 family 키에 상대 폴더(`relative_path`의 parent, 부분마다 정규화)를 붙였다(`resolve_version`). manifest family는 그대로. 단위 테스트(`test_same_name_in_other_folders_is_another_document`: studyA/Protocol_v2 대 studyB/Protocol_v3 → 둘 다 최신, 같은 폴더·대소문자 달라도·루트는 경쟁)와 통합 테스트 1건(`test_same_file_name_in_other_folders_does_not_hide_a_study`).
- **R2(a)** 날짜만 있는 이름은 family를 만들지 않는다(날짜는 표시용으로 `VersionInfo.date`에만 남음). `compare_versions`는 날짜를 (같은 종류 번호가 동률) 또는 (양쪽이 manifest) 일 때만 쓴다. `test_dates_only`는 coordinator 승인대로 `test_dates_only_never_hide_anything`(둘 다 최신)으로 바꿨고, manifest `date` 비교 테스트 `test_manifest_dates_compare_when_stated` 1건 추가.
- **R2(b)** 단독 `R\d+`는 판이 아니다. 인정: `(R3)` 괄호, `Rev`/`Revision`, 앞에 식별자(영문+숫자 1~3자리)가 붙은 `E6R3`·`E10R3`, 앞자리 0(`R01`·`R021`)은 항상 제외. 리뷰 표의 8쌍(NIH R01/R21·R01/R02, Site R1/R2, COVID-19 R0/R1, 회의록, Monitoring Visit Report, Lot, weekly)을 `test_identifiers_and_date_series_are_not_editions`로, `ICH E6(R2)/(R3)`·`ICH_E6R2/E6R3`는 `test_ich_style_editions_are_editions_and_group_into_one_family`로 고정. 의도 변경 2건: `test_names_without_a_token`에서 `02_ich_e6r3_2025.pdf`를 뺐고(이제 `E6R3`이라 판 `r3`로 잡힘), `sample gcp R2/R3` 쌍을 `(R2)/(R3)`로 바꿨다(단독 R 불인정). `parse_version_key`는 manifest의 `"R3"` 같은 검증된 label을 위해 느슨한 R 패턴을 label 파싱에만 쓴다.
- **R3** ADR 0006 Consequences와 journey §16 "잃은 것"에 p32 한계 문장(옛 판 문서를 이름으로 지목한 요청을 기본값이 막음, 평가셋이 아닌 기능의 한계, 대응은 "옛 판 포함" 또는 Not decided의 질문 속 판·문서 이름 필터)과 p33·p34는 평가셋 정의 문제라는 구분을 추가. README·issue 005에 각 한 줄. ADR §1·§2도 새 규칙에 맞게 고쳤다.
- **public 측정 영향 없음 → 재측정 안 함.** `corpus/public` 11개 파일의 `resolve_version(file_name, relative_path, manifest)` 결과를 fix 전후로 덤프해 `diff`가 비었다(02·05는 manifest, 03은 filename `rev6`/family `03 ema anticancer`, 나머지 8개는 source=none). 파일이 코퍼스 루트라 폴더 접두도 붙지 않는다.
- **사고 기록:** 중간에 `ruff format`을 `--config` 없이 돌려 범위 밖 테스트 파일이 재포맷됐다가 `git restore`로 되돌리고 `make format`으로 맞췄다. 최종 `git diff --name-only`는 원래 16개 그대로다.
- **게이트:** `make lint` exit 0. `uv run --project backend pytest --junitxml=.ai/packets/2026-10-11-doc-versions/evidence/junit-fix1.xml` exit 0 — `evidence/junit-fix1.xml`: tests=578, failures=0, errors=0, skipped=0, timestamp 2026-10-11T17:34:00.924163+09:00.

## fix2 (review-r2 R4)
- **R4** `compare_versions`: 날짜는 양쪽 source가 모두 manifest일 때만 비교한다. 파일명에서 읽은 날짜는 `VersionInfo.date`(표시용)에만 남고 숨김 판단에는 쓰지 않는다. 같은 종류 번호가 동률이고 manifest 날짜가 없으면 0 → 둘 다 최신.
- **의도 변경(승인됨)**: `test_version_first_then_date_on_a_tie`의 첫 assert(`plan v2 20250101` 대 `plan v2 20250915`)를 "앞쪽 숨김"에서 "둘 다 최신"으로 바꿨다. 두 번째 assert(v3 > v2, 날짜 무관)는 그대로.
- **테스트 추가**: `test_identifiers_and_date_series_are_not_editions`에 리뷰의 쌍(Minutes v1, 회의록_v1, MVR_v1.0, weekly report v1, Protocol v2 Amendment 1, plan v2/v2.0 — 모두 날짜 2개)을 '둘 다 최신'으로 고정. `test_manifest_dates_break_a_version_tie` 추가(manifest 날짜 동률 깨기 유지, manifest 날짜 대 파일명 날짜는 비교 안 함).
- **문서**: ADR §2(비문 포함)·README·journey §16의 "날짜" 문장을 "파일명 날짜는 숨김 판단에 쓰지 않는다 / 날짜는 manifest끼리만"으로 정정. ADR Consequences에 남은 오탐(방문 번호 V1/V2, 식별자 접두 R `IL1R1`, 괄호 R 식별자 → manifest로 family 명시 또는 `SEARCH_LATEST_ONLY=false`) 한 문장 추가. `doc_versions.py` 모듈 docstring도 맞췄다.
- **public 영향 없음**: `corpus/public` 11개 파일의 `resolve_version` 결과가 fix 전(02·05 manifest, 03 filename `rev6`, 나머지 source=none)과 같다. 파일명에 8자리 날짜가 든 파일이 없어 날짜 규칙이 닿지 않는다. 재측정 불필요.
- **게이트**: `make lint` exit 0. `uv run --project backend pytest --junitxml=.ai/packets/2026-10-11-doc-versions/evidence/junit-fix2.xml` exit 0 — `evidence/junit-fix2.xml`: tests=585, failures=0, errors=0, skipped=0, timestamp 2026-10-11T17:39:47+09:00.
