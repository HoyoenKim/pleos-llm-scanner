# Figure Redesign Plan

This plan defines the target figure set for the final static-analysis results. Runtime PoC evidence is intentionally excluded from the main figure flow and should remain a separate validation track.

## Design Principle

Figures should explain the experiment flow, not preserve internal work-log terminology. The main sequence is:

```text
JADX output is checked for Java/Kotlin readability
  -> LLM scan creates candidate findings
  -> Android context validation filters candidate findings
  -> metrics improve
  -> confirmed vulnerability findings are analyzed by APK/severity
  -> multi-role reviewer consensus threshold is justified
```

Use reader-facing labels such as `LLM-proposed candidate findings`, `Android context validation`, `confirmed vulnerabilities`, and `role-prompted reviewers`. Avoid using `Stage 1/2/3`, `combined n=47`, `rows`, or `labelled findings` as front-facing chart language unless the chart specifically explains the evaluation protocol.

## Main Figures

### Main Figure 1: Decompiled Identifier Obfuscation Pre-Screen For Static Review

Purpose: show how many classes were flagged by the heuristic identifier-name screen during the static-analysis pass over JADX output.

- Chart type: bar chart.
- X-axis: test APK/sample.
- Y-axis: `Flagged classes`.
- Color: sample origin, such as `MASTG`, `OSS`, `PleOS`.
- Bar label: `flagged / analyzed classes` plus percentage, so small benchmark APKs are not overread through ratio alone.
- Main message: classes are flagged by high-obfuscation identifier-name patterns such as `C0010a`, `m5a`, and `f2a`; the labels keep both absolute count and corpus size visible.
- Boundary: this is a readability screen for static analysis, not a validated obfuscation benchmark or vulnerability metric.
- Position in the research flow: static analysis / JADX readability and obfuscation check.
- Current source: `data/viz/01_obfuscation_profile_across_test_apks.png`.

### Main Figure 2: Final Outcomes For LLM-Proposed Candidate Findings

Purpose: show which LLM-proposed candidate findings are confirmed, rejected as false positives, or missed by the selected threshold.

- Chart type: grouped bar.
- X-axis: vulnerability category.
- Series: `Confirmed vulnerabilities`, `Rejected as false positives`, and `Missed true vulnerability`.
- Main message: final outcomes are 37 confirmed, 9 rejected as false positives, and one low-severity true vulnerability missed.
- Current source: `data/viz/02_candidate_verification_by_pattern.png`.

### Main Figure 3: Context-Aware Review Improves Precision And F1

Purpose: show the headline metric improvement from adding context verification after the LLM scan.

- Chart type: grouped bar.
- X-axis: `Precision`, `Recall`, `F1`.
- Series: `LLM scan only` and `Context validation + multi-role review`.
- Values: `80.9 / 100.0 / 89.4` versus `100.0 / 97.4 / 98.7`.
- Main message: context-aware review removes measured false positives with one low-severity miss.
- Current source: `data/viz/03_scan_quality_before_after_verification.png`.

### Main Figure 4: Confirmed Vulnerability Findings By APK And Severity

Purpose: show where confirmed vulnerability findings appear and which PleOS APKs are priority targets for follow-up analysis.

- Chart type: heatmap.
- Entries: APK/sample name with source tag: `[PleOS]`, `[MASTG]`, `[External]`, `[AOSP]`.
- Columns: `HIGH`, `MEDIUM`, `LOW`.
- Main message: HIGH severity cells identify follow-up priority, especially in PleOS project-target entries; this is not a prevalence estimate. The missed low-severity true vulnerability is excluded from confirmed counts.
- Current source: `data/viz/04_verified_vulnerabilities_by_apk_severity.png`.

### Main Figure 5: Multi-Role LLM Review: Precision-Recall Trade-Off By Consensus Threshold

Purpose: explain which role-prompted reviewer threshold is used after candidate claims and Android context-validation evidence packages already exist.

