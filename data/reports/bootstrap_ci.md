# R1.b — Bootstrap CI for Stage 1 metrics

_Latest measurement: 2026-05-07 / scope: combined GT n=28 (PleOS self 15 + MASTG 4 + InsecureBankv2 9)_

## 방법

`src/eval.py --bootstrap 1000 --bootstrap-ci 0.95 --bootstrap-seed 42`. Non-parametric percentile bootstrap — n 라벨을 with-replacement 1000 회 resample → metric 분포 산출 → 2.5th / 97.5th percentile 로 95% CI.

## 결과 비교 (R1.d 표본 확장 효과)

| Metric | n=19 (5/6) | n=28 (5/7) | Δ point | Δ CI 폭 |
|---|---|---|---|---|
| Precision (lenient) point | 78.9% | **85.7%** | +6.8%p | — |
| Precision 95% CI | [57.9%, 94.7%] (폭 36.8%p) | **[71.4%, 96.4%]** (폭 25.0%p) | — | **−11.8%p** |
| F1 (lenient) point | 88.2% | **92.2%** | +4.0%p | — |
| F1 95% CI | [73.3%, 97.3%] (폭 24.0%p) | **[83.3%, 98.2%]** (폭 14.9%p) | — | **−9.1%p** |
| FP rate (lenient) point | 21.1% | **14.3%** | −6.8%p | — |
| FP rate 95% CI | [5.3%, 42.1%] (폭 36.8%p) | **[3.6%, 28.6%]** (폭 25.0%p) | — | **−11.8%p** |
| Recall | 100% (CI 100%) | 100% (CI 100%) | 0 | 0 |

## 새 corpus (InsecureBankv2)

InsecureBankv2 (Android-InsecureBankv2 master prebuilt APK) 도입으로:
- 추가 finding 9 건 (모두 TP — InsecureBankv2 는 의도된 vuln 학습용 corpus)
- 카테고리 분포: intent 4 / hardcoded 2 / crypto 1 / network 2
- 외부 정답이 명확히 문서화된 corpus 라 self-label bias 추가 완화

## RQ1 implication

표본을 19 → 28 로 확장한 결과:
- **CI 폭이 약 1/3 줄어듦** (Precision / FP rate 36.8%p → 25.0%p, F1 24.0%p → 14.9%p). 본 학기 처음으로 n 증가 → CI 좁힘 의 직접 측정.
- Precision lenient lower bound 가 57.9% → **71.4%** 로 olympic. 즉 corpus 가 n=28 가까울 때 Precision 의 통계적 보장 근거가 71.4% 이상.
- 12주차 추가 표본 확장 시 CI 폭 추가 감소 가능. n=40 부터는 통계적 보고서 신뢰성 sub. 

## 재현

```bash
python src/eval.py \
    --labels data/ground_truth/combined_labels.json \
    --reports 'data/reports/ai.umos.vehiclecontrol_20260429.json' \
              'data/reports/ai.pleos.sync.syslog_20260429.json' \
              'data/reports/ai.pleos.llm.model.provider_20260429.json' \
              'data/reports/UnCrackable-Level1_20260430.json' \
              'data/reports/UnCrackable-Level3_20260430.json' \
              'data/reports/InsecureBankv2_20260507.json' \
    --by-stage stage1 \
    --bootstrap 1000 \
    --bootstrap-ci 0.95 \
    --bootstrap-seed 42
```

deterministic (seed 42) — 동일 commit 에서 동일 결과.

## 변경 이력

| 날짜 | n | Precision | F1 | CI 폭 (Precision) |
|---|---:|---:|---:|---:|
| 2026-05-06 | 19 | 78.9% | 88.2% | 36.8%p |
| 2026-05-07 | 28 | **85.7%** | **92.2%** | **25.0%p** (−11.8%p) |
