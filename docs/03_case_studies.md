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
| `am-3` | hardcoded credential | TP | L0 | OAuth client-secret pattern in account flow |
| `acc-4` | exported component / secret flow | TP | L0 | SSO secret crosses an Activity boundary |
| `ssl-6` | plaintext transport | TP | L0 | gRPC plaintext in diagnostic/system-log context |
| `lmp-1` | exported provider | TP | L1/L2 when runtime response evidence is attached | IVI LLM prompt/corpus exposure surface |
| `vc-6` | exported receiver | TP | L0 unless runtime reachability evidence is attached | untrusted payload accepted by receiver under IVI threat model |
| `vc-3/4` | permission API | FP | L0 | caller route blocked |
| `usb-2` | USB permission path | FP | L0 | framework permission checks block exploitability |
| `ss-1` | exported receiver | FP | L0 | protected broadcast blocks normal-app trigger |
| `ssl-5` / `ucl1-1` | hardcoded crypto comparison | TP | L0 | PleOS self-label aligns with external MASTG pattern |

## 1. `amb-1` - AmbientAI Production LLM API Key

| Field | Value |
|---|---|
| Finding | Production LLM API-key exposure pattern |
| Evidence type | Static decompiled-code evidence |
| Why Stage 1 flagged it | External LLM-style credential pattern appeared in production APK code |
| Why Stage 2 kept it | The value was associated with reachable production call paths, not only a dead string |
| Final claim level | L0 |
| Public redaction note | Literal secret values are redacted |

Final claim: `amb-1` is a confirmed credential-exposure finding in the static corpus. The public artifact does not publish the secret literal.

## 2. `am-3` - AppMarket OAuth Secret

| Field | Value |
|---|---|
| Finding | OAuth client-secret pattern in AppMarket account flow |
| Evidence type | Static decompiled-code and flow-context evidence |
| Why Stage 1 flagged it | Credential-like `client_secret` material appeared near authentication code |
| Why Stage 2 kept it | The surrounding flow indicated production account integration rather than a harmless identifier |
| Final claim level | L0 |
| Public redaction note | Secret values are redacted |

Final claim: `am-3` is a confirmed static credential finding. It is not presented as a completed account-takeover exploit.

## 3. `acc-4` - SSO Activity Receives Secret Through Intent Extra

| Field | Value |
|---|---|
| Finding | SSO secret crosses an Activity boundary |
| Evidence type | Manifest and decompiled-source context |
| Why Stage 1 flagged it | Secret-like extra name appeared in an Activity flow |
| Why Stage 2 kept it | The value crossed a component boundary and was not only an internal local variable |
| Final claim level | L0 |
| Public redaction note | Public docs describe the boundary and omit proprietary code |

Final claim: `acc-4` is a confirmed boundary-crossing secret-flow finding in the static corpus.

## 4. `ssl-6` - SysLog gRPC Plaintext Transport

| Field | Value |
|---|---|
| Finding | Plaintext gRPC transport in diagnostic/system-log context |
| Evidence type | Static API-use evidence plus service context |
| Why Stage 1 flagged it | `.usePlaintext()` appeared in network-client setup |
| Why Stage 2 kept it | The call was part of a diagnostic/system-log package rather than an unreachable sample |
| Final claim level | L0 |
| Public redaction note | Endpoint and code excerpts stay redacted when needed |

Final claim: `ssl-6` is a confirmed static transport-security finding.

## 5. `lmp-1` - Exported LLM Prompt Provider

| Field | Value |
|---|---|
| Finding | Exported provider exposes LLM prompt/corpus surface |
| Evidence type | Manifest/provider evidence and selected runtime-provider track |
| Why Stage 1 flagged it | Provider and prompt/corpus terms appeared in a sensitive IVI LLM package |
| Why Stage 2 kept it | Provider exposure was security-relevant under the IVI threat model |
| Final claim level | L1 or L2 only when runtime query/response evidence is attached; otherwise L0 |
| Public redaction note | Prompt/corpus contents are not reproduced in public docs |

