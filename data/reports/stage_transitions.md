# R1.a — Stage 1 → Stage 2 → Stage 3 transition matrix

_Measured: 2026-05-06 / scope: combined GT n=28 (PleOS self 15 + MASTG 4)_

## 단계 정의

- **Stage 1**: 모든 후보 finding 이 stage1_severity (high/medium/low) 로 emit 됨.
- **Stage 2**: caller chain + manifest + Stage 2.b deep-link 검증 후 라벨링한 GT (TP/FP/uncertain).
- **Stage 3**: 시각 3종 합의 (strong-TP=3/3, TP=2/3, uncertain=1/3, clean=0/3).

## Per-finding 전체 표

| ID | APK | Class | Line | Cat | S1 sev | S2 (GT) | S2 true sev | S3 class (count) |
|---|---|---|---:|---|---|---|---|---|
| `vc-1` | vehiclecontrol | `HtmlWebViewKt` | 58 | network | high | **FP** | low | **uncertain** (1) |
| `vc-2` | vehiclecontrol | `HtmlWebViewKt` | 82 | network | medium | **FP** | low | **uncertain** (1) |
| `vc-3` | vehiclecontrol | `AppPermissionManager` | 149 | permission | high | **FP** | none | **uncertain** (1) |
| `vc-4` | vehiclecontrol | `AppPermissionManager` | 124 | permission | high | **FP** | none | **uncertain** (1) |
| `vc-5` | vehiclecontrol | `GleoActionSender` | 40 | intent | medium | **TP** | medium | **strong-TP** (3) |
| `vc-6` | vehiclecontrol | `VehicleBroadcastReceiver` | 58 | intent | medium | **TP** | high | **strong-TP** (3) |
| `vc-7` | vehiclecontrol | `Broadcasts` | 92 | intent | low | **TP** | low | **uncertain** (1) |
| `ssl-1` | syslog | `ECCCrypto` | 49 | crypto | medium | **TP** | high | **strong-TP** (3) |
| `ssl-2` | syslog | `AuthData` | 82 | hardcoded | high | **TP** | high | **strong-TP** (3) |
| `ssl-3` | syslog | `CCGAuthenticator` | 49 | network | medium | **TP** | medium | **strong-TP** (3) |
| `lmp-1` | provider | `PromptsContentProvider` | 62 | intent | high | **TP** | high | **strong-TP** (3) |
| `lmp-2` | provider | `LLMModelProviderReceiver` | 43 | intent | medium | **TP** | medium | **strong-TP** (3) |
| `ssl-4` | syslog | `HMGAuthenticator$HmgUserInfo` | 365 | hardcoded | high | **TP** | high | **TP** (2) |
| `ssl-5` | syslog | `SyncConfigsProvider` | 83 | hardcoded | high | **TP** | high | **strong-TP** (3) |
| `ssl-6` | syslog | `SysLogService` | 76 | network | medium | **TP** | high | **strong-TP** (3) |
| `ucl1-1` | UnCrackable-Level1 | `C0005a` | 15 | hardcoded | high | **TP** | high | **strong-TP** (3) |
| `ucl1-2` | UnCrackable-Level1 | `C0000a` | 15 | crypto | medium | **TP** | medium | **strong-TP** (3) |
| `ucl1-3` | UnCrackable-Level1 | `C0005a` | 17 | crypto | low | **TP** | low | **TP** (2) |
| `ucl3-1` | UnCrackable-Level3 | `MainActivity` | 25 | hardcoded | high | **TP** | high | **strong-TP** (3) |
| `ib2-1` | InsecureBankv2 | `DoLogin` | 51 | network | high | **TP** | high | **strong-TP** (3) |
| `ib2-2` | InsecureBankv2 | `DoLogin` | 115 | hardcoded | high | **TP** | high | **strong-TP** (3) |
| `ib2-3` | InsecureBankv2 | `CryptoClass` | 22 | hardcoded | high | **TP** | high | **strong-TP** (3) |
| `ib2-4` | InsecureBankv2 | `CryptoClass` | 23 | crypto | high | **TP** | high | **strong-TP** (3) |
| `ib2-5` | InsecureBankv2 | `MyBroadCastReceiver` | 32 | intent | high | **TP** | high | **strong-TP** (3) |
| `ib2-6` | InsecureBankv2 | `AndroidManifest` | 64 | intent | high | **TP** | high | **strong-TP** (3) |
| `ib2-7` | InsecureBankv2 | `AndroidManifest` | 68 | intent | medium | **TP** | high | **strong-TP** (3) |
| `ib2-8` | InsecureBankv2 | `AndroidManifest` | 49 | intent | medium | **TP** | medium | **TP** (2) |
| `ib2-9` | InsecureBankv2 | `ViewStatement` | 30 | network | medium | **TP** | medium | **TP** (2) |

## Stage 1 severity → Stage 2 verdict

| Stage 1 severity | Stage 2 verdict | count |
|---|---|---:|
| high | FP | 3 |
| high | TP | 12 |
| low | TP | 2 |
| medium | FP | 1 |
| medium | TP | 10 |

## Stage 2 verdict → Stage 3 class

| Stage 2 (GT) | Stage 3 class | count |
|---|---|---:|
| FP | uncertain | 4 |
| TP | TP | 4 |
| TP | strong-TP | 19 |
| TP | uncertain | 1 |

## FP / TP flow

- Stage 2 에서 FP 로 라벨된 finding: **4건** (모두 PleOS VehicleControl)
  - Stage 3 에서 정상적으로 걸러짐 (clean/uncertain): **4건**
  - Stage 3 에서 잘못 promote 됨 (TP/strong-TP): **0건**
- Stage 2 에서 TP 로 라벨된 finding: **24건**
  - Stage 3 에서 유지 (TP/strong-TP): **23건**
  - Stage 3 에서 손실 (clean/uncertain — 보고 누락): **1건**

## RQ1 implication

- Stage 3 의 합의 임계 ≥2/3 가 Stage 2 의 모든 FP 를 정확히 걸렀다 (FP→clean/uncertain). 이는 Stage 3 가 단순 noise 가 아니라 정확한 filtering 을 한다는 직접 증거.
- 단, n=19 라 표본 우연성 배제 불가. **R1.b bootstrap CI / R1.d 표본 확장 (n ≥ 30) 후 paired McNemar 가 필요**.
- TP 손실 (Stage 2→3 에서 보고 누락) 은 합의 임계의 trade-off. 본 corpus 에서는 1건 발생 — recall hit 은 임계 ≥2/3 default 의 알려진 약점.
