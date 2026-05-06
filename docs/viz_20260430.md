# 시각화 지표 (2026-04-30, 8주차 lag 해소)

> Phase A~C + Stage 2.b + Phase B-4.c.2 측정 결과를 6 차트로 시각화.
> 산출 스크립트: `src/viz/plot_metrics.py` (matplotlib 3.10.8, Malgun Gothic). 산출 PNG: `data/viz/`.

## 차트 인덱스

| # | 파일 | 다루는 측정 | PPT 매핑 |
|---|---|---|---|
| 01 | `01_category_distribution.png` | Stage 1 카테고리별 정·오탐 (combined n=18) | 6주차 — 카테고리별 정확도 |
| 02 | `02_apk_severity_heatmap.png` | APK × severity (TP n=14 + FP=4 표시) | 5/9주차 — APK별 심각도 |
| 03 | `03_fp_rate_trend.png` | Stage 1/2/3 오탐률 — PPT 가설 vs 실측 (PleOS-only / combined). x축은 검증 단계, 시간 아님 | 6/8주차 — FP 25→12→7% |
| 04 | `04_deobf_accuracy_trend.png` | Corpus별 난독화 분포 + 측정된 corpus의 LLM rename 정확도 (시간축 아님, 단일 측정) | 6주차 — 난독화 정확도 40→78% |
| 05 | `05_ablation_bars.png` | A 변형 (stage ablation) + B 변형 (합의 임계 sensitivity) | 9주차 — Ablation Study |
| 06 | `06_entropy_distribution.png` | 6 APK 의 obfuscation composite score 분포 | 6주차 — 난독화 강도 corpus 비교 |

## 차트별 해석

### 01 카테고리 분포 (combined n=18)

- **intent (5/5 TP)**, **hardcoded (4/4 TP)**, **crypto (3/3 TP)**: 100% Precision
- **network (2 TP / 2 FP)**: 50% — VehicleControl HtmlWebView 2건이 FP (Stage 2.b CONFIRMED)
- **permission (0 TP / 2 FP)**: 0% — VehicleControl AppPermissionManager 2건이 FP (Stage 2.b CONFIRMED)
- → FP가 두 카테고리에 집중되어 있고, 이미 Stage 2.b deep-link 검증으로 모두 internal Nav arg / OTA-trusted 으로 강등 확정. **Stage 3 ≥2/3 합의에서 모두 제거되어 P 100%**.

### 02 APK × Severity 히트맵

- **sync.syslog**: HIGH 4건 (ssl-2 token logcat / ssl-4 PII / ssl-5 BuildConfig.IDENTIFIER / ssl-6 gRPC plaintext) + MEDIUM 2건. **본 corpus 가장 위험**. FP 0.
- **VehicleControl**: HIGH 2 (vc-5/vc-6) + MEDIUM 1 + LOW 1 + **FP 4건 모두 여기**.
- **llm.model.provider**: HIGH 1 (lmp-1 PromptsContentProvider) + MEDIUM 1 (lmp-2 model file delete DoS).
- **UnCrackable-Level1**: HIGH 1 + MEDIUM 1 + LOW 1, MASTG 외부 baseline.
- → **FP는 Stage 2.b CONFIRMED 4건 외 0** — 외부 corpus까지 포함 후에도 패턴 동일.

### 03 FP rate 추이 — PPT 가설 vs 실측

- **1차**: PPT 25% / 실측 PleOS-only 26.7% / combined 22.2% — **PPT 가설 충족** (-2.8%p, combined 기준)
- **2차**: PPT 12% / 실측 0% — caller 추적이 모든 FP 제거 (P-ceiling)
- **3차**: PPT 7% / 실측 0% — D3=B ≥2/3 합의에서도 동일
- **caveat**: stage 2/3는 PleOS-only n=15 측정. MASTG 외부 GT는 stage 3 미평가 (Phase B-4.c.2 narrative)

