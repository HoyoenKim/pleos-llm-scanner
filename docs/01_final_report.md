# LLM-Assisted Security Analysis of PleOS/AAOS IVI APKs

This report is the measured-claim source of truth for the final 15-week archive.

Completed reinforcement experiments A-E are integrated into the final result and are summarized only as supporting tracks here; detailed A-E records live in `08_completed_reinforcements.md`.

## 1. Problem

PleOS / AAOS IVI APKs combine Android application surfaces with vehicle-adjacent permissions, exported components, local providers, and system integrations.

A keyword scan or one-pass LLM review can identify suspicious code, but Android exploitability depends on context: manifest export state, caller reachability, permissions, route binding, protected broadcasts, and trust boundaries.

The project therefore evaluates an LLM-assisted APK security-analysis pipeline where the LLM is not a standalone scanner. It is used as a reasoning component between deterministic triage and Android-domain contextual verification.

## 2. Threat Model

The final claims use a conservative Android/IVI threat model.

| Attacker Model | In Scope | Boundary |
|---|---|---|
| Same-device normal app | Non-privileged app can send ordinary intents, query exported providers, and interact with exported components. | No signature, system UID, or privileged permission is assumed unless stated. |
| Local IVI integration abuse | Exported components, local providers, custom actions, and local LLM or account surfaces. | Supports IVI isolation and data-exposure claims, not real-vehicle actuation claims. |
| Network attacker | Cleartext transport, missing TLS validation, or sensitive network-client configuration. | No remote code execution or remote vehicle control is assumed from static evidence alone. |
| Emulator / runtime lab actor | Harness APKs, ADB probes, and Frida hooks can record provider reads, broadcasts, Binder calls, state changes, or UI markers. | Runtime traces refine claim level; they do not change the static `n=47` precision/recall metric. |

Out of scope: remote vehicle control, real-vehicle actuation, privilege escalation that depends on undisclosed OEM credentials, and exhaustive proof of every possible Android reachability path.

## 3. Approach

The final pipeline is:

```text
APK
  -> jadx --deobf
  -> keyword triage
  -> Stage 0 obfuscation check
  -> Stage 1 LLM candidate detection
  -> Stage 2 contextual verification
  -> Stage 3 multi-perspective consensus
  -> AAOS / MASVS / TARA mapping
```

| Stage | Role | Final Interpretation |
|---|---|---|
| Stage 0 | Obfuscation and rename-plausibility screen | Boundary/robustness check, not the dominant obstacle in this corpus |
| Stage 1 | High-recall candidate generation | Useful for finding suspicious rows, but not sufficient for reporting |
| Stage 2 | Semi-automated contextual verification | Manifest, caller-chain, permission, route, component, and protected-broadcast checks |
| Stage 3 | Same-model multi-perspective consensus | Attacker, defender, and IVI-domain views; `>=2/3` is the final reporting threshold |
| Mapping | Automotive-security translation | AAOS / MASVS / TARA labels and risk-language output |

Stage 3 is multi-perspective consensus, not a multi-vendor model ensemble. The Codex 3-model cross-read was a separate reinforcement check and did not outperform the calibrated Stage 3 baseline.

## 4. Dataset And Labels

The final labelled corpus contains `n=47` finding-level rows.

| Origin | Findings | TP | FP | Precision | Role |
|---|---:|---:|---:|---:|---|
| PleOS-customized | 30 | 23 | 7 | 76.7% | Main IVI security target |
| External vulnerable corpus | 13 | 13 | 0 | 100.0% | OWASP MASTG and InsecureBankv2 control evidence |
| AOSP-derived / framework-like | 4 | 2 | 2 | 50.0% | Framework blocking and false-positive controls |
| Total | 47 | 38 | 9 | 80.9% | Final combined GT |

### 4.1 Finding Unit

A finding row is one security-relevant candidate with a stable `(apk, entrypoint or class, sink/source pattern, category)` identity. The metric is finding-level, not APK-level and not line-level.

Rows are split when the entrypoint differs, the sink/source pattern differs, the security consequence differs, or the row is needed as a separate TP/FP control for a contextual rule.

Rows are grouped when nearby lines implement the same root cause, repeated constants belong to the same credential exposure, or helper calls are part of one exploitability argument.

This definition keeps `n=47` tied to reportable candidate units rather than raw grep hits or APK counts.

### 4.2 Label Construction Protocol

Labels were constructed from three sources.

| Source | Construction | Bias Boundary |
|---|---|---|
| PleOS-customized findings | Self-labelled from decompiled code, manifest context, Stage 2 notes, and redacted public reports. | Main IVI target rows; independent reviewer confirmation remains future work. |
| External vulnerable corpus | Rows derived from known vulnerable Android benchmark-style apps and MASTG examples. | Used as positive controls for common Android vulnerability patterns. |
| AOSP-derived / framework-like controls | Rows selected to exercise framework blocking, protected broadcasts, and false-positive behavior. | Used as negative/control evidence, not as a claim about all AOSP components. |

