# Task Packet: EmbeddingGemma 2 vs bge-m3 (Ollama 0.40.2 기준선 재측정 포함)

- **ID:** 2026-10-10-embeddinggemma2
- **날짜:** 2026-10-10
- **Planner:** coordinator (Claude Opus 5.5, 기본 workspace)
- **Implementer:** Claude Sonnet 5.5 (`orca orchestration worker-start --agent claude --model claude-sonnet-5-5`)
- **관련:** ADR 0002, 이슈 001(GitHub #1), 이슈 011(#12), 이슈 009(#10), base `3342ce5`
- **Workspace:** 새 top-level worktree `embeddinggemma2` (repo `82621f70-ad18-426d-9c6a-c2d1e7c79fa0`) / base = `origin/main`
- **통합 대상:** 기본 workspace → `main` — PR (rebase merge)

## 배경
- 레포: `~/Workspace/personal/clinical-rag-qa`. 규칙은 `.ai/rules/*`(특히 scope.md의 절대 금지·평가 규칙).
- 현재 embedding은 `bge-m3`(1024d, 접두어 없음, ADR 0002). 지금까지의 수치는 **Ollama 0.24.0** 결과이고, 호스트 Ollama는 2026-10-10 **0.40.2**로 올렸다. 서로 다른 Ollama 버전의 결과를 비교하지 않으므로 bge-m3 기준선부터 다시 잰다.
- 후보: `embeddinggemma-2:270m`(텍스트 전용, 378MB), `embeddinggemma-2:740m`(1.3GB). **둘 다 이미 호스트 Ollama에 있다.** 새로 받지 않는다.
  - 768d, Matryoshka 512/256/128. 접두어: 질의 `task: search result | query: {q}`, 문서 `title: {t} | text: {c}`(제목이 없으면 `title: none`).
  - 한국어 개별 성능은 공개되지 않았고, bge-m3와 직접 비교한 수치도 없다. 그래서 이 측정이 필요하다.
- 코드 현황:
  - `backend/app/config.py`의 `KNOWN_EMBEDDING_MODELS`(`EmbeddingModelSpec(dim, query_prefix, document_prefix)`)와 `embedding_service.py`가 접두어를 **고정 문자열**로 붙인다. 따라서 문서 접두어 `title: none | text: `는 지금 코드로 된다. 문서별 실제 제목을 넣으려면 코드를 바꿔야 한다.
  - Matryoshka 절단은 지원하지 않는다(`ollama_client.embed`는 `model`·`input`만 보냄).
  - 차원을 바꾸면 `make reset-embeddings`로 DB 열 크기를 바꾸고 재색인해야 한다.
- **모델에 묶인 임계값 2개:** `min_relevance_score=0.45`(cosine 게이트)와 `scope_margin=0.056`(B6 kNN 판별기, 예시만으로 leave-one-out Youden J, bge-m3 기준). 새 모델의 cosine 분포는 다르므로, 각 모델에서 **dev 또는 예시만으로** 다시 정해야 공정한 비교가 된다.
- 평가 명령: `make eval CORPUS=toy|public`, `make eval-private PRIVATE_DIR=~/clinical-rag-private`, `make scope-eval`. `eval/run_eval.py`는 `--label`, `--vector-search exact`, `--min-relevance-score`, `--reindex` 등을 지원한다. 지난 비용: public 1회 약 12분, private 색인 약 12분 30초 + 1회 약 30분.
- DB: 모델마다 **일회용** pgvector 컨테이너를 쓴다(`crqa_pgdata` 금지). 색인 상태(코퍼스별 chunk 수, HNSW/exact)를 결과에 남긴다. 이슈 009 때문에 모델 비교는 `--vector-search exact`로 한다.

## 할 일
### Phase 0 — bge-m3 기준선 (Ollama 0.40.2)
1. 일회용 DB에서 toy·public·private를 색인한다. bge-m3 embedding이 0.24.0 때와 같은지 표본 chunk 20개의 cosine으로 확인해 보고한다(같은 결과일 필요는 없고, 차이만 보고).
2. exact 검색으로 toy 1회, public 2회, private 1회, `make scope-eval` 1회를 돌린다. 생성 모델은 gemma4:e4b, reranker는 끈다.
3. **중간 확인 (blocking)**: Phase 0이 끝나면 결과 요약을 preamble의 `ask` 명령으로 coordinator에게 보내고 답을 기다린다. 0.24.0 결과와 크게 다르면(public hit@5 ±2%p 초과 등) 그 사실을 맨 앞에 쓴다.

### Phase 1 — 지원 코드 (최소 변경)
4. `KNOWN_EMBEDDING_MODELS`에 `embeddinggemma-2:270m`·`:740m`(768d, 위 접두어, 문서 접두어는 `title: none | text: `)을 추가한다.
5. Matryoshka 절단 설정 `EMBEDDING_TRUNCATE_DIM`(기본 None)을 추가한다. 먼저 Ollama 0.40.2 `/api/embed`가 `dimensions` 파라미터를 지원하는지 실제 호출로 확인한다. 지원하면 그 값을 보내고, 지원하지 않으면 클라이언트에서 앞 N차원을 자른 뒤 L2 정규화한다. 어느 쪽을 택했는지 근거와 함께 보고한다.
6. 단위 테스트: 접두어 적용, 절단 후 차원·노름 1, 알 수 없는 차원 조합 거부. 기존 테스트 455개는 모두 통과해야 한다.

### Phase 2 — 측정
7. 설정 4개를 같은 절차로 잰다: 270m·768d, 740m·768d, 그리고 768d에서 더 나은 쪽의 512d·256d.
8. 각 설정에서 임계값을 다시 정한다. **held-out은 보지 않는다.**
   - `scope_margin`은 `scope_exemplars.yaml` 예시만으로 leave-one-out(bge-m3 때와 같은 방법, k=3)으로 정한다.
   - `min_relevance_score`는 게이트를 끈 실행(`--min-relevance-score -1`)에서 `eval/tune_gate.py`와 같은 dev 분할(toy 전부 + public 짝수 번째)과 사전 등록 목적함수로 정한다. 목적함수는 실행 **전에** packet 보고에 적는다.
9. 측정 범위:
   - 4개 설정 모두: 검색 단계 지표(file hit@5, 섹션 hit; toy/public/private)와 `make scope-eval`.
   - 768d 중 나은 1개 + 그 512d·256d: 생성까지 포함한 toy/public 2회, private 1회.
   - 시간도 기록한다: 색인 시간, 질문 embedding p50, 메모리.
10. 비교표를 만든다: bge-m3(0.40.2) 대 각 설정. 지표는 hit@5, 섹션 hit, Citation, Keyword, 거절 정확도, 오거절, B6 P/R/오거절, 지연이다.

### Phase 3 — 문서
11. ADR 0002에 "2026-10 재평가" 절을 추가한다. 채택·불채택과 근거를 적고, 기본값 변경은 coordinator 승인 후에만 한다.
12. `docs/journey.md` §14와 README 결과 표를 갱신한다. 측정하지 않은 것(문서 실제 제목 접두어, 128d, 740m의 멀티모달)은 "측정 안 함"으로 표시한다.

## Scope
### Read (참고만, 수정 금지)
- `docs/**`(아래 Edit 제외), `eval/eval_metrics.py`, `eval/tune_gate.py`, `eval/compare_search_modes.py`, 기존 `eval/results/**`
- `~/clinical-rag-private/eval/protocol_questions.yaml`(로컬 실행에만 사용)
### Edit (수정 허용)
- `backend/app/config.py`, `backend/app/services/embedding_service.py`, `backend/app/services/ollama_client.py`
- `tests/unit/**`(새 테스트 추가, 기존 assert 완화 금지)
- `eval/results/<새 폴더>/**`(집계만), `eval/run_eval.py`·`eval/run_scope_eval.py`(라벨·차원 기록이 필요할 때만)
- `docs/decisions/0002-embedding-model.md`(절 추가만), `docs/journey.md`, `README.md`, `.env.example`
- `.ai/packets/2026-10-10-embeddinggemma2/report-implementer.md`, `.ai/packets/2026-10-10-embeddinggemma2/evidence/`(evidence는 gitignore됨, 실행 로그·junit). `packet.md`는 coordinator 소유라 수정 금지
### Protect (scope.md 상시 목록에 추가로)
- `backend/app/rules/scope_exemplars.yaml`(예시 문장 수정 금지, margin 재계산만 허용)
- 기본 embedding 모델 값(`ollama_embedding_model="bge-m3"`) — 채택 결정 전 변경 금지
- Alembic 마이그레이션 추가 금지(차원은 `reset-embeddings`로)

## 완료 조건 (검증 게이트)
- Tester: `make lint`, `make test` 모두 exit 0. `--junitxml=.ai/packets/2026-10-10-embeddinggemma2/evidence/junit.xml`의 tests·failures=0·errors=0·timestamp를 인용한다(skip 수 증가 시 이유).
- Tester: Phase 2의 각 결과 폴더가 있고 `summary`의 분모가 0보다 큰지 확인한다(존재·분모만 본다).
- Reviewer: scope.md의 평가 규칙 1~5와 위반 검출 1~6을 확인한다. 특히 임계값이 dev 또는 예시만으로 정해졌는지, 모든 비교가 exact·같은 Ollama 버전인지, private 결과가 집계만 커밋되는지 본다.
- `git diff --name-only` ⊆ Edit 목록

## 제약
- git commit / push / 브랜치 생성 / checkout / stash 전부 금지(커밋은 게이트 통과 후 coordinator가 한다)
- **모델·패키지 다운로드 금지**(필요한 모델은 이미 있음). 외부 LLM API 금지
- Edit 목록 밖 수정이 필요하면 `orca orchestration ask`로 묻는다
- 의미 있는 체크포인트마다 `orca worktree set --worktree active --comment "..." --json`
- 질문은 preamble의 `ask` 명령, 완료는 preamble의 `worker_done` 명령을 그대로 쓴다(인자를 재구성하지 않는다)
- 이 worktree의 브랜치 이름은 신경 쓰지 않는다(push 전에 coordinator가 바꾼다)
- 호스트 수면에 주의한다. 긴 실행은 `caffeinate -i`로 감싼다(지난 private 실행이 수면으로 중단됨)

## 보고 (`worker_done`)
preamble의 명령으로 `--outcome succeeded|failed`, 3문장 요약, `--files-modified`를 넣어 정확히 1회 보낸다(실패해도). 상세 보고는 `.ai/packets/2026-10-10-embeddinggemma2/report-implementer.md`에 쓰고 `--report-path`로 넘긴다.
body에 넣을 것: Phase별 결과 요약과 비교표, 정한 임계값과 그 방법, `dimensions` 지원 여부, 수정 파일과 이유, 남은 것.