Final claim: `lmp-1` is a confirmed static provider-exposure finding. Runtime evidence can upgrade the claim to reachability or local data exposure, but the static metric does not depend on that runtime track.

## 6. `vc-6` - VehicleBroadcastReceiver Payload Surface

| Field | Value |
|---|---|
| Finding | Exported receiver accepts untrusted MAC-like payload under IVI threat model |
| Evidence type | Static receiver, manifest, and payload-handling evidence |
| Why Stage 1 flagged it | Vehicle-adjacent receiver handled externally shaped payload data |
| Why Stage 2 kept it | The receiver surface remained relevant after contextual checks |
| Final claim level | Static TP at L0 unless runtime receiver invocation is observed; L1/L2 only with local evidence |
| Public redaction note | No proprietary code excerpts or vehicle-control secrets are published |

Final claim: `vc-6` is a static TP under the IVI threat model. It is not claimed as remote exploitation or real-vehicle control. Any stronger runtime claim must cite local evidence separately.

## 7. `vc-3` / `vc-4` - Runtime Permission Grant/Revoke False Positive

| Field | Value |
|---|---|
| Finding | Permission-management API looked dangerous in Stage 1 |
| Evidence type | Decompiled API-use evidence plus caller-route context |
| Why Stage 1 flagged it | `grantRuntimePermission` / `revokeRuntimePermission` are sensitive APIs |
| Why Stage 2 removed it | Caller route was blocked by manifest, navigation, or internal binding constraints |
| Final claim level | L0 FP |
| Public redaction note | Public docs summarize the route-blocking reason |

Final claim: these rows are false positives in the final corpus.

## 8. `usb-2` - USB Permission Path False Positive

| Field | Value |
|---|---|
| Finding | USB permission path looked caller-controllable |
| Evidence type | Framework source and permission-check context |
| Why Stage 1 flagged it | USB permission APIs appeared in a security-sensitive component |
| Why Stage 2 removed it | Framework permission checks blocked the normal-app trigger path |
| Final claim level | L0 FP |
| Public redaction note | Public docs keep this as a framework blocking-control example |

Final claim: `usb-2` is a false positive and is useful as a Stage 2 control case.

## 9. `ss-1` - `BOOT_COMPLETED` Receiver False Positive

| Field | Value |
|---|---|
| Finding | Exported receiver looked externally triggerable |
| Evidence type | Manifest and Android protected-broadcast semantics |
| Why Stage 1 flagged it | Exported receiver and broadcast handling appeared suspicious |
| Why Stage 2 removed it | `BOOT_COMPLETED` is a protected broadcast, so a normal app cannot trigger the path |
| Final claim level | L0 FP |
| Public redaction note | Public docs describe only Android platform semantics |

Final claim: `ss-1` is a false positive in the final corpus.

## 10. `ssl-5` and `ucl1-1` - Hardcoded Crypto Pattern

| Field | Value |
|---|---|
| Finding | Hardcoded crypto material or comparison pattern |
| Evidence type | Static source-pattern evidence |
| Why Stage 1 flagged it | Crypto-sensitive literals and comparison logic appeared in relevant code |
| Why Stage 2 kept it | PleOS self-label and external MASTG-style evidence aligned on the pattern |
| Final claim level | L0 |
| Public redaction note | Sensitive literals are not reproduced |

Final claim: these rows show that the PleOS self-label pattern aligns with an external vulnerable-corpus pattern.

## Dynamic Verification Hooks

These hooks are completed verification infrastructure. Runtime capture remains environment-dependent and must not be confused with the static `n=47` metric.

| Finding | Hook Purpose | Metric Boundary |
|---|---|---|
| `vc-5` | observe implicit broadcast path | not part of static precision/recall |
| `vc-6` | observe receiver caller/source and payload | can upgrade claim only with captured runtime evidence |
| `ssl-2` | observe token-leak emission path | selected runtime evidence track |
| `ssl-5` | observe KDF passphrase use | selected runtime evidence track |
| `lmp-1` | confirm provider query caller and row exposure | can support L1/L2 claim strength |
