# LLM-Assisted Security Analysis of PleOS/AAOS IVI APKs

This report is the measured-claim source of truth for the final 15-week archive. Completed reinforcement experiments A-E are integrated into the final result and are summarized only as supporting tracks here; detailed A-E records live in `08_completed_reinforcements.md`.

## 1. Problem

PleOS / AAOS IVI APKs combine Android application surfaces with vehicle-adjacent permissions, exported components, local providers, and system integrations. A keyword scan or one-pass LLM review can identify suspicious code, but Android exploitability depends on context: manifest export state, caller reachability, permissions, route binding, protected broadcasts, and trust boundaries.

The project therefore evaluates an LLM-assisted APK security-analysis pipeline where the LLM is not a standalone scanner. It is used as a reasoning component between deterministic triage and Android-domain contextual verification.

## 2. Approach

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

## 3. Dataset And Labels

The final labelled corpus contains `n=47` finding-level rows.

| Origin | Findings | TP | FP | Precision | Role |
|---|---:|---:|---:|---:|---|
| PleOS-customized | 30 | 23 | 7 | 76.7% | Main IVI security target |
| External vulnerable corpus | 13 | 13 | 0 | 100.0% | OWASP MASTG and InsecureBankv2 control evidence |
| AOSP-derived / framework-like | 4 | 2 | 2 | 50.0% | Framework blocking and false-positive controls |
| Total | 47 | 38 | 9 | 80.9% | Final combined GT |

Category distribution in the Stage 1 candidate set is `intent` 18, `hardcoded` 11, `network` 9, `crypto` 5, `permission` 3, and `reflection_dynamic` 1. False positives concentrate in `intent`, `network`, and `permission`, which is why Stage 2 contextual verification is central to the final claim.

## 4. Results

### 4.1 Main Metric

| Variant | Accepted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage 1 initial detection | 47 | 38 | 9 | 0 | 80.9% | 100.0% | 0.894 |
| Stage 3 `>=1/3` | 45 | 38 | 7 | 0 | 84.4% | 100.0% | 0.916 |
| Stage 3 `>=2/3` | 37 | 37 | 0 | 1 | 100.0% | 97.4% | 0.987 |
| Stage 3 `>=3/3` | 33 | 33 | 0 | 5 | 100.0% | 86.8% | 0.930 |

The default final reporting threshold is Stage 3 `>=2/3`. It removed the nine measured false positives from Stage 1 while missing one low-severity hardening finding.

### 4.2 Paired Significance

|  | Stage 3 correct | Stage 3 incorrect |
|---|---:|---:|
| Stage 1 correct | 37 | 1 |
| Stage 1 incorrect | 9 | 0 |

The paired McNemar exact test has `b+c=10` and exact two-tailed `p=0.0215`, so the Stage 1 to Stage 3 improvement is statistically visible on this labelled corpus.

### 4.3 Supporting Tracks

| Track | Measured Result | Boundary |
|---|---|---|
| Bootstrap CI | Stage 1 precision 95% bootstrap CI `[70.2%, 91.5%]` | Still corpus-bound, not a universal scanner guarantee |
| RAG intrinsic retrieval | nearest-neighbor verdict propagation 85.1%, AAOS category alignment 85.1% | Retrieval quality measured; prompted with/without-RAG LLM gain remains separate work |
| Native static scan | sample `n=4`, additional native-bound vulnerability 0 | Static sample-level track only; dynamic JNI/Go/runtime flow is not closed |
| Dynamic verification scaffolding | deterministic state machine plus Frida hook scripts | Infrastructure exists; runtime evidence is separate from the static `n=47` metric |
| Codex 3-model cross-read | precision 100.0%, recall 76.3%, F1 0.866 | Did not beat Stage 3 `>=2/3`; prompt calibration and evidence packaging mattered more than model count |

## 5. Case Summary

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

## 6. Limitations

| Limit | Final State | Remaining Boundary |
|---|---|---|
| Label bias | External corpora were added | PleOS-customized labels still need independent reviewer validation |
| Corpus selection | Security-value selected corpus | Not an app-store random benchmark |
| Native/runtime behavior | Native static sample and dynamic scaffolding exist | Dynamic JNI, Go runtime, and syscall argument flow remain only partially observed |
| RAG effect | Intrinsic retrieval quality measured | End-to-end prompted LLM improvement is not yet measured |
| ProGuard-heavy APKs | Priority-class yield can drop | Stronger Stage 0 and manifest-only modes remain useful |
| Stage 2 automation | Semi-automated contextual verification works on this corpus | Not a complete Android reachability engine |
| Public disclosure | Redacted public artifacts exist | Raw APKs, JADX output, logs, videos, and unredacted evidence stay local-only |

## 7. Contributions

1. A four-stage LLM-assisted APK security-analysis pipeline for PleOS / AAOS IVI.
2. A final combined GT corpus of 47 labelled finding rows with origin breakdown.
3. Paired evidence that contextual and multi-perspective verification reduces measured false positives.
4. AAOS / MASVS / TARA mapping artifacts that translate code-level findings into automotive-security language.
5. A public/private artifact boundary for redacted reporting without publishing proprietary PleOS evidence.
6. Completed reinforcement tracks covering statistics, RAG, native static analysis, dynamic scaffolding, and Codex cross-read.

## 8. Artifact Index

| Purpose | Path |
|---|---|
| One-page brief | `docs/02_final_brief.md` |
| Case studies | `docs/03_case_studies.md` |
| Stage 2 method | `docs/04_methodology_stage2.md` |
| Charts | `docs/05_charts.md`, `data/viz/` |
| Limitations and cost | `docs/06_limitations_and_costs.md` |
| Remaining work | `docs/07_remaining_work.md` |
| Completed A-E tracks | `docs/08_completed_reinforcements.md` |
| GT labels | `data/ground_truth/combined_labels.json` |
| Aggregate reports | `data/reports/aggregate/` |
| Public masked reports | `data/reports/public/` |
| Local-only evidence | `data/_local/`, `data/reports/*_local/` |
