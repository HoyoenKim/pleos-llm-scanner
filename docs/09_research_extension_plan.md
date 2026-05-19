# Research Extension Plan

This document describes future experiment designs that build beyond the final 15-week artifact. It does not re-list completed reinforcement experiments A-E as unfinished work.

## Fixed Baseline

| Baseline Item | Final Value |
|---|---:|
| Combined GT | 47 |
| Stage 1 Precision / Recall / F1 | 80.9% / 100.0% / 0.894 |
| Stage 3 `>=2/3` Precision / Recall / F1 | 100.0% / 97.4% / 0.987 |
| McNemar exact p-value | 0.0215 |
| Native static sample | 4 |
| Additional native-bound vulnerabilities | 0 |

Any extension should treat Stage 3 `>=2/3` as the current baseline.

## Experiment Designs

| Design | Question | Conditions | Metrics | Leakage Control |
|---|---|---|---|---|
| Independent label review | Do external reviewers agree with self-labelled PleOS findings? | reviewer A, reviewer B, adjudicated label | agreement rate, adjudication count, updated confidence | reviewers do not see final verdicts |
| Corpus expansion | Does Stage 3 improvement remain significant at larger `n`? | current corpus vs expanded corpus | precision, recall, F1, bootstrap CI, McNemar | preserve origin labels and avoid duplicate findings |
| RAG end-to-end ablation | Does retrieved context improve prompted judgment? | `no_rag` vs `with_rag` | paired precision/recall/F1, discordance, FP suppression | remove target finding's own historical row and redact GT verdicts |
| Runtime validation | Which static findings become stronger or weaker with runtime evidence? | selected static cases with hooks/harnesses | claim-level upgrade/downgrade, trace reproducibility | keep runtime evidence separate from static `n=47` metrics |
| Native deep dive | Are secrets or endpoints hidden beyond string-level scan? | radare2/Ghidra/native runtime use-site analysis | recovered use sites, JNI argument flows, additional findings | separate Java/Kotlin metrics from native/runtime evidence |
| OS transfer | Does the method transfer to QNX or AGL? | labelled pilot corpus on another IVI OS | adapted categories, precision/recall/F1, new rule gaps | do not reuse Android-specific reachability assumptions blindly |

## RAG End-To-End Ablation

The next RAG experiment should judge already discovered findings, not search for new vulnerabilities.

| Condition | Context |
|---|---|
| `no_rag` | finding only |
| `with_rag` | same finding plus retrieved AAOS / MASVS / TARA / history context |

Required controls:

- remove the target finding's own historical row from retrieval
- redact GT verdict fields from retrieved examples
- run judgment in a fresh session that has not inspected `combined_labels.json`

Required outputs:

- precision / recall / F1 per condition
- paired discordance table
- FP-control suppression rate
- evidence-use audit in model reasons

## Runtime Validation

Use the existing state machine and hook scripts for selected high-value findings such as `vc-6`, `ssl-2`, `ssl-5`, and `lmp-1`.

The goal is not to change the static metric table. The goal is to attach runtime observations to selected findings and identify cases where runtime evidence upgrades, downgrades, or clarifies the static verdict.

## Native Deep Dive

The native static scan found no additional vulnerabilities in the checked sample. A deeper track should focus on:

- Go symbol/function recovery for `libgojni.so`
- endpoint and certificate-verification use sites
- JNI boundary arguments
- syscall and network call paths

This work should be reported as native/runtime evidence, separate from the Java/Kotlin Stage 1/2/3 metrics.
