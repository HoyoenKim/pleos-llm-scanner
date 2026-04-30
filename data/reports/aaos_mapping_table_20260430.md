# AAOS / MASVS / TARA Mapping Table

_Generated: 2026-04-30 (deterministic from `configs/aaos_mapping.yaml` + GT)_

**n = 18** (PleOS self 15 + MASTG 3)

## 1. Finding-level Mapping

| ID | APK | Cat | Sev | TP | AAOS | MASVS | TARA Asset | Threats |
|---|---|---|---|---|---|---|---|---|
| vc-1 | vehiclecontrol | network | high | FP | 5.1 Communication Security | MASVS-NETWORK-1, MASVS-NETWORK-2 | 진단/시스템 로그 | I (Information Disclosure) |
| vc-2 | vehiclecontrol | network | medium | FP | 5.1 Communication Security | MASVS-NETWORK-1, MASVS-NETWORK-2 | 진단/시스템 로그 | T (Tampering) |
| vc-3 | vehiclecontrol | permission | high | FP | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-3 | 사용자 자격증명 | E (Elevation of Privilege) |
| vc-4 | vehiclecontrol | permission | high | FP | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-3 | 사용자 자격증명 | E (Elevation of Privilege), D (Denial of Service) |
| vc-5 | vehiclecontrol | intent | medium | ✓ | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-2 | 차량 제어 명령 | I (Information Disclosure) |
| vc-6 | vehiclecontrol | intent | medium | ✓ | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-2 | 차량 제어 명령 | S (Spoofing), T (Tampering) |
| vc-7 | vehiclecontrol | intent | low | ✓ | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-2 | 진단/시스템 로그 | I (Information Disclosure) |
| ssl-1 | syslog | crypto | medium | ✓ | 4.2 Credential Protection | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | 사용자 자격증명 | I (Information Disclosure) |
| ssl-2 | syslog | hardcoded | high | ✓ | 4.2 Credential Protection | MASVS-STORAGE-2, MASVS-CRYPTO-1, MASVS-AUTH-2 | 사용자 자격증명 | I (Information Disclosure) |
| ssl-3 | syslog | network | medium | ✓ | 5.1 Communication Security | MASVS-NETWORK-1, MASVS-NETWORK-2 | 진단/시스템 로그 | I (Information Disclosure) |
| lmp-1 | provider | intent | high | ✓ | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-2 | LLM 시스템 프롬프트 / 모델 | I (Information Disclosure) |
| lmp-2 | provider | intent | medium | ✓ | 3.7 Permission Model | MASVS-PLATFORM-1, MASVS-PLATFORM-2 | LLM 시스템 프롬프트 / 모델 | D (Denial of Service) |
| ssl-4 | syslog | hardcoded | high | ✓ | 4.2 Credential Protection | MASVS-STORAGE-2, MASVS-CRYPTO-1, MASVS-AUTH-2 | 개인정보 (PII) | I (Information Disclosure) |
| ssl-5 | syslog | hardcoded | high | ✓ | 4.2 Credential Protection | MASVS-STORAGE-2, MASVS-CRYPTO-1, MASVS-AUTH-2 | 사용자 자격증명 | I (Information Disclosure) |
| ssl-6 | syslog | network | medium | ✓ | 5.1 Communication Security | MASVS-NETWORK-1, MASVS-NETWORK-2 | 진단/시스템 로그 | I (Information Disclosure), T (Tampering) |
| ucl1-1 | UnCrackable-Level1 | hardcoded | high | ✓ | 4.2 Credential Protection | MASVS-STORAGE-2, MASVS-CRYPTO-1, MASVS-AUTH-2 (MASVS-CRYPTO-1, MASVS-STORAGE-2) | 사용자 자격증명 | I (Information Disclosure) |
| ucl1-2 | UnCrackable-Level1 | crypto | medium | ✓ | 4.2 Credential Protection | MASVS-CRYPTO-1, MASVS-CRYPTO-2 (MASVS-CRYPTO-1) | 사용자 자격증명 | I (Information Disclosure) |
| ucl1-3 | UnCrackable-Level1 | crypto | low | ✓ | 4.2 Credential Protection | MASVS-CRYPTO-1, MASVS-CRYPTO-2 (MASVS-STORAGE-3) | 사용자 자격증명 | I (Information Disclosure) |

## 2. AAOS Section Coverage

| AAOS Section | Findings | TP | HIGH |
|---|---|---|---|
| 3.7 Permission Model | 7 | 5 | 3 |
| 4.2 Credential Protection | 7 | 7 | 4 |
| 5.1 Communication Security | 4 | 2 | 1 |

## 3. TARA Asset × Threat Matrix (TP only)

| Asset \ Threat | S | T | I | D |
|---|---|---|---|---|
| LLM 시스템 프롬프트 / 모델 | 0 | 0 | 1 | 1 |
| 개인정보 (PII) | 0 | 0 | 1 | 0 |
| 사용자 자격증명 | 0 | 0 | 6 | 0 |
| 진단/시스템 로그 | 0 | 1 | 3 | 0 |
| 차량 제어 명령 | 1 | 1 | 1 | 0 |

## 4. Notes per Finding

- **vc-1** — WebView setAllowFileAccess — TP였다면 LFI 가능. FP CONFIRMED (Stage 2.b OTA-trusted source)
- **vc-2** — WebView loadUrl 미검증 — FP CONFIRMED (4중 차단)
- **vc-3** — AppPermissionManager grantRuntimePermission caller-controlled pkg — FP CONFIRMED (NavRouter binding 부재)
- **vc-4** — revokeRuntimePermission 동일 — FP CONFIRMED
- **vc-5** — GleoActionSender implicit broadcast — TP CONFIRMED, response JSON 외부 가시
- **vc-6** — VehicleBroadcastReceiver macAddress 미검증 — TP CONFIRMED, exported
- **vc-7** — registerReceiver flag 미지정 — TP LOW (API 34 hardening)
- **ssl-1** — ECCCrypto KDF (BuildConfig.IDENTIFIER) — TP HIGH, 모든 device 동일 키
- **ssl-2** — AuthData.toString() — TP HIGH, logcat 누출 가능
- **ssl-3** — CCGAuthenticator hardcoded endpoint + secret POST — TP MEDIUM
- **lmp-1** — PromptsContentProvider exported — TP HIGH, prompt injection chain
- **lmp-2** — LLMModelProviderReceiver 외부 앱 모델 삭제/process kill — TP MEDIUM
- **ssl-4** — HmgUserInfo PII toString — TP HIGH, GDPR/개인정보보호법
- **ssl-5** — BuildConfig.IDENTIFIER as KDF passphrase — TP HIGH, ssl-1과 동일 chain의 hardcoded layer
- **ssl-6** — gRPC .usePlaintext() — TP HIGH, 평문 syslog + systemID
- **ucl1-1** — UnCrackable Level1 hardcoded AES key (sg.vantagepoint.uncrackable1.C0005a:15) — TP HIGH, MASVS-CRYPTO-1 / MASVS-STORAGE-2
- **ucl1-2** — UnCrackable Level1 weak crypto (sg.vantagepoint.p000a.C0000a:15) — TP MEDIUM, MASVS-CRYPTO-1
- **ucl1-3** — UnCrackable Level1 unsafe storage (sg.vantagepoint.uncrackable1.C0005a:17) — TP LOW, MASVS-STORAGE-3
