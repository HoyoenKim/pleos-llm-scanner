# Reading Guide

This repo has three audiences. Use the path that matches your task.

## For A First-Time Evaluator

1. `02_final_brief.md` - concise project summary and conclusions.
2. `01_final_report.md` - full v1.4 supplement report.
3. `03_case_studies.md` - concrete TP/FP/dynamic examples.
4. `05_charts.md` - chart interpretation and reproduction notes.

## For Method Review

1. `04_methodology_stage2.md` - contextual verification rules.
2. `08_future_work_implementations.md` - completed A-E follow-up work.
3. `06_limitations_and_costs.md` - limits, costs, and boundary conditions.
4. `09_research_extension_plan.md` - optional next research units.

## For Reproduction

1. `../README.md` - repository map and quickstart.
2. `../configs/prompts/README.md` - Stage 0/1/3 prompt protocol.
3. `../data/README.md` - data boundary and local-only policy.
4. `../data/reports/README.md` - report folder classification.
5. `../src/README.md` and `../scripts/README.md` - code and helper layout.

## What Is Local-Only

Do not publish or commit:

- `data/_local/`
- `data/reports/local/`
- `data/reports/per_apk_local/`
- `data/reports/runtime_local/`
- `data/reports/native_local/`
- `data/reports/rag_local/`

These may contain PleOS APKs, decompiled code, raw runtime evidence, videos,
vector DBs, native extracts, or unredacted report details.
