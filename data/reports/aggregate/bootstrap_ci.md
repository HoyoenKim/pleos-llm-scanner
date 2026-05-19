# R1.b — Bootstrap CI for Stage 1 metrics

_Latest measurement: 2026-05-14 (R1.d.5, 학기 외 A) / scope: combined GT n=47 (PleOS-customized 30 + MASTG 4 + InsecureBankv2 9 + AOSP-derived 4)_

## 방법

`src/evaluation/eval.py --bootstrap 1000 --bootstrap-ci 0.95 --bootstrap-seed 42`. Non-parametric percentile bootstrap — n 라벨을 with-replacement 1000 회 resample → metric 분포 산출 → 2.5th / 97.5th percentile 로 95% CI.

## 결과 비교 (R1.d ~ R1.d.5 표본 확장 효과)

| Metric | n=19 (5/6) | n=28 (5/7) | n=37 (5/11 R1.d.4) | **n=47 (5/14 R1.d.5)** | Δ vs n=19 |
|---|---:|---:|---:|---:|---|
| Precision (lenient) point | 78.9% | 85.7% | 83.8% | **80.9%** | +2.0%p |
| Precision 95% CI | [57.9%, 94.7%] (36.8%p) | [71.4%, 96.4%] (25.0%p) | [73.0%, 94.6%] (21.6%p) | **[70.2%, 91.5%]** (21.3%p) | 폭 **-15.5%p** |
| F1 (lenient) point | 88.2% | 92.2% | 91.1% | **89.4%** | +1.2%p |
| F1 95% CI | [73.3%, 97.3%] (24.0%p) | [83.3%, 98.2%] (14.9%p) | [84.4%, 97.2%] (12.8%p) | **[82.5%, 95.6%]** (13.1%p) | 폭 **-10.9%p** |
| FP rate (lenient) point | 21.1% | 14.3% | 16.2% | **19.1%** | -2.0%p |
| FP rate 95% CI | [5.3%, 42.1%] (36.8%p) | [3.6%, 28.6%] (25.0%p) | [5.4%, 27.0%] (21.6%p) | **[8.5%, 29.8%]** (21.3%p) | 폭 **-15.5%p** |
| Recall | 100% | 100% | 100% | **100%** | 0 |

## 새 corpus (R1.d.2 expansion — android.car.usb.handler)

PleOS Connect 시스템 APK 중 AAOS-derived car USB host handler (system UID + MANAGE_USB + READ_PRIVILEGED_PHONE_STATE). 14 클래스 분석 후 3 finding 추가:
- usb-1 (MD5 weak hash for AOAP serial) — TP medium crypto
- usb-2 (UsbManager.grantPermission flow) — **FP** (PackageManager + AOAP permission check sound)
- usb-3 (Build.getSerial() + MD5 to USB accessory) — TP medium hardcoded

usb-2 FP 1건 추가로 Precision 85.7% → 83.9% 약간 후퇴. 그러나 PleOS context (AAOS-derived 시스템 component) 의 R1.d.2 첫 확장으로 GT diversity 강화.

## RQ1 implication

표본을 19 → 28 → 37 → 47 로 확장한 결과:
- **CI 폭이 약 40% 줄어듦** (n=19 → n=47 Precision 폭 36.8%p → 21.3%p, F1 24.0%p → 13.1%p). "n 증가 → CI 좁힘" 의 직접 측정.
- Precision lenient lower bound 가 57.9% → **70.2%** 로 안정화 (+12.3%p). 즉 corpus 가 n=47 일 때 Precision 의 통계적 보장 근거가 70.2% 이상 — 가설 25% FP rate (= Precision 75%) 가 lower bound 근처가 아니라 그 위.
- **point 값 변동 ≠ 통계적 보장 약화**: n=37 → n=47 에서 R1.d.5 신규 FP 3건 (am-4 / amb-4 / amb-5) 으로 Precision point 83.8% → 80.9% 후퇴했으나, CI 폭은 계속 좁아짐 (21.6%p → 21.3%p). point 후퇴는 PleOS-customized application code 의 진짜 FP 이므로 정직 기록.
- **R1.c McNemar 와 결합**: bootstrap CI 좁힘 (R1.b) + paired test 유의성 (R1.c, n=47 p_exact=0.0215) 둘 다 학기 외 A 작업에서 도달 — RQ1 의 통계적 보장 완성.
- **단 n ≥ 60 추가 확장**: 무료 commercial closed-source corpus 다운로드 시도 실패 (GitHub LFS pointer / HTML 404). Future Work 로 명시.