### 04 Corpus별 난독화 분포 + LLM rename 정확도 (재설계 2026-05-06)

이전 버전은 5/6/8주차 시간축에 단일 측정값(2026-04-30 n=17)을 세 번 그려 추이가 있는 것처럼 보이는 misleading 시각화였다 → corpus-level view로 재구성:

- **MASTG hand-crafted (측정 대상)**:
  - UnCrackable-Level1: HIGH 50.0% / rename n=11 / exact 100%
  - UnCrackable-Level2: HIGH 40.0% / rename n=6 / exact 100%
  - r2pay-v1.0: HIGH 0.0% (난독화 약함) / 정확도 측정 X
- **PleOS (측정 대상 부족)**:
  - VehicleControl: HIGH 0.2% / 정확도 측정 X
  - SyncSyslog: HIGH 0.4% / 정확도 측정 X
  - LLMModelProvider: HIGH 0.0% / 정확도 측정 X
- **PPT 가설 (5/6/8주차 40→65→78%)**: 시간축 추이 가정 — 본 측정은 단일 시점이라 reference로만 caption에 명시.
- **caveat**: hand-crafted MASTG anti-tamper helper에 한정되어 upper-bound. Real-world commercial ProGuard 코드에서는 contextual hint 약화로 정확도 하락 예상.

### 05 Ablation 변형 (A: stage / B: 합의 임계)

**Variant A (combined n=18)**:
- A.1 stage 1: P 77.8% / R 100% / F1 0.875
- A.2 stage 2 caller (P-ceiling): P 100% / R 100% / F1 1.000
- A.3 stage 3 ≥3/3: P 100% / R 64.3% / F1 0.783 (artifact: stage3 ensemble은 self GT n=15에 한정 평가)

**Variant B (PleOS-only n=15, D3=B 합의 임계)**:
- ≥1/3 (any flag): P 73.3% / R 100% / F1 0.846
- **≥2/3 (default)**: P 100% / R 90.9% / **F1 0.952** ← PPT 가설 0.93 도달·초과
- ≥3/3 (unanimous): P 100% / R 81.8% / F1 0.900

→ **stage 2 caller 추적 + D3=B ≥2/3 합의가 정량 차별 동력** (P 73.3% → 100%, +26.7%p).

### 06 Entropy 분포 (6 APK obfuscation composite)

- **MASTG corpus**: UnCrackable-Level1 mean 0.618 / Level2 0.529. HIGH 임계 (0.7) 위 클래스 다수.
- **PleOS corpus**: 3종 모두 mean 0.03~0.05. HIGH 임계 위 클래스 0.2~0.4%만 존재.
- → **PleOS는 가정과 다르게 의미적 클래스명 유지** (release engineering / debug build). 본 corpus에서 deobf pipeline 효과는 작음. 외부 OWASP corpus에서는 100% 정확도로 검증.

## 재현

```bash
cd pleos-llm-scanner
python src/viz/plot_metrics.py
# → data/viz/01_*.png ~ 06_*.png 6 PNG 생성
```

데이터 출처:
- `data/ground_truth/combined_labels_20260430.json` (n=18 GT)
- `data/deobf/{6 APK}.json` (entropy 측정)
- `docs/archive/ablation_results_20260429.md` + `docs/archive/phase_b4c_mastg_baseline_20260430.md` (ablation/baseline 측정)

## 8주차 lag 해소 — 본 doc + chart로 PPT 8주차 deliverable 충족

PPT 8주차 항목:
- ✅ 3차 교차 검증 — Stage 3 D3=B (chart 03/05)
- ✅ FP 12 → 7% — 측정 0% (chart 03)
- ✅ **시각화** — chart 01~06 (이전 미진척 항목 해소)

→ Phase D 진입 직전. **9주차까지 본체 deliverable 모두 충족 + 시각화 + 베이스라인 비교 완료**.


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
