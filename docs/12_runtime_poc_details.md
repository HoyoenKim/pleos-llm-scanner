# Runtime PoC Details

This document records the runtime PoC track that supports the final 15-week archive.

The PoC work is a bounded validation layer for selected static findings. It does not replace the main `n=47` static evaluation, and it does not change the Stage 1 / Stage 3 precision-recall metric. Its role is to decide whether a finding stays at static-only L0 or can be strengthened to L1, L2, or L3 under a same-device PleOS / AAOS emulator threat model.

## Claim Boundary

| Level | Runtime Meaning | Required Evidence |
|---|---|---|
| L0 | Static-only finding | Decompiled code, manifest, or config evidence only |
| L1 | Runtime reachability observed | Provider query, broadcast delivery, Activity launch, Binder call, or hook trigger |
| L2 | Local data or state effect observed | Provider response, marker write/read, log emission, preference/database diff, or equivalent local effect |
| L3 | Emulator-visible UI or IVI behavior observed | Reversible UI marker, navigation effect, or visible emulator behavior |
| L4 | End-to-end exploit impact | Not claimed by this project without explicit evidence |

Runtime PoC evidence is local-only unless it is redacted into public-safe summaries. Public documents may include claim level, target surface, sanitized row counts, booleans, hashes, exception classes, and screenshots with sensitive data removed. Raw APKs, decompiled code, prompt rows, logs, videos, screenshots, local runtime reports, and proprietary strings stay out of the public repo.

## Threat Model

The PoC track uses two in-scope actor models.

| Actor | Capability | Boundary |
|---|---|---|
| Same-device normal app | Can send ordinary intents, query exported providers, and interact with exported components as an unprivileged app. | No signature permission, system UID, root, or OEM credential is assumed unless a specific test says so. |
| Emulator lab actor | Can use ADB, a harness APK, Frida hooks, and local screenshots/log filters on an owner-authorized emulator. | Evidence refines claim level; it is not a remote attack model. |

Out of scope: remote vehicle control, real-vehicle actuation, production backend abuse, credential theft in the wild, full exploit chains, and any test that requires publishing proprietary PleOS evidence.

## Completed PoC Artifacts

| Artifact | Path | Role |
|---|---|---|
| Harness APK builder | `scripts/runtime_poc/research_runtime_poc_harness.py` | Builds a small local-only Android harness package, `org.codex.pleos.poc`, without Gradle. The harness drives provider, broadcast, Activity, Binder, and marker checks and logs sanitized metadata. |
| Evidence wrappers | `scripts/runtime_poc/record_*`, `scripts/runtime_poc/run_*` | Run or record selected emulator checks into local-only output directories. |
| Static-to-dynamic state machine | `src/dynamic/state_machine.py` | Deterministically routes selected findings from Stage 1 / Stage 2 into dynamic-observation correlation. It does not call an external LLM API. |
| Frida hook set | `src/dynamic/hooks/` | Observes caller UID, receiver payloads, provider query results, token/log emission paths, KDF passphrase use, and native command candidates. |
| Compromise scenario matrix | `scripts/research/research_compromise_scenarios.py` | Converts verified findings into safe local PoC feasibility, attacker position, required evidence, and claim status. |
| Prompt-leak attack primitive pack | `scripts/runtime_poc/research_prompt_leak_attack_primitive.py` | Builds a redacted demonstration that leaked prompt/corpus structure can guide prompt-aware input construction without calling a live backend. |

The harness intentionally records counts, booleans, hashes, exception classes, and redacted metadata rather than raw secrets or proprietary content.

## Evidence Summary

| Finding / Surface | Completed Runtime Result | Allowed Claim |
|---|---|---|
| `lmp-1` prompt provider | Same-device provider query path was exercised; prompt-provider rows were reachable without a permission denial in the emulator smoke track. | L1 provider reachability; L2 data-read strength when the local evidence pack captures redacted returned-row metadata. |
| `vc-6` vehicle broadcast receiver | Benign explicit broadcast delivery to the receiver was exercised, and the dry-run hook can observe the payload without database mutation. | L1 receiver reachability. L2 requires a captured benign state/log diff. No vehicle actuation claim. |
| PairedDevices provider control | `READ_PAIRED_DEVICES` / `WRITE_PAIRED_DEVICES` permission enforcement was observed. | Negative/control evidence showing the pipeline does not treat every provider-like surface as exploitable. |
| `am-1` AppMarket suggestions provider | Harness and evidence-check wrappers implement harmless marker write/read, cleanup, screenshot, and UI-window checks for the exported suggestions surface. | L2 only when marker write/read is captured; L3 only when the marker appears in UI under lab conditions. |
| `acc-4` SSO Activity boundary | A hook exists to observe client-parameter boundary behavior around the exported SSO Activity. | Runtime infrastructure exists; no production OAuth token exchange is claimed. |
| `ssl-2` AuthData token emission | A hook exists to observe whether an AuthData token-like field reaches a log/emission path. | L2 only with synthetic or redacted emission evidence; no live credential collection claim. |
| `ssl-5` KDF passphrase use | A hook exists to observe the static BuildConfig-derived KDF passphrase path. | Runtime corroboration of a static crypto design issue; no derived production keys are published. |
| `vc-5` implicit broadcast path | A hook exists to observe implicit-broadcast behavior and caller/payload metadata. | Runtime reachability only unless a local state or response effect is captured. |
| Native command candidate | A hook exists to capture native command invocation candidates. | Observation infrastructure only; no additional native-bound vulnerability is claimed from this hook alone. |

