# .ai — 에이전트 공용 자산 (도구 비종속)

AI Development Orchestra 워크플로우(Planner/Implementer/Reviewer/Tester)의
공용 규칙과 task packet을 보관한다. 특정 도구(Claude/Codex)에 종속되지 않으며,
각 도구의 진입 파일(CLAUDE.md, AGENTS.md)은 이 폴더를 참조만 한다.

**전체 워크플로우 상세 설명: [WORKFLOW.md](WORKFLOW.md)** (지시 체인, 역할 배치, Orca 명령, 함정 목록)

```
.ai/
├── rules/
│   ├── common.md    # 🔵 공용: 규범 우선순위, 역할, Orchestration 프로토콜, workspace 수명주기
│   ├── reviewer.md  # 🔵 공용: Reviewer 차터 (read-only, APPROVE/REQUEST_CHANGES)
│   ├── tester.md    # 🔵 공용: Tester 차터 (게이트 실행, PASS/FAIL + 증빙)
│   ├── project.md   # 🟠 프로젝트별: 경로·브랜치·빌드/테스트 명령·코드 컨벤션
│   └── scope.md     # 🟠 프로젝트별: 상시 Protect 목록 (+ 공용 위반검출 체크리스트)
├── templates/
│   └── packet.md    # task packet 템플릿 (배경/할 일/Scope/완료 조건/제약/보고)
└── packets/
    └── <YYYY-MM-DD-slug>/
        ├── packet.md   # dispatch한 spec 원본
        ├── report.md   # worker 보고 + Reviewer 판정
        └── evidence/   # 실행 산출물 (로그·응답·xlsx) — .gitignore 대상
```

## 워크플로우

기본 workspace는 **계획·통합 전용**이며 base는 항상 최신 `origin/main`다.
구현은 반드시 별도 workspace에서 한다. 상세 규칙: [rules/common.md](rules/common.md#작업-공간-workspaces)

1. **Planner**(coordinator)가 templates/packet.md 를 복사해 packets/<id>/packet.md 작성
   (헤더에 통합 대상 브랜치와 통합 방식 명시)
2. 작업용 workspace를 **새로** 만든다 — `--base-branch origin/main`, worker 1명
3. `orca orchestration task-create --spec "$(cat packets/<id>/packet.md)"` → `dispatch --to <worker> --inject`
4. **Implementer**(worker)가 Edit 목록 안에서 구현·테스트하고 **worker_done 보고** (커밋하지 않는다)
5. **Reviewer**가 diff·테스트 실물 검증 + scope.md 체크리스트 수행, packets/<id>/report.md 기록
6. 게이트 통과 후 **coordinator가 그 workspace 안에서 커밋** → 기본 workspace가 **merge/cherry-pick으로 통합** → PR
7. 통합된 workspace와 브랜치를 **회수**한다 (공식: "delete merged worktrees aggressively")

## 다른 프로젝트로 확산

🔵 **공용 파일은 그대로 복사**, 🟠 **프로젝트별 파일은 새로 작성**한다.
블로그 원칙(프로젝트 내 `.ai`, 도구 비종속)을 지키면서 중복 관리 대상만 최소화한 구조다.

```bash
# 1) 공용 4개 복사 (수정 없이)
mkdir -p <target>/.ai/rules <target>/.ai/templates
cp .ai/rules/{common,reviewer,tester}.md <target>/.ai/rules/
cp .ai/templates/packet.md              <target>/.ai/templates/
cp .ai/README.md                        <target>/.ai/

# 2) 프로젝트별 2개는 이 레포 것을 참고해 새로 작성
#    rules/project.md — 경로·기준 브랜치·빌드/테스트 명령·증빙 파일 경로·코드 컨벤션
#    rules/scope.md   — 그 레포의 상시 Protect 목록 (위반 검출 절은 복사 가능)

# 3) 진입점 연결 — 이걸 빼먹으면 에이전트가 .ai 를 아예 읽지 않는다
#    <target>/CLAUDE.md, <target>/AGENTS.md 상단에 ".ai/rules 우선" 참조 섹션 추가

# 4) 레포 위생 설정 (이 레포의 것을 참고)
#    .gitignore  — .ai/packets/**/evidence/, .ai/wip-backup/
#    .gitattributes — gradlew/*.sh/.ai/** eol=lf (core.autocrlf=true 환경)
```

- **`packets/` 는 복사하지 않는다** — 프로젝트 이력이다
- 규칙 개정 시 배포 대상은 🔵 3개(+템플릿)뿐이다. 🟠 는 각 레포가 소유한다
- `common.md` 에 프로젝트 고유 내용을 추가하지 않는다 (추가하면 복사가 다시 깨진다)

## 커밋 정책
- `rules/`, `templates/`, `packets/*/*.md`(packet·report·review) → **커밋한다.**
  블로그가 말한 "공통 규칙과 작업 패킷"의 본체이고, 커밋해야 workspace 생성 시 자동 상속된다
- `packets/*/evidence/`(boot 로그·API 응답·xlsx 등 실행 산출물), `wip-backup/` → **커밋하지 않는다** (.gitignore)

## 역할 분리 수준 (작업 규모에 따라)
- **소형**: coordinator가 Planner+Reviewer 겸임, Implementer 1개 — 2-role
- **대형**: Reviewer(별도 터미널, Implementer와 다른 모델 권장)·Tester 분리 — 4-role.
  Reviewer/Tester는 Implementer worktree에서 read-only로 동작하며 각각
  rules/reviewer.md, rules/tester.md 차터를 따른다. dispatch spec에 "너의 역할은
  Reviewer/Tester, .ai/rules/<role>.md 를 따르라"를 명시한다
