# Limitations And Cost

This document states the current claim limits and operating cost after the final 15-week scope. Completed reinforcement experiments A-E are detailed in `08_completed_reinforcements.md`.

## Current Claim Limits

| ID | Limitation | Final State | Remaining Boundary |
|---|---|---|---|
| L1 | Java/Kotlin scanner misses native behavior | Native static track added; sample `n=4`, additional native-bound vulnerability 0 | Dynamic JNI, Go runtime, and syscall argument flow are not fully observed |
| L2 | Small sample size | Combined GT expanded to `n=47`; McNemar `p=0.0215` | Wider confidence requires more labels and independent review |
| L3 | Same-model verification bias | Codex 3-model cross-read completed; it did not beat Stage 3 | True multi-vendor comparison depends on policy and budget |
| L4 | Hand-crafted vulnerable-corpus bias | External and real-world references added | More commercial ProGuard-heavy APKs would strengthen generalization |
| L5 | Static-first evidence | Dynamic state machine and hooks exist | Reproducible runtime capture remains environment-dependent |
| L6 | ProGuard-heavy APK yield drop | Observed in PleOS-customized apps | Stronger Stage 0 and manifest-only Stage 1 mode remain useful |
| L7 | RAG effect not end-to-end measured | Intrinsic retrieval quality measured | Prompted with/without-RAG LLM ablation remains outside the final metric |

## Residual Risks

- Stage 3 performance is measured on a security-selected corpus, not an app-store random sample.
- PleOS-customized labels still need independent reviewer confirmation.
- Native analysis is static and conservative.
- Dynamic hooks exist, but runtime capture depends on emulator and Frida conditions.
- RAG has not yet been measured as an end-to-end LLM performance improvement.
- Stage 2 is semi-automated contextual verification, not a complete Android reachability engine.

## Cost Model

| Activity | Observed / Estimated Cost | Notes |
|---|---:|---|
| APK pull and decompile | minutes per APK after environment setup | dominated by APK size and JADX runtime |
| Keyword triage | seconds to minutes | deterministic |
| Stage 1 LLM analysis | about 1 hour for selected priority classes | interactive reading included |
| Stage 2 contextual verification | about 30-90 minutes per complex APK | caller/manifest reasoning cost |
| Stage 3 consensus | about 30 minutes for selected findings | prompt reuse helps |
| AAOS/TARA mapping | minutes once labels are stable | deterministic scripts |

The original plan assumed a fully batched LLM workflow. The actual project used interactive Codex/Claude Code sessions, so human reading time is included in observed effort.

## Operating Recommendation

1. Run deterministic extraction, decompilation, and triage automatically.
2. Use Stage 1 as high-recall candidate generation.
3. Require Stage 2 contextual checks before reporting.
4. Use Stage 3 `>=2/3` for final report inclusion.
5. Route native-heavy APKs into the native binary track.
6. Keep raw APKs, JADX output, runtime evidence, videos, and unredacted reports local-only.
