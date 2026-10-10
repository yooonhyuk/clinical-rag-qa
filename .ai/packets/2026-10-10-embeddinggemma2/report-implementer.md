# Implementer 보고 — EmbeddingGemma 2 vs bge-m3 (2026-10-10)

> 상태: 완료(Phase 0~3). "사전 등록" 절은 Phase 2 측정 **전에** 적었고 이후 바꾸지 않았다.

## 사전 등록 (Phase 2 임계값 규칙, 측정 전)

두 임계값 모두 held-out(`scope_heldout.yaml`, public 홀수 번째 문항, private)을 보지 않고 정한다.

1. `scope_margin`: `eval/run_scope_eval.py`의 기존 방법 그대로. `scope_exemplars.yaml` 예시만으로
   leave-one-out(k=3), Youden J 최대 지점의 중점. 모델마다 한 번 계산하고, 결과는 그 설정의 `SCOPE_MARGIN`에 쓴다.
2. `min_relevance_score`(cosine 게이트): 게이트를 끈 실행(`--min-relevance-score -1`)을 dev에서 재생한다.
   - dev = toy 전부 + public 문항을 질문 유형별로 id 정렬해 짝수 번째(0,2,4,…) — `eval/tune_gate.py`의 `split`과 동일.
   - 재생: `refused(t) = 실행에서 이미 거절됨 or maxCosine < t` (프롬프트가 임계값에 의존하지 않아 정확히 재생된다).
   - **목적함수(v1)**: dev에서 `거절 정확도(must-refuse) − 오거절률(answerable)` 최대화. 부분답변은 답한 것으로 센다.
   - 동률: 최대값을 주는 임계값 구간의 중점(양쪽 여유가 가장 큰 값), 소수 3자리 반올림.
   - 후보 격자: dev의 distinct maxCosine 값 사이 중점 + 0.01 간격(−1 ~ 1).
   - 목적함수는 이후 바꾸지 않는다. 바꾸면 보고에 "post-hoc"로 따로 표시한다.
3. 모든 설정에서 같은 규칙을 쓴다. bge-m3(출하값 0.45, margin 0.056)는 기존 값을 그대로 두며,
   같은 규칙을 bge-m3에도 적용한 값은 참고로만 병기한다(별도 gate-off 실행이 필요한 경우에만).

## 요약
- **결론: bge-m3 유지 권고(270m 불채택).** 같은 규칙·같은 색인·같은 Ollama(0.40.2) 비교에서 270m은 검색(hit@5, 섹션 hit)과 B6 판별기가 모두 열세, 이득은 크기·질문 embedding 지연뿐. 기본값은 바꾸지 않음.
- Phase 0: bge-m3 기준선은 0.24.0과 검색 지표가 같다(public hit@5 96.2% 동일, ±2%p 초과 차이 없음). 생성 지표는 런타임·GGUF 변환 차이로 직접 비교 주의.
- 740m은 270m과 텍스트 벡터가 비트 단위로 동일(max|diff|=0.0)해서 측정 생략(coordinator 승인).

## Phase 0 (bge-m3, Ollama 0.40.2)
- 색인: toy 32 / public 2,029 / private 8,447 chunk(0.24.0 DB와 같은 수), 2.1 s / 67.5 s / 267.4 s.
- 표본 chunk 20개(toy 4, public 8, private 8): 0.24.0 시절 DB에 저장된 벡터 vs 현재 재계산 cosine min 0.999985 / mean 0.999996 / max 0.999999. 새 DB 저장 벡터와도 같은 값(`evidence/bge-m3_cosine_check.json`).
- **버린 실행**: Ollama 0.40.2가 gemma4:e4b에서 thinking을 기본 켬(660토큰, 질문당 ~45초). toy 25문항 중 15번째까지 진행한 첫 기준선을 중단하고 결과는 만들지 않았다(로그만 `evidence/discarded_thinking_run/`). coordinator 승인(A)으로 `OllamaClient`가 `think:false`를 보내고 기준선을 처음부터 다시 쟀다. gemma4:e4b ID가 ollama list에서 바뀐 것은 0.40.2의 로컬 compat GGUF 변환(다운로드 아님, coordinator 확인).
- 결과 폴더: `2026-10-10_{toy,public,public(run2),private-protocols}_bge-m3-ollama0.40.2-exact-gemma4-e4b_*`, `2026-10-10_scope-b6_bge-m3_*`.

