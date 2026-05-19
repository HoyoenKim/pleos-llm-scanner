# Chart Inventory

This document records the chart artifacts used by the final report. The chart images are evidence summaries, not weekly progress snapshots. Do not regenerate chart PNGs just because this document had stale names; regenerate only if outputs are missing, source metrics changed, or `src/viz/plot_metrics.py` behavior changes.

## Chart Source Table

| Chart | Source input | Command | Boundary |
|---|---|---|---|
| `data/viz/01_category_distribution.png` | 47-candidate vulnerability-pattern summary embedded in plotting script | `python src/viz/plot_metrics.py` | LLM candidates after context verification; TP/FP appears only in the legend |
| `data/viz/02_apk_severity_heatmap.png` | verified-vulnerability APK/severity matrix in script | same | HIGH-severity coverage map for follow-up analysis; PleOS rows are marked |
| `data/viz/03_fp_rate_trend.png` | Stage 1/2/3 FP-rate comparison | same | stage comparison, not chronological trend |
| `data/viz/04_deobf_accuracy_trend.png` | `data/deobf/*.json` plus fixed corpus annotations | same | corpus comparison, not time trend |
| `data/viz/05_ablation_bars.png` | final `n=47` ablation and consensus-threshold values | same | threshold sensitivity, not new independent evaluation |
| `data/viz/06_entropy_distribution.png` | live `data/deobf/*.json` | same | obfuscation score distribution only |

## Reading Rules

- The Stage 3 `0.0%` false-positive rate means no false positives among accepted Stage 3 findings in this measured corpus. It is not a universal guarantee.
- Chart 01 shows candidates proposed from decompiled APK code and then kept or rejected after Android context checks.
- Chart 02 colors count verified security vulnerabilities by final severity. Rows marked `[PleOS]` are project target apps, and HIGH cells identify priority APKs for follow-up analysis.
- The FP-rate chart uses "trend" in the filename, but the x-axis is pipeline stage, not time.
- The deobfuscation chart uses "trend" in the filename, but it compares corpora, not time.
- The deobfuscation chart combines two measurements: HIGH-obfuscation ratio and rename-evaluation annotations. The bar height is not rename accuracy.
- The ablation chart contains both stage ablation and consensus-threshold sensitivity. The `>=2/3` threshold is the final reporting default.
- Runtime/local evidence charts must not be published unless redaction review is complete.

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

If labels, stage metrics, ablation outputs, or deobfuscation measurements change, update the plotting script and regenerate the PNG outputs. Do not keep old chart values after changing `data/ground_truth/combined_labels.json`, `data/reports/local/stage3_ensemble.json`, or `data/deobf/*.json`.
