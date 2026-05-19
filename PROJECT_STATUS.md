# Project Status

Last cleaned: 2026-05-19.

## Status

The repository is arranged as the final 15-week research artifact. Reinforcement experiments A-E are completed and are part of the final project.

## Canonical Artifacts

| Purpose | File |
|---|---|
| First-read summary | `docs/02_final_brief.md` |
| Full final report | `docs/01_final_report.md` |
| Case evidence | `docs/03_case_studies.md` |
| Stage 2 method | `docs/04_methodology_stage2.md` |
| Completed reinforcement experiments | `docs/08_completed_reinforcements.md` |
| Remaining research extensions | `docs/09_research_extension_plan.md` |

## Final Numbers

| Metric | Value |
|---|---:|
| Combined GT | 47 |
| Stage 1 precision | 80.9% |
| Stage 1 false-positive rate | 19.1% |
| Stage 1 recall | 100.0% |
| Stage 1 F1 | 0.894 |
| Stage 3 `>=2/3` precision | 100.0% |
| Stage 3 `>=2/3` recall | 97.4% |
| Stage 3 `>=2/3` F1 | 0.987 |
| McNemar exact p-value | 0.0215 |
| Native static scan sample | 4 |
| Additional native-bound vulnerabilities | 0 |

## Disclosure Boundary

Public-safe:

- `data/reports/aggregate/`
- `data/reports/external/`
- `data/reports/public/`
- `data/ground_truth/`
- `data/viz/`

Local-only:

- `data/_local/`
- `data/reports/local/`
- `data/reports/per_apk_local/`
- `data/reports/runtime_local/`
- `data/reports/native_local/`
- `data/reports/rag_local/`
