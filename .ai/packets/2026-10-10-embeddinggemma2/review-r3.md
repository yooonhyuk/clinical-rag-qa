# Review r3 — 2026-10-10-embeddinggemma2 (fix2 재검토)

- Reviewer: Claude Opus 5.5 (read-only)
- 대상: review-r2의 N1(차단)과 N2(권고) 수정
- 확인 파일: `docs/decisions/0002-embedding-model.md`, `docs/journey.md`, `report-implementer.md`
- 대조 근거: `eval/results/2026-10-10_{public,private-protocols}_*/summary.json`

## 판정: APPROVE

N1과 N2가 세 파일 모두에서 고쳐졌다. 새로 넣은 수치는 `summary.json`과 맞는다. 이번 수정은 세 파일 밖을 바꾸지 않았다.

## 항목별 확인

- **N1 해결.**
  - "1~2문항"은 세 파일 본문에 남아 있지 않다(grep). report `:114`의 변경 기록에서 인용으로만 나온다.
  - ADR `:96`, journey `:109`, report `:67`이 이제 코퍼스별로 적는다. public은 1문항 차이, private은 4문항 차이다.
- **N2 해결.**
  - ADR `:96`, journey `:109`, report `:67`이 "512d ≈ 768d"를 public hit@5와 섹션 hit 범위로 좁혔다.
  - private 섹션 hit도 512d와 768d가 같다(22/64 = 34.4%). 그래서 "섹션 hit에서 거의 같다"는 private에도 맞다.
- **수치 대조** (`overall.hit_at_k`, `section_hit_at_k`):

  | 코퍼스 | 768d | 512d | 256d | bge-m3 (b) |
  |---|---|---|---|---|
  | public hit@5 | 0.9241 = 73/79 | 0.9114 = 72/79 | 0.9241 = 73/79 | 0.9620 = 76/79 |
  | private hit@5 | 0.6875 = 44/64 | 0.7500 = 48/64 | 0.7031 = 45/64 | 0.7500 = 48/64 |
  | public 섹션 | 0.8101 | 0.8101 | 0.7975 | 0.8734 |
  | private 섹션 | 0.3438 | 0.3438 | 0.3125 | 0.4531 |

  - 문서의 "public 72 vs 73/79"와 "private 44/45/48 of 64"(68.8 / 70.3 / 75.0)가 표와 맞다.
  - "256d 섹션 hit 최저(public 79.7, private 31.2)"도 맞다.
  - ADR의 "private hit@5 512d 75.0%가 bge-m3와 같다"도 맞다. 둘 다 48/64다.
  - report의 "public −3.8%p = 3문항"(76 → 73)도 맞다.
  - public은 run1, run2, gate-off의 검색 지표가 설정마다 같다.
- **변경 범위.**
  - `review-r2.md`(20:54:17)보다 새 파일을 `find -newer`로 찾았다. journey, ADR, report-implementer, `test-r1.md`, `evidence/junit-tester.xml`, `.pytest_cache`가 나왔다.
  - 뒤의 세 개는 Tester 산출물과 도구 캐시다. Implementer 수정이 아니다.
  - 코드, 테스트, README, `eval/results/**`는 바뀌지 않았다. `git diff --stat`의 tracked 파일 수도 r2와 같은 12개다.
- **새 오류**: 없다.

## 권고 (비차단)

- journey `:109`의 "(72 대 73·79 중)"은 읽기 어렵다. "(79문항 중 72 대 73)" 같은 어순이 낫다. 수치는 맞으므로 차단하지 않는다.
