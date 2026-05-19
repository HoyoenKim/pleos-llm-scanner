# Remaining Work

This file lists only work that remains after the final 15-week evidence base. Completed reinforcement experiments A-E are not unresolved items; see `08_completed_reinforcements.md`.

## Priority 1

| Item | Why It Remains | Next Action | Done Criterion |
|---|---|---|---|
| Independent label review | PleOS-customized findings still have self-label bias | Have two external reviewers label all PleOS-customized findings without seeing final verdicts | Adjudication matrix completed and disagreements resolved |
| Expand corpus to `n>=60` | Larger corpus would narrow confidence intervals and strengthen by-origin analysis | Add labelled rows from redaction-safe PleOS, external, or AOSP-derived sources | Updated metrics, bootstrap CI, and McNemar table published |
| Reproducible runtime capture | Hooks and state machine exist, but stable target capture is environment-dependent | Re-run selected hooks on a documented AVD setup | At least three traces with command, environment, output, and redaction notes |
| Native dynamic flow | Static native scan does not observe Go runtime, JNI, or syscall arguments | Select high-value libraries for runtime or decompiler-assisted use-site tracing | Native dynamic evidence table completed with claim levels |

## Priority 2

| Item | Why It Remains | Next Action | Done Criterion |
|---|---|---|---|
| Prompted with/without-RAG ablation | Current RAG result is intrinsic retrieval quality only | Run paired `no_rag` and `with_rag` judgments on the same finding set | Precision/recall/F1 and discordance table completed |
| ProGuard-heavy commercial APKs | Stage 0 generalization needs a stronger real-world baseline | Add a redaction-safe commercial or open-source ProGuard-heavy sample | Obfuscation and rename-plausibility report completed |
| Broader scanner comparison | Missed-finding comparison against non-LLM scanners is incomplete | Run MobSF/Semgrep-like Android scanner baselines where policy allows | Missed/overlap table completed |
| Stage 2 automation | Current rules are structured but not a general analyzer | Convert recurring checks into reusable reachability rules | Scripted rule output agrees with documented Stage 2 cases on a pilot set |

## Priority 3

| Item | Why It Remains | Next Action | Done Criterion |
|---|---|---|---|
| True multi-vendor LLM comparison | Blocked by IP, budget, and API policy during this project | Revisit only with approved non-sensitive evidence packages | Vendor-comparison protocol and redaction review approved |
| QNX / AGL transfer | Method may transfer, but OS-specific labels are missing | Build a small labelled pilot corpus for another IVI OS | OS-specific rule adaptation documented |
| CI integration | Useful for operations, but outside final research measurement | Add JSON validation and public-doc checks to CI | CI passes without local-only data |

## Do Not Relabel As Remaining

The following are already complete in the final artifact:

- corpus expansion to `n=47`
- Stage 3 evaluation on final corpus
- McNemar paired test
- local RAG index and intrinsic ablation
- native static sample analysis
- dynamic state machine and Frida hook scripts
- Codex 3-model cross-read
