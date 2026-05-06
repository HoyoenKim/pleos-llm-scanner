# Ablation 결과 (2026-04-29, full B-3.c follow-up 후)

산출: `src/ablation.py` 실행. 입력은 `data/ground_truth/self_labels_20260429.json` (n=15) + `data/reports/*.json` (4 files, 15 stage-1 findings indexed) + `data/reports/stage3_ensemble_20260429.json` (n=15 entries 포함 — ssl-4/5/6 stage 3 평가 추가 후).

## A — Stage ablation

각 단계 추가 시 정확도 변화.

| variant | accepted | TP | FP | FN | unc | Precision (lenient) | FP-rate | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| A.1 stage 1 only | 15 | 11 | 4 | 0 | 0 | **73.3%** | 26.7% | 100.0% | **0.846** |
| A.2 + stage 2 (caller) | 11 | 11 | 0 | 0 | 0 | 100.0% | 0.0% | 100.0% | 1.000* |
| A.3 + stage 3 (≥3/3) | 9 | 9 | 0 | 2 | 0 | 100.0% | 0.0% | 81.8% | **0.900** |

\* A.2의 100%는 self-GT `is_real==true` 기반 P-ceiling (시뮬). 실측 아님.

### 해석
- **A.1 stage 1**: PPT 가설 25% 대비 26.7% — **+1.7%p로 사실상 매칭**.
- **A.2 stage 2 caller**: P 73.3% → 100% (FP 4건 모두 internal Nav arg / no deep-link로 강등).
- **A.3 stage 3 (≥3/3)**: Strong TP 9 채택. **Recall 81.8%** = vc-7 (LOW) + ssl-4 (PII leak primitive without confirmed emission) 두 건 FN. 보고서 실용 측면에서 LOW + uncertain emission 누락은 수용 가능 trade-off.

## B — Consensus-threshold sensitivity (D3=B 멀티 프롬프트)

stage 3에서 attacker/defender/domain_expert 합의 임계 변화.

| threshold | accepted | TP | FP | FN | unc | Precision (lenient) | FP-rate | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| ≥ 1/3 (defender만 보고도 채택) | 15 | 11 | 4 | 0 | 0 | 73.3% | 26.7% | 100.0% | 0.846 |
| **≥ 2/3 (다수결)** | 10 | 10 | 0 | 1 | 0 | **100.0%** | 0.0% | **90.9%** | **0.952** |
| ≥ 3/3 (만장일치) | 9 | 9 | 0 | 2 | 0 | 100.0% | 0.0% | 81.8% | 0.900 |

### 해석
- **≥ 1/3**: stage 1과 동일 측정 결과 — 합의 효과 X.
- **≥ 2/3 (default 적합)**: P 100% + Recall 90.9% **동시 달성** → **F1 0.952 최적**. PPT 가설 Precision 0.93에 도달 + 초과.
- **≥ 3/3**: ssl-4 (PII leak primitive, 2/3 TP)가 제외되어 Recall 81.8%로 하락. F1 0.900.
- **≥2/3과 ≥3/3 차이가 발생** = D3=B 합의 규칙의 진짜 가치 — ssl-4 같은 "leak primitive는 real이지만 실 emission 미확인" finding을 ≥2/3에서 보고서에 채택할지 ≥3/3에서 보수적으로 제외할지 선택 가능.

## 핵심 시사점 (PPT 8/9주차에 직접 반영)

1. **D3=B의 정량 효과 입증**: 멀티 모델 (D3=A)을 자동화할 수 없는 환경 제약 안에서, 단일 LLM × 다중 시각으로 **F1 0.846 → 0.952** (+12.5%p). PPT 가설 Precision 0.93을 ≥2/3 합의 임계에서 도달·초과.
2. **stage 2 caller 분석이 가장 큰 P 개선 동력** — 73.3% → 100%. Internal Nav arg / 비 deep-link 강등으로 stage 1의 4 FP를 모두 제거.
3. **합의 임계 sensitivity** = 보고서/PPT의 새 ablation 차원. 표본 확장 시 threshold curve 가 더 매끄럽게 그려질 것.
4. **표본 작음 caveat**: n=15 단일 세션 self-GT. OWASP MASTG 외부 GT로 본 결과의 통계적 의미 확정은 Phase B-4.c 작업.

## 변화 (이전 측정 vs 현재)

| 변형 | 이전 (n=15, ssl-6 uncertain) | 현재 (full B-3.c, ssl-6 strong TP HIGH) | Δ |
|---|---|---|---|
| A.1 stage 1 F1 | 0.833 | 0.846 | +0.013 |
| A.3 stage 3 (≥3/3) F1 | 0.824 | 0.900 | **+0.076** |
| B ≥2/3 F1 | 0.824 (≥3/3과 동률) | **0.952** | **+0.128** |

ssl-6 격상 (uncertain → strong TP HIGH) + ssl-4 stage3 평가 추가 (2/3 TP) 의 영향이 가장 큼.

## 재현

```bash
python src/ablation.py \
    --labels data/ground_truth/self_labels_20260429.json \
    --reports 'data/reports/*.json' \
    --stage3  data/reports/stage3_ensemble_20260429.json
```

`--json` 옵션으로 machine-readable.


---

## 2026-04-30 update (L5 + L2 부분 해소 후 재측정)

| 변형 | 이전 (n=15 또는 n=18) | 현재 (combined n=19) | 변화 |
|---|---|---|---|
| A.1 stage 1 only | F1 0.846 (n=15) → 0.875 (n=18) | F1 **0.882** (n=19) | +0.007 |
| A.2 + stage 2 (caller) | F1 1.000 (P-ceiling) | F1 1.000 | 동일 |
| A.3 + stage 3 ≥3/3 | F1 0.783 (n=18 artifact) | F1 **0.889** | +0.106 (artifact 해소) |
| B ≥2/3 (default) | F1 0.952 (PleOS-only n=15) | F1 **0.966** (combined n=19) | +0.014 |
| B ≥3/3 | F1 0.900 (n=15) | F1 0.889 (n=19) | -0.011 (ucl1-3 2/3) |
| 1차 오탐률 | 22.2% (n=18) | **21.1%** (n=19) | -1.1%p (가설 25% -3.9%p) |

**해소 작업**:
- L5: ucl1-1/2/3에 stage 3 multi-prompt 합의(attacker/defender/domain_expert) 평가 추가 → `data/reports/stage3_ensemble_20260429.json` 갱신
- L2 부분: UnCrackable-Level3 디컴파일 + Stage 1 → ucl3-1 (XOR 키 hardcoded HIGH) 추가, GT 라벨 + stage 3 평가 동시 진행

**전체 재실행**: `src/eval.py`, `src/ablation.py`, `src/aaos_map.py`, `src/tara_generate.py`, `src/deobf/entropy.py` (UnCrackable-Level3 측정 추가), `src/viz/plot_metrics.py` 모두 자동 재생성됨.