For all rows, `is_real=true` means the final evidence package supports reporting the finding under the stated threat model. It does not imply runtime exploitation unless a runtime claim level above L0 is attached.

Category distribution in the Stage 1 candidate set is `intent` 18, `hardcoded` 11, `network` 9, `crypto` 5, `permission` 3, and `reflection_dynamic` 1.

False positives concentrate in `intent`, `network`, and `permission`, which is why Stage 2 contextual verification is central to the final claim.

## 5. Results

### 5.1 Main Metric

| Variant | Accepted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage 1 initial detection | 47 | 38 | 9 | 0 | 80.9% | 100.0% | 0.894 |
| Stage 3 `>=1/3` | 45 | 38 | 7 | 0 | 84.4% | 100.0% | 0.916 |
| Stage 3 `>=2/3` | 37 | 37 | 0 | 1 | 100.0% | 97.4% | 0.987 |
| Stage 3 `>=3/3` | 33 | 33 | 0 | 5 | 100.0% | 86.8% | 0.930 |

The default final reporting threshold is Stage 3 `>=2/3`. It removed the nine measured false positives from Stage 1 while missing one low-severity hardening finding.

The headline metric reports Stage 1 vs Stage 3 because Stage 3 is the final reporting gate. Stage 2 is the evidence-packaging and context-filtering layer; this report does not claim Stage 2 alone as an independently automated classifier.

### 5.2 False-Positive Removal Attribution

The nine Stage 1 false positives were demoted below the final `>=2/3` reporting threshold after contextual evidence packaging and consensus review.

| FP ID | Stage 1 Trigger | Stage 2 Blocking Reason | Stage 3 Outcome | Final Reason |
|---|---|---|---|---|
| `vc-1` | WebView file/network pattern | no exploitable external producer established | `1/3`, not reported | hardening concern only |
| `vc-2` | WebView load URL pattern | same caller-chain boundary as `vc-1` | `1/3`, not reported | no reportable trust-boundary crossing |
| `vc-3` | `grantRuntimePermission` API | navigation/route binding kept package name internal | `1/3`, not reported | not externally reachable |
| `vc-4` | `revokeRuntimePermission` API | symmetric to `vc-3` caller-route block | `1/3`, not reported | not externally reachable |
| `usb-2` | USB permission grant path | framework filters and `MANAGE_USB` checks blocked caller control | `1/3`, not reported | no normal-app bypass found |
| `ss-1` | exported boot receiver | `BOOT_COMPLETED` is a protected broadcast | `0/3`, not reported | normal app cannot trigger path |
| `am-4` | custom install/uninstall action | action reached UI navigation only; user confirmation preserved | `1/3`, not reported | no auto-install primitive |
| `amb-4` | cross-package broadcast | explicit component targets PleOS-internal receiver | `0/3`, not reported | not an implicit broadcast leak |
| `amb-5` | exported voice service action | signature-level voice interaction permission gates binding | `1/3`, not reported | framework permission mitigates path |

This table attributes the evidence path, not an independent Stage 2 score. The measured result remains the paired Stage 1 vs Stage 3 comparison.

### 5.3 Stage 3 False Negative

| Missed ID | True Severity | Category | Why Stage 3 Missed It | Impact on Claim |
|---|---|---|---|---|
| `vc-7` | low | intent hardening | API 34 `registerReceiver` hardening pattern received only defender-side support (`1/3`) and did not pass `>=2/3`. | Recall becomes 97.4%; the miss is retained rather than manually corrected. |

The miss is kept in the metric so the Stage 3 threshold result remains reproducible and not post-hoc corrected.

### 5.4 Paired Significance

|  | Stage 3 correct | Stage 3 incorrect |
|---|---:|---:|
| Stage 1 correct | 37 | 1 |
| Stage 1 incorrect | 9 | 0 |

The paired McNemar exact test has `b+c=10` and exact two-tailed `p=0.0215`, so the Stage 1 to Stage 3 improvement is statistically visible on this labelled corpus.

### 5.5 Supporting Tracks

