# Final Metrics N47

_Final 15-week archive headline metrics. This file is the README-facing source of truth for the final `n=47` claims._

## Corpus

| Source | Findings |
|---|---:|
| PleOS-customized | 30 |
| External vulnerable corpus | 13 |
| AOSP-derived | 4 |
| **Total** | **47** |

Ground truth labels: **38 TP / 9 FP / 0 uncertain**.

## Main Evaluation

| Step | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Stage 1 candidate generation | 38 | 9 | 0 | 80.9% | 100.0% | 0.894 |
| Stage 3 `>=2/3` verified reporting | 37 | 0 | 1 | 100.0% | 97.4% | 0.987 |

Paired Stage 1 vs Stage 3 McNemar exact test: **p = 0.0215** with contingency `a/b/c/d = 37/1/9/0`.

## Supporting Measurements

| Track | Result | Boundary |
|---|---|---|
| Native static scan | `n=4`, additional native-bound vulnerabilities 0 | Sample-level static scan, not full native/runtime closure |
| RAG intrinsic ablation | nearest-neighbor verdict 85.1%, AAOS category alignment 85.1% | Retrieval-quality measurement, not prompted end-to-end LLM gain |
| Codex multi-model cross-read | Did not beat Claude Code Stage 3 | Model count was less important than prompt calibration and evidence packaging |

## Notes

- Older aggregate files such as some `n=28` stage-transition and bootstrap artifacts are retained as historical/intermediate measurement records.
- Stage 2 upper-bound simulation rows are not independent automated performance claims.