## `dimensions` 지원 여부 (Phase 1 #5)
- **지원한다.** Ollama 0.40.2 `/api/embed`에 `"dimensions": N`을 보내면 앞 N차원이 L2 정규화돼 온다. 270m·740m × N∈{512,256,128} × 입력 3개(질의·영문 문서·한국어 문서 접두어 포함): 서버 결과와 "클라이언트에서 앞 N차원 절단 + L2 정규화"의 max|diff| ≤ 6.6e-8, 노름 1(`evidence/dimensions_check.txt`). 1024는 400 오류(`dimensions 1024 exceeds embedding length 768`).
- 그래서 서버측 방식을 택했다: `OllamaClient(embedding_truncate_dim)`가 `dimensions`를 보낸다. 클라이언트 절단 코드는 넣지 않았다. coordinator가 이 방식을 승인했다.

## 임계값 (사전 등록 규칙 그대로)
| 설정 | scope_margin (예시 LOO, k=3) | LOO Youden J | min_relevance_score (dev v1) | tied interval | dev 거절 정확도 / 오거절 @선택 |
|---|---|---|---|---|---|
| bge-m3 (a) 출하값 | 0.056 | 0.9206 | 0.45(기존값 유지) | – | – |
| bge-m3 (b) 같은 규칙 | 0.056 | 0.9206 | **−0.235** | −1.0..0.53 | 16/17 / 2/60 |
| 270m 768d | 0.0198 | 0.8540 | **−0.150** | −1.0..0.70 | 17/17 / 7/60 |
| 270m 512d | 0.0369 | 0.8635 | **−0.148** | −1.0..0.7041 | 17/17 / 7/60 |
| 270m 256d | 0.0191 | 0.8762 | **−0.145** | −1.0..0.71 | 17/17 / 5/60 |
- **v1 목적함수는 모든 모델에서 포화**했다: dev(toy 전부 + public 짝수, 77문항)의 거절 대상 17문항을 범위 판별기·생성 모델이 이미 거절해 게이트가 얻을 것이 없고 오거절만 늘어, 최대값 구간이 [−1, ~0.7]이다. 동률 규칙(구간 중점)이 음수를 골라 사실상 "게이트 없음". 규칙을 사후에 바꾸지 않았다. 이 결과가 못마땅하면 새 목적함수(예: tune_gate의 v2류)는 **사전 등록 후 새 held-out으로** 쟤야 한다.
- held-out(`scope_heldout.yaml`, public 홀수 번째)은 임계값 선택에 쓰지 않았다. `tune_cosine_gate.py`는 test 절반을 읽지 않는다(개수만 셈). 최종 평가가 전체 문항을 도는 것은 임계값 선택과 별개.

## Phase 2 결과 (exact, gemma4:e4b think:false, reranker 없음, top_k 5)
toy(25) / public 1회 / public 2회(99) / private(79). 파일: `evidence/compiled.txt`.

