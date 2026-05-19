# Case Studies

Representative cases from the final PleOS / AAOS IVI APK analysis. Public files do not reproduce proprietary PleOS code snippets or secret literals.

## Runtime Claim Levels

These levels describe how strong the evidence is for a case. The static `n=47` metric is separate from runtime claim strength.

| Level | Meaning | Boundary |
|---|---|---|
| L0 | Static-only evidence | Decompiled code, manifest, or config evidence only |
| L1 | Runtime reachability observed | Component invocation, provider query, broadcast delivery, Binder call, or hook trigger observed |
| L2 | Local data/state effect observed | Safe provider response, marker value, log emission, preference/database state change, or equivalent local effect observed |
| L3 | Emulator-visible UI/IVI behavior effect observed | Reversible UI marker, navigation effect, or emulator-visible IVI behavior observed |
| L4 | End-to-end exploit impact | Full exploit chain with externally meaningful impact |

This project does not claim L4 real-vehicle control unless explicitly supported by evidence. The final public docs use conservative claim levels.

## Case Map

| Finding | Category | Static Verdict | Conservative Claim Level | Why It Matters |
|---|---|---|---|---|
| `amb-1` | hardcoded credential | TP | L0 | production LLM API-key exposure pattern |
| `am-1` | exported provider / intent injection | TP | L0 unless runtime UI/state evidence is attached | AppMarket search suggestion surface reaches privileged intent context |
| `am-3` | hardcoded credential | TP | L0 | OAuth client-secret pattern in account flow |
| `acc-4` | exported component / secret flow | TP | L0 | SSO secret crosses an Activity boundary |
| `ssl-6` | plaintext transport | TP | L0 | gRPC plaintext in diagnostic/system-log context |
| `lmp-1` | exported provider | TP | L1/L2 when runtime response evidence is attached | IVI LLM prompt/corpus exposure surface |
| `vc-6` | exported receiver | TP | L0 unless runtime reachability evidence is attached | untrusted payload accepted by receiver under IVI threat model |
| `vc-3/4` | permission API | FP | L0 | caller route blocked |
| `usb-2` | USB permission path | FP | L0 | framework permission checks block exploitability |
| `ss-1` | exported receiver | FP | L0 | protected broadcast blocks normal-app trigger |
| `ssl-5` / `ucl1-1` | hardcoded crypto comparison | TP | L0 | PleOS self-label aligns with external MASTG pattern |

## Case Template Fields

Each case below uses the same public-safe frame:

- Finding
- Evidence type
- Required attacker capability
- Blocking controls checked
- Public-safe evidence breadcrumb
- Why Stage 1 flagged it
- Why Stage 2 kept or removed it
- Final claim level
- Not claimed
- Public redaction note

## Confirmed Static Findings

### `amb-1` - AmbientAI Production LLM API Key

| Field | Value |
|---|---|
| Finding | Production LLM API-key exposure pattern |
| Evidence type | Static decompiled-code evidence |
| Required attacker capability | APK access and reverse engineering; no privileged runtime access required for static extraction |
| Blocking controls checked | Dead/test string distinction, production call-site association, and secret-vs-identifier classification |
| Public-safe evidence breadcrumb | LLM API-key family literal in a production LLM call path; literal value redacted |
| Why Stage 1 flagged it | External LLM-style credential pattern appeared in production APK code |
| Why Stage 2 kept it | The value was associated with reachable production call paths, not only a dead string |
| Final claim level | L0 |
| Not claimed | No raw secret disclosure in public docs, no project-side external LLM API call, no runtime exploit chain |
| Public redaction note | Literal secret values are redacted |

### `am-1` - AppMarket Suggestions Provider Intent Surface

| Field | Value |
|---|---|
| Finding | Exported search-suggestions provider exposes an intent-bearing suggestion surface |
| Evidence type | Manifest/provider and decompiled-source context |
| Required attacker capability | Same-device normal app interacting with exported provider APIs under the local IVI threat model |
| Blocking controls checked | Provider export state, permission attribute, write surface, and whether the payload reaches a privileged UI intent context |
| Public-safe evidence breadcrumb | Exported `SearchRecentSuggestionsProvider` style surface with empty permission and an intent-URI field |
| Why Stage 1 flagged it | Provider and intent fields appeared in privileged AppMarket/search context |
| Why Stage 2 kept it | Static context supported a reportable local provider-to-intent boundary under the same-device model |
| Final claim level | L0 unless runtime marker or UI/state evidence upgrades it |
| Not claimed | No automatic install/uninstall, no real user-click proof, no real-vehicle effect |
| Public redaction note | Public docs keep proprietary code and raw UI/runtime evidence out of the repo |

