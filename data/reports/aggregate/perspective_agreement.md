# R2.a — Perspective disagreement matrix (multi-prompt ensemble)

_Measured: 2026-05-06 / scope: n=28 findings from `data/reports/local/stage3_ensemble.json`_

## 시각별 flag 빈도

| Perspective | flagged | flag rate |
|---|---:|---:|
| attacker | 21 | 75.0% |
| defender | 28 | 100.0% |
| domain_expert | 21 | 75.0% |

## Consensus count 분포

| consensus_count | finding 수 | 비율 |
|---:|---:|---:|
| 3/3 | 19 | 67.9% |
| 2/3 | 4 | 14.3% |
| 1/3 | 5 | 17.9% |
| 0/3 | 0 | 0.0% |

## Pairwise agreement + Cohen's κ

| Pair | agree | agree % | both flag | only A | only B | neither | κ |
|---|---:|---:|---:|---:|---:|---:|---:|
| attacker ↔ defender | 21 | 75.0% | 21 | 0 | 7 | 0 | 0.0 |
| attacker ↔ domain_expert | 24 | 85.7% | 19 | 2 | 2 | 5 | 0.619 |
| defender ↔ domain_expert | 21 | 75.0% | 21 | 7 | 0 | 0 | 0.0 |

## RQ2 implication

**시각 간 diversity 가 진짜인가?** Cohen's κ 가 낮을수록 시각 간 disagreement 가 많음 = perspective 다양성이 실제로 작동. 모두 동일 finding 을 flag 하면 κ → 1.0 이고 멀티 시각이 redundant 가 됨.

본 측정 (n=28, 동일 모델 Opus 4.7) 에서:
- 평균 flag rate: attacker 75.0% / defender 100.0% / domain_expert 75.0%
- 만장일치 (3/3): 19건 (67.9%) / 단독 flag (1/3): 5건 (17.9%)
- κ 해석은 위 표 참조. κ ≥ 0.61 (substantial) 이면 합의 임계 ≥2/3 가 reliable.

**한계 및 최종 반영**: 본 측정은 동일 모델 (Opus 4.7) 에 시각 prompt 만 다르게 한 결과다. 이후 보강 E에서 Codex 3-model cross-read를 별도로 완료했으며, 최종 결론은 `docs/08_completed_reinforcements.md`에 통합했다. 이 R2.a 문서는 multi-prompt baseline 측정 기록으로 유지한다.
