# R3.a — Native lib inventory across PleOS Connect APKs

_Measured: 2026-05-06 / scope: 207 system APKs from PleOS Connect v2.0.5 emulator_

## Overall

| 지표 | 값 |
|---|---|
| Total APKs | 207 |
| APKs with at least one native lib | 22 (10.6%) |
| Total .so files | 221 |

## By origin

| Origin | n | with native | % | total .so |
|---|---|---|---|---|
| PleOS | 28 | 14 | 50.0% | 184 |
| AOSP | 174 | 6 | 3.4% | 15 |
| third-party | 5 | 2 | 40.0% | 22 |

## Top 15 APKs by .so count

| Rank | APK | .so count | Origin |
|---|---|---:|---|
| 1 | `ai.pleos.playground.caas` | 62 | PleOS |
| 2 | `ai.umos.maps.android.navigation.app` | 44 | PleOS |
| 3 | `ai.umos.ambientai` | 24 | PleOS |
| 4 | `com.antutu.benchmark.full.lite` | 20 | third-party |
| 5 | `ai.umos.appmarket` | 12 | PleOS |
| 6 | `ai.pleos.playground.account` | 8 | PleOS |
| 7 | `ai.umos.drivingview` | 8 | PleOS |
| 8 | `ai.umos.inputmethod` | 8 | PleOS |
| 9 | `ai.pleos.sync.syslog` | 4 | PleOS |
| 10 | `ai.umos.callandmessage` | 4 | PleOS |
| 11 | `ai.umos.sync.internal` | 4 | PleOS |
| 12 | `android.ext.services` | 3 | AOSP |
| 13 | `com.android.providers.media.module` | 3 | AOSP |
| 14 | `com.android.webview` | 3 | AOSP |
| 15 | `ai.umos.car.evs` | 2 | PleOS |

## RQ3 implication

PleOS Connect 시스템 APK 중 native lib 보유 비율은 **10.6%** (22/207). PleOS 자체 패키지 한정으로는 **50.0%** (14/28). 본 파이프라인은 Java-only 정적 분석이라 native 부분 (MASVS-CRYPTO / RESILIENCE 일부 위반 가능성) 미커버 — 한계 L1 의 corpus-level 인덱스. 차량 제어 / map navigation / 음성 비서 등 보안 가치가 큰 컴포넌트가 native 비중이 높은 점 (top 3: PleOS playground caas / maps navigation / ambientai) 은 추가 보강 필요성을 시사.
