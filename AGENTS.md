# 에이전트 진입점

이 레포의 모든 에이전트 규칙은 `.ai/` 에 있다. **작업 전에 아래를 읽고 우선 적용한다.**

1. [.ai/rules/common.md](.ai/rules/common.md) — 역할, Orchestration 프로토콜, workspace 수명주기
2. [.ai/rules/project.md](.ai/rules/project.md) — 경로, 기준 브랜치(`origin/main`), 게이트 명령, GitHub 계정, 역할 배치
3. [.ai/rules/scope.md](.ai/rules/scope.md) — 절대 금지(외부 LLM API, 승인 없는 다운로드, 로컬 전용 자료), 상시 Protect, 평가 규칙
4. 역할이 Reviewer/Tester면 [.ai/rules/reviewer.md](.ai/rules/reviewer.md) / [.ai/rules/tester.md](.ai/rules/tester.md)
5. task packet: `.ai/packets/<id>/packet.md` (템플릿 [.ai/templates/packet.md](.ai/templates/packet.md))

기술 정본은 `docs/journey.md`, `docs/decisions/`, `docs/issues/`, `docs/analysis/` 다.
이 파일에는 규칙을 추가하지 않는다 — `.ai/rules/` 를 고친다.
