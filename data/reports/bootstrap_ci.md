# R1.b — Bootstrap CI for Stage 1 metrics (n=19)

_Measured: 2026-05-06 / scope: combined GT n=19 (PleOS self 15 + MASTG 4)_

## 방법

`src/eval.py --bootstrap 1000 --bootstrap-ci 0.95 --bootstrap-seed 42` 실행. Non-parametric percentile bootstrap — 19 라벨을 with-replacement 1000 회 resample → metric 분포 산출 → 2.5th / 97.5th percentile 로 95% CI.

## 결과

| Metric | Point estimate | Bootstrap mean | 95% CI low | 95% CI high | n_valid |
|---|---:|---:|---:|---:|---:|
| Precision (lenient) | **78.9%** | 79.0% | **57.9%** | **94.7%** | 1000 |
| Precision (strict) | 78.9% | 79.0% | 57.9% | 94.7% | 1000 |
| FP rate (lenient) | 21.1% | 21.0% | 5.3% | 42.1% | 1000 |
| FP rate (strict) | 21.1% | 21.0% | 5.3% | 42.1% | 1000 |
| Recall | 100.0% | 100.0% | 100.0% | 100.0% | 1000 |
| F1 (lenient) | **88.2%** | 87.9% | **73.3%** | **97.3%** | 1000 |
| F1 (strict) | 88.2% | 87.9% | 73.3% | 97.3% | 1000 |

(Recall CI 가 [100%, 100%] 인 이유: 본 GT 가 stage 1 reports 의 superset 이라 모든 라벨이 reports 에 매칭됨 → resample 시에도 FN=0 유지. 외부 corpus 확장으로 GT 가 reports 보다 큰 superset 이 되면 CI 폭 발생.)

## RQ1 implication

- **±15%p 가량의 CI 폭** (Precision lenient 57.9% → 94.7%, F1 73.3% → 97.3%) 이 n=19 표본 작음의 직접 정량 시각화.
- Point estimate 78.9% / 88.2% 는 95% CI 안에서만 의미 있다 — Stage 1 의 "평균적 Precision 80% 근처" 라는 주장은 가능하지만 "정확히 78.9%" 는 우연성 영향 큼.
- FP rate 의 CI [5.3%, 42.1%] 는 한 가지 finding 의 라벨 reshuffle 만으로도 큰 변동. 11주차에 n ≥ 30 (DIVA / InsecureBankv2 / 추가 MASTG) 으로 확장 시 CI 폭 ↓ 예상.

## 재현

```bash
python src/eval.py \
    --labels data/ground_truth/combined_labels.json \
    --reports 'data/reports/ai.umos.vehiclecontrol_20260429.json' \
              'data/reports/ai.pleos.sync.syslog_20260429.json' \
              'data/reports/ai.pleos.llm.model.provider_20260429.json' \
              'data/reports/UnCrackable-Level1_20260430.json' \
              'data/reports/UnCrackable-Level3_20260430.json' \
    --by-stage stage1 \
    --bootstrap 1000 \
    --bootstrap-ci 0.95 \
    --bootstrap-seed 42
```

deterministic (seed 42 고정) — 동일 commit 에서 동일 결과.
