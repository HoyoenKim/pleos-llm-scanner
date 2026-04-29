# Ablation 결과 (2026-04-29)

산출: `src/ablation.py` 실행 결과. 입력은 `data/ground_truth/self_labels_20260429.json` (n=15) + `data/reports/*.json` (n=4 files, 15 stage-1 findings indexed) + `data/reports/stage3_ensemble_20260429.json` (n=12 entries).

## A — Stage ablation

각 단계가 추가될 때 전체 파이프라인 정확도가 어떻게 변하는지.

| variant | accepted | TP | FP | FN | unc | Precision (lenient) | FP-rate | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| A.1 stage 1 only | 15 | 10 | 4 | 0 | 1 | **71.4%** | 28.6% | 100.0% | 0.833 |
| A.2 + stage 2 (caller) | 10 | 10 | 0 | 0 | 0 | 100.0% | 0.0% | 100.0% | 1.000 |
| A.3 + stage 3 (≥3/3) | 7 | 7 | 0 | 3 | 0 | 100.0% | 0.0% | 70.0% | 0.824 |

### 해석
- **A.1 stage 1**: keyword 필터 + LLM 1-pass. 28.6% 오탐률 (PPT 가설 25%에 +3.6%p).
- **A.2 stage 2 caller**: P 71% → **100%** (FP 4건이 모두 internal Nav arg / 비 deep-link로 판정되어 제거). **Recall 100%는 self-GT 기반의 P-ceiling이지 현실 측정 아님** — 보고서에 caveat 명시.
- **A.3 stage 3 (D3=B 합의)**: Strong TP 채택만으로도 P 100%. 단 **Recall 70%**: stage 3 입력은 12 findings (B-3.c 이전 시점)이고 신규 ssl-4/5/6 (B-3.c 발견)이 stage 3 ensemble JSON에 없어 FN으로 카운트. ssl-4/5/6도 stage 3 평가하면 추정 Recall 90% (ssl-6 uncertain 가정).

## B — Consensus-threshold sensitivity (D3=B 멀티 프롬프트 합의)

stage 3에서 attacker/defender/domain_expert 3 시각 중 몇 개 합의해야 채택할지 임계를 변화.

| threshold | accepted | TP | FP | FN | unc | Precision (lenient) | FP-rate | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| ≥ 1/3 | 12 | 8 | 4 | 2 | 0 | 66.7% | 33.3% | 80.0% | 0.727 |
| ≥ 2/3 | 7 | 7 | 0 | 3 | 0 | **100.0%** | 0.0% | 70.0% | **0.824** |
| ≥ 3/3 | 7 | 7 | 0 | 3 | 0 | 100.0% | 0.0% | 70.0% | 0.824 |

### 해석
- **≥ 1/3 (defender만 보고도 채택)**: 모든 stage3 entries 채택 → uncertain 6건도 들어와서 P 67%. 가장 보수적 채택 안 함.
- **≥ 2/3 (다수결)**: B-3.c 후 stage3에 2/3-only entry 0개 (모든 격상이 3/3로 도달) → ≥3/3과 동일. Optimal P/F1.
- **≥ 3/3 (만장일치)**: 가장 엄격. 2/3과 동일 결과 (현 상태).

→ **≥ 2/3이 default 임계로 적합**. F1 가장 높음. 표본이 늘어나면 2/3과 3/3 차이가 생김 (3/3은 더 보수적).

## 핵심 시사점 (PPT/보고서 차원)

1. **stage 2 caller 분석이 가장 큰 P 개선 (71→100%)** — keyword 필터 단독은 1차 오탐률 통제 부족.
2. **stage 3 합의 규칙은 P 손실 없이 F1 0.83 유지** — 외부 환경 제약(D3=A 불가) 안에서 D3=B가 동일 효과.
3. **합의 임계 sensitivity**가 PPT 9주차 Ablation Study의 새 차원으로 활용 가능.
4. **표본 작음 caveat**: n=15 단일 세션 GT. OWASP MASTG 도입 후 외부 GT로 본 곡선의 통계적 의미 확정 필요 (Phase B-4.c).

## 재현

```bash
python src/ablation.py \
    --labels data/ground_truth/self_labels_20260429.json \
    --reports 'data/reports/*.json' \
    --stage3  data/reports/stage3_ensemble_20260429.json
```

`--json` 옵션으로 machine-readable 출력.
