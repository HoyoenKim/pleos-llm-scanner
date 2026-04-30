# TARA Artifact — PleOS IVI APK Static Analysis

_Generated: 2026-04-30 (auto from `configs/aaos_mapping.yaml` + GT, TP-only)_

> ISO/SAE 21434 흐름을 정적 분석 결과에 매핑한 산출물. Attack Feasibility 등급은 정적
> 분석 단계의 추정치이며, 실차 시나리오 측정 후 갱신 필요.

## 1. Item Definition (Asset Catalog)

| Asset | Examples | Criticality | Impact if compromised |
|---|---|---|---|
| 차량 제어 명령 | seat / climate / door / engine commands, Gleo car action API | Severe | 차량 안전 손상, 운전자 위협 |
| 사용자 자격증명 | OAuth tokens, user_id / passwords, session keys | Major | 계정 탈취, 차량 원격 제어 |
| 개인정보 (PII) | UUID, 생년월일, 이메일, 이름, 위치 / 센서 데이터 | Major | GDPR/개인정보보호법 위반, 평판 손상 |
| 차량 식별자 | VIN, IMEI, systemID | Moderate | 차량 추적, 핀포인트 공격 |
| 진단/시스템 로그 | syslog, modem diagnostic, vehicle state telemetry | Moderate | 공격 표면 정보 수집, 차량 상태 추정 |
| LLM 시스템 프롬프트 / 모델 | IVI LLM system prompts, GGUF model files | Moderate | Prompt injection / model jailbreak / DoS |

## 2. Threat Scenarios (n = 15, TP only)

| ID | APK | Asset | Threats (STRIDE) | Impact | Feasibility | Risk | Treatment |
|---|---|---|---|---|---|---|---|
| TS-VC-5 | vehiclecontrol | 차량 제어 명령 | I | Severe | High | **Critical** | Avoid (must fix before release) |
| TS-VC-6 | vehiclecontrol | 차량 제어 명령 | S, T | Severe | High | **Critical** | Avoid (must fix before release) |
| TS-VC-7 | vehiclecontrol | 진단/시스템 로그 | I | Moderate | Low | **Low** | Accept with monitoring |
| TS-SSL-1 | syslog | 사용자 자격증명 | I | Major | Medium | **Medium** | Mitigate (next minor release) or Transfer |
| TS-SSL-2 | syslog | 사용자 자격증명 | I | Major | High | **High** | Mitigate (fix in current sprint) |
| TS-SSL-3 | syslog | 진단/시스템 로그 | I | Moderate | Low | **Low** | Accept with monitoring |
| TS-LMP-1 | provider | LLM 시스템 프롬프트 / 모델 | I | Major | High | **High** | Mitigate (fix in current sprint) |
| TS-LMP-2 | provider | LLM 시스템 프롬프트 / 모델 | D | Moderate | High | **Medium** | Mitigate (next minor release) or Transfer |
| TS-SSL-4 | syslog | 개인정보 (PII) | I | Major | High | **High** | Mitigate (fix in current sprint) |
| TS-SSL-5 | syslog | 사용자 자격증명 | I | Major | High | **High** | Mitigate (fix in current sprint) |
| TS-SSL-6 | syslog | 진단/시스템 로그 | I, T | Major | High | **High** | Mitigate (fix in current sprint) |
| TS-UCL1-1 | UnCrackable-Level1 | 사용자 자격증명 | I | Major | High | **High** | Mitigate (fix in current sprint) |
| TS-UCL1-2 | UnCrackable-Level1 | 사용자 자격증명 | I | Major | Medium | **Medium** | Mitigate (next minor release) or Transfer |
| TS-UCL1-3 | UnCrackable-Level1 | 사용자 자격증명 | I | Major | Medium | **Medium** | Mitigate (next minor release) or Transfer |
| TS-UCL3-1 | UnCrackable-Level3 | 사용자 자격증명 | I | Major | High | **High** | Mitigate (fix in current sprint) |

## 3. Risk Matrix (count of scenarios per cell)

| Impact \ Feasibility | High | Medium | Low |
|---|---|---|---|
| Severe | 2 | 0 | 0 |
| Major | 7 | 3 | 0 |
| Moderate | 1 | 0 | 2 |
| Negligible | 0 | 0 | 0 |

