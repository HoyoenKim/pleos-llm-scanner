# Chart Inventory

This document records the chart artifacts used by `FINAL_REPORT.md`. The chart images are evidence summaries, not weekly progress snapshots. Regenerate PNGs only when source metrics or `src/viz/plot_metrics.py` behavior changes.

## Main Figure Set

| Figure | Chart | What It Explains | Source input |
|---:|---|---|---|
| 1 | `data/viz/01_obfuscation_profile_across_test_apks.png` | Static-review readability pre-screen based on JADX-decompiled identifier-name patterns such as `C0010a`, `m5a`, and `f2a`. | `data/deobf/*.json` |
| 2 | `data/viz/02_candidate_verification_by_pattern.png` | Final outcomes for LLM-proposed candidate findings by vulnerability category. | Final 47-candidate summary embedded in `src/viz/plot_metrics.py` |
| 3 | `data/viz/03_scan_quality_before_after_verification.png` | How context-aware review changes precision, recall, and F1 over the same 47 candidate findings. | `data/reports/aggregate/final_metrics_n47.json` values embedded in the plotting script |
| 4 | `data/viz/04_verified_vulnerabilities_by_apk_severity.png` | Which APK/severity cells should drive follow-up analysis after findings are confirmed. | Confirmed-vulnerability APK/severity matrix in the plotting script |
| 5 | `data/viz/05_accept_candidates_as_vulnerabilities_by_three_role_review.png` | Precision-recall trade-off for role-prompted reviewer consensus thresholds. | Final role-agreement threshold values embedded in the plotting script |

## Appendix Figure Set

| Figure | Chart | What It Explains | Source input |
|---:|---|---|---|
| A1 | `data/viz/appendix_a1_corpus_composition.png` | Source composition of the 47 candidate findings, without implying APK counts or prevalence. | Final source counts: PleOS-customized 30, MASTG 4, InsecureBankv2 9, AOSP-derived 4 |
| A2 | `data/viz/appendix_a2_bootstrap_ci.png` | Bootstrap uncertainty for the LLM-only candidate scan, including false discovery share as `1 - precision`. | Final n=47 bootstrap values preserved from `data/reports/aggregate/bootstrap_ci.md` |
| A3 | `data/viz/appendix_a3_obfuscation_score_distribution.png` | Heuristic identifier-name obfuscation score distributions behind the flagged-class readability screen. | `data/deobf/*.json` |
| A4 | `data/viz/appendix_a4_mapping_summary.png` | AAOS/MASVS-aligned control-area grouping for the 38 reference vulnerability findings. | `data/ground_truth/combined_labels.json` category-to-control mapping |
| A5 | `data/viz/appendix_a5_validation_track_comparison.png` | Supporting validation tracks and their separate measurement roles. | `data/reports/aggregate/final_metrics_n47.json`, `codex_multimodel_agreement.json` |

## Reading Rules

- Figures should be read in the main sequence: decompiled-code readability, candidate filtering, metric improvement, confirmed-vulnerability analysis, then consensus-threshold choice.
- Figure 1 is a readability screen for static analysis, not a validated obfuscation benchmark or vulnerability metric. It uses flagged-class counts plus `flagged / analyzed classes` labels so small benchmark APKs are not overread through ratio alone. A flagged class means its decompiled identifiers matched the heuristic detector, for example `C0010a`-style class names or `m5a`/`f2a`-style member names.
- Figure 2 should be read as candidate-finding outcome filtering. It asks which LLM-proposed candidate findings become confirmed vulnerabilities, which are rejected as false positives, and which true vulnerability is missed by the selected threshold.
- Figure 3 is the headline quality comparison. F1 is plotted as a percentage so it can be read on the same axis as precision and recall; all values refer to the same 47 candidate findings.
- Figure 4 is a follow-up priority map, not a prevalence claim about the full PleOS/AAOS ecosystem or external vulnerable corpora.
- Figure 5 shows how precision, recall, and F1 change under `>=1`, `>=2`, and `3/3` role-prompted reviewer thresholds. The selected threshold is `>=2`.
- Appendix A5 summarizes supporting checks. It does not create new vulnerability counts.
- Appendix A1 uses candidate findings as the unit, not APKs. Appendix A2 is limited to the LLM-only candidate scan and uses false discovery share, not the standard false-positive-rate definition. Appendix A3 is the detailed identifier-name score distribution behind Figure 1. Appendix A4 maps the 38-finding reference set, while Figure 5/A5 explain that the primary `>=2` rule confirms 37 of those 38. Appendix A5 is intentionally a table because F1, paired-test p-values, native-boundary counts, and retrieval-alignment rates should not be plotted as one comparable score.
- Runtime/local PoC evidence remains separate from this static-analysis chart set unless redaction review is complete.

## Final Numbers To Preserve

| Metric | Value |
|---|---:|
| Combined GT | 47 candidate findings |
| Reference vulnerability findings | 38 |
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
