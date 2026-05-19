# Completed Reinforcement Experiments A-E

These tracks started as late-stage reinforcement ideas and were completed by the final 15-week archive. They are integrated into the final result and should not be described as unfinished work.

## Summary Matrix

| Code | Reinforcement | Artifact Path | Metric | Claim Boundary |
|---|---|---|---|---|
| A | Corpus and statistics | GT labels and aggregate metric reports | combined GT `n=47`, McNemar `p=0.0215` | Strengthens paired evidence on this corpus; not a universal benchmark |
| B | RAG domain knowledge | `src/rag/`, `data/reports/rag_local/rag_ablation.*` | nearest-neighbor verdict 85.1%, AAOS alignment 85.1% | Intrinsic retrieval only; prompted LLM gain remains separate |
| C | Native-code boundary scan | native inventory and local native reports | sample `n=4`, additional native-code-boundary vulnerabilities 0 | Static sample-level track; dynamic native/runtime flow not closed |
| D | Dynamic verification scaffolding | `src/dynamic/`, `scripts/runtime_poc/`, `data/reports/runtime_local/` | deterministic state machine plus Frida hook scripts | Infrastructure complete; runtime traces separate from static `n=47` metrics |
| E | Independent LLM cross-review | `data/reports/aggregate/codex_multimodel_agreement.*`, `data/reports/local/codex_multimodel/` | precision 100.0%, recall 76.3%, F1 0.866 | Independent check; did not beat calibrated Stage 3 |

## A. Corpus And Statistics

Final combined GT reached `n=47`.

| Origin | Findings | TP | FP | Precision |
|---|---:|---:|---:|---:|
| PleOS-customized | 30 | 23 | 7 | 76.7% |
| External vulnerable corpus | 13 | 13 | 0 | 100.0% |
| AOSP-derived | 4 | 2 | 2 | 50.0% |
| Total | 47 | 38 | 9 | 80.9% |

Main metric: Stage 1 vs Stage 3 paired improvement reached McNemar exact `p=0.0215`.

Claim boundary: this supports the final project corpus, not app-store-scale generalization.

## B. RAG Domain Knowledge

The RAG track created a local retrieval base without external embedding API calls.

| Collection | Contents |
|---|---|
| `aaos_guidelines` | AAOS / MASVS / TARA mapping context |
| `masvs_controls` | MASTG / MASVS documentation chunks |
| `tara_templates` | threat and risk templates |
| `finding_patterns_historical` | historical GT finding patterns |

The intrinsic ablation used the final `n=47` finding rows as retrieval queries. It measured top-1 retrieval behavior, not an end-to-end LLM-with-RAG improvement.

| Metric | Value |
|---|---:|
| nearest-neighbor verdict propagation | 85.1% |
| AAOS category alignment | 85.1% |
| MASVS area match | 23.4% |

| Metric | Measurement Unit |
|---|---|
| nearest-neighbor verdict propagation | For each finding query, exclude the query itself and check whether the top-1 historical finding's TP/FP verdict matches GT |
| AAOS category alignment | For each finding query, check whether the top-1 AAOS guideline category matches the finding's Stage 1 category |
| MASVS area match | For each finding query, check whether the top-1 MASVS control covers the expected MASVS area mapping |

Claim boundary: retrieval quality is promising for calibration, but this is not an end-to-end prompted LLM ablation.

## C. Native-Code Boundary Scan

The native track was added because Java/Kotlin `jadx` analysis does not cover `.so` behavior.

The inventory denominator was 207 system APKs from the PleOS Connect emulator: 22 APKs had at least one native library, with 221 `.so` files total.

The static deep-check sample covered 4 `.so` samples selected from security-relevant native-bearing packages.

| Sample | Result |
|---|---|
| `libgojni.so` variants | Go crypto/tls and x509 signals present; no additional vulnerability |
| `libairspeech_stt` | no additional static vulnerability in checked surface |
| `libmapbox-maps` | no additional static vulnerability in checked surface |

Claim boundary: native static analysis reduced the blind spot from "not inspected" to "sample-level static track exists." The "0 additional vulnerability" result applies only to the checked static sample, not to the full native/runtime closure.

## D. Dynamic Verification Scaffolding

The dynamic track added deterministic state-machine logic and Frida hook scripts for selected findings.

| Finding | Hook Purpose |
|---|---|
| `vc-5` | implicit broadcast observation |
| `vc-6` | receiver caller/payload observation |
| `ssl-2` | token leak emission check |
| `ssl-5` | KDF passphrase observation |
| `lmp-1` | provider query caller and exposure check |

Claim boundary: verification infrastructure is complete, but runtime capture is environment-dependent and separate from the static `n=47` measurement.

## E. Independent LLM Cross-Review

The independent LLM cross-review used three model perspectives as a check against the Claude Code multi-perspective baseline.

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| Claude Code Stage 3 `>=2/3` | 100.0% | 97.4% | 0.987 |
| Codex 3-model `>=2/3` | 100.0% | 76.3% | 0.866 |

Claim boundary: adding models did not automatically improve the result. The stronger lesson is that evidence packaging, prompt calibration, and domain-specific verification matter more than model count alone.

## Final Integration Rule

When editing README/docs, refer to A-E as completed reinforcement experiments. Do not describe them as unresolved or outside the 15-week result.
