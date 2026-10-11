# Task Packet: 변경대비표 판 오탐 수정 + 판 정보 초안 도구

- **ID:** 2026-10-11-versions-draft
- **날짜:** 2026-10-11
- **실행 방식 판정:** 4-role. 숨김 판단(검색 경로)이 바뀌고, 로컬 전용 자료로 재측정한다.
- **Planner:** coordinator (Claude Opus 5.5) / **Implementer:** Claude Sonnet 5.5 / **Reviewer:** Claude Opus 5.5 (read-only) / **Tester:** Claude Sonnet 5.5
- **관련:** packet 2026-10-11-doc-versions(PR #22), ADR 0006, base = 최신 `origin/main`
- **Workspace:** 새 top-level worktree `versions-draft` / base = `origin/main`
- **통합 대상:** 기본 workspace → `main` — PR (rebase merge)

## 배경
- #22 머지 후 coordinator가 로컬 업무 문서 87건으로 쟀다(집계만).
  - 파일명 추정은 옛 판 71건 중 10건만 숨겼다. 나머지 61건 중 34건은 새 판과 이름이 판 말고도 달라 family가 갈렸다.
    26건은 같은 family 안에서 판 번호가 같거나 비교할 수 없었다(판 번호가 같은 xlsx가 많다). 1건은 판 토큰이 없었다.
  - 정답 파일 top-5는 필터 끔 21/42 → 켬 24/42였다. 옛 판 chunk 비율은 79.5% → 77.6%에 그쳤다.
    최신판 16건만 넣었을 때는 39/42였다.
  - **오탐 2건:** 파일명에 판이 둘 있는 문서(`… v2.1 v2.2`, 판에서 판으로의 변경을 담은 문서)를 앞 판만 읽었다.
    그래서 서로 다른 변경 문서가 한 family의 판처럼 비교됐고, 최신판으로 지정된 문서 2건이 숨겨졌다.
- 결론: "확신 없으면 숨기지 않음"은 안전하지만, 실제 문서에서 효과를 내려면 판 정보를 명시해야 한다.
  사람이 87건을 손으로 쓰는 것은 비현실적이다. 그래서 **추정으로 초안을 만들고 운영자가 확인·수정하는** 흐름을 만든다.

## 설계 (coordinator 결정)
1. **오탐 수정:** 파일명에 같은 종류의 판 토큰이 2개 이상이면(`v2.1 v2.2`, `R2 R3`, `Rev5→Rev6`) 판을 추정하지 않는다.
   그 문서는 family 없음(단독)으로 둔다.
2. **별도 판 정보 파일:** 코퍼스 루트의 `.versions.yaml`(형식은 `.corpus.yaml`의 `versions:`와 같음)도 읽는다.
   - 두 곳에 다 있으면 `.corpus.yaml` 항목이 먼저 매칭된다.
   - 분류 marker와 운영자가 고치는 판 목록을 분리하려는 것이다.
   - `.versions.yaml`은 문서가 아니므로 색인 대상에서 뺀다. 숨김 파일이라 이미 빠지지만 테스트로 고정한다.
3. **초안 도구** `scripts/draft_versions.py <corpus_dir> [--out PATH]`(기본 출력은 stdout, 파일을 쓰려면 `--out`):
   - (a) 파일명 추정 결과를 family별로 묶는다.
   - (b) family가 갈린 **후보 묶음**을 제안한다. 같은 폴더·같은 형식 계열에서, 판·날짜 토큰을 뺀 이름이
     접미어 몇 개만 다르거나 문자열 유사도가 높으면 묶는다. 규칙은 report에 적는다.
   - (c) family 안에서 판 번호가 같거나 비교할 수 없으면, 파일명 날짜를 `date` **후보**로 넣는다.
     manifest 날짜가 되어야 비교되므로, 운영자가 확인해야 효력이 생긴다.
   - (d) 출력은 `.versions.yaml` 형식이다. 항목마다 `# 근거:` 주석(추정 토큰, 묶은 이유)과 `# 확인 필요` 표시를 단다.
     자동으로 숨김을 확정하지 않는다. `superseded`는 쓰지 않고, 판·날짜 비교로 정해지게 둔다.
   - (e) 요약을 stderr로 낸다: 파일 수, family 수, 후보 묶음 수, 확인 필요 항목 수.
4. **이번 범위가 아닌 것:** 질문 속 판 이름으로 거르기, chunk 머리말 식별자(3c), UI에서 판 정보 편집.

## 할 일
### Phase 1 — 오탐 수정
1. `doc_versions.infer_from_filename`에서 같은 종류의 판 토큰이 2개 이상이면 단독으로 둔다.
   단위 테스트: `Change table v2.1 v2.2` / `v2.2 v3.0` → 둘 다 최신, `Protocol v2.1`과 `Protocol v2.2`는 그대로 판으로 비교.

### Phase 2 — `.versions.yaml`
2. `indexing_pipeline`이 `.corpus.yaml`의 `versions:`에 이어 `.versions.yaml`도 읽게 한다. 매칭 우선순위와 형식 오류 처리도 정한다.
   형식이 틀리면 색인을 멈추지 않고 경고만 남기고, 그 파일은 무시한다(추정으로 대체).
3. 통합 테스트:
   - `.versions.yaml`로 날짜를 명시한 같은 판 두 문서 → 옛 날짜가 숨겨진다
   - `.versions.yaml`을 지우고 재색인 → 둘 다 최신으로 돌아간다
   - 형식 오류 → 경고 + 추정으로 대체

### Phase 3 — 초안 도구
4. `scripts/draft_versions.py`와 단위 테스트를 만든다(합성 파일명만, 회사 파일명 금지).
   - 묶음 제안: 접미어 차이(`_clean`/`_tracked`/`_final`/`_구두보완` 같은 형태)
   - 폴더가 다르면 묶지 않는다
   - 날짜 후보, 출력 YAML이 `parse_manifest`로 다시 읽히는지
   - 출력 YAML을 그대로 적용하면 판 순서가 기대대로인지
5. README 사용법 절과 ADR 0006에 "초안 → 확인 → `.versions.yaml`" 흐름을 추가한다.

### Phase 4 — 업무 문서 재측정 (coordinator, 머지 후 로컬, 집계만)
6. 초안 도구를 87건에 돌린다. 보고는 다음과 같다.
   - **초안을 그대로 적용:** 숨긴 최신판 수, 숨긴 옛 판 수, 정답 파일 top-5, 옛 판 chunk 비율
   - **운영자 확인 흉내:** 초안을 수동 최신판 목록과 대조해 고친다. 고친 항목 수(= 운영자가 손댈 양)를 세고, 같은 지표를 낸다.
   - 비교 기준: 필터 끔 21/42, 파일명 추정만 24/42, 최신판만 넣은 코퍼스 39/42
7. #22의 Phase 4 수치와 이번 수치를 journey §16·README에 집계만 반영한다.

## Scope
### Read
- `docs/decisions/0006-document-versions.md`, `backend/app/services/llm_guardrail.py`
### Edit
- `backend/app/services/doc_versions.py`, `backend/app/services/indexing_pipeline.py`
- 신규: `scripts/draft_versions.py`
- `tests/unit/**`, `tests/integration/**`(새 테스트 추가, 기존 assert 완화 금지. 의도 변경이 필요하면 `ask`)
- `docs/decisions/0006-document-versions.md`(절 추가·정정), `README.md`, `docs/journey.md`(§16 보강은 coordinator가 Phase 4에서)
- `.ai/packets/2026-10-11-versions-draft/report-implementer.md`, `…/evidence/`
### Protect (scope.md 상시 목록에 더해)
- 검색·생성 경로의 다른 부분(`vector_search_service`, `rag_service`, `prompt_builder`), chunker·embedding 입력
- `corpus/public/**`(이번에는 고칠 일 없음), 평가셋, 임계값, 기존 `eval/results/**`

## 완료 조건
- Tester: `make lint`, `make test` exit 0. junit의 tests·failures=0·errors=0·skipped=0·timestamp를 인용한다.
- Reviewer:
  - 오탐 수정이 진짜 판 비교를 깨지 않는지(합성 파일명으로 직접 실행)
  - `.versions.yaml` 우선순위·오류 처리
  - 초안 도구가 숨김을 자동 확정하지 않는지(`superseded` 미사용, 파일명 날짜는 `date` 후보로만)
  - 묶음 제안이 다른 폴더·다른 문서를 묶지 않는지
  - public 코퍼스 판정이 이번 변경 전후로 같은지(`resolve_version`으로 직접 확인)
  - `git diff --name-only` ⊆ Edit 목록
  - denylist 0건

## 제약
- git commit/push/브랜치/checkout/stash 금지. 패키지·모델 다운로드 금지, 외부 LLM API 금지
- 로컬 전용 업무 문서는 Implementer가 열지 않는다(Phase 4는 coordinator 몫)
- Edit 목록 밖을 고쳐야 하면 `ask`로 묻는다. 완료는 `worker_done`으로 1회 보낸다
