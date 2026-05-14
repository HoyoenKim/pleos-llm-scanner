# 시각화 지표 (2026-04-30 초안 → 2026-05-14 n=47 재생성)

> 본 보고서의 6 차트 — Stage 1/2/3 측정값 + 베이스라인 비교 + 난독화 분포 + Ablation.
> 산출 스크립트: `src/viz/plot_metrics.py` (matplotlib, Malgun Gothic). 산출 PNG: `data/viz/`.
> finding ID 정의는 [`01_report.md`](01_report.md) 의 Notation 섹션 참조.

> **2026-05-14 갱신**: 차트 01~05 를 **combined GT n=47** 기준으로 재생성 (학기 외 A 작업 반영). chart 06 은 `data/deobf/*.json` 라이브 로드라 obfuscation corpus (6 APK) 그대로. 차트 데이터는 `plot_metrics.py` 에 n=47 분포로 하드코딩 — 재측정 시 `combined_labels.json` 기준으로 갱신 후 재실행. 정량값 정합: [`01_report.md`](01_report.md) § 3.2 / § 3.6.5 + [`bootstrap_ci.md`](../data/reports/bootstrap_ci.md).

## 차트 인덱스

| # | 파일 | 다루는 측정 | PPT 매핑 |
|---|---|---|---|
| 01 | `01_category_distribution.png` | Stage 1 카테고리별 정·오탐 (combined n=47, 6 카테고리) | 6주차 — 카테고리별 정확도 |
| 02 | `02_apk_severity_heatmap.png` | APK × severity (12 APK, TP n=38 + FP n=9 표시) | 5/9주차 — APK별 심각도 |
| 03 | `03_fp_rate_trend.png` | Stage 1/2/3 오탐률 — PPT 가설 vs 실측 (n=18 초기 / n=47 최종). x축은 검증 단계, 시간 아님 | 6/8주차 — FP 25→12→7% |
| 04 | `04_deobf_accuracy_trend.png` | Corpus별 난독화 분포 + LLM rename 정확도 (MASTG hand-crafted / OSS NewPipe / PleOS) | 6주차 — 난독화 정확도 40→78% |
| 05 | `05_ablation_bars.png` | A 변형 (stage ablation) + B 변형 (합의 임계 sensitivity), combined n=47 | 9주차 — Ablation Study |
| 06 | `06_entropy_distribution.png` | 6 APK 의 obfuscation composite score 분포 (live data/deobf) | 6주차 — 난독화 강도 corpus 비교 |

## 차트별 해석

### 01 카테고리 분포 (combined n=47)

- **crypto (5/5 TP)**, **hardcoded (11/11 TP)**, **reflection_dynamic (1/1 TP)**: 100% Precision
- **intent (14 TP / 4 FP)**: 77.8% — VehicleControl deep-link FP 4건 (vc-1~4) 이 이 카테고리
- **network (7 TP / 2 FP)**: 77.8% — VehicleControl HtmlWebView 2건이 FP (Stage 2.b CONFIRMED)
- **permission (0 TP / 3 FP)**: 0% — VehicleControl AppPermissionManager 2 + usb.handler 1 모두 FP (OS/framework-level mitigation)
- → FP 9건이 intent/network/permission 3 카테고리에 집중. 모두 Stage 2 caller-chain + manifest 분석으로 강등, **Stage 3 ≥2/3 합의에서 제거되어 P 100%**.

### 02 APK × Severity 히트맵 (12 APK, n=47)

- **InsecureBankv2**: HIGH 7 + MEDIUM 2 — 의도된 vuln corpus, FP 0. 본 corpus 최다 finding.
- **sync.syslog**: HIGH 5 (ssl-1/2/4/5/6) + MEDIUM 1 (ssl-3). PleOS 자체 패키지 중 가장 위험. FP 0.
- **account / appmarket / ambientai**: R1.d.4/d.5 PleOS-customized — account HIGH 3+MED 2, appmarket HIGH 2+MED 1 (FP 1), ambientai HIGH 2+MED 1 (FP 2).
- **VehicleControl**: HIGH 1 + MEDIUM 1 + LOW 1 + **FP 4건 (vc-1~4 deep-link)**.
- **AOSP-derived** (usb.handler MED 2 / FP 1, statementservice FP 1): OS/framework-level mitigation 으로 FP 비율 높음.
- → FP 9건 = VehicleControl 4 + ambientai 2 + appmarket/usb.handler/statementservice 각 1. PleOS-customized 와 AOSP-derived 모두 Stage 2 가 essential.

### 03 FP rate 추이 — PPT 가설 vs 실측

- **1차 (Stage 1)**: PPT 25% / 실측 n=18 초기 22.2% / **n=47 최종 19.1%** — PPT 가설 충족
- **2차 (Stage 2)**: PPT 12% / 실측 0% — caller 추적이 모든 FP 제거 (P-ceiling)
- **3차 (Stage 3 ≥2/3)**: PPT 7% / 실측 0% — 멀티 프롬프트 ≥2/3 합의 (n=47 P 100% / R 97.4% / F1 0.987)
- **caveat**: Stage 1 → Stage 3 향상은 McNemar paired test 에서 통계적 유의 (p_exact=0.0215 < α=0.05, n=47).

### 04 Corpus별 난독화 분포 + LLM rename 정확도 (재설계 2026-05-06, 2026-05-14 NewPipe 추가)

corpus-level view — 시간축 추이가 아니라 corpus별 단일 측정:

- **MASTG hand-crafted (exact match)**:
  - UnCrackable-Level1: HIGH 50.0% / rename n=11 / exact 100%
  - UnCrackable-Level2: HIGH 40.0% / rename n=6 / exact 100%
  - r2pay-v1.0: HIGH 0.0% (난독화 약함) / 정확도 측정 X