| Track | Measured Result | Boundary |
|---|---|---|
| Bootstrap CI | Stage 1 precision 95% bootstrap CI `[70.2%, 91.5%]` | Still corpus-bound, not a universal scanner guarantee |
| RAG intrinsic retrieval | nearest-neighbor verdict propagation 85.1%, AAOS category alignment 85.1% | Retrieval quality measured; prompted with/without-RAG LLM gain remains separate work |
| Native static scan | sample `n=4`, additional native-bound vulnerability 0 | Static sample-level track only; dynamic JNI/Go/runtime flow is not closed |
| Runtime PoC validation | same-device ADB proof points plus deterministic state machine, harness scripts, and Frida hooks | Claim-level evidence only; separate from the static `n=47` metric |
| Codex 3-model cross-read | precision 100.0%, recall 76.3%, F1 0.866 | Did not beat Stage 3 `>=2/3`; prompt calibration and evidence packaging mattered more than model count |

### 5.6 Runtime PoC And Claim-Level Evidence

The runtime PoC track was completed as a bounded validation layer for selected high-value static findings. Its purpose is not to change the Stage 1/Stage 3 precision-recall table, but to decide whether a static row remains L0 or can be strengthened to L1/L2/L3 evidence under the same-device emulator threat model.

| PoC Component | Completed Artifact | Role In The Research |
|---|---|---|
| Runtime harness | `scripts/runtime_poc/research_runtime_poc_harness.py` and recording wrappers | Builds and drives a same-device test APK for safe provider, broadcast, Activity, Binder, and marker checks |
| Static-to-dynamic state machine | `src/dynamic/state_machine.py` | Routes selected findings from static verdicts to runtime-observation correlation |
| Frida hook set | `src/dynamic/hooks/` | Captures caller UID, receiver payloads, provider queries, token/log emission paths, KDF passphrase use, and native command candidates |
| Compromise scenario matrix | `scripts/research/research_compromise_scenarios.py` | Translates findings into safe local PoC feasibility, attacker position, required evidence, and claim status |
| Recording helpers | `scripts/runtime_poc/record_*` and `run_*` scripts | Produce local-only evidence runs and video/report artifacts without publishing raw logs or proprietary data |

The completed PoC work produced three kinds of positive evidence.

| Finding / Surface | Runtime Evidence Status | Claim-Level Interpretation |
|---|---|---|
| `lmp-1` prompt provider | Same-device provider query path was exercised; prompt-provider rows were reachable without a permission denial in the emulator smoke track. | Supports L1 reachability and L2 data-read strength when redacted row data is captured. |
| `vc-6` vehicle broadcast receiver | Benign explicit broadcast delivery to the receiver was exercised in the emulator track. | Supports L1 receiver reachability; L2 requires a captured benign state/log diff. |
| PairedDevices provider control | Permission enforcement was observed for `READ_PAIRED_DEVICES` / `WRITE_PAIRED_DEVICES`. | Serves as a negative/control check showing that not every provider-like surface is treated as exploitable. |
| `am-1` AppMarket suggestions provider | Harness and evidence-check scripts implement marker write/read and cleanup checks for the exported suggestion surface. | Designed to support L2 only when harmless marker read/write evidence is captured; UI effect would require L3 evidence. |
| `acc-4`, `ssl-2`, `ssl-5`, `vc-5`, native command candidate | Hook scripts and runtime plans exist for boundary, token/log, KDF, implicit-broadcast, and native-command observation. | Completed as validation infrastructure; individual claim upgrades require local redacted runtime traces. |

Runtime PoC results are intentionally local-evidence artifacts. Public docs may state the observed claim level and redacted breadcrumb, but raw APKs, harness outputs, screenshots, videos, logs, prompt rows, and proprietary code remain local-only.

This track does not claim remote exploitation, real-vehicle control, credential theft in the wild, or a full end-to-end compromise chain. It shows that selected static findings were translated into safe, owner-authorized emulator checks and that some surfaces were runtime-reachable under the same-device model.

## 6. Case Summary

Representative final cases are documented in `03_case_studies.md`.

| Finding | APK | Final Verdict | Claim Boundary |
|---|---|---|---|
| `amb-1` | `ai.umos.ambientai` | TP | Production LLM API-key exposure pattern; public docs keep literal secret redacted |
| `am-3` | `ai.umos.appmarket` | TP | OAuth client-secret pattern in account flow; public docs keep secret value redacted |
| `acc-4` | `ai.pleos.playground.account` | TP | SSO secret crosses an Activity boundary |
| `ssl-6` | `ai.pleos.sync.syslog` | TP | gRPC plaintext transport in diagnostic/system-log context |
| `lmp-1` | `ai.pleos.llm.model.provider` | TP | Prompt-provider exposure; runtime strength depends on captured provider response |
| `vc-6` | `ai.umos.vehiclecontrol` | TP | Static TP under IVI threat model; no remote exploitation or real-vehicle control claim |
| `vc-3/4` | `ai.umos.vehiclecontrol` | FP | Caller route blocked by manifest/navigation/internal binding |
| `usb-2` | `android.car.usb.handler` | FP | Framework permission checks block caller control |
| `ss-1` | `com.android.statementservice` | FP | Protected broadcast blocks normal-app trigger |

