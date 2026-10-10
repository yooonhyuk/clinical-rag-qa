# Task Packet: <제목>

- **ID:** <YYYY-MM-DD-slug> (packets/ 폴더명과 동일)
- **날짜:** YYYY-MM-DD
- **Planner:** <coordinator 터미널/모델>
- **Implementer:** <worker 터미널 handle/모델>
- **관련:** <GitHub 이슈, 브랜치, 커밋 SHA>
- **Workspace:** <worktree id `<repoId>::<path>` / base = 레포 기준 base (rules/project.md)> <!-- 1작업 1개, 통합 후 회수 -->
- **통합 대상:** 기본 workspace → `<대상 브랜치>` — <통합 방식: merge / cherry-pick> <!-- 필수. rules/common.md "작업 공간" 참조. patch apply 금지 -->

## 배경
<!-- worker는 이 packet 밖의 대화 맥락을 전혀 모른다.
     repo 경로, 브랜치, 관련 커밋, 현재 상태(무엇이 되어 있고 무엇이 안 되어 있는지)를
     여기에 전부 적는다. Planner가 조사한 관련 파일/기존 패턴/제약도 포함. -->

## 할 일
<!-- 번호 목록. 각 항목은 검증 가능한 단위로. 판단 기준이 필요한 항목은 기준까지 명시.
     "실패 시 수정하되 테스트의 검증 의도는 바꾸지 말 것" 같은 가드레일 포함. -->

## Scope
### Read (참고만, 수정 금지)
-
### Edit (수정 허용)
-
### Protect (절대 수정 금지 — .ai/rules/scope.md 상시 목록에 추가로)
-

## 완료 조건 (검증 게이트)
<!-- Reviewer/Tester가 기계적으로 판정할 수 있는 조건.
     테스트 명령과 증빙 파일 경로는 rules/project.md 에 정의된 것을 쓴다. 예:
     - <project.md 의 단일 테스트 명령> "<식별자>" 전부 통과 (결과 파일 타임스탬프·카운트로 증빙)
     - git diff --name-only ⊆ Edit 목록 -->

## 제약
- git commit / push / 브랜치 생성 / checkout / stash 전부 금지 (커밋은 게이트 통과 후 coordinator가 수행)
- Edit 목록 밖 수정 필요 시 **`orca orchestration ask`** 로 질문 (임의 수정 금지, escalation은 "막혔다" 신호)
- 의미 있는 체크포인트마다 `orca worktree set --worktree active --comment "..." --json` 갱신

## 보고 (`worker_done`)
`--outcome succeeded|failed` + `--task-id` + `--dispatch-id` + `--files-modified` 필수.
실패해도 정확히 1회. 상세: `.ai/rules/common.md` Orchestration 프로토콜

body에 포함할 것:
- 수행 결과 요약 (테스트별 pass/fail 수)
- 수정한 파일과 각각의 이유
- 발견한 리스크 / 후속 작업 제안 / 남은 것