### `am-3` - AppMarket OAuth Secret

| Field | Value |
|---|---|
| Finding | OAuth client-secret pattern in AppMarket account flow |
| Evidence type | Static decompiled-code and flow-context evidence |
| Required attacker capability | APK access and reverse engineering; no same-device runtime trigger needed for static extraction |
| Blocking controls checked | Secret-vs-client-ID distinction, account-flow context, and release-code relevance |
| Public-safe evidence breadcrumb | OAuth `client_secret` role near account-token retrieval logic; literal value redacted |
| Why Stage 1 flagged it | Credential-like `client_secret` material appeared near authentication code |
| Why Stage 2 kept it | The surrounding flow indicated production account integration rather than a harmless identifier |
| Final claim level | L0 |
| Not claimed | No public raw secret, no live account takeover demonstration |
| Public redaction note | Secret values are redacted |

### `acc-4` - SSO Activity Receives Secret Through Intent Extra

| Field | Value |
|---|---|
| Finding | SSO secret crosses an Activity boundary |
| Evidence type | Manifest and decompiled-source context |
| Required attacker capability | Same-device component interaction with the relevant Activity boundary |
| Blocking controls checked | Activity export state, intent-extra role, component boundary, and secret-vs-local-variable distinction |
| Public-safe evidence breadcrumb | Secret-like extra name crosses into SSO Activity handling; proprietary code omitted |
| Why Stage 1 flagged it | Secret-like extra name appeared in an Activity flow |
| Why Stage 2 kept it | The value crossed a component boundary and was not only an internal local variable |
| Final claim level | L0 |
| Not claimed | No raw secret, no runtime dump, no account compromise proof |
| Public redaction note | Public docs describe the boundary and omit proprietary code |

### `ssl-6` - SysLog gRPC Plaintext Transport

| Field | Value |
|---|---|
| Finding | Plaintext gRPC transport in diagnostic/system-log context |
| Evidence type | Static API-use evidence plus service context |
| Required attacker capability | Network attacker only for transport-risk interpretation; static finding itself is code evidence |
| Blocking controls checked | Production endpoint relevance, diagnostic context, cleartext API use, and dead-code risk |
| Public-safe evidence breadcrumb | `.usePlaintext()` style transport API in diagnostic/system-log service context |
| Why Stage 1 flagged it | `.usePlaintext()` appeared in network-client setup |
| Why Stage 2 kept it | The call was part of a diagnostic/system-log package rather than an unreachable sample |
| Final claim level | L0 |
| Not claimed | No packet capture, no active MITM demonstration, no remote exploit chain |
| Public redaction note | Endpoint and code excerpts stay redacted when needed |

### `lmp-1` - Exported LLM Prompt Provider

| Field | Value |
|---|---|
| Finding | Exported provider exposes LLM prompt/corpus surface |
| Evidence type | Manifest/provider evidence and selected runtime-provider track |
| Required attacker capability | Same-device normal app querying an exported provider in the IVI environment |
| Blocking controls checked | Provider export state, permission gate, caller verification, query behavior, and prompt/corpus sensitivity |
| Public-safe evidence breadcrumb | Exported prompt-provider surface with queryable prompt/corpus semantics; prompt contents omitted |
| Why Stage 1 flagged it | Provider and prompt/corpus terms appeared in a sensitive IVI LLM package |
| Why Stage 2 kept it | Provider exposure was security-relevant under the IVI LLM threat model |
| Final claim level | L1 or L2 only when runtime query/response evidence is attached; otherwise L0 |
| Not claimed | No public prompt dump, no remote exploit, no real-vehicle control |
| Public redaction note | Prompt/corpus contents are not reproduced in public docs |

### `vc-6` - VehicleBroadcastReceiver Payload Surface

| Field | Value |
|---|---|
| Finding | Exported receiver accepts untrusted MAC-like payload under IVI threat model |
| Evidence type | Static receiver, manifest, and payload-handling evidence |
| Required attacker capability | Same-device normal app sending an allowed receiver invocation or equivalent local component interaction |
| Blocking controls checked | Receiver export state, permission gate, action/payload shape, caller boundary, and runtime-upgrade requirement |
| Public-safe evidence breadcrumb | Vehicle-adjacent receiver consumes externally shaped payload data; proprietary code omitted |
| Why Stage 1 flagged it | Vehicle-adjacent receiver handled externally shaped payload data |
| Why Stage 2 kept it | The receiver surface remained relevant after contextual checks |
| Final claim level | Static TP at L0 unless runtime receiver invocation is observed; L1/L2 only with local evidence |
| Not claimed | No remote exploitation, no real-vehicle control, no actuation proof |
| Public redaction note | No proprietary code excerpts or vehicle-control secrets are published |

