# R1.c — Paired McNemar test (Stage 1 vs Stage 3, n=47)

_Measured: 2026-05-14 / scope: n=47_

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

## 한계 + follow-up

- McNemar's test 는 paired discordant pair 수 (b + c) 가 작으면 power 가 낮다. 본 측정 b+c = 10 로 매우 작음.
- 현재 corpus 는 n=47 이며, 더 넓은 독립 label set 으로 재측정하면 신뢰구간과 검정 power 를 추가로 안정화할 수 있다.
- 본 측정은 단순 paired 검정. effect size (odds ratio of discordant pairs = b/c) 도 함께 보고:
  - b/c = 1/9 → Stage 3 가 Stage 1 의 오류를 잡은 비율이 더 큼 (c > b 이면 Stage 3 가 더 좋음).

## RQ1 implication

- 본 학기 데이터에서 Stage 3 가 Stage 1 의 오류 9 건 (9/47 = 19.1%) 을 추가로 정확히 처리.
- Stage 1 이 정답인데 Stage 3 가 누락한 케이스 b = 1 건 (1/47 = 2.1%).
- net 효과: Stage 3 가 정답 케이스를 추가로 +8 건 더 잡았다 (n=47, p_exact=0.0215). 이는 통계적으로 유의하다.
- 정직한 결론: bootstrap CI 좁힘 (R1.b) 과 paired test (R1.c) 를 함께 보고한다. 본 측정에서 Stage 3 의 net 정정은 +8건이며, p_exact=0.0215.
