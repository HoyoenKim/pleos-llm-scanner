# Figure Redesign Plan

This plan defines the target figure set for the final static-analysis results. Runtime PoC evidence is intentionally excluded from the main figure flow and should remain a separate validation track.

## Design Principle

Figures should explain the experiment flow, not preserve internal work-log terminology. The main sequence is:

```text
JADX output is checked for Java/Kotlin readability
  -> LLM scan creates candidates
  -> context verification filters candidates
  -> metrics improve
  -> verified vulnerabilities are analyzed by APK/severity
  -> consensus threshold is justified
  -> supporting validation tracks clarify robustness and limits
```

Use reader-facing labels such as `LLM Scan`, `Context Verification`, `candidate`, and `verified vulnerability`. Avoid using `Stage 1/2/3`, `combined n=47`, or `labelled findings` as front-facing chart language unless the chart specifically explains the evaluation protocol.

## Main Figures

### Main Figure 1: JADX Identifier-Pattern Obfuscation Screen

Purpose: show how many classes were flagged by the heuristic identifier-pattern screen during the static-analysis pass over JADX output.

- Chart type: bar chart.
- X-axis: test APK/sample.
- Y-axis: `HIGH-obfuscation classes (count)`.
- Color: sample origin, such as `MASTG`, `OSS`, `PleOS`.
- Bar label: `HIGH / analyzed classes` plus percentage, so small benchmark APKs are not overread through ratio alone.
- Main message: HIGH classes are counted by a heuristic screen over JADX-style identifiers such as `C0010a`, `m5a`, and `f2a`; the labels keep both absolute count and corpus size visible.
- Boundary: this is a readability screen for static analysis, not a validated obfuscation benchmark or vulnerability metric.
- Position in the research flow: static analysis / JADX readability and obfuscation check.
- Current source: `data/viz/01_obfuscation_profile_across_test_apks.png`.

### Main Figure 2: Candidate Verification By Vulnerability Pattern

Purpose: show which LLM-proposed vulnerability patterns remained after Android context verification and which patterns produced false-positive candidates.

- Chart type: grouped bar.
- X-axis: vulnerability pattern.
- Series: `Kept for reporting (TP)` and `Rejected after context check (FP)`.
- Main message: `intent`, `network`, and `permission` patterns require Android-specific checks before reporting.
- Current source: `data/viz/02_candidate_verification_by_pattern.png`.

### Main Figure 3: Scan Quality Before And After Verification

Purpose: show the headline metric improvement from adding context verification after the LLM scan.

- Chart type: grouped bar.
- X-axis: `Precision`, `Recall`, `F1`.
- Series: `LLM Scan` and `LLM Scan + Context Verification`.
- Values: `80.9 / 100.0 / 89.4` versus `100.0 / 97.4 / 98.7`.
- Main message: verification removes measured false positives with a small recall trade-off.
- Current source: `data/viz/03_scan_quality_before_after_verification.png`.

### Main Figure 4: Verified Security Vulnerabilities By APK And Severity

Purpose: show where verified vulnerabilities appear and which PleOS APKs are priority targets for follow-up analysis.

- Chart type: heatmap.
- Rows: APK/sample name with source tag: `[PleOS]`, `[MASTG]`, `[External]`, `[AOSP]`.
- Columns: `HIGH`, `MEDIUM`, `LOW`.
- Main message: HIGH cells identify follow-up priority, especially in rows marked `[PleOS]`.
- Current source: `data/viz/04_verified_vulnerabilities_by_apk_severity.png`.

### Main Figure 5: Consensus Threshold Trade-Off

Purpose: justify the final consensus threshold.

- Chart type: grouped bar or line/point chart.
- X-axis: `Any flag (>=1/3)`, `Majority (>=2/3)`, `Unanimous (>=3/3)`.
- Metrics: precision, recall, F1.
- Main message: `>=2/3` keeps precision at 100.0% while retaining 97.4% recall; `>=3/3` loses too many verified vulnerabilities.
- Current source: `data/viz/05_consensus_threshold_tradeoff.png`.

### Main Figure 6: Supporting Validation Summary

Purpose: summarize robustness and boundary checks that support, but do not replace, the main precision/recall result.

- Chart type: compact table-style chart or horizontal summary bars.
- Rows:
  - `Corpus/statistics`: `n=47`, McNemar `p=0.0215`.
  - `Native static scan`: `4 .so samples`, `0 additional native-bound vulnerabilities`.
  - `RAG intrinsic evaluation`: `85.1% verdict alignment`, `85.1% AAOS category alignment`.
  - `Codex cross-read`: `100% precision`, lower recall than the main consensus.
- Main message: supporting tracks clarify robustness, blind spots, and limits without changing the main static metric table.
- Current source: `data/viz/06_supporting_validation_tracks.png`.

## Appendix Figures

### Appendix Figure A1: Corpus Composition

Purpose: show where the 47 candidates came from.

- Chart type: horizontal bar or donut.
- Values: `PleOS (30)`, `MASTG (4)`, `InsecureBankv2 (9)`, `AOSP (4)`.
- Main message: the evaluation set combines project-target PleOS APKs with external vulnerable-corpus and AOSP-derived samples.

### Appendix Figure A2: Bootstrap Confidence Interval

Purpose: show uncertainty around candidate-generation metrics.

- Chart type: error-bar chart.
- Metrics: precision, F1, and false-positive rate.
- Source: `data/reports/aggregate/bootstrap_ci.*`.
- Main message: corpus expansion reduces uncertainty around the first LLM scan, but the result is still a measured corpus result rather than a universal benchmark.

### Appendix Figure A3: Obfuscation Score Distribution

Purpose: provide the technical evidence behind Main Figure 1.

- Chart type: boxplot.
- Y-axis: composite obfuscation score.
- Threshold lines: `HIGH = 0.7`, `MEDIUM = 0.4`.
- Main message: the obfuscation screen is a decompiled-code readability check based on identifier-pattern scores, not a vulnerability metric or a general obfuscation benchmark.
- Current source: `data/viz/appendix_a3_obfuscation_score_distribution.png`.

### Appendix Figure A4: AAOS / MASVS / TARA Mapping Summary

Purpose: show that verified vulnerabilities were mapped into automotive-security artifacts.

- Chart type: stacked bar or matrix.
- Option 1: vulnerability pattern by AAOS/MASVS section count.
- Option 2: TARA asset by threat matrix.
- Source: `data/reports/aggregate/aaos_mapping_table.*` and `data/reports/aggregate/tara_artifact.*`.
- Main message: the pipeline output is not just APK findings; it is connected to AAOS/MASVS/TARA reporting.

### Appendix Figure A5: Cross-Validation Track Comparison

Purpose: show the supporting validation tracks in more detail than Main Figure 6.

- Chart type: small multiple or table-style chart.
- Rows: RAG, native static scan, Codex cross-read, and statistical retest.
- Main message: these tracks check robustness and blind spots; they do not replace the main static evaluation.

## Implementation Notes

- Keep figure filenames aligned with the report order so opening `data/viz/` by filename matches the intended reading sequence.
- Regenerate PNGs only when `src/viz/plot_metrics.py` or source metrics change.
- After regenerating, open each PNG and check for overlapping title, legend, axis labels, value labels, and captions.
- Keep runtime PoC figures out of this main/static chart set.
