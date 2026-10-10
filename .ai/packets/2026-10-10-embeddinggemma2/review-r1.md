# Review r1 — 2026-10-10-embeddinggemma2

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: working tree diff (base `origin/main` 3342ce5) + untracked 파일
- 입력: `packet.md`, `report-implementer.md`, `eval/results/2026-10-10_*`, `evidence/`

## 판정: REQUEST_CHANGES (문서만 고치면 됨)

코드, 평가 절차, 데이터 규칙은 통과다. 막는 이유는 ADR 0002, journey §14, report의 결론 문장 몇 곳이
수치와 맞지 않거나, 이미 잰 측정을 "구분하지 못함"으로 적은 것이다. 아래 R1~R4를 고치면 APPROVE한다.
R5 이하는 권고다.

## 반려 항목

| # | 위치 | 문제 | 고칠 방향 |
|---|---|---|---|
| R1 | `docs/decisions/0002-embedding-model.md:99` (표 `:94`), `report-implementer.md:64` | "256d의 443초는 같은 호스트의 변동 안인지 구분하지 못했습니다"라고 적었다. 그런데 절전 뒤 다시 만든 DB에서 256d를 다시 색인했고(`evidence/index_rr256_*.json`), 그 시간이 private **288.5 s**, public **76.1 s**다. 768d·512d(288 s / 76 s)와 같다. 따라서 이미 잰 측정이 있고, 443 s는 호스트 변동이었다고 말할 수 있다 | 재색인 288.5 s를 쓰거나 두 값을 함께 적는다. 443 s는 첫 색인(17:32~17:40)의 변동이라고 밝힌다. "구분하지 못했다"는 문장은 지운다 |
| R2 | `docs/decisions/0002-embedding-model.md:96`, `docs/journey.md:109`, `report-implementer.md:67` | "256d가 가장 낮다"가 지표를 밝히지 않아 일부가 틀리다. hit@5에서 private 최저는 **768d 68.8**이다(256d는 70.3). public 최저는 **512d 91.1**이다(256d = 768d = 92.4). journey의 문장은 hit@5를 말하는 문장 바로 다음에 와서 그대로 틀리게 읽힌다. 256d가 모든 코퍼스에서 최저인 것은 **섹션 hit**(84.2 / 79.7 / 31.2)와 toy hit@5뿐이다 | 예: "섹션 hit는 256d가 모든 코퍼스에서 가장 낮고, hit@5는 세 설정이 1~2문항 안에서 엇갈린다" |
| R3 | `docs/decisions/0002-embedding-model.md:103` | "이득은 모델 크기(약 1/3)"가 어느 크기인지 밝히지 않는다. 1/3은 **디스크**(`ollama list` 378 MB / 1.2 GB = 0.31)에만 맞는다. 표의 `ollama ps` **적재 메모리**(346 / 673 MB)로는 약 **1/2**이다. 같은 절에서 두 기준을 섞었다. 같은 줄의 "질문 embedding 지연(약 3ms)"도 실제 차이 16.9 − 13.3 = **3.6 ms**와 맞지 않는다 | "디스크 약 1/3, 적재 메모리(`ollama ps`) 약 1/2, 질문 embedding p50 3.6 ms 차이" |
| R4 | `docs/decisions/0002-embedding-model.md:98` | "Citation 정확도… (85 → 91~93%)"는 256d(88.9 / 90.3)를 빠뜨렸다. bge-m3 (b)도 85.3 / 86.7이다 | "85~87% → 89~93%" |

## 권고 (비차단)

