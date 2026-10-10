# Review r2 — 2026-10-10-embeddinggemma2 (fix1 재검토)

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: r1 반려 R1~R4, 권고 R5·R7의 수정(`report-implementer.md` "fix1" 절)
- 확인 파일: `docs/decisions/0002-embedding-model.md`, `docs/journey.md`, `README.md`, `report-implementer.md`
- 대조 근거: `eval/results/2026-10-10_*/summary.json`, `evidence/index_*.json`, `evidence/embed_bench_*.json`

## 판정: REQUEST_CHANGES (문장 1곳, 세 파일)

R1, R3, R4, R5, R7은 고쳐졌고 수치도 맞다. R2는 지표를 나눠 적었다. 그런데 새로 넣은 "hit@5는 세 설정이
**1~2문항 안에서** 엇갈린다"가 private에서 틀리다. 이 문구는 r1이 예시로 제안한 것이어서 r1의 잘못도 있다.
아래 N1만 고치면 APPROVE한다.

| # | 위치 | 문제 | 고칠 방향 |
|---|---|---|---|
| N1 | `docs/decisions/0002-embedding-model.md:96`, `docs/journey.md:109`, `report-implementer.md:67` | private hit@5는 768d 44/64(68.8), 256d 45/64(70.3), 512d 48/64(75.0)이다. 최저와 최고가 **4문항** 차이다. "1~2문항 안"은 public(512d 72/79, 256d·768d 73/79, 차이 1문항)에만 맞는다 | 예: "hit@5는 설정 사이에 일관된 순서가 없다(public은 1문항 차이, private은 4문항 차이: 768d 68.8 / 256d 70.3 / 512d 75.0)". 또는 "1~2문항" 표현을 빼고 괄호 안 수치만 남긴다 |

## 항목별 확인

- **R1 해결.**
  - 근거 값: `index_rr256_*.json`에 private 288.5 s, public 76.1 s, toy 0.9 s가 있다. 768d와 512d는 private 288.1 / 287.8 s, public 75.8 / 76.2 s다. 첫 256d 색인은 private 442.7 s, public 97.0 s다.
  - ADR 표(`:94`)와 본문(`:99`), report 표와 주석에 위 값이 맞게 들어갔다.
  - "구분하지 못했다"는 문장은 남아 있지 않다(grep 0건).
  - 시점: `db_rr256.log`는 20:31:53, `index_rr256.done`은 20:38:07이다. 문서의 "절전 뒤 다시 만든 DB"와 맞는다.
- **R2 일부 해결, 새 오류 N1.**
  - 섹션 hit에서 256d가 모든 코퍼스 최저인 것은 맞다. toy 16 < 17, public 63 < 64, private 20 < 22다.
  - toy hit@5도 256d가 최저(84.2)로 맞다.
  - "private 최저 768d 68.8, public 최저 512d 91.1"도 맞다.
  - 같은 문장의 "1~2문항 안"만 틀리다(N1).
- **R3 해결.**
  - ADR `:103`과 journey `:109`가 디스크(`ollama list`) 약 1/3, 적재 메모리(`ollama ps`) 약 1/2로 기준을 나눴다.
  - 적재 메모리 346 / 673 MB = 0.51이다. 질문 embedding p50은 16.9 − 13.3 = 3.6 ms다(`embed_bench_*.json`과 일치).
  - 디스크 378 MB / 1.2 GB는 evidence 파일에 없다. r1에서 확인한 값을 그대로 둔다.
- **R4 해결.**
  - "85~87% → 89~93%"로 고쳤다.
  - bge (b)는 85.3 / 86.7이다. 270m은 88.9~92.9인데, 256d의 88.9는 반올림하면 89다.
  - 같은 줄의 "오거절 5.1% → 7.6~11.4%"도 summary와 맞다.
- **R5 해결.** ADR `:73`과 journey `:108`이 추정이라고 밝히고 근거(capability, 비트 동일 출력)를 적었다. README의 "비트 단위로 같아 생략"은 사실만 적은 문장이라 문제없다.
- **R7 해결.** README `:386`이 `적재 메모리(\`ollama ps\`)`로 바뀌었다.
- **표 수치 재대조.** README와 ADR 표의 hit@5, 섹션, Citation, 오거절 칸을 `summary.json` 29개 폴더 값으로 다시 맞춰 봤다. 모두 일치한다.

## 변경 범위 (r1 이후)

- r1 이후 수정된 파일은 `review-r1.md`(20:51:14)보다 새 파일로 찾았다(`find -newer`). README.md, docs/journey.md, docs/decisions/0002-embedding-model.md, report-implementer.md 네 개뿐이다.
  - 그 밖에는 `.ruff_cache/` 두 파일이 있다. git 추적 대상이 아닌 도구 캐시다.
- `git diff --stat`의 tracked 목록은 r1과 같은 12개 파일이다. 코드, 테스트, `eval/results/**`, evidence는 r1 이후 바뀌지 않았다.
- fix1 diff는 문서 문장만 바꿨다. 표 구조와 결론(불채택, bge-m3 유지)은 그대로다.

## 권고 (비차단)

- N2: ADR `:96`과 journey `:109`의 "512d는 768d와 거의 같고"는 public(91.1 / 92.4)과 섹션 hit에는 맞는다. 하지만 private hit@5는 512d 48 / 768d 44로 4문항 차이다. N1을 고칠 때 "public과 섹션 hit에서"로 범위를 좁히면 좋다. report `:67`의 "512d ≈ 768d"도 같다.
- r1의 R6, R8~R11과 medgemma 실호출 권고는 fix1에서 하지 않았다고 report에 적혀 있다. 비차단이므로 그대로 둔다.
