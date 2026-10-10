# 공용 규칙 (모든 에이전트 공통)

이 파일은 도구 비종속 공용 규칙이다. Claude Code(CLAUDE.md), Codex(AGENTS.md) 등
어떤 에이전트든 이 규칙을 우선 적용한다. 도구별 파일에는 이 파일 참조만 남긴다.

> **이 파일은 프로젝트 무관이다 — 다른 프로젝트로 그대로 복사한다.**
> 빌드 명령·경로·브랜치·Protect 목록 등 레포마다 다른 것은 [project.md](project.md) 와
> [scope.md](scope.md) 에 있다. 이 파일에 프로젝트 고유 내용을 추가하지 말 것.

## 규범 우선순위 (충돌 시 판단 기준)

1. **AI Development Orchestra 블로그** — 1차 규범.
   [keyflow.me @ekyu, "혼자 일하는 AI는 끝났다"](https://www.keyflow.me/ko/@ekyu/post/2026-07-10-%ED%98%BC%EC%9E%90-%EC%9D%BC%ED%95%98%EB%8A%94-ai%EB%8A%94-%EB%81%9D%EB%82%AC%EB%8B%A4-ai-development-orchestra-13)
   - 역할 분리: 기획(Planner) / 구현(Implementer) / 검토(Reviewer) / 테스트(Tester)
   - 작업 범위(Read/Edit/Protect) 제어
   - 오케스트레이션이 모델 성능보다 우선
   - 도구 종속 회피: 공통 규칙과 작업 패킷을 프로젝트 내 `.ai` 폴더에 구조화
2. **Orca 공식 지침** — 2차 규범. 블로그가 다루지 않는 **workspace 운영과 worker 프로토콜**의 근거.
   - **1순위 출처: 바이너리 내장 version-matched 지침** — `orca skills get orchestration`,
     `orca skills get orca-cli`. 에이전트 행동 지침이므로 이 레포 규칙에 직접 적용된다
   - 2순위: [onorca.dev/docs](https://www.onorca.dev/docs) (제품 모델·사람용 UX 문서)
   - **둘이 갈리면 내장 지침을 따른다.** 실제로 worktree 생성 정책에서 갈린다 (아래 참조)
3. **충돌 시 블로그 > 공식 문서 > 팀 관행.**
   블로그가 침묵하는 영역에서만 공식 문서가 결정력을 갖고, 둘 다 침묵할 때만 관행으로 정한다.

> `.ai` 하위 구조(rules/templates/packets), packet 필드 규격, 커밋 정책 세부는 블로그에 없다 —
> 이 레포의 자체 결정이며, 블로그 원칙(도구 비종속·스코프 제어)에 어긋나지 않는 범위에서 유지한다.
>
> ⚠️ 출처 불명 지침을 규칙으로 승격하지 않는다. "Worker가 구현·테스트·**커밋**한다"는 6단계 패턴을
> 한때 채택했으나, 블로그에도 공식 문서에도 근거가 없고 공식 worker 프로토콜과 어긋나 철회했다
> (2026-07-30). 공식 모델은 **worker = 변경 + 보고, 커밋은 diff 리뷰 후**다.

## 역할 규칙 (AI Development Orchestra)
- **Planner/Reviewer** (coordinator): packet 작성, task dispatch, diff 리뷰, 검증 게이트 판정
- **Implementer** (worker): packet의 Edit 목록 안에서만 수정.
  **git commit / push / 브랜치 생성 / 다른 브랜치 checkout / stash 전부 금지**
  - 완료 조건은 **구현 + 테스트 + `worker_done` 보고**까지다.
    공식 프로토콜대로 `--outcome`(실패해도 정확히 1회), `--body`(무엇을 했고 무엇이 남았는지),
    `--files-modified` 를 채워 보고한다
  - **커밋은 게이트 통과 후 coordinator가 해당 workspace 안에서 수행한다.**
    그러면 그 workspace 브랜치에 커밋이 쌓이고, 기본 workspace는 **그 브랜치를 merge/cherry-pick으로만** 통합한다
  - ❌ 메인 checkout에 uncommitted 로 얹어 수동 `patch apply` 하지 않는다.
    이 방식은 workspace를 재사용하던 시절의 이관 수단이며, 1작업 1 workspace를 지키면 필요가 없다
    (파일 단위 채택 판단과 CRLF 노이즈를 사람이 떠안게 됨 — 2026-07-28 실측)
- 완료 주장은 반드시 **실물로 증빙**한다: 빌드는 exit code, 테스트는 결과 파일의 타임스탬프·카운트 확인
  (증빙 파일 경로와 테스트 명령은 [project.md](project.md) 에 정의)

## Orchestration 프로토콜 (내장 지침 준수 — 모든 역할)

### worker → coordinator 보고
```bash
orca orchestration send --to <coordinator handle> --type worker_done \
  --outcome succeeded|failed --task-id <taskId> --dispatch-id <dispatchId> \
  --subject "<한 줄>" --body "<무엇을 했고/찾았고/무엇이 남았는지>" \
  --files-modified "<경로,경로>" --json
```
- **`worker_done` 은 실패해도 정확히 1회 보낸다.** `--outcome` 필수
- **`taskId` + `dispatchId` 를 반드시 함께 넣는다** — 없으면 stale 재시도가 엉뚱한 dispatch를 완료시킬 수 있다.
  터미널 핸들 비교로 provenance를 판정하지 않는다 (재시작하면 핸들이 바뀜)
- **구체 coordinator 핸들로 보낸다.** `@all` 등 그룹 주소로 lifecycle 메시지를 보내지 않는다
- `worker_done` 은 자기 터미널에서 보낸다 (다른 pane에서 보내면 런타임이 무시)
- **`worker_done` 뒤에 `task-update --status completed` 를 붙이지 않는다** — 자동 완료 처리된다

### 질문은 `escalation` 이 아니라 `ask`
- **`ask`** = coordinator에게 **블로킹 질문**. 답을 직접 반환한다. Edit 목록 밖 수정이 필요할 때 이것을 쓴다
  ```bash
  orca orchestration ask --to <coordinator handle> --question "<질문>" [--options <csv>] --json
  ```
- **`escalation`** = "막혔다(I'm stuck)" 신호. 질문 용도가 아니다
- `gate-create` 는 **coordinator가 자기 DAG 결정을 걸 때만** 쓴다 — worker의 `ask` 응답용이 아니다

### coordinator 대기 규칙
- `check --wait --types worker_done,escalation,decision_gate --timeout-ms <n>` 로 대기한다 (sleep/poll 루프 금지)
- **타임아웃이나 `{count:0}` 은 체크포인트이지 실패가 아니다.** 코딩 작업은 통상 15~60분 걸린다
- **하트비트·터미널 활동은 "살아있다"는 뜻이지 "끝났다"가 아니다 — 그 이유로 worker를 죽이거나 재시작하지 않는다**
- `check --wait` 는 **한 번에 메시지 하나**를 반환한다. worker N명이면 N회 루프
- `decision_gate` 는 `orca orchestration reply --id <msg_id> --body <답> --json` 로 답하고 계속 대기
- **한 task에서 3회 연속 실패하면 dispatch가 circuit-break 되어 task가 `failed` 로 바뀐다** — 무한 재시도 금지
- 통합 준비가 끝나면 `--type merge_ready` 로 알린다

### supervised vs full handoff
- 이 레포의 기본은 **supervised orchestration** (사용자가 오케스트레이션을 요청한 맥락)
- 단 사용자가 "hand off / 넘겨라 / 다른 에이전트가 맡아라" 로 **소유권 이전**을 요청하면 full handoff다 —
  이때는 `task-create` / `dispatch --inject` / `check --wait` 를 **쓰지 않고** 프롬프트만 전달하고 감시를 멈춘다
- review-only `worker_done` 은 **coordinator의 파일 수정 권한을 주지 않는다.**
  리뷰 결과는 종합해서 **재dispatch 하거나 지정된 소유자에게 넘긴다**

## 작업 공간 (Workspaces)

근거: Orca 공식 문서. 아래 세 인용이 이 절 전체의 출처다.

> "Instead of branching and stashing on one checkout, **every task gets its own on-disk copy of the repo**
> via `git worktree`." — [docs/model/worktrees](https://www.onorca.dev/docs/model/worktrees)
>
> start-from ref 선택: **"The repo's base ref (the fast path)"** / 다른 로컬 브랜치는
> "useful for **stacking work on top of a PR in review**" (예외 용도) — 같은 문서
>
> "**Delete merged worktrees aggressively.** Orca makes this cheap — one click, worktree and branch both
> gone. Leaving dozens of merged worktrees around just slows down the palette."
> — [docs/recipes/jump-worktrees](https://www.onorca.dev/docs/recipes/jump-worktrees)

### 기본 Workspace = 계획·통합 전용
경로와 기준 브랜치는 [project.md](project.md) 참조 (Orca "기본" workspace)

- 역할은 **packet 작성 / 리뷰 / merge / PR / 릴리즈**뿐이다. **여기서 구현하지 않는다**
  - 예외: **사용자가 명시적으로 기본 workspace에서 작업하라고 지시한 경우.**
    에이전트가 규모·난이도("이건 한 줄이니까")를 근거로 스스로 예외를 판단하지 않는다 —
    작업 요청이 오면 기본은 새 workspace 생성이다
- **base는 항상 레포의 최신 기준 브랜치**(`project.md` 의 기준 base). feature 브랜치를 base로 두지 않는다
  - 작업 시작 전 `git fetch origin && git switch <base> && git merge --ff-only origin/<base>`
  - 통합 대상이 다른 브랜치여도 기준점은 base이며, 대상 브랜치는 merge 시점에만 checkout 한다
- **워킹트리를 항상 clean 하게 유지한다.** 구현 WIP를 두지 않는다
  - 구현이 필요해지면 그 자리에서 하지 말고 새 workspace를 만든다
  - 공식 문서가 "branching and stashing on one checkout"을 **대비되는 안티패턴으로 제시**한 그 상태다
  - WIP가 상주하면 브랜치 전환마다 stash/restore 마찰이 생기고, 상위 버전이 이미 반영됐는지조차 늦게 발견된다
    (2026-07-27~30 실측: video mask WIP가 3일간 stash/backup/이관을 돌다 결국 폐기됨)

### Implementer Workspace = 1작업 1개, 일회용
경로 루트는 [project.md](project.md) 참조

> ⚠️ **이 규칙은 사용자의 상시 요청에 근거한다.** 내장 지침의 기본값은 정반대다 —
> *"`Fresh worker` means a fresh agent session, **not a new git worktree**"*,
> *"Create a new worktree only when **the user explicitly requests one** or a concrete checkout or
> filesystem conflict makes sharing unsafe. Independent tasks, parallel execution, convenience, or a
> preference for separate checkouts are **not** isolation requirements."*
> 사용자가 1작업 1 workspace를 명시 요청했으므로 그 예외 조건을 충족한다.
> **단 에이전트가 자기 판단으로 추가 worktree를 만들지 않는다** — 필요하면 근거를 먼저 말하고 승인받는다.
> 같은 workspace에 worker를 더 붙일 때는 worktree가 아니라 터미널을 추가한다:
> `orca terminal create --worktree active --command "codex" --json`

- **작업 하나마다 새로 만든다.** 상시 worker석으로 재사용하지 않는다
- **생성은 agent-first 한 줄로 한다** (내장 지침: bare create 후 `terminal create --command <agent>` 는
  **명시된 안티패턴**):
  ```bash
  orca worktree create --name <task-name> --no-parent --agent codex --prompt "<brief>" --json
  ```
  - 이후 **핸들은 응답의 `startupTerminal.handle` 하나만** 쓴다. `terminal_handle_stale` 나면
    `orca terminal list --worktree id:<repoId>::<path> --json` 로 재해석 — **구/신 핸들 동시 전송 금지**
- **`--base-branch`는 생략(레포 기본 base)하거나 명시적으로 `origin/main`.**
  내장 지침 문언: *"**never base it on the current feature branch** unless the user asks for stacked work
  or 'branch from current'. Put current-branch context in the prompt instead."*
  (실측 사례: base를 feature 브랜치로 준 탓에 base drift → 강제 리셋, 2026-07-28)
  - `--no-parent` 는 Orca lineage만 정하고 **Git base를 정하지 않는다** — 별개로 판단할 것
- worker 한 명 + 명확한 완료 조건을 준다 (packet 필수)
- **진행 상태를 Orca에 반영한다** (내장 지침: 의미 있는 체크포인트마다 갱신):
  ```bash
  orca worktree set --worktree active --comment "fix 구현 완료; 게이트 실행 중" --json
  orca worktree set --worktree active --workspace-status in-review --json   # todo|in-progress|in-review|completed
  ```
- **통합이 끝나면 회수한다** — raw git 대신 Orca 명령을 쓴다 (추적 상태까지 정리됨):
  ```bash
  orca worktree rm --worktree id:<repoId>::<path> --force --json
  ```
- 여기서의 변경은 검증(Reviewer APPROVE + Tester PASS) 후 기본 workspace가 통합하기 전까지
  어디에도 반영된 것이 아니다

### 공통
- `.ai/`는 레포에 커밋되어 있으므로 workspace 생성 시 자동으로 따라간다 — **수동 복사 금지**
- 모든 packet은 헤더에 **통합 대상 브랜치와 통합 방식(merge/cherry-pick)** 을 명시한다
  (템플릿의 "통합 대상" 항목). 없으면 worker/reviewer는 `orca orchestration ask` 로 확인한다
- 통합 후 기본 workspace에서 게이트를 재실행하는 것이 원칙이다

## Scope
- 작업 범위(Read/Edit/Protect)는 각 task packet에 정의한다. 상시 보호 목록은 [scope.md](scope.md) 참조
- packet의 Edit 목록에 없는 파일을 수정해야 하는 상황이면, 수정하지 말고 **`orca orchestration ask`** 로
  coordinator에 물어본다 (`escalation` 은 "막혔다" 신호이지 질문 채널이 아니다 — 위 프로토콜 절 참조)
