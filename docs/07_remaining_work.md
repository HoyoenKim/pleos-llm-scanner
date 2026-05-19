# Remaining Work

This file lists only the work that remains **after** the final 15-week scope. Completed reinforcement experiments A-E are not listed here as unresolved items; they are summarized in `08_completed_reinforcements.md`.

## Priority 1

| Item | Why It Remains |
|---|---|
| Independent label review | PleOS-customized findings still have self-label bias |
| Expand corpus to `n>=60` | further narrow confidence intervals and strengthen by-origin analysis |
| Reproducible runtime capture | Frida hooks/state machine exist, but target AVD runtime capture must be repeated in a stable environment |
| Native dynamic flow | static native scan does not observe Go runtime/JNI/syscall argument flow |

## Priority 2

| Item | Why It Remains |
|---|---|
| with/without-RAG prompted LLM ablation | current RAG result is intrinsic retrieval quality, not end-to-end LLM gain |
| ProGuard-heavy commercial APKs | Stage 0 generalization needs real mapping/debug baseline |
| Broader scanner comparison | compare missed findings against MobSF/Semgrep-like Android scanners |
| Stage 2 automation | convert current contextual rules into a more general reachability analyzer |

## Priority 3

| Item | Why It Remains |
|---|---|
| True multi-vendor LLM comparison | blocked by IP/budget/API policy during this project |
| QNX / AGL swap experiment | methodology likely transfers, but OS-specific findings need new labels |
| CI integration | useful for operations, but outside final research measurement |

## Do Not Mislabel Completed Work

The following are already complete in the final artifact:

- corpus expansion to `n=47`
- Stage 3 evaluation on final corpus
- McNemar paired test
- local RAG index and intrinsic ablation
- native static sample analysis
- dynamic state machine and Frida hooks
- Codex 3-model cross-read

These should not be described as remaining work.