## 4. Risk Distribution

| Risk Level | Count | Treatment |
|---|---|---|
| **Critical** | 2 | Avoid (must fix before release) |
| **High** | 7 | Mitigate (fix in current sprint) |
| **Medium** | 4 | Mitigate (next minor release) or Transfer |
| **Low** | 2 | Accept with monitoring |

## 5. Top Concerns (Critical / High)

### TS-VC-5 — 차량 제어 명령 (Critical)
- **APK**: `ai.umos.vehiclecontrol`
- **Category**: intent (medium → medium)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Severe / High
- **Treatment**: Avoid (must fix before release)
- **Note**: GleoActionSender implicit broadcast — TP CONFIRMED, response JSON 외부 가시

### TS-VC-6 — 차량 제어 명령 (Critical)
- **APK**: `ai.umos.vehiclecontrol`
- **Category**: intent (medium → high)
- **Threats**: S (Spoofing), T (Tampering)
- **Impact / Feasibility**: Severe / High
- **Treatment**: Avoid (must fix before release)
- **Note**: VehicleBroadcastReceiver macAddress 미검증 — TP CONFIRMED, exported

### TS-SSL-2 — 사용자 자격증명 (High)
- **APK**: `ai.pleos.sync.syslog`
- **Category**: hardcoded (high → high)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: AuthData.toString() — TP HIGH, logcat 누출 가능

### TS-LMP-1 — LLM 시스템 프롬프트 / 모델 (High)
- **APK**: `ai.pleos.llm.model.provider`
- **Category**: intent (high → high)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: PromptsContentProvider exported — TP HIGH, prompt injection chain

### TS-SSL-4 — 개인정보 (PII) (High)
- **APK**: `ai.pleos.sync.syslog`
- **Category**: hardcoded (high → high)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: HmgUserInfo PII toString — TP HIGH, GDPR/개인정보보호법

### TS-SSL-5 — 사용자 자격증명 (High)
- **APK**: `ai.pleos.sync.syslog`
- **Category**: hardcoded (high → high)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: BuildConfig.IDENTIFIER as KDF passphrase — TP HIGH, ssl-1과 동일 chain의 hardcoded layer

### TS-SSL-6 — 진단/시스템 로그 (High)
- **APK**: `ai.pleos.sync.syslog`
- **Category**: network (medium → high)
- **Threats**: I (Information Disclosure), T (Tampering)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: gRPC .usePlaintext() — TP HIGH, 평문 syslog + systemID

### TS-UCL1-1 — 사용자 자격증명 (High)
- **APK**: `UnCrackable-Level1`
- **Category**: hardcoded (high → high)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: UnCrackable Level1 hardcoded AES key (sg.vantagepoint.uncrackable1.C0005a:15) — TP HIGH, MASVS-CRYPTO-1 / MASVS-STORAGE-2

### TS-UCL3-1 — 사용자 자격증명 (High)
- **APK**: `UnCrackable-Level3`
- **Category**: hardcoded (high → high)
- **Threats**: I (Information Disclosure)
- **Impact / Feasibility**: Major / High
- **Treatment**: Mitigate (fix in current sprint)
- **Note**: UnCrackable Level3 hardcoded XOR key passed to native init (sg.vantagepoint.uncrackable3.MainActivity:25) — TP HIGH, MASVS-CRYPTO-1 / MASVS-STORAGE-2


## 6. Methodology

- **Impact**: max(asset_criticality, severity_to_impact). 자산 본질적 가치와 finding 심각도 중 큰 값.
- **Attack Feasibility**: category + note 기반 룰. exported intent / hardcoded in APK / plaintext network → High.
- **Risk Matrix**: ISO/SAE 21434 단순화 4-tier (Critical / High / Medium / Low / Negligible).
- **Treatment**: Critical=Avoid, High=Mitigate(현 sprint), Medium=Mitigate(차 minor) 또는 Transfer, Low=Accept w/ monitoring.
- **Caveat**: Attack Feasibility는 정적 분석 단계 추정. 실차 시나리오 (네트워크 위치, 권한 grant 경로) 측정 후 재평가 필요.
