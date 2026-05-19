# Limitations And Cost

This document states the final limitations after all 15-week work and completed reinforcement experiments A-E.

## 1. Final Limitation Table

| ID | Limitation | Final State | Remaining Work |
|---|---|---|---|
| L1 | Java/Kotlin scanner misses native behavior | Native static track added; sample `n=4`, additional vuln 0 | Ghidra Go recovery, JNI/runtime argument tracing |
| L2 | Small sample size | Improved from early feasibility to combined GT `n=47`; McNemar `p=0.0215` | Expand to `n>=60` and add external reviewers |
| L3 | Same-model verification bias | Codex 3-model cross-read completed; did not beat Stage 3 | True multi-vendor comparison only if policy/budget allows |
| L4 | Hand-crafted vulnerable corpus bias | External and real-world samples added | More commercial ProGuard-heavy APKs with ground truth |
| L5 | Static-only evidence | Dynamic state machine and hooks prepared | Complete reproducible runtime capture on target AVD |
| L6 | ProGuard-heavy APK yield drop | Observed in PleOS-customized apps | Stronger Stage 0 and manifest-only Stage 1 mode |
| L7 | RAG effect not end-to-end measured | Intrinsic retrieval measured | with/without-RAG prompted LLM ablation |

## 2. What Was Actually Resolved

| Concern | Resolution |
|---|---|
| Stage 3 not evaluated on expanded corpus | Stage 3 applied to final `n=47` |
| No statistical significance | McNemar exact `p=0.0215` reached |
| Native boundary only described abstractly | corpus-level native inventory plus sample-level static scan added |
| Multi-model comparison absent | Codex 3-model cross-read completed |
| Domain knowledge only hardcoded in prompt | Local RAG knowledge path implemented and intrinsically evaluated |

## 3. What Is Still Not Resolved

The remaining limitations are real and should stay visible:

- Stage 3 performance is measured on a security-selected corpus, not an app-store random sample.
- PleOS-customized labels still need independent reviewer confirmation.
- Native analysis is static and conservative.
- Dynamic hooks exist, but reproducible runtime capture is environment-dependent.
- RAG has not yet been measured as an end-to-end prompted LLM performance improvement.
- Stage 2 is not a complete Android reachability engine.

## 4. Cost Model

| Activity | Observed / Estimated Cost | Notes |
|---|---:|---|
| APK pull/decompile | minutes per APK after environment setup | dominated by APK size and JADX runtime |
| Keyword triage | seconds to minutes | deterministic |
| Stage 1 LLM analysis | about 1 hour for selected priority classes | interactive reading included |
| Stage 2 contextual verification | about 30-90 minutes per complex APK | caller/manifest reasoning cost |
| Stage 3 consensus | about 30 minutes for selected findings | prompt reuse helps |
| AAOS/TARA mapping | minutes once labels are stable | deterministic scripts |

The original plan assumed a fully batched LLM workflow. The actual project used interactive Codex/Claude Code sessions, so human reading time is included in observed effort.

## 5. Operating Recommendation

For a production-like PleOS workflow:

1. Run deterministic extraction/decompile/triage automatically.
2. Use Stage 1 as high-recall candidate generation.
3. Require Stage 2 contextual checks before reporting.
4. Use Stage 3 `>=2/3` for final report inclusion.
5. Route native-heavy APKs into the native binary track.
6. Keep raw APKs, JADX output, and runtime evidence local-only.
