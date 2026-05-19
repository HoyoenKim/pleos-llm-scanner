# Completed Reinforcement Experiments A-E

During the project, these items moved from late-stage candidate extensions into completed work. By the final 15-week archive, they had been measured and integrated into the results. This document records them as completed reinforcement experiments.

## Summary Matrix

| Code | Reinforcement | Final Status | Main Result |
|---|---|---|---|
| A | Corpus and statistics | Complete | combined GT `n=47`, McNemar `p=0.0215` |
| B | RAG domain knowledge | Complete | Chroma 4 collections, NN/AAOS 85.1% |
| C | Native static scan | Complete | native sample `n=4`, additional vuln 0 |
| D | Dynamic verification scaffolding | Complete | state machine + 5 Frida hooks |
| E | Codex multi-model cross-read | Complete | precision 100%, recall lower than Stage 3 |

## A. Corpus And Statistics Reinforcement

Final combined GT reached `n=47`.

| Origin | Findings | TP | FP | Precision |
|---|---:|---:|---:|---:|
| PleOS-customized | 30 | 23 | 7 | 76.7% |
| External vulnerable corpus | 13 | 13 | 0 | 100.0% |
| AOSP-derived | 4 | 2 | 2 | 50.0% |
| Total | 47 | 38 | 9 | 80.9% |

The key added value was not only a larger point estimate but stronger paired evidence: Stage 1 vs Stage 3 McNemar exact `p=0.0215`.

## B. RAG Domain Knowledge Reinforcement

The RAG track created a local retrieval base without external embedding API calls.

| Collection | Contents |
|---|---|
| `aaos_guidelines` | AAOS/MASVS/TARA mapping context |
| `masvs_controls` | MASTG/MASVS documentation chunks |
| `tara_templates` | threat/risk templates |
| `finding_patterns_historical` | historical GT finding patterns |

Measured intrinsic result:

| Metric | Value |
|---|---:|
| nearest-neighbor verdict propagation | 85.1% |
| AAOS category alignment | 85.1% |
| MASVS area match | 23.4% |

Interpretation: retrieval quality is promising for calibration, but end-to-end prompted LLM performance gain remains separate remaining work.

## C. Native Static Scan Reinforcement

The native track was added because Java/Kotlin `jadx` analysis does not cover `.so` logic.

| Sample | Result |
|---|---|
| `libgojni.so` variants | Go crypto/tls and x509 signals present; no additional vuln |
| `libairspeech_stt` | no additional static vuln in checked surface |
| `libmapbox-maps` | no additional static vuln in checked surface |

Final claim: native static analysis reduced the blind spot from “not inspected” to “sample-level static track exists.” It did not close dynamic native/runtime behavior.

## D. Dynamic Verification Scaffolding

The dynamic track added deterministic state-machine logic and Frida hook scripts for selected findings:

| Finding | Hook Purpose |
|---|---|
| `vc-5` | implicit broadcast observation |
| `vc-6` | receiver caller/payload observation |
| `ssl-2` | token leak emission check |
| `ssl-5` | KDF passphrase observation |
| `lmp-1` | provider query caller and exposure check |

Final claim: verification infrastructure is complete. Runtime capture is environment-dependent and remains separate from the static `n=47` measurement.

## E. Codex Multi-Model Cross-Read

The Codex cross-read used three model perspectives as an independent check against the Claude Code multi-perspective baseline.

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| Claude Code Stage 3 `>=2/3` | 100.0% | 97.4% | 0.987 |
| Codex 3-model `>=2/3` | 100.0% | 76.3% | 0.866 |

Interpretation: adding models did not automatically improve the result. The stronger lesson is that evidence packaging, prompt calibration, and domain-specific verification matter more than model count alone.

## Final Integration Rule

When editing README/docs, refer to A-E as completed reinforcements. Do not describe them as unresolved or outside the 15-week result.