- R5 `docs/decisions/0002-embedding-model.md:73`, `docs/journey.md:108`: "740m은 vision·audio 타워만 추가된 모델이고 텍스트 경로의 가중치는 같습니다"는 단정이다. 실제로 확인한 것은 두 가지다. 하나는 `ollama show`의 capability(740m: embedding/vision/audio, 270m: embedding)이고, 다른 하나는 6개 입력에서 출력이 비트 단위로 같다는 것이다. 가중치를 직접 비교하지는 않았다. "출력이 같으므로 텍스트 경로가 같은 것으로 보인다"처럼 추정으로 적는 것이 좋다.
- R6 `docs/decisions/0002-embedding-model.md:97`: "B6는 270m이 더 약합니다"는 정밀도와 오거절 기준으로는 맞다. 다만 256d의 재현율이 96.0으로 bge-m3의 92.0보다 높으니 한 마디 덧붙이면 좋다.
- R7 `README.md:386`: "적재 메모리"에 `(ollama ps)`를 붙이면 ADR 표와 기준이 같아진다. ADR `:99`는 이미 디스크와 메모리를 구분해 적어서 문제없다.
- R8 `report-implementer.md` 표의 "검색 p50 public"은 두 실행 중 **작은 값**을 골랐다. (b): 69 / 68 → 68, c1: 66 / 64 → 64. 생성 p50은 1회 값을 썼다. 기준을 하나로 맞추거나 표에 적는다. ADR과 README에는 이 행이 없어 영향은 report에만 있다.
- R9 `tests/integration/test_embedding_truncation_live.py`: 모듈을 불러올 때 `localhost:11434`에 연결을 시도한다(최대 2초). `OLLAMA_BASE_URL`을 따르지 않는다. 동작에는 문제없다.
- R10 결과 `config.json`의 `git_commit`이 `3342ce5`로 기록된다. 실제 실행 코드는 커밋하지 않은 working tree다(기존과 같은 한계). 커밋 메시지에 이 사실을 적어 두면 추적할 수 있다.
- R11 `2026-10-10_scope-b6_bge-m3_*`(Phase 0, 16:24)는 같은 이름의 (b) 실행(20:00)으로 덮어써졌다. 같은 날 만든 새 폴더라 상시 Protect 위반은 아니다. 두 실행은 결정적이라 값도 같다. 다만 Phase 0 원본이 남지 않았다는 것은 알아 둔다.

## 체크리스트 결과

### scope.md 위반 검출 1~6
1. **Edit 목록**: tracked diff 12개 파일은 모두 Edit 목록 안이거나 승인된 예외다(`container.py` 1줄). untracked는 `eval/results/2026-10-10_*` 신규, `eval/tune_cosine_gate.py`(승인), `tests/integration/test_embedding_truncation_live.py`(승인), `tests/unit/test_tune_cosine_gate.py`(tests/unit), `.ai/packets/`다. 통과.
2. **Protect**: `scope_exemplars.yaml`, `corpus/**`, held-out yaml, 기존 `eval/results/**`, `pyproject`/`uv.lock`, compose, offline-bundle, Alembic에 변경이 없다. 기본 `ollama_embedding_model="bge-m3"`와 `min_relevance_score` / `scope_margin` 기본값도 그대로다. ADR은 절만 추가했다. 통과.
3. **테스트 assert 완화**: tests diff에 삭제된 줄이 0줄이고 전부 추가다. 새 테스트는 `dimensions`를 절단할 때만 보내는지, `think`의 기본값이 False이고 True도 보낼 수 있는지, 알 수 없는 조합을 거부하는지 검증한다. 통과.
4. **회사 문자열**: `git diff origin/main... | grep -inEf ~/clinical-rag-private/commit-denylist.txt` 결과 **0건**이다(`git diff origin/main`도 0건). evidence를 뺀 untracked 파일의 내용과 경로도 **0건**이다. 통과.
5. **외부 호출**: 새 SDK가 없다. `run_eval.ollama_version()`은 `urllib`로 **로컬 Ollama** `/api/version`만 부르고, live 테스트는 localhost만 부른다. 통과.
6. **로컬 전용 자료**: `eval/results/*private-protocols*` 5개 폴더는 `config` / `summary` / `diagnostics` / `report`로만 이뤄져 있다. JSON에는 40자를 넘는 자유 텍스트도 한글도 없다(해시와 인덱스 DDL만 있음). `report.md`에도 한글이 없다. 들어 있는 것은 문항 id(r01…), 실패 유형, ClinicalTrials.gov 파일명뿐이고, 이는 `origin/main`의 `2026-10-09_private-protocols_*`와 같은 형식이다. 질문, 근거, 답변 원문은 없다. 통과.

