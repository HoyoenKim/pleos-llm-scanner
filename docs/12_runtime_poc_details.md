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

## Main PoC Storyline

The main runtime PoC is the combined IVI chain, not the isolated LLM-provider demo.

The scenario starts from a realistic Android/AAOS precondition: an attacker has already installed and launched one same-device untrusted app. The app is not assumed to be a platform-signed PleOS component. From that position, the PoC shows two IVI-relevant primitives in one attacker-controlled UI.

1. The attacker app sends a route request through the exported NaviService Binder surface.
2. Maps renders a visible route preview for the attacker-supplied destination marker.
3. The attacker app returns to its own UI.
4. The same app invokes a weakly protected VehicleService property path.
5. The run records `MIRROR_FOLD` before/set/after/restore evidence as a reversible vehicle-property mutation.

The resulting safety argument is conditional and should be stated exactly:

| Assumption | Evidence In This Project | Safety Interpretation |
|---|---|---|
| Assumption 1: route selection is trusted by downstream autonomous or assisted-driving logic | The PoC confirms same-device route UI injection / route preview through NaviService. | If autonomous driving or assisted route-following trusts the injected route state, this becomes a route-influence hazard. The project does not independently prove autonomous-driving takeover. |
| Assumption 2: route influence alone is insufficient, but vehicle-property mutation can affect driver or vehicle state | The PoC confirms reversible `MIRROR_FOLD` mutation through VehicleService. A separate earlier pentest track showed emulator VHAL `GEAR_POSITION=D` spoofing through ADB-root `car_service` injection. | Even without autonomous driving, weak vehicle-property paths are safety-relevant because they can affect manual-driving context, driver visibility/attention, or vehicle-state assumptions. The same-device app path proves `MIRROR_FOLD`, while the VHAL gear-position evidence remains a separate stronger emulator-only risk track. |

Allowed main claim:

> Under a same-device malicious-app threat model, the combined PoC confirms that an unprivileged app can trigger visible route-setting behavior through NaviService and can mutate a reversible vehicle property through VehicleService. If downstream driving or IVI logic trusts those route/property states, the chain is safety-relevant and should be treated as a potential IVI compromise path.

Not claimed:

- remote vehicle compromise
- autonomous-driving takeover as a completed exploit
- attacker-triggered automatic guidance start unless separately proven
- active-route hijack of a user trip
- steering, brake, powertrain, or gear control from the same-device app harness
- real-vehicle actuation

The `lmp-1` prompt-provider PoC remains a strong companion story for IVI LLM boundary exposure, but it is no longer the main runtime-impact narrative.

## Evidence Summary

| Finding / Surface | Completed Runtime Result | Allowed Claim |
|---|---|---|
| `chain-1` combined IVI app | One attacker-controlled harness UI drives NaviService route preview and VehicleService `MIRROR_FOLD` mutation in the same live replay. | Main PoC: same-device route influence plus reversible vehicle-property mutation. Safety impact is conditional on downstream trust in route/property state. |
| `navi-1` NaviService route request | The attacker app sends a route request through exported NaviService Binder and Maps renders the attacker-supplied destination as visible route UI. | L3 emulator-visible route UI injection. Do not call it autonomous-driving takeover or automatic guidance start. |
| `vs-1` VehicleService property mutation | The attacker app binds to VehicleService and records `MIRROR_FOLD before=false -> set=true -> after=true -> restore=false`. | L2/L3 reversible vehicle-property mutation under emulator conditions, depending on whether the UI/state evidence is cited. |
| `vhal-pentest-1` gear-position spoofing | Separate earlier pentest evidence showed emulator VHAL `GEAR_POSITION=D` spoofing through ADB-root `car_service` injection. | Supports the broader safety concern around vehicle-state trust. It is not the same same-device app Binder path and must remain separate from `chain-1`. |
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

### `chain-1`, `navi-1`, and `vs-1` - Combined IVI Route / Property Chain

The combined chain is the main PoC narrative for runtime impact.

The attacker position is a same-device app. The route step uses NaviService Binder to request an attacker-supplied destination and records Maps route-preview UI. The vehicle-property step uses VehicleService to mutate the reversible `MIRROR_FOLD` property and then restore it.

Public-safe evidence may include the route marker string, route-preview screenshots with sensitive UI removed, sanitized Binder result lines, `MIRROR_FOLD` before/set/after/restore status, and the local video path. It must not include proprietary code, raw logs with sensitive state, or claims about real vehicles.

Allowed claim: same-device app can influence route-setting UI and mutate a reversible vehicle property in the emulator. This is safety-relevant when downstream autonomous, assisted-driving, or manual-driving workflows trust those IVI route/property states.

Not claimed: real-vehicle actuation, automatic route-following takeover, active-route hijack, steering/brake/gear/powertrain control from the same-device app, or remote exploitability.

The separate VHAL gear-position pentest track strengthens the concern that vehicle-state assumptions can be safety-relevant, but it used ADB-root `car_service` injection and must not be merged into the same-device app claim.

### `lmp-1` - Prompt Provider Read

The `lmp-1` demo is the companion PoC for IVI LLM boundary exposure.

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

The PoC track shows that selected static findings were translated into safe, owner-authorized emulator checks.

The main runtime story is now the combined IVI route/property chain: a same-device untrusted app can trigger route-setting UI through NaviService and mutate a reversible VehicleService property. Under the explicit assumption that downstream autonomous, assisted-driving, or manual-driving workflows trust these IVI route/property states, this is a safety-relevant compromise path.

The companion runtime story is `lmp-1`: the same-device attacker model can cross an IVI LLM provider boundary and read prompt/corpus output that should have been permission-gated.

Neither story turns the project into a remote exploit or real-vehicle takeover claim. The final claim remains an LLM-assisted static security-analysis artifact with bounded runtime validation for selected high-value rows.