- **OSS ProGuard (semantic plausibility)**:
  - NewPipe v0.27.6: HIGH 1.7% / rename n=6 / **GOOD+ 67%** (R4 — ProGuard mapping 부재로 exact 불가)
- **PleOS (측정 대상 부족)**: VehicleControl 0.2% / SyncSyslog 0.4% / LLMModelProvider 0.0% — 정확도 측정 X
- **해석**: hand-crafted MASTG 100% exact = upper-bound, real-world OSS NewPipe 67% GOOD+ = real-world floor. PPT 가설 5/6/8주차 40→65→78%는 reference로만.

### 05 Ablation 변형 (A: stage / B: 합의 임계), combined n=47

**Variant A (combined n=47)**:
- A.1 stage 1: P 80.9% / R 100% / F1 0.894
- A.2 stage 2 caller (P-ceiling): P 100% / R 100% / F1 1.000 (GT 기반 upper bound)
- A.3 stage 3 ≥3/3: P 100% / R 86.8% / F1 0.930

**Variant B (combined n=47, 멀티 프롬프트 합의 임계)**:
- ≥1/3 (any flag): P 84.4% / R 100% / F1 0.916
- **≥2/3 (default)**: P 100% / R 97.4% / **F1 0.987** ← PPT 가설 0.93 도달·초과
- ≥3/3 (unanimous): P 100% / R 86.8% / F1 0.930

→ **stage 2 caller 추적 + 멀티 프롬프트 ≥2/3 합의가 정량 차별 동력** (Stage 1 P 80.9% → Stage 3 ≥2/3 P 100%).

### 06 Entropy 분포 (6 APK obfuscation composite)

- **MASTG corpus**: UnCrackable-Level1 mean 0.618 / Level2 0.529. HIGH 임계 (0.7) 위 클래스 다수.
- **PleOS corpus**: 3종 모두 mean 0.03~0.05. HIGH 임계 위 클래스 0.2~0.4%만 존재.
- → **PleOS는 가정과 다르게 의미적 클래스명 유지** (release engineering / debug build). 본 corpus에서 deobf pipeline 효과는 작음. 외부 OWASP corpus에서는 100% 정확도로 검증. (본 차트는 `data/deobf/*.json` 라이브 로드 — obfuscation corpus 6 APK 고정)

## 재현

```bash
cd pleos-llm-scanner
python src/viz/plot_metrics.py
# → data/viz/01_*.png ~ 06_*.png 6 PNG 생성
```

데이터 출처:
- `data/ground_truth/combined_labels.json` (n=47 GT) — charts 01/02/05 의 분포는 이 파일 기준으로 `plot_metrics.py` 에 하드코딩
- `data/deobf/{6 APK}.json` (entropy 측정) — chart 06 라이브 로드
- charts 03/04 의 정량값: [`01_report.md`](01_report.md) § 3.2 / § 3.4 / § 3.6 + [`bootstrap_ci.md`](../data/reports/bootstrap_ci.md) / [`r4_real_world_baseline.md`](../data/reports/r4_real_world_baseline.md)

## 초기 계획서의 시각화 항목 충족 매트릭스

| 초기 계획서 항목 | 본 doc / chart 위치 |
|---|---|
| 3차 교차 검증 시각화 | Stage 3 멀티 프롬프트 앙상블 — chart 03 / 05 |
| 오탐률 12% → 7% 추이 | 측정값은 0% (chart 03) |
| 차트 / 히트맵 | chart 01~06 6장 |


---

## 변경 이력

### 2026-05-14 — combined n=47 재생성 (학기 외 A)

차트 01~05 를 R1.d.2~d.5 표본 확장 (n=19 → n=47) + Stage 3 ensemble 19건 반영해 재생성:

| 차트 | 이전 (n=18/n=19) | 현재 (combined n=47) |
|---|---|---|
| 01 카테고리 | 5 카테고리, TP 14 / FP 4 | 6 카테고리, TP 38 / FP 9 |
| 02 히트맵 | 4 APK | 12 APK (PleOS 7 + MASTG 2 + InsecureBankv2 + AOSP-derived 2) |
| 03 FP rate | Stage 1 22.2% | Stage 1 **19.1%** / Stage 3 ≥2/3 0% (McNemar p_exact=0.0215 유의) |
| 04 난독화 | MASTG + PleOS | + NewPipe OSS ProGuard (GOOD+ 67%) 추가 |
| 05 Ablation | A.1 F1 0.882 / B≥2/3 0.966 | A.1 F1 **0.894** / B≥2/3 **0.987** |
| 06 Entropy | (live data) | 변화 없음 — obfuscation corpus 6 APK 고정 |

`plot_metrics.py` 의 차트 01~05 데이터는 `combined_labels.json` n=47 분포로 하드코딩 갱신. `python src/viz/plot_metrics.py` 재실행으로 6 PNG 재생성.

### 2026-04-30 — L5 + L2 부분 해소 후 재측정 (당시 combined n=19)

| 변형 | 이전 (n=15/n=18) | 당시 (combined n=19) |
|---|---|---|
| A.1 stage 1 only | F1 0.846 → 0.875 | F1 0.882 |
| A.3 + stage 3 ≥3/3 | F1 0.783 (n=18 artifact) | F1 0.889 (artifact 해소) |
| B ≥2/3 (default) | F1 0.952 (PleOS-only n=15) | F1 0.966 |
| 1차 오탐률 | 22.2% (n=18) | 21.1% (n=19) |

해소 작업: L5 (ucl1-1/2/3 stage 3 ensemble 평가 추가), L2 부분 (UnCrackable-Level3 추가). 위 수치는 학기 외 A 작업으로 n=47 까지 확장됨 (상단 표 참조).
