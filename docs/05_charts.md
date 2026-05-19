# Chart Inventory

This document records the chart artifacts used by `FINAL_REPORT.md`. The chart images are evidence summaries, not weekly progress snapshots. Regenerate PNGs only when source metrics or `src/viz/plot_metrics.py` behavior changes.

## Main Figure Set

| Figure | Chart | What It Explains | Source input |
|---:|---|---|---|
| 1 | `data/viz/01_obfuscation_profile_across_test_apks.png` | Heuristic screen for JADX-style identifier patterns such as `C0010a`, `m5a`, and `f2a`. | `data/deobf/*.json` |
| 2 | `data/viz/02_candidate_verification_by_pattern.png` | Which LLM-proposed vulnerability patterns were kept or rejected after Android context verification. | Final 47-candidate summary embedded in `src/viz/plot_metrics.py` |
| 3 | `data/viz/03_scan_quality_before_after_verification.png` | Scan quality before and after context verification: precision, recall, and F1. | `data/reports/aggregate/final_metrics_n47.json` values embedded in the plotting script |
| 4 | `data/viz/04_verified_vulnerabilities_by_apk_severity.png` | Where verified vulnerabilities appear by APK and severity, with PleOS rows marked. | Verified-vulnerability APK/severity matrix in the plotting script |
| 5 | `data/viz/05_consensus_threshold_tradeoff.png` | Why majority consensus is used as the final reporting threshold. | Final threshold-sensitivity values embedded in the plotting script |
| 6 | `data/viz/06_supporting_validation_tracks.png` | Supporting validation tracks and what each one does or does not claim. | Final metrics, RAG/native/Codex summary values |

## Appendix Figure Set

| Figure | Chart | What It Explains | Source input |
|---:|---|---|---|
| A1 | `data/viz/appendix_a1_corpus_composition.png` | Where the 47 candidates came from. | Final source counts: PleOS-customized 30, MASTG 4, InsecureBankv2 9, AOSP-derived 4 |
| A2 | `data/viz/appendix_a2_bootstrap_ci.png` | Bootstrap confidence intervals for candidate-generation precision, F1, and false-positive rate. | Final n=47 bootstrap values preserved from `data/reports/aggregate/bootstrap_ci.md` |
| A3 | `data/viz/appendix_a3_obfuscation_score_distribution.png` | Full obfuscation-score distributions behind the simpler main obfuscation profile. | `data/deobf/*.json` |
| A4 | `data/viz/appendix_a4_mapping_summary.png` | AAOS/MASVS control-area grouping for verified vulnerabilities. | `data/ground_truth/combined_labels.json` category-to-control mapping |
| A5 | `data/viz/appendix_a5_validation_track_comparison.png` | Cross-validation tracks next to the final consensus result. | `data/reports/aggregate/final_metrics_n47.json`, `codex_multimodel_agreement.json`, `native_lib_inventory.json` |

## Reading Rules

- Figures should be read in the main sequence: decompiled-code readability, candidate filtering, metric improvement, verified-vulnerability analysis, threshold choice, then supporting validation.
- Figure 1 is a readability screen for static analysis, not a validated obfuscation benchmark or vulnerability metric. It uses HIGH-obfuscation class counts plus `HIGH / analyzed classes` labels so small benchmark APKs are not overread through ratio alone. A HIGH class means its decompiled identifiers matched the heuristic detector, for example `C0010a`-style class names or `m5a`/`f2a`-style member names.
- Figure 2 uses TP/FP only in the legend. The explanation should focus on candidates kept or rejected by Android context checks.
- Figure 3 is the headline quality comparison. F1 is plotted as a percentage so it can be read on the same axis as precision and recall.
- Figure 4 is a follow-up priority map, not a prevalence claim about the full PleOS/AAOS ecosystem.
- Figure 5 replaces the older two-panel ablation chart. It shows threshold sensitivity only; the final threshold is majority consensus.
- Figure 6 and appendix A5 summarize supporting checks. They do not create new vulnerability counts.
- Runtime/local PoC evidence remains separate from this static-analysis chart set unless redaction review is complete.

## Final Numbers To Preserve

| Metric | Value |
|---|---:|
| Combined GT | 47 labelled findings |
| Stage 1 TP / FP / FN | 38 / 9 / 0 |
| Stage 1 precision / recall / F1 | 80.9% / 100.0% / 0.894 |
| Stage 3 `>=2/3` TP / FP / FN | 37 / 0 / 1 |
| Stage 3 `>=2/3` precision / recall / F1 | 100.0% / 97.4% / 0.987 |
| Stage 1 vs Stage 3 McNemar exact test | `p=0.0215` |

## Regeneration

```bash
python src/viz/plot_metrics.py
```

If labels, metric outputs, threshold values, or deobfuscation measurements change, update the plotting script and regenerate the PNG outputs. Do not keep old chart values after changing `data/ground_truth/combined_labels.json`, `data/reports/local/stage3_ensemble.json`, or `data/deobf/*.json`.