## 재현

```bash
python src/evaluation/eval.py \
    --labels data/ground_truth/combined_labels.json \
    --reports 'data/reports/ai.umos.vehiclecontrol_20260429.json' \
              'data/reports/ai.pleos.sync.syslog_20260429.json' \
              'data/reports/ai.pleos.llm.model.provider_20260429.json' \
              'data/reports/external/UnCrackable-Level1_20260430.json' \
              'data/reports/external/UnCrackable-Level3_20260430.json' \
              'data/reports/external/InsecureBankv2_20260507.json' \
              'data/reports/android.car.usb.handler_20260511.json' \
              'data/reports/com.android.statementservice_20260511.json' \
              'data/reports/ai.pleos.playground.account_20260511.json' \
              'data/reports/ai.umos.appmarket_20260514.json' \
              'data/reports/ai.umos.ambientai_20260514.json' \
              'data/reports/ai.umos.maps_20260514.json' \
    --by-stage stage1 \
    --bootstrap 1000 \
    --bootstrap-ci 0.95 \
    --bootstrap-seed 42
```

deterministic (seed 42) — 동일 commit 에서 동일 결과.

## 변경 이력

| 날짜 | n | Precision | F1 | FP rate | CI 폭 (Precision) | 비고 |
|---|---:|---:|---:|---:|---:|---|
| 2026-05-06 | 19 | 78.9% | 88.2% | 21.1% | 36.8%p | self+MASTG baseline |
| 2026-05-07 | 28 | 85.7% | 92.2% | 14.3% | 25.0%p (-11.8%p) | +InsecureBankv2 9 finding (모두 TP) |
| 2026-05-11 (R1.d.2) | 31 | 83.9% | 91.2% | 16.1% | 25.8%p (+0.8%p) | +android.car.usb.handler 3 finding (2 TP / 1 FP) |
| 2026-05-11 (R1.d.3) | 32 | 81.2% | 89.6% | 18.8% | 25.0%p (-0.8%p) | +com.android.statementservice 1 finding (0 TP / 1 FP) — AOSP-derived |
| 2026-05-11 (R1.d.4) | 37 | 83.8% | 91.1% | 16.2% | 21.6%p (-3.4%p) | +ai.pleos.playground.account 5 finding (5 TP / 0 FP) — PleOS-customized auth/SSO |
| **2026-05-14 (R1.d.5, 학기 외 A)** | **47** | **80.9%** | **89.4%** | **19.1%** | **21.3%p (-0.3%p)** | **+appmarket 4 + ambientai 5 + maps 1 = 10 finding (7 TP / 3 FP) — PleOS-customized. point 후퇴, CI 폭 계속 좁힘** |

## 표본 origin 별 정밀도 분리 (n=47)

| Origin | n | TP | FP | Precision | 비고 |
|---|---:|---:|---:|---:|---|
| PleOS-customized (`ai.umos.*`, `ai.pleos.*`) | 30 | 23 | 7 | **76.7%** | 사용자 변경 가능 application code. R1.d.5 3 APK 추가로 n=20 80.0% → n=30 76.7% (-3.3%p, FP 3건 am-4/amb-4/amb-5 영향). Stage 1 detect rule 의 가장 효과적 작동 영역 |
| AOSP-derived (`android.car.usb.handler`, `com.android.statementservice`) | 4 | 2 | 2 | **50.0%** | AOSP/AAOS 표준 system component — OS/framework-level mitigation 으로 Stage 2 FP 다수 |
| External vuln corpus (MASTG + InsecureBankv2) | 13 | 13 | 0 | **100.0%** | 의도된 vuln corpus — Stage 1 detect rule 의 upper bound 검증 |

**RQ1 implication 추가**: PleOS 적용 시 stage1 detect rule이 catch 하는 finding 중 AOSP-derived 컴포넌트는 OS-level mitigation 으로 FP 비율이 높음 → 본 파이프라인의 Stage 2 caller-chain 검증 + manifest 분석이 AOSP-derived 컴포넌트의 FP filter 에 essential. R1.d.5 추가 발견: PleOS-customized 도 ProGuard 활성 APK (maps) 와 application-tier FP (gleo navigation, explicit broadcast, signature gate) 가 섞여 있어 Stage 2 가 필수.
