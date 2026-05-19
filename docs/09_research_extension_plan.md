# Research Extension Plan

This document lists optional research expansions after the final 15-week artifact. It does not re-list completed reinforcement experiments A-E as unfinished work.

## Current Fixed Baseline

| Baseline Item | Final Value |
|---|---:|
| Combined GT | 47 |
| Stage 1 Precision / Recall / F1 | 80.9% / 100.0% / 0.894 |
| Stage 3 `>=2/3` Precision / Recall / F1 | 100.0% / 97.4% / 0.987 |
| McNemar exact p-value | 0.0215 |
| Native static sample | 4 |
| Additional native-bound vulnerabilities | 0 |

The main research baseline is fixed: Stage 3 multi-perspective consensus is currently the strongest validation layer. Codex 3-model cross-read was useful as an independent check, but it did not outperform the Stage 3 baseline.

## Extension Roadmap

| Priority | Extension | Question | Done Criteria |
|---:|---|---|---|
| 1 | Independent label review | Do external reviewers agree with self-labelled PleOS findings? | reviewer matrix, adjudication log, updated confidence labels |
| 2 | Corpus expansion to `n>=60` | Does Stage 3 improvement remain significant? | updated bootstrap CI and McNemar table |
| 3 | RAG end-to-end ablation | Does retrieved context improve prompted judgment? | paired `no_rag` vs `with_rag` metrics |
| 4 | Runtime validation | Which static findings become stronger/weaker with Frida evidence? | at least 3 reproducible runtime traces |
| 5 | Native deep dive | Are secrets/endpoints hidden beyond string-level native scan? | Ghidra/radare2 use-site analysis for high-value libs |
| 6 | Public redaction expansion | Can all final evidence be shared safely? | public masked full `n=47` report reviewed |
| 7 | OS transfer | Does the method transfer to QNX or AGL? | labelled pilot corpus and OS-specific rule adaptation |

## RAG End-To-End Ablation Design

The next RAG experiment should judge already discovered findings, not search for new vulnerabilities.

| Condition | Context |
|---|---|
| `no_rag` | finding only |
| `with_rag` | same finding plus retrieved AAOS/MASVS/TARA/history context |

Required leakage controls:

- remove the target finding's own historical row from retrieval
- redact GT verdict fields from retrieved examples
- run judgment in a fresh session that has not inspected `combined_labels.json`

Metrics:

- Precision / Recall / F1 per condition
- paired discordance table
- FP-control suppression rate
- evidence-use audit in model reasons

## Runtime Validation Design

Use the existing state machine and hook scripts for:

- `vc-5`
- `vc-6`
- `ssl-2`
- `ssl-5`
- `lmp-1`

The goal is not to change the static metric table. The goal is to attach runtime observations to selected high-value findings and identify cases where runtime evidence upgrades, downgrades, or clarifies the static verdict.

## Native Deep Dive Design

The native static scan found no additional vulnerabilities in the checked sample. A deeper track should focus on:

- Go symbol/function recovery for `libgojni.so`
- endpoint and certificate verification use-sites
- JNI boundary arguments
- syscall/network call paths

This work should be reported as native/runtime evidence, separate from the Java/Kotlin Stage 1/2/3 metrics.
