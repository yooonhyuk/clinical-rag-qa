# 프로젝트별 규칙 (clinical-rag-qa)

> **이 파일은 프로젝트마다 새로 작성한다.** `common.md`·`reviewer.md`·`tester.md`·`templates/` 는
> 프로젝트 무관이라 그대로 복사하지만, 아래 항목은 레포마다 다르므로 복사 대상이 아니다.
> 확산 절차는 [../README.md](../README.md#다른-프로젝트로-확산) 참조.

## 프로젝트 식별

| 항목 | 값 |
|---|---|
| 레포 | `yooonhyuk/clinical-rag-qa` (Python 3 / FastAPI / PostgreSQL+pgvector / Ollama / Streamlit, uv) |
| 기본 workspace 경로 | `~/Workspace/personal/clinical-rag-qa` |
| Implementer workspace 루트 | Orca 기본값 (`orca worktree create` 응답의 경로) |
| Orca repo id | `82621f70-ad18-426d-9c6a-c2d1e7c79fa0` (`orca repo list --json` 으로 확인) |
| 기술 정본 | `docs/journey.md`, `docs/decisions/`(ADR), `docs/issues/`, `docs/analysis/` |

## 브랜치 정책

- **기준 base: `origin/main`** — 모든 workspace의 출발점
- 작업 브랜치는 Conventional Commits 접두어를 따른다 (`feat/…`, `fix/…`, `eval/…`, `docs/…`, `chore/…`)
- `main` 에 직접 push 하지 않는다 — 항상 PR. push·PR은 사용자 확인 후

## GitHub 계정 (절대 규칙)

- **개인 계정 `yooonhyuk` 만 쓴다.** 커밋 작성자 `yoonhyuk <dbsgur01@gmail.com>` (레포 로컬 git config)
- 회사 계정은 이 레포에서 절대 쓰지 않는다
- gh: `GH_TOKEN=$(gh auth token --user yooonhyuk) gh …` / push: 레포 로컬 credential helper(설정됨)
- 커밋 트레일러: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## 빌드/테스트

```bash
make lint                # ruff check + format --check (backend tests eval scripts frontend)
make test                # 전체 pytest (integration은 Docker / TEST_DATABASE_URL 없으면 skip)
make test-unit           # tests/unit 만
make test-integration    # PostgreSQL+pgvector (testcontainers 또는 TEST_DATABASE_URL)
make scope-eval          # B6 범위 판별기 held-out (호스트 Ollama 필요)
uv run --project backend pytest <경로>::<테스트>   # 단일 테스트 (게이트 기본형)
```

- **게이트 증빙**: 명령 exit code + pytest 마지막 요약 줄(`N passed, M skipped …`) 인용.
  결과 파일이 필요한 게이트는 `--junitxml=.ai/packets/<id>/evidence/junit.xml` 을 붙이고
  `tests/failures/errors/skipped/timestamp` 를 인용한다 (timestamp가 이번 실행인지 확인)
- 캐시 스킵 문제는 없다. 환경 문제 재시도: `uv sync --project backend --all-extras` 후 1회
- skip 수가 늘었으면 이유를 보고한다 (integration이 조용히 skip된 것을 PASS로 세지 않는다)

## 평가(eval) 작업

- 평가는 `make eval` / `make eval-private` / `make scope-eval`. 결과는 `eval/results/<날짜>_<설정>_<sha>/`
- **평가 결과의 검증은 Tester가 아니라 Reviewer가 한다.** Tester는 명령 실행·exit code·산출물 존재만 본다.
  Reviewer는 분모>0, 카나리아, 같은 색인끼리 비교, 임계값을 held-out 이전에 정했는지,
  집계만 커밋됐는지를 확인한다 (상세: [scope.md](scope.md))
- DB는 일회용 컨테이너만. `crqa_pgdata` 볼륨은 쓰지 않는다
- 결과에 Ollama 버전과 DB 상태(코퍼스별 chunk 수, HNSW/exact)를 남긴다

## 역할 배치 (Orca)

| 역할 | 실행 | 비고 |
|---|---|---|
| Planner/총괄 (coordinator) | Claude Opus 5.5 (기본 workspace) | packet 작성·통합·커밋 |
| Implementer | `claude --model claude-sonnet-5-5` (어려운 작업은 `claude-opus-5-5`) | packet Edit 목록 안에서만 |
| Reviewer | `claude --model claude-opus-5-5`, read-only | 코드 + **평가 결과 검증** |
| Tester | `codex` | 게이트 실행·PASS/FAIL·증빙만 |

Orca 명령 요지 (상세·함정: `orca skills get orchestration`):

```bash
orca worktree create --name <task> --no-parent --agent claude --prompt "<brief>" --json  # 핸들은 startupTerminal.handle
orca terminal create --worktree active --command "codex" --json                           # 같은 workspace에 Tester 추가
orca orchestration task-create --task-title "..." --display-name "..." --spec "$(cat .ai/packets/<id>/packet.md)" --json
orca orchestration dispatch --task <taskId> --to <handle> --inject --json
orca orchestration check --wait --types worker_done,escalation,decision_gate --timeout-ms 1800000 --json
orca worktree rm --worktree id:82621f70-ad18-426d-9c6a-c2d1e7c79fa0::<path> --force --json
```

## 코드 컨벤션

- 커밋 메시지: Conventional Commits (`feat:`, `fix:`, `eval:`, `docs:`, `chore:` …), 영어 제목
- 문서(`docs/`)는 한국어. 결정은 ADR, 실패는 `docs/issues/NNN-*.md` + GitHub 이슈, 경과는 `docs/journey.md`
- 측정하지 않은 것은 "측정 안 함"으로 쓴다. 수치는 결과 폴더로 추적 가능해야 한다
- ruff 설정: `backend/pyproject.toml`

## 상시 Protect

[scope.md](scope.md) 참조 — 이 레포 고유 목록이므로 함께 프로젝트별로 관리한다.

## 로컬 환경 메모

- 로컬 전용 자료는 레포 밖 `~/clinical-rag-private/` (원문·프로토콜·로컬 평가셋·결과 원본). 새 workspace에 따라가지 않으며,
  필요한 packet은 `PRIVATE_DIR` 등 경로를 명시한다
- 호스트 Ollama(Homebrew, 서비스 라벨 `sh.brew.ollama`). 안 떠 있으면
  `launchctl kickstart -k gui/$(id -u)/sh.brew.ollama`
- `.env` 는 gitignore — 새 workspace에는 따라가지 않는다 (`.env.example` 참고)
- `CLAUDE.md` · `AGENTS.md` 는 커밋되어 있어 workspace에 자동 상속된다