### 평가 규칙 1~5
1. **임계값은 dev나 예시만으로 정했다**
   - `tune_cosine_gate.py`는 `tune_gate.split`의 `assignment == "dev"` 행만 `dev`에 넣는다. test 행은 `n_test` 개수만 센다. 입력 run도 toy와 public gate-off뿐이다(각 `cosine-gate_*/summary.json`의 `runs`). `dev_questions=77`, `test_questions_not_read=47`.
   - `scope_margin`은 기존 `run_scope_eval.py`가 예시만으로 LOO(k=3)해 구한 값이다. 각 eval `config.json`의 `scope_margin`과 `min_relevance_score`는 해당 tuning 결과와 일치한다(0.0198 / −0.15, 0.0369 / −0.148, 0.0191 / −0.145, bge (b) 0.056 / −0.235).
   - 사전 등록 절은 v1 목적함수와 동률 규칙을 적었다. 결과가 포화했어도 규칙을 사후에 바꾸지 않았다. 통과.
2. **분모 > 0**: toy 25(19 / 6), public 99(79 / 20), private 79(64 / 15), B6 held-out 61(25 / 36)이다. 모든 실행이 errors 0이다. 카나리아로 bge-m3 cosine 표본 20개, `dimensions_check`, 270m과 740m의 동일성을 확인했다. 통과.
3. **같은 조건 비교**: 결과 폴더 34개 전부에서 다음을 `config.json` / `summary.json`으로 확인했다. 통과.
   - `ollama_version=0.40.2`
   - eval 실행 전부 `vector_search=exact`, `reranker=none`
   - chunk 수 toy 32 / public 2,029 / private 8,447, pgvector 0.8.0, ef_search 40
   - 270m 계열은 `embedding_dim`과 `truncate_dim`이 라벨과 일치
4. 실패를 본 평가셋으로 수정 효과를 잰 경우는 없다(모델 비교이고 임계값 선택은 dev만 씀). 통과.
5. private은 집계만 남겼다(위 6 참조). 원본은 레포 밖에 있다고 보고됐다. 통과.

### 표본 대조 (report 비교표 대 summary.json)
대조한 칸은 28개이고 모두 일치한다. 270m과 bge-m3 (b)를 포함한다.
- (b): Citation toy 89.5 / public 86.7·85.3 / private 44.4, Keyword private 64.1, 오거절 public 5.1·5.1 / private 29.7, 거절 public 90·90, 검색 p50 toy 58 / private 101, 생성 p50 public 3109 / private 5307
- (c1) 768d: hit@5 89.5 / 92.4 / 68.8, 섹션 34.4(private), Citation 88.2 / 92.9·91.4 / 54.8, 거절 private 80.0, 오거절 34.4
- (c2) 512d: hit@5 private 75.0, 오거절 public 8.9·7.6 / private 17.2, Keyword 86.1·86.3
- (c3) 256d: hit@5 84.2 / 92.4 / 70.3, 섹션 79.7 / 31.2, Citation 88.9·90.3, 생성 p50 private 5025.5 → 5026
- (a): 검색 p50 toy 862, 생성 p50 public 4934(1회) / private 5587
- B6(scope-b6 summary): bge 95.8 / 92.0 / 2.8, 768d 88.5 / 92.0 / 8.3, 512d 92.0 / 92.0 / 5.6, 256d 88.9 / 96.0 / 8.3. margin과 Youden J도 일치한다.
- tuning: 선택값, tied interval, dev 거절과 오거절(16/17·2/60, 17/17·7/60, 17/17·7/60, 17/17·5/60)이 일치한다.
- embed bench: 16.9 / 18.0 ms와 673 MB, 13.3 / 14.2 ms와 346 MB가 일치한다.
- 0.24.0 비교 문장("public hit@5 96.2, 섹션 87.3, private 75.0 / 45.3 동일", "0.24.0 p50 4.4초")은 `2026-10-07_public_bge-m3-vector-gemma4-e4b-b7*`, `2026-10-09_private-protocols_bge-m3-vector-exact*`, `2026-10-07_toy_bge-m3-vector-gemma4-e4b`(4384 ms)와 일치한다.
- 불일치는 R8(report의 검색 p50 기준)뿐이다.