| 지표 | (a) bge-m3 0.45 | **(b) bge-m3 규칙 v1** | (c1) 270m 768d | (c2) 270m 512d | (c3) 270m 256d |
|---|---|---|---|---|---|
| hit@5 toy / public / private | 100 / 96.2 / 75.0 | **100 / 96.2 / 75.0** | 89.5 / 92.4 / 68.8 | 89.5 / 91.1 / 75.0 | 84.2 / 92.4 / 70.3 |
| 섹션 hit toy / public / private | 100 / 87.3 / 45.3 | **100 / 87.3 / 45.3** | 89.5 / 81.0 / 34.4 | 89.5 / 81.0 / 34.4 | 84.2 / 79.7 / 31.2 |
| Citation toy / public(1,2) / private | 89.5 / 85.1,85.1 / 45.7 | 89.5 / 86.7,85.3 / 44.4 | 88.2 / 92.9,91.4 / 54.8 | 82.4 / 91.7,91.8 / 58.5 | 82.4 / 88.9,90.3 / 52.2 |
| Keyword toy / public(1,2) / private | 94.7 / 91.9,91.9 / 59.4 | 94.7 / 92.0,92.0 / 64.1 | 94.1 / 88.6,88.6 / 65.5 | 88.2 / 86.1,86.3 / 59.4 | 88.2 / 88.9,88.9 / 62.0 |
| 거절 정확도 toy / public(1,2) / private | 100 / 90,95 / 86.7 | 100 / 90,90 / 86.7 | 100 / 95,95 / 80.0 | 100 / 95,95 / 86.7 | 100 / 95,95 / 86.7 |
| 오거절 toy / public(1,2) / private | 0 / 6.3,6.3 / 28.1 | 0 / 5.1,5.1 / 29.7 | 10.5 / 11.4,11.4 / 34.4 | 10.5 / 8.9,7.6 / 17.2 | 10.5 / 8.9,8.9 / 28.1 |
| B6 P / R / 오거절 (held-out 61) | 95.8 / 92.0 / 2.8 | 95.8 / 92.0 / 2.8 | 88.5 / 92.0 / 8.3 | 92.0 / 92.0 / 5.6 | 88.9 / 96.0 / 8.3 |
| 검색 p50 (ms) toy / public / private | 862* / 68 / 100 | 58 / 68 / 101 | 52 / 64 / 95 | 45 / 59 / 85 | 46 / 49 / 59 |
| 생성 p50 (ms) public / private | 4934 / 5587 | 3109 / 5307 | 3000 / 4927 | 3137 / 5235 | 3007 / 5026 |
| 질문 embedding p50 / p95 (ms) | 16.9 / 18.0 | 16.9 / 18.0 | 13.3 / 14.2 | 13.4 / 15.1 | 13.3 / 14.5 |
| `ollama ps` 모델 크기 | 673 MB | 673 MB | 346 MB | 346 MB | 346 MB |
| 색인 시간 toy / public / private (s) | 2.1 / 67.5 / 267 | – | 2.0 / 75.8 / 288 | 0.8 / 76.2 / 288 | 0.8 / 97.0 / 443 (재색인 0.9 / 76.1 / 288.5) |
*(a) toy 첫 쿼리에 모델 적재 시간이 섞임. 색인 시간·지연은 호스트 상태(다른 앱, 스왑)에 따라 흔들리므로 정밀 비교가 아님(예: 256d 첫 색인 443 s는 호스트 변동이었고, 재색인은 private 288.5 s / public 76.1 s).
- private은 설정당 1회. diagnostics(top-5 중 다른 시험 chunk 비율): (a)/(b) 48.8%, 768d 45.3%, 512d 45.9%, 256d 52.2%(같은 폴더 `diagnostics.json`).
- DB 상태(모든 config.json): chunk toy 32 / public 2,029 / private 8,447, `vector_search=exact`(HNSW 인덱스는 존재하지만 사용 안 함, ef_search 40), pgvector 0.8.0, Ollama 0.40.2.
- 해석: 검색은 270m이 모든 코퍼스에서 같거나 낮다(public −3.8%p = 3문항, 섹션 −6.3%p, toy −10.5%p = 2문항). 512d ≈ 768d는 public hit@5·섹션 hit 범위만(private hit@5는 512d 48 / 256d 45 / 768d 44 of 64). 섹션 hit는 256d가 모든 코퍼스 최저(public 79.7, private 31.2), hit@5 차이는 public 1문항(72 vs 73/79), private 4문항(44~48/64). 270m의 Citation↑는 답하는 문항 구성이 달라진 효과(오거절 증가)와 섞여 있어 장점으로 읽지 않는다. 생성 지표는 gemma4 런타임이 0.24.0과 달라 0.24.0 수치와 직접 비교하지 않는다.
- 740m: 6개 입력(질의·한국어 문서 접두어·긴 영문 등) 768d 벡터가 270m과 비트 단위로 동일(`evidence/270m_vs_740m_identity.txt`). 생성 포함 실행은 270m 3종만(coordinator 승인).