## 7. Limitations

| Limit | Final State | Remaining Boundary |
|---|---|---|
| Label bias | External corpora were added | PleOS-customized labels still need independent reviewer validation |
| Corpus selection | Security-value selected corpus | Not an app-store random benchmark |
| Native/runtime behavior | Native static sample and dynamic scaffolding exist | Dynamic JNI, Go runtime, and syscall argument flow remain only partially observed |
| Runtime PoC evidence | Same-device ADB proof points and harness/hook infrastructure exist | Raw traces remain local-only; PoC evidence does not imply real-vehicle exploitation |
| RAG effect | Intrinsic retrieval quality measured | End-to-end prompted LLM improvement is not yet measured |
| ProGuard-heavy APKs | Priority-class yield can drop | Stronger Stage 0 and manifest-only modes remain useful |
| Stage 2 automation | Semi-automated contextual verification works on this corpus | Not a complete Android reachability engine |
| Public disclosure | Redacted public artifacts exist | Raw APKs, JADX output, logs, videos, and unredacted evidence stay local-only |

## 8. Contributions

1. A four-stage LLM-assisted APK security-analysis pipeline for PleOS / AAOS IVI.
2. A final combined GT corpus of 47 labelled finding rows with origin breakdown and explicit finding-unit rules.
3. Paired evidence that contextual evidence packaging and multi-perspective verification reduce measured false positives.
4. AAOS / MASVS / TARA mapping artifacts that translate code-level findings into automotive-security language.
5. A public/private artifact boundary for redacted reporting without publishing proprietary PleOS evidence.
6. Completed reinforcement tracks covering statistics, RAG, native static analysis, runtime PoC validation, and Codex cross-read.

## 9. Completed Research Coverage

This report covers the completed research tracks at result level. Detailed evidence, scripts, and local-only runtime artifacts are referenced rather than embedded.

| Completed Track | Covered In This Report | Detail Location |
|---|---|---|
| APK collection, JADX decompilation, keyword triage | Approach | `README.md`, `scripts/apk/`, `configs/keywords.yaml` |
| Stage 0 obfuscation and rename-plausibility screen | Approach, supporting tracks | `src/deobf/`, `data/deobf/` |
| Stage 1 LLM candidate detection | Approach, main metric | `configs/prompts/stage1_detect.md`, `data/reports/` |
| Stage 2 contextual verification | Approach, FP attribution | `docs/04_methodology_stage2.md` |
| Stage 3 multi-perspective consensus | Approach, main metric, FN analysis | `configs/prompts/stage3_*.md`, `data/reports/public/stage3_ensemble.md` |
| Combined GT and final metrics | Dataset, labels, results | `data/ground_truth/combined_labels.json`, `data/reports/aggregate/` |
| Bootstrap, ablation, and significance checks | Results, supporting tracks | `data/reports/aggregate/`, `src/evaluation/` |
| AAOS / MASVS / TARA mapping | Contributions, artifact index | `src/mapping/`, `data/reports/aggregate/` |
| RAG intrinsic retrieval evaluation | Supporting tracks | `src/rag/`, `docs/08_completed_reinforcements.md` |
| Native static boundary scan | Supporting tracks, limitations | `src/native/`, `docs/08_completed_reinforcements.md` |
| Runtime PoC validation | Runtime PoC and claim-level evidence | `scripts/runtime_poc/`, `src/dynamic/` |
| Codex cross-read reinforcement | Supporting tracks | `docs/08_completed_reinforcements.md` |
| Public disclosure and redaction boundary | Threat model, limitations, artifact index | `docs/10_project_inventory.md` |

Failed or inconclusive experiments are not promoted into final claims. They remain visible only as limitations or remaining-work boundaries when they affect interpretation.

## 10. Artifact Index

| Purpose | Path |
|---|---|
| One-page brief | `docs/02_final_brief.md` |
| Case studies | `docs/03_case_studies.md` |
| Stage 2 method | `docs/04_methodology_stage2.md` |
| Charts | `docs/05_charts.md`, `data/viz/` |
| Limitations and cost | `docs/06_limitations_and_costs.md` |
| Remaining work | `docs/07_remaining_work.md` |
| Completed A-E tracks | `docs/08_completed_reinforcements.md` |
| Runtime PoC tooling | `scripts/runtime_poc/`, `src/dynamic/` |
| PoC feasibility matrix | `scripts/research/research_compromise_scenarios.py` |
| GT labels | `data/ground_truth/combined_labels.json` |
| Aggregate reports | `data/reports/aggregate/` |
| Public masked reports | `data/reports/public/` |
| Local-only evidence | `data/_local/`, `data/reports/*_local/` |
