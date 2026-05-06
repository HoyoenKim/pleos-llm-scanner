# R1.c — Paired McNemar test (Stage 1 vs Stage 3, n=28)

_Measured: 2026-06-07 / scope: n=28_

## 2x2 contingency table

Stage 별 'GT 와 일치 여부' 의 paired binary outcome.

|  | Stage 3 correct | Stage 3 incorrect | total |
|---|---:|---:|---:|
| Stage 1 correct | a = 23 | b = 1 | 24 |
| Stage 1 incorrect | c = 4 | d = 0 | 4 |
| total | 27 | 1 | **28** |

## 검정 통계량

- McNemar's chi-square (uncorrected): χ² = 1.800  (df=1)
- p-value (chi-square approximation): **0.1797**
- p-value (exact binomial, two-tailed): **0.3750**  ← b+c=5 작으므로 권고

## 해석

p_exact = **0.3750** → α=0.05 기준으로 **통계적 유의성 미달**. n=28, b+c=5 의 표본 크기에서는 검정 power 가 부족하다. Stage 1 과 Stage 3 의 paired 차이가 우연이 아니라는 결론을 통계적으로 도출하기에는 표본이 작다.

## 한계 + Future Work

- McNemar's test 는 paired discordant pair 수 (b + c) 가 작으면 power 가 낮다. 본 측정 b+c = 5 로 매우 작음.
- n=28 (combined GT) 까지 확장된 corpus 에서도 이 한계가 명확. 다음 단계 R1.d (n ≥ 50) 확장 후 재측정 필요.
- 본 측정은 단순 paired 검정. effect size (odds ratio of discordant pairs = b/c) 도 함께 보고:
  - b/c = 1/4 → Stage 3 가 Stage 1 의 오류를 잡은 비율이 더 큼 (c > b 이면 Stage 3 가 더 좋음).

## RQ1 implication

- 본 학기 데이터에서 Stage 3 가 Stage 1 의 오류 4 건 (4/28 = 14.3%) 을 추가로 정확히 처리.
- Stage 1 이 정답인데 Stage 3 가 누락한 케이스 b = 1 건 (1/28 = 3.6%).
- net 효과: Stage 3 가 정답 케이스를 추가로 +3 건 더 잡았으나 (n=28, p_exact=0.3750) 이는 통계적으로 유의하지 않다.
- 정직한 결론: bootstrap CI 좁힘 (R1.b 결과) 은 측정값의 분포를 좁혔지만, paired test 의 통계적 유의성 (R1.c) 는 본 표본 크기로 검출 불가. 본 학기의 'Stage 3 향상' 주장은 **effect size 는 양수 (Stage 3 의 net 정정 +3건) 이지만 표본 우연성 배제는 미완**.