## 수정 파일과 이유
| 파일 | 이유 |
|---|---|
| `backend/app/config.py` | `KNOWN_EMBEDDING_MODELS`에 270m·740m(768d, 접두어, `matryoshka_dims`), `EMBEDDING_TRUNCATE_DIM` 검증(알 수 없는 조합 거부, `EMBEDDING_DIM`은 절단 차원과 일치해야 함) |
| `backend/app/services/ollama_client.py` | `embedding_truncate_dim` → `/api/embed` `dimensions`; `think`(기본 False) → `/api/generate`에 `think` 전송 |
| `backend/app/container.py` (**Protect 해제 1줄, 승인됨**) | `OllamaClient.create`에 `embedding_truncate_dim` 전달. `think`는 설정으로 노출하지 않고 클라이언트 기본값(False)에 둠(container.py 추가 수정 금지 조건) |
| `eval/run_eval.py` | config에 `ollama_version`, `embedding_truncate_dim`, 접두어 기록 |
| `eval/run_scope_eval.py` | `OllamaClient`에 절단 차원 전달, summary에 `embedding_dim`/`embedding_truncate_dim`/`ollama_version`, 폴더 이름에 `-<N>d` |
| `eval/tune_cosine_gate.py` (**신규, 승인됨**) | gate-off 실행을 dev에서 재생해 `min_relevance_score` 선택(사전 등록 v1) |
| `tests/unit/test_embedding_config.py`, `test_embedding_service.py`, `test_ollama_client.py`, `test_tune_cosine_gate.py`(신규) | 접두어·절단 차원·알 수 없는 조합 거부·`dimensions`/`think` 전송·dim 불일치 오류·게이트 재생. 기존 assert 완화 없음 |
| `tests/integration/test_embedding_truncation_live.py` (신규, 요청에 따라 integration으로) | 로컬 Ollama에 270m이 있으면 512/256/128 절단 후 차원·노름 1·"앞 N차원+L2"와 일치 확인, 없으면 skip |
| `docs/decisions/0002-embedding-model.md`, `docs/journey.md`(§14), `README.md`, `.env.example` | 문서화(ADR은 절 추가만) |
| `eval/results/2026-10-10_*` | 결과 폴더(집계 + public/toy 전체; private는 집계·diagnostics만, 전체는 `~/clinical-rag-private/eval/results/`) |

## 게이트 증빙 (Tester가 재확인)
- `make lint`: exit 0 (`All checks passed!`, `173 files already formatted`).
- `make test --junitxml=...`: exit 0, **475 passed, 0 skipped**, junit `tests=475 failures=0 errors=0 skipped=0 timestamp=2026-10-10T20:28:21+09:00`(`evidence/junit.xml`). 기존 455개 모두 통과, 20개 추가. Docker·Ollama가 있어 통합·live 테스트도 skip 없이 실행됐다.
- `git diff --name-only` ⊆ Edit 목록(승인된 예외: container.py 1줄, tune_cosine_gate.py, tests/integration). packet.md는 수정하지 않음.
- 회사 문자열 denylist 검사 0건, private는 집계만(문항 id·파일명, 이전 커밋과 같은 형식).