Final claim: `vc-6` is a static TP under the IVI threat model. It is not claimed as remote exploitation or real-vehicle control. Any stronger runtime claim must cite local evidence separately.

## False-Positive Control Cases

### `vc-3` / `vc-4` - Runtime Permission Grant/Revoke False Positive

| Field | Value |
|---|---|
| Finding | Permission-management API looked dangerous in Stage 1 |
| Evidence type | Decompiled API-use evidence plus caller-route context |
| Required attacker capability | Same-device normal app would need an external route to the permission-management screen/state |
| Blocking controls checked | Manifest exposure, Compose navigation route, deep-link binding, and internal router mapping |
| Public-safe evidence breadcrumb | Sensitive permission APIs exist, but package-name producer remains internally bound |
| Why Stage 1 flagged it | `grantRuntimePermission` / `revokeRuntimePermission` are sensitive APIs |
| Why Stage 2 removed it | Caller route was blocked by manifest, navigation, or internal binding constraints |
| Final claim level | L0 FP |
| Not claimed | No normal-app permission grant/revoke primitive |
| Public redaction note | Public docs summarize the route-blocking reason |

### `usb-2` - USB Permission Path False Positive

| Field | Value |
|---|---|
| Finding | USB permission path looked caller-controllable |
| Evidence type | Framework source and permission-check context |
| Required attacker capability | Normal app or accessory path would need to bypass framework permission checks |
| Blocking controls checked | `PackageManager` filtering, AOAP handler permission, and `MANAGE_USB` service requirement |
| Public-safe evidence breadcrumb | USB permission API appears in handler path, but framework filters are present |
| Why Stage 1 flagged it | USB permission APIs appeared in a security-sensitive component |
| Why Stage 2 removed it | Framework permission checks blocked the normal-app trigger path |
| Final claim level | L0 FP |
| Not claimed | No caller-controlled USB permission bypass |
| Public redaction note | Public docs keep this as a framework blocking-control example |

### `ss-1` - `BOOT_COMPLETED` Receiver False Positive

| Field | Value |
|---|---|
| Finding | Exported receiver looked externally triggerable |
| Evidence type | Manifest and Android protected-broadcast semantics |
| Required attacker capability | Normal app would need to emit `BOOT_COMPLETED`, which Android protects |
| Blocking controls checked | Protected-broadcast semantics and receiver triggerability |
| Public-safe evidence breadcrumb | Exported receiver exists, but trigger action is platform-protected |
| Why Stage 1 flagged it | Exported receiver and broadcast handling appeared suspicious |
| Why Stage 2 removed it | `BOOT_COMPLETED` is a protected broadcast, so a normal app cannot trigger the path |
| Final claim level | L0 FP |
| Not claimed | No normal-app trigger path |
| Public redaction note | Public docs describe only Android platform semantics |

## External Alignment Case

### `ssl-5` and `ucl1-1` - Hardcoded Crypto Pattern

| Field | Value |
|---|---|
| Finding | Hardcoded crypto material or comparison pattern |
| Evidence type | Static source-pattern evidence |
| Required attacker capability | APK access and reverse engineering for the static pattern |
| Blocking controls checked | Secret-vs-constant role, crypto use site, and alignment with external MASTG-style pattern |
| Public-safe evidence breadcrumb | PleOS hardcoded crypto pattern is compared against public MASTG-style sample |
| Why Stage 1 flagged it | Crypto-sensitive literals and comparison logic appeared in relevant code |
| Why Stage 2 kept it | PleOS self-label and external MASTG-style evidence aligned on the pattern |
| Final claim level | L0 |
| Not claimed | No raw sensitive literal in public docs |
| Public redaction note | Sensitive literals are not reproduced |

## Dynamic Verification Hooks

These hooks are completed verification infrastructure. Runtime capture remains environment-dependent and must not be confused with the static `n=47` metric.

| Finding | Hook Purpose | Metric Boundary |
|---|---|---|
| `vc-5` | observe implicit broadcast path | not part of static precision/recall |
| `vc-6` | observe receiver caller/source and payload | can upgrade claim only with captured runtime evidence |
| `ssl-2` | observe token-leak emission path | selected runtime evidence track |
| `ssl-5` | observe KDF passphrase use | selected runtime evidence track |
| `lmp-1` | confirm provider query caller and row exposure | can support L1/L2 claim strength |
