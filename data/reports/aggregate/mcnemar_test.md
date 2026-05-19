# R1.c — Paired McNemar test (Stage 1 vs Stage 3, n=47)

_Measured: 2026-05-14 (보강 A, R1.d.5 + Stage 3 ensemble 19건 확장 후 재측정) / scope: combined GT n=47_

## 2x2 contingency table

Stage 별 'GT 와 일치 여부' 의 paired binary outcome.

|  | Stage 3 correct | Stage 3 incorrect | total |
|---|---:|---:|---:|
| Stage 1 correct | a = 37 | b = 1 | 38 |
| Stage 1 incorrect | c = 9 | d = 0 | 9 |
| total | 46 | 1 | **47** |

## 검정 통계량

- McNemar's chi-square (uncorrected): χ² = 6.400  (df=1)
- p-value (chi-square approximation): **0.0114**
- p-value (exact binomial, two-tailed): **0.0215**  ← b+c=10 작으므로 권고

## 해석

p < 0.05 → Stage 1 과 Stage 3 의 paired 분류 일치율 차이는 **통계적으로 유의**. Stage 3 의 향상이 우연이 아니라는 첫 증거.

## 14주차 중간 측정 (n=28) → 최종 통합 측정 (n=47)

| 측정 시점 | n | contingency (a/b/c/d) | p_exact | 결론 |
|---|---:|---|---:|---|
| 본 학기 14주차 | 28 | 23 / 1 / 4 / 0 | 0.375 | discordant b+c=5 — power 부족, 유의성 미달 |
| **보강 A (R1.d.5 + Stage 3 ensemble 19건)** | **47** | **37 / 1 / 9 / 0** | **0.0215** | **discordant b+c=10 — α=0.05 통계적 유의 도달** |

## 한계 + 확장 가능성

- McNemar's test 는 paired discordant pair 수 (b + c) 가 작으면 power 가 낮다. n=28 시점 b+c=5 로 유의성 미달이었으나, 보강 A에서 R1.d.5 (n=47) + Stage 3 ensemble 19건 확장 → b+c=10 으로 power 확보, α=0.05 유의 도달.
- 본 측정 b+c=10 도 여전히 작은 편 — n ≥ 60 추가 확장 시 power 강화 여지.
- effect size (odds ratio of discordant pairs = b/c) = 1/9 → Stage 3 가 Stage 1 의 오류를 잡은 비율이 압도적 (c=9 ≫ b=1).

## RQ1 implication

- n=47 데이터에서 Stage 3 가 Stage 1 의 오류 9 건 (9/47 = 19.1%) 을 추가로 정확히 처리 (9 FP 모두 uncertain/clean 강등).
- Stage 1 이 정답인데 Stage 3 가 누락한 케이스 b = 1 건 (1/47 = 2.1%, vc-7 LOW hardening — defender-only 1/3 합의).
- net 효과: Stage 3 가 정답 케이스를 +8 건 추가 정정 (p_exact=0.0215 < α=0.05 → **통계적으로 유의**).
- 정직한 결론: bootstrap CI 좁힘 (R1.b) + paired test 통계적 유의성 (R1.c) 둘 다 보강 A에서 도달 — n=28 시점의 "effect size 양수이나 표본 우연성 배제 미완" 한계가 **n=47 확장으로 해소**. RQ1 의 핵심 정량 contribution.
