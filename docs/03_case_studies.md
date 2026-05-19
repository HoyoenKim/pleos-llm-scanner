# Case Studies

Representative final cases from the 15-week PleOS IVI APK analysis. Code excerpts are not reproduced here; public files keep PleOS proprietary snippets redacted.

## Case Map

| Case | Finding | Type | Final Verdict | Why It Matters |
|---:|---|---|---|---|
| 1 | `amb-1` | hardcoded credential | TP | production LLM API key in AmbientAI |
| 2 | `am-3` | hardcoded credential | TP | HMG OAuth client secret in AppMarket |
| 3 | `acc-4` | exported component / secret flow | TP | SSO secret crosses Activity boundary |
| 4 | `ssl-6` | plaintext transport | TP | gRPC `.usePlaintext()` in SysLog |
| 5 | `lmp-1` | exported provider | TP | IVI LLM prompt/corpus disclosure |
| 6 | `vc-6` | vehicle-control spoofing | TP | exported receiver accepts untrusted MAC-like payload |
| 7 | `vc-3/4` | permission API | FP | caller route blocked |
| 8 | `usb-2` | USB permission path | FP | framework permission checks block exploitability |
| 9 | `ss-1` | exported receiver | FP | protected broadcast blocks normal-app trigger |
| 10 | `ssl-5` / `ucl1-1` | hardcoded crypto comparison | TP | PleOS self-label aligns with external MASTG pattern |

## 1. `amb-1` — AmbientAI Production LLM API Key

| Field | Value |
|---|---|
| APK | `ai.umos.ambientai` |
| Category | `hardcoded` |
| Stage 1 | HIGH |
| Final | TP HIGH |

`amb-1` is the most important credential finding in the final corpus. The APK contained an `sk-...` style external LLM API credential on a production call path. A related release-shipped test handler also repeated the same credential pattern, so the issue is not best described as a dead string.

Security impact:

- API key extraction by APK reverse engineering
- billing abuse or unauthorized API calls
- privacy risk when LLM requests contain voice/message/contact context

Recommended treatment:

- remove secrets from APK assets/classes
- rotate exposed credentials
- move LLM credential use to a server-side broker or KeyStore-bound trusted component

## 2. `am-3` — AppMarket HMG OAuth Secret

| Field | Value |
|---|---|
| APK | `ai.umos.appmarket` |
| Category | `hardcoded` |
| Stage 1 | HIGH |
| Final | TP HIGH |

`am-3` exposed HMG OAuth `client_id` and `client_secret` material in AppMarket. The finding matters because it connects to a related account/SSO flow (`acc-4`), creating a cross-APK credential-handling pattern rather than a single isolated string.

Security impact:

- global client identity exposure from one APK reverse
- credential reuse risk across AppMarket and Account flows
- server-side abuse until rotation and client hardening

## 3. `acc-4` — SSO Activity Receives Secret Through Intent Extra

| Field | Value |
|---|---|
| APK | `ai.pleos.playground.account` |
| Category | `intent` |
| Stage 1 | HIGH |
| Final | TP HIGH |

`SsoActivity` receives `user-client-secret` through an Intent extra. Intent extras are observable through crash dumps, instrumentation, logs, or same-device malicious apps depending on component exposure and caller controls.

This finding is connected to `am-3`: the same credential domain appears in both AppMarket and Account flows. The final interpretation is a systematic credential-boundary problem.

## 4. `ssl-6` — SysLog gRPC Plaintext Transport

| Field | Value |
|---|---|
| APK | `ai.pleos.sync.syslog` |
| Category | `network` |
| Stage 1 | MEDIUM |
| Final | TP HIGH |

The relevant pattern is not merely an `http://` string. The gRPC channel builder calls `.usePlaintext()`, which explicitly disables TLS transport. Because the service handles system/logging context, the finding was escalated to HIGH in final review.

Recommended treatment:

- use TLS channel credentials
- separate prod/dev endpoints
- enforce certificate validation and deployment policy

## 5. `lmp-1` — Exported LLM Prompt Provider

| Field | Value |
|---|---|
| APK | `ai.pleos.llm.model.provider` |
| Category | `intent` |
| Stage 1 | HIGH |
| Final | TP HIGH |

`PromptsContentProvider` exposes prompt/corpus material without a strong permission gate. In a normal Android app this would be information disclosure. In an IVI LLM context it is more specific: prompt/corpus leakage helps prepare prompt injection, jailbreak, or model-behavior probing attacks.

Recommended treatment:

- mark provider non-exported where possible
- require signature-level read permission
- split public metadata from prompt/system corpus

## 6. `vc-6` — VehicleBroadcastReceiver MAC Payload

| Field | Value |
|---|---|
| APK | `ai.umos.vehiclecontrol` |
| Category | `intent` |
| Stage 1 | MEDIUM |
| Final | TP HIGH / Critical TARA concern |

`VehicleBroadcastReceiver` accepts a MAC-like external payload and connects it to vehicle/Bluetooth state. Because the asset is vehicle control context, the final risk is higher than the initial category severity suggests.

Recommended treatment:

- restrict receiver to trusted caller
- require signature permission
- validate MAC format and trusted source
- prefer explicit in-process or bound-service channel

## 7. `vc-3` / `vc-4` — Runtime Permission Grant/Revoke FP

| Field | Value |
|---|---|
| APK | `ai.umos.vehiclecontrol` |
| Category | `permission` |
| Stage 1 | HIGH |
| Final | FP |

Stage 1 flagged calls to permission grant/revoke APIs. Stage 2 removed them because the external route was blocked by a combination of manifest, internal-only Compose navigation, route binding, and caller reachability constraints.

This is the cleanest example of why API-name search alone is insufficient.

## 8. `usb-2` — USB Permission Path FP

| Field | Value |
|---|---|
| APK | `android.car.usb.handler` |
| Category | `permission` |
| Stage 1 | HIGH |
| Final | FP |

Stage 1 saw a permission-relevant USB path. Contextual verification found framework-level constraints such as permission gating and component resolution. The path is security-sensitive, but not a confirmed caller-controlled vulnerability in this corpus.

## 9. `ss-1` — BOOT_COMPLETED Receiver FP

| Field | Value |
|---|---|
| APK | `com.android.statementservice` |
| Category | `intent` |
| Stage 1 | LOW |
| Final | FP |

An exported `BOOT_COMPLETED` receiver can look suspicious in a shallow scan. Android protects this broadcast, so a normal third-party app cannot simply spoof it. This case validates the protected-broadcast check in Stage 2.

## 10. `ssl-5` and `ucl1-1` — Hardcoded Crypto Pattern

| Finding | Source | Meaning |
|---|---|---|
| `ssl-5` | PleOS self-label | BuildConfig-derived material enters crypto/KDF path |
| `ucl1-1` | OWASP MASTG | hardcoded AES key in public challenge |

This comparison ties a PleOS-specific hardcoded credential/crypto pattern to an external vulnerable-corpus pattern. It does not prove the two are identical in exploitability, but it shows the detector is not only learning project-specific language.

## Dynamic Verification Hooks

The final artifact includes state-machine and Frida hook scaffolding for:

| Finding | Hook Purpose |
|---|---|
| `vc-5` | confirm implicit broadcast target at runtime |
| `vc-6` | observe receiver caller/source and payload |
| `ssl-2` | confirm token `toString()` emission |
| `ssl-5` | confirm BuildConfig material entering KDF |
| `lmp-1` | confirm provider query caller and row exposure |

These hooks are completed as verification infrastructure. Runtime capture remains environment-dependent and should not be confused with the static `n=47` metric.