## Per-Finding Notes

### `lmp-1` - Prompt Provider Read

The static finding is an exported IVI LLM prompt/corpus provider without an adequate caller gate. The runtime PoC asks whether a same-device caller can query the provider and receive rows.

Public-safe evidence may include row count, provider URI family, caller UID class, exception status, and redacted schema information. It must not include raw prompt text or proprietary prompt rows.

Allowed claim: same-device prompt-provider read primitive under emulator conditions. This supports L1, and it supports L2 when returned-row metadata is captured in a redacted local evidence pack.

Not claimed: jailbreak success, production backend compromise, raw prompt disclosure in the public artifact, or vehicle control.

### `vc-6` - Vehicle Broadcast Receiver

The static finding is an exported receiver that accepts a vehicle-adjacent payload. The runtime PoC sends a benign local marker broadcast or uses a dry-run Frida hook to observe the receiver path without mutating paired-device state.

Allowed claim: receiver reachability from a same-device actor. This is L1 unless a pre/post state or log diff proves a benign local state effect.

Not claimed: real-vehicle control, physical actuation, safety-critical command execution, or remote exploitability.

### PairedDevices Provider Control

This control case is important because it shows the runtime track can also prove blocking controls. Permission enforcement for `READ_PAIRED_DEVICES` and `WRITE_PAIRED_DEVICES` prevents the report from treating every provider-shaped surface as exploitable.

Allowed claim: negative/control validation of permission gating.

### `am-1` - AppMarket Suggestions Marker

The PoC harness supports a harmless marker write/read path against the AppMarket suggestions surface, followed by cleanup. Optional UI checks search for the marker in the emulator UI.

Allowed claim: L2 only when marker write/read evidence is captured. L3 requires the marker to become visible in the AppMarket/global-search UI under lab conditions.

Not claimed: install hijack, AppMarket compromise, credential abuse, or persistent malicious app installation.

### `acc-4` - SSO Activity Boundary

The static finding concerns a secret-bearing SSO parameter crossing an Activity boundary. The runtime hook is used only to observe boundary behavior with benign or redacted inputs.

Allowed claim: runtime boundary instrumentation exists. Stronger claims require local evidence showing parameter exposure under the same-device model.

Not claimed: production OAuth token exchange, account takeover, or live backend abuse.

### `ssl-2` and `ssl-5` - Syslog Token / KDF Paths

The syslog hooks target two different proof goals.

| Finding | Hook Goal | Claim Boundary |
|---|---|---|
| `ssl-2` | Observe whether token-like AuthData reaches a log/emission path. | Use synthetic or redacted evidence only; do not collect live tokens. |
| `ssl-5` | Observe whether a BuildConfig-derived constant reaches the KDF passphrase path. | Demonstrates design weakness; do not publish production keys or decrypted configs. |

### `vc-5` and Native Command Candidate

The `vc-5` and native-command hooks are runtime-observation infrastructure. They are useful for future or local-only correlation, but they do not independently change the final `n=47` metric.

## Relationship To Static Evaluation

The main quantitative result remains:

| Evaluation Step | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Stage 1 candidate generation | 38 | 9 | 0 | 80.9% | 100.0% | 0.894 |
| Stage 3 `>=2/3` verified reporting | 37 | 0 | 1 | 100.0% | 97.4% | 0.987 |

Runtime PoC evidence should be read as claim-strengthening evidence for selected rows, not as an additional row-level classifier. A static TP can stay L0 if runtime evidence is absent. A static FP can remain FP even if a related component exists, when permissions, protected broadcasts, route binding, or caller controls block the threat model.

## Public / Local Split

| Data Type | Public? | Reason |
|---|---|---|
| Claim level, target surface, sanitized status | Yes | Needed for evaluator understanding |
| Harness and hook source code | Yes, when it contains no proprietary code or secrets | Reproducibility and method transparency |
| Raw APKs and JADX output | No | Proprietary / local-only evidence |
| Raw runtime logs, screenshots, videos | No | May contain proprietary UI, prompt rows, or local device state |
| Full prompt/corpus rows, secrets, tokens, keys | No | Sensitive content |
| Redacted hashes, booleans, counts, exception classes | Yes | Public-safe evidence breadcrumbs |

## Final Interpretation

The PoC track shows that selected static findings were translated into safe, owner-authorized emulator checks. It provides concrete runtime support for provider reachability, receiver reachability, marker-based local state checks, and permission-gating controls.

It does not turn the project into an exploit campaign. The final claim remains an LLM-assisted static security-analysis artifact with bounded runtime validation for selected high-value rows.
