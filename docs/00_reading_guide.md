# Reading Guide

Read this directory as the final 15-week archive. Reinforcement experiments A-E are completed and integrated into the final result unless a document explicitly labels a separate item as remaining work.

## Fast Paths

| Reader | Start Here | Then Read |
|---|---|---|
| First-time evaluator | `02_final_brief.md` | `01_final_report.md`, `03_case_studies.md` |
| Method reviewer | `04_methodology_stage2.md` | `03_case_studies.md`, `06_limitations_and_costs.md` |
| Reproducer | `../README.md` | `05_charts.md`, `10_project_inventory.md`, `../data/README.md`, `../src/README.md` |
| Project maintainer | `10_project_inventory.md` | `07_remaining_work.md`, `08_completed_reinforcements.md` |

## Document Roles

| File | Role |
|---|---|
| `01_final_report.md` | Full final report and measured claims |
| `02_final_brief.md` | Compact evaluator-facing summary |
| `03_case_studies.md` | Representative TP/FP/runtime-boundary cases |
| `04_methodology_stage2.md` | Contextual verification method |
| `05_charts.md` | Final chart inventory and reproduction notes |
| `06_limitations_and_costs.md` | Limits, residual risks, and cost trade-offs |
| `07_remaining_work.md` | True remaining follow-up work after 15 weeks |
| `08_completed_reinforcements.md` | Completed reinforcement experiments A-E |
| `09_research_extension_plan.md` | Future experiment designs |
| `10_project_inventory.md` | Repo disclosure and push boundary |

## Local-Only Rule

Do not publish or commit raw files from:

- `data/_local/`
- `data/reports/local/`
- `data/reports/per_apk_local/`
- `data/reports/runtime_local/`
- `data/reports/native_local/`
- `data/reports/rag_local/`

These paths may contain APKs, decompiled code, raw runtime evidence, videos, native extracts, vector DBs, or unredacted report details. See `10_project_inventory.md` for the full disclosure boundary.
