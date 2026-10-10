# 상시 Scope 규칙 (clinical-rag-qa)

> **이 파일은 프로젝트마다 새로 작성한다** — Protect 목록은 본질적으로 레포 고유다.
> 아래 "위반 검출" 절의 1~3번만 프로젝트 무관이다.

task packet의 Protect 목록과 별개로, 아래는 **모든 작업에서 기본 보호**된다.
예외가 필요하면 packet에 명시적으로 "Protect 해제: <대상> — <사유>"를 적어야 한다.
데이터·외부 호출 규칙(아래 "절대 금지")은 packet으로도 해제할 수 없다 — 사용자만 바꾼다.

## 절대 금지 (해제 불가)
- **외부 LLM API 호출** (평가·채점 포함). 생성·임베딩·재정렬은 로컬 Ollama / 로컬 HF 캐시만
- **사용자 승인 없는 다운로드** (모델·데이터셋·PDF·패키지). 승인 요청 시 파일명·출처·크기를 먼저 알린다
- **로컬 전용 자료를 레포에 넣는 것**: `~/clinical-rag-private/` 의 원문·프로토콜·질문·근거·답변 원문,
  의뢰사 문서와 그 파생물. 레포에는 **집계 수치만** 커밋한다 (`.gitignore` 의 `corpus/private/`, `corpus/originals/` 참조)
- **회사 관련 문자열** 커밋 (목록은 레포 밖 `~/clinical-rag-private/commit-denylist.txt`)
- `crqa_pgdata` 볼륨 사용 — DB는 일회용 컨테이너만
- 측정하지 않은 결과를 문서·README·커밋 메시지에 쓰는 것

## 상시 Protect (수정 금지, packet 해제 가능)
- `corpus/public/**`, `corpus/SHA256SUMS` — 공개 코퍼스와 체크섬
- **held-out 평가셋**: `eval/scope_heldout.yaml`, `eval/public_questions.yaml`, `eval/questions.yaml`의 기존 문항
  (문항 추가는 새 파일 또는 packet 해제 후. 기존 문항 수정·삭제 금지)
- **확정된 임계값·예시**: `backend/app/rules/scope_exemplars.yaml`, 설정의 margin·게이트 기본값 —
  dev에서만 다시 정하고, held-out을 본 뒤 바꾸지 않는다
- `eval/results/**` 의 기존 결과 폴더 — 결과는 덧붙이기만 한다
- `docs/decisions/*.md` 의 기존 ADR 결정 — 뒤집을 때는 새 ADR 또는 "Superseded" 절 추가
- `backend/pyproject.toml` / `backend/uv.lock` 의존성 추가·변경 — 명시 승인 필요
- `docker-compose*.yml`, `offline-bundle/**`(`verify-offline.sh` 포함) — 폐쇄망 egress 보장(journey §5)

## 평가 규칙 (Reviewer가 확인)
1. 임계값·목적함수는 **dev에서만** 정하고, held-out을 본 뒤 바꾸지 않는다
2. 모든 지표에 **분모>0** 확인, 측정 경로가 실제로 동작하는지 **카나리아**로 확인
3. 비교는 **같은 색인**(같은 DB·같은 chunk 수·같은 검색 모드)끼리. Ollama 버전이 다르면 기준선을 다시 잰다
4. 실패를 본 평가셋으로 수정 효과를 재지 않는다 — 새 held-out으로 잰다
5. private 평가는 질문·근거·답변이 레포 밖에 남고, `eval/results/` 에는 집계만 들어갔는지

## 위반 검출 (Reviewer 체크리스트)
1. `git diff --name-only` 결과를 packet의 Edit 목록과 대조 — 목록 밖 파일이 있으면 반려
2. 위 상시 Protect 파일이 diff에 있으면 packet에 해제 명시가 있는지 확인
3. 테스트 assert 완화 여부 확인 — 테스트의 검증 의도를 바꾸는 수정은 반려
4. 회사 문자열 검사 — 0건이어야 한다:
   `git diff origin/main... | grep -inEf ~/clinical-rag-private/commit-denylist.txt`
5. 외부 호출 검사 — 새 HTTP 클라이언트·API 키·클라우드 LLM SDK(`anthropic`, `openai`, `google.generativeai` 등) 도입 여부
6. 로컬 전용 자료 검사 — diff에 프로토콜·의뢰사 문서 원문, 개별 질문/답변 원문, 개인정보가 없는지