## 남은 것 / 주의
- 기본값 변경 없음. 채택 결정은 coordinator 승인 대상(권고: 불채택).
- private 설정당 1회, 문서 제목 접두어·128d·740m 멀티모달·nvfp4 빌드의 양자화 영향은 "측정 안 함".
- cosine 게이트 규칙(v1)이 포화해 "게이트 없음"이 됐다. 게이트가 필요하면 새 목적함수를 사전 등록하고 새 held-out으로 잴 것.
- `think` 설정 노출(Settings → container)은 container.py 제약 때문에 하지 않았다. 필요하면 별도 packet.
- 일회용 DB 컨테이너(`crqa-eg2-*`)는 삭제했다. `crqa-private-eval`(기존)은 읽기만 했고 그대로 둔다.

## 호스트 절전 구간 처리 (coordinator 공지: 17:43~19:31 KST hibernate)
- 영향받은 실행: 270m 256d의 public gate-off(17:42:51 시작, 완료 19:42). 질문 p05의 생성 지연이 47.6 s(중앙값 4.9 s)로 절전 경계에 걸린 것으로 보여 **그 실행을 버렸다**(`evidence/discarded_sleep_run/`).
- 처리: 같은 DB 조건을 다시 만들어(일회용 컨테이너 새로 생성, 256d 색인 재수행) public gate-off를 처음부터 다시 돌렸다(20:38~20:45, 오류 0, 최대 생성 11.5 s). `tune_cosine_gate.py` 재실행 결과가 **이전과 같다**(선택 −0.145, 최대값 구간 [−1.0, 0.71], dev 거절 17/17, 오거절 5/60). 최종 256d 실행(toy·public 2회·private)은 19:44 이후(AC, 절전 후) 실행이고 선택 임계값이 같아 그대로 유효하다.
- 영향 없음: 절전 전에 끝난 폴더(768d 전부, 512d 전부, 256d 색인·scope·toy gate-off). 256d toy gate-off(17:42:51 종료)는 절전 직전에 끝났고 오류 0, 최대 생성 26.5 s는 첫 질문의 모델 적재(다른 toy 실행도 26 s대).
- 지연 지표는 모두 절전 이후 또는 이전에 완결된 실행에서 가져왔다. bge-m3 (b) 실행은 20:00 이후(절전 후)다.

## fix1
Reviewer r1 반려 R1~R4와 권고 R5·R7을 문서에서만 고쳤다. 수치는 `evidence/index_rr256_*.json`(private 288.5 s, public 76.1 s, toy 0.9 s)과 결과 폴더 summary.json(섹션 hit public 79.7 / private 31.2)에서 다시 확인했다.
- R1: ADR 0002 표·본문, report 표 주석. 256d 첫 색인 443 s는 호스트 변동이고 재색인은 288.5 s / 76.1 s라고 적었다. "구분하지 못했다" 문장 삭제.
- R2: ADR 0002, journey §14, report 해석 줄. 섹션 hit는 256d가 모든 코퍼스 최저, hit@5는 세 설정이 엇갈림(private 최저 768d 68.8, public 최저 512d 91.1)으로 지표별 표기.
- R3: ADR 0002 결정·장점 줄, journey. 디스크(`ollama list`) 약 1/3, 적재 메모리(`ollama ps`) 약 1/2, 질문 embedding p50 3.6 ms 차이.
- R4: ADR 0002 Citation 범위를 85~87% → 89~93%로.
- R5: ADR 0002, journey. 740m 타워 문장을 추정으로 바꾸고 근거(capability, 비트 동일 출력)를 밝혔다.
- R7: README 메모리 칸에 `(ollama ps)` 표기.
- 하지 않음: medgemma 실호출(R 권고 3번째), report p50 기준 통일(R8), R6, R9~R11. 코드·결과 폴더·테스트는 건드리지 않았다.

## fix2
- review-r2 N1·N2 반영: "1~2문항" 표현을 코퍼스별 차이(public 1문항, private 4문항)로 교체, "512d≈768d"를 public hit@5·섹션 hit로 한정(ADR 0002, journey, 이 보고서). summary.json 수치 재확인.