### 절전 구간 (17:43~19:31 KST)
- 로그 생성 및 수정 시각으로 확인했다.
- 구간에 걸친 실행은 256d public gate-off(17:42:51~19:42:07) 하나다. 이 실행은 `evidence/discarded_sleep_run/`로 옮겨 버렸다. 지금 결과 폴더의 `public_…d256-gateoff`는 `run_at` 20:38:07의 재실행이고, `cosine-gate_…d256`도 이 재실행을 쓴다.
- 최종 표에 쓴 256d 실행은 모두 19:31 이후다: toy 19:42, public 19:44 / 19:49, private 19:54, embed bench 20:00.
- 절전 전에 끝난 256d 실행은 scope 17:40:15와 toy gate-off 17:42:51(구간 시작 9초 전)이다.
- 512d private은 17:24:45~17:31:01로 절전 전에 끝났다. 768d와 bge (a) / (b)는 구간 밖이다.
- 위반 없음. 다만 같은 재실행에서 나온 재색인 시간을 문서에 반영하지 않았다(R1).

### 코드 결함
- `think`
  - `/api/generate`에 항상 `"think": False`를 보낸다.
  - 구버전 Ollama(think 필드가 없던 버전): Go JSON 디코더가 모르는 필드를 무시하므로 오류가 나지 않는다.
  - thinking을 지원하지 않는 모델: `medgemma:4b`는 `ollama show`에 thinking capability가 없다. Ollama는 think가 **true**일 때만 "does not support thinking"으로 거부하므로 false는 안전하다고 판단한다.
  - 다만 이 판단은 Ollama 소스 동작에 근거한 것이다. 0.40.2에서 medgemma에 실제로 호출해 보지는 않았다. 호스트에서 다른 실행(gemma4와 270m 적재)이 돌고 있어 모델 적재를 피했다. **커밋 전에 medgemma로 짧게 `generate` 1회 해 볼 것을 권고한다.**
  - gemma4:e4b는 `ollama show` 기준 thinking의 기본값이 true다. 수정 근거가 확인된다.
- `dimensions`: `embedding_truncate_dim is None`이면 payload에 넣지 않는다. 단위 테스트로 검증된다. bge-m3, nomic, 알 수 없는 모델에 truncate를 지정하면 Settings 검증이 `matryoshka_dims`가 없다는 이유로 거부하므로 bge-m3 경로에는 들어가지 않는다. OllamaClient를 만드는 곳은 `container.py`와 `run_scope_eval.py` 두 곳이고 둘 다 값을 넘긴다. `scripts/diagnose_embedding.py`는 진단용 직접 호출이라 무관하다.
- 설정 검증
  - 768 같은 전체 크기나 1024처럼 큰 값, 300 같은 비 Matryoshka 값을 거부한다.
  - `EMBEDDING_DIM`이 절단 차원과 다르면 거부한다.
  - 빈 문자열은 None으로 처리한다.
  - 차원이 바뀌면 DB 열 크기가 달라 다른 차원의 chunk가 섞일 수 없다.
- 문제 없음.

### 문서
- 측정하지 않은 것 표시는 충실하다. 다음 항목을 모두 "측정 안 함"으로 적었다: 제목 접두어, 128d, 740m과 그 멀티모달, nvfp4 양자화, 다른 게이트 목적함수, private 2회.
- 0.24.0과 생성 지표를 직접 비교하지 않는다는 점도 분명하다.
- ADR `:99`는 디스크(`ollama list`)와 적재 메모리(`ollama ps`)를 구분해 적었고, 표 머리말도 `모델 메모리(ollama ps)`다. 다만 결정 문단 `:103`의 "약 1/3"이 두 기준을 흐린다(R3).
- 결론(불채택, bge-m3 유지)은 수치와 맞는다. 문장 단위로는 R1~R4가 어긋난다.

## 게이트 메모
- 기존 테스트 455개 이후 475 passed 0 skipped라는 결과는 report와 junit evidence를 근거로 한 것이다. 재실행은 Tester 몫이라 여기서는 다시 돌리지 않았다.