- Chart type: grouped bar or line/point chart.
- X-axis: `>=1 role agrees`, `>=2 roles agree`, `3/3 roles agree`.
- Subtitle: each candidate finding is reviewed by role-prompted attacker, defender, and in-vehicle infotainment (IVI)-domain reviewers.
- Y-axis: precision / recall / F1 (%).
- Metrics: precision, recall, F1 against the 47 candidate-finding reportability labels.
- Main message: `>=1` preserves recall but leaves seven false positives; `3/3` preserves precision but lowers recall to 86.8%; `>=2` confirms 37 findings with zero false positives and one low-severity false negative.
- Interpretation: the chart should make the candidate-acceptance rule readable without implying that ungrounded LLM agreement alone determines a vulnerability.
- Current source: `data/viz/05_accept_candidates_as_vulnerabilities_by_three_role_review.png`.

## Appendix Figures

### Appendix Figure A1: Source Composition Of The 47 Candidate Findings

Purpose: show where the 47 candidates came from.

- Chart type: horizontal bar.
- Values: `PleOS (30)`, `MASTG (4)`, `InsecureBankv2 (9)`, `AOSP (4)`.
- Main message: each unit is one candidate finding, not one APK or an ecosystem prevalence estimate.

### Appendix Figure A2: Bootstrap Uncertainty For The LLM-Only Candidate Scan

Purpose: show uncertainty around LLM-only candidate-scan metrics.

- Chart type: horizontal confidence-interval chart.
- Metrics: precision, F1, and false discovery share.
- Visual rule: label false discovery share as `1 - precision`, because the candidate-only setup does not define a standard FPR denominator with true negatives.
- Source: `data/reports/aggregate/bootstrap_ci.*`.
- Main message: corpus expansion reduces uncertainty around the first LLM scan, but the result is still a measured corpus result rather than a universal benchmark.

### Appendix Figure A3: Distribution Of Heuristic Identifier-Name Obfuscation Scores

Purpose: provide the technical evidence behind Main Figure 1.

- Chart type: boxplot.
- Y-axis: composite identifier-name score.
- Threshold lines: `High-score threshold = 0.7`, `Medium-score threshold = 0.4`.
- Mean marker: diamond marker per sample.
- Sample set: match Main Figure 1, including MASTG, OSS/NewPipe, and PleOS samples.
- Main message: the obfuscation screen is a decompiled-code readability check based on identifier-name pattern scores, not a vulnerability metric or a general obfuscation benchmark.
- Current source: `data/viz/appendix_a3_obfuscation_score_distribution.png`.

### Appendix Figure A4: AAOS/MASVS-Aligned Control-Area Summary

Purpose: show that the 38 reference vulnerability findings were mapped into automotive-security artifacts.

- Chart type: stacked bar or matrix.
- View: primary Android security control area count.
- Source: `data/reports/aggregate/aaos_mapping_table.*` and `data/reports/aggregate/tara_artifact.*`.
- Main message: the mapping describes the 38-finding reference set; the primary `>=2` role-prompted rule confirms 37 of these 38.

### Appendix Figure A5: Supporting Validation Tracks And Their Measurement Roles

Purpose: show the supporting validation tracks without adding a sixth main figure.

- Chart type: table-style chart.
- Entries: primary multi-role LLM review, paired comparison, independent LLM cross-review, native-code boundary scan, and retrieval-grounded consistency check.
- Main message: F1, paired-test p-values, native-boundary counts, and retrieval-alignment rates are different measurement types; they should not be shown as one comparable percent score.

## Implementation Notes

- Keep figure filenames aligned with the report order so opening `data/viz/` by filename matches the intended reading sequence.
- Regenerate PNGs only when `src/viz/plot_metrics.py` or source metrics change.
- After regenerating, open each PNG and check for overlapping title, legend, axis labels, value labels, and captions.
- Keep runtime PoC figures out of this main/static chart set.
