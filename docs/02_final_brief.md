# One-Page Evaluator Brief

## Conclusion

For PleOS / AAOS IVI APK security analysis, the strongest result is not an LLM acting alone. The useful pattern is deterministic triage, followed by LLM-assisted reasoning, Android-context verification, and calibrated multi-perspective consensus.

## Core Numbers

| Metric | Value |
|---|---:|
| Combined GT | 47 finding rows |
| Stage 1 Precision / Recall / F1 | 80.9% / 100.0% / 0.894 |
| Stage 3 `>=2/3` Precision / Recall / F1 | 100.0% / 97.4% / 0.987 |
| Stage 1 vs Stage 3 McNemar exact test | `p=0.0215` |
| Native static scan sample | `n=4`, additional native-bound vulnerability 0 |

## Pipeline

```text
APK -> jadx --deobf -> keyword triage -> Stage 1 candidates
    -> Stage 2 contextual verification -> Stage 3 >=2/3 consensus
    -> AAOS / MASVS / TARA mapping
```

## Most Important Limitation

The results are measured on a security-value selected corpus, not a random Android app-store population. The Stage 3 `0 FP` result means no false positives among accepted findings in this measured corpus; it is not a universal guarantee.

## Where To Read Next

| Need | File |
|---|---|
| Full measured report | `01_final_report.md` |
| Representative cases and claim levels | `03_case_studies.md` |
| Stage 2 method | `04_methodology_stage2.md` |
| Limitations and cost | `06_limitations_and_costs.md` |
| Completed reinforcement tracks A-E | `08_completed_reinforcements.md` |
