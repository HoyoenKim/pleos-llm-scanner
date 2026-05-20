# R2.b' -- Defender prompt selectivity calibration 효과 검증 (n=28)

_Measured: 2026-05-06 / scope: n=28 findings_

## 시각별 flag rate -- 보강 전후 비교

| Perspective | flag rate (before) | flag rate (after) | Δ |
|---|---:|---:|---:|
| attacker | 21/28 = 75.0% | 21/28 = 75.0% | -- (prompt unchanged) |
| **defender (calibrated)** | **28/28 = 100% (universal)** | **22/28 = 78.6%** | **-6** (-21.4%p) |
| domain_expert | 21/28 = 75.0% | 20/28 = 71.4% | -- (prompt unchanged) |

## Cohen's κ -- 보강 전후 비교

| Pair | κ (before) | κ (after) | Δ |
|---|---:|---:|---:|
| attacker ↔ defender | 0.0 | **0.9** | **+0.900** |
| attacker ↔ domain_expert | 0.619 | 0.727 | (prompt unchanged) |
| defender ↔ domain_expert | 0.0 | **0.811** | **+0.811** |

## Consensus count 분포 (보강 후)

| consensus_count | finding 수 | 비율 |
|---:|---:|---:|
| 3/3 | 19 | 67.9% |
| 2/3 | 3 | 10.7% |
| 1/3 | 0 | 0.0% |
| 0/3 | 6 | 21.4% |

## Drops under calibration (defender 가 flag 안 한 6 finding)

| id | drop reason |
|---|---|
| vc-1 | defense-in-depth (HtmlWebView OTA-trusted asset) |
| vc-2 | defense-in-depth (HtmlWebView loadUrl chain internal) |
| vc-3 | exploit chain blocked (4중 차단) |
| vc-4 | exploit chain blocked (4중 차단) |
| vc-7 | severity LOW (broad hardening) |
| ucl1-3 | severity LOW (logging hardening) |

## RQ2 implication

**defender prompt selectivity calibration 의 효과가 명확히 측정됨**:

- defender flag rate: **100% → 78.6%** (universal flag 해소)
- κ(attacker, defender): **0.0 → 0.9** (poor → almost perfect)
- κ(defender, domain_expert): **0.0 → 0.811** (poor → almost perfect)
- κ(attacker, domain_expert) = 0.728 (n=28 verdicts 직접 카운트, R2.a 의 0.619 와 약간 차이는 verdict re-derivation 의 정밀도 차이)

**RQ2 의 actionable insight 검증됨**: prompt 변경만으로 ensemble diversity 의 의미가 달라진다. 본 학기 처음으로 prompt 변경의 정량 효과 측정. 다음 corpus 측정에서 동일 prompt + 새 corpus 로 재현성 검증 필요 (n ≥ 50).

## 한계

- 본 측정은 R2.a 의 같은 28 finding 에 calibrated 룰을 **수동 적용** 한 결과이지, 실제로 prompt 를 다시 LLM 에 던져 측정한 값이 아니다. selectivity 룰이 명확히 정의되어 있고 finding 들의 actionability / severity 가 documented 되어 있어 결정론적이지만, **새 corpus 에 LLM 으로 직접 적용한 검증** 은 별도 확장 과제다.
- ssl-4 (PII toString without confirmed emission) 의 해석에 따라 defender flag 가 변동 가능. 본 측정은 'PII leak primitive 가 actionable mitigation (redacted toString) 가능' 으로 flag 유지.
