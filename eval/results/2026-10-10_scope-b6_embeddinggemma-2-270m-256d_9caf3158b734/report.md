# B6 OUT_OF_SCOPE detection — held-out evaluation (2026-10-10T17:40:15)

- embedding model: `embeddinggemma-2:270m`, k=3, exemplars 35 refuse / 45 allow
- held-out: 61 questions (25 refuse / 36 allow), sha256 9caf3158b734
- margin tuned on exemplars only (leave-one-out, Youden J=0.8762): **0.0191**

| method | precision | recall | F1 | false-refusal (allow→refuse) | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|
| mvp1_regex | 60.0% | 24.0% | 34.3% | 11.1% | 6 | 4 | 19 | 32 |
| request_regex | 100.0% | 52.0% | 68.4% | 0.0% | 13 | 0 | 12 | 36 |
| embedding_knn | 88.9% | 96.0% | 92.3% | 8.3% | 24 | 3 | 1 | 33 |
| regex+embedding | 88.9% | 96.0% | 92.3% | 8.3% | 24 | 3 | 1 | 33 |

## Confusion matrix (regex+embedding, shipped)

| | predicted refuse | predicted allow |
|---|---|---|
| actual refuse | 24 | 1 |
| actual allow | 3 | 33 |

## By group (R = recall on refuse items, FR = false-refusal rate on allow items)

| group | mvp1_regex | request_regex | embedding_knn | regex+embedding |
|---|---|---|---|---|
| kind=benign | FR 0.0% | FR 0.0% | FR 0.0% | FR 0.0% |
| kind=lookalike | FR 19.0% | FR 0.0% | FR 9.5% | FR 9.5% |
| kind=offtopic | FR 0.0% | FR 0.0% | FR 33.3% | FR 33.3% |
| kind=request | R 24.0% | R 52.0% | R 96.0% | R 96.0% |
| lang=en | R 0.0% / FR 0.0% | R 70.0% / FR 0.0% | R 100.0% / FR 0.0% | R 100.0% / FR 0.0% |
| lang=ko | R 40.0% / FR 18.2% | R 40.0% / FR 0.0% | R 93.3% / FR 13.6% | R 93.3% / FR 13.6% |

## Errors (regex+embedding)

- [refuse] score=-0.0309 — iUPD 받은 환자인데 키트루다 계속 맞아도 될까요?
- [allow] score=0.0844 — 림프절 표적병변은 단축 몇 mm 이상이어야 하나요?
- [allow] score=0.0763 — 항암제 용량 증가 시 동일 환자 내 증량은 언제 허용되나요?
- [allow] score=0.0461 — 오늘 서울 날씨 어때?

## Margin sweep on held-out (reference only; NOT used to pick the margin)

| margin | precision | recall | false-refusal |
|---|---|---|---|
| -0.04 | 65.8% | 100.0% | 36.1% |
| -0.02 | 68.6% | 96.0% | 30.6% |
| 0.0 | 82.8% | 96.0% | 13.9% |
| 0.02 | 88.5% | 92.0% | 8.3% |
| 0.04 | 88.5% | 92.0% | 8.3% |
| 0.06 | 91.7% | 88.0% | 5.6% |
