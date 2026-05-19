# Project Status

Last cleaned: 2026-05-19.

## Summary

The repo now separates final research artifacts from local working evidence.

- Completed: semester Phase A-E and off-semester Future Work A-E.
- Canonical report: `docs/01_final_report.md`.
- First-read brief: `docs/02_final_brief.md`.
- Public-safe reports: `data/reports/aggregate/`, `data/reports/external/`, `data/reports/public/`.
- Local-only evidence: `data/_local/`, `data/reports/local/`, `data/reports/per_apk_local/`, `data/reports/runtime_local/`, `data/reports/native_local/`, `data/reports/rag_local/`.

## Current Numbers

- Combined GT: n=47.
- Stage 1: precision 80.9%, false-positive rate 19.1%, recall 100%, F1 0.894.
- Stage 3 2/3 consensus: precision 100%, recall 97.4%, F1 0.987.
- McNemar exact p-value: 0.0215.
- Native scan sample: n=4, additional native-bound vulnerabilities found: 0.

## Next Deliverable

Prepare the final presentation deck from the parent workspace. The repository is now arranged so the deck can cite:

- `docs/02_final_brief.md` for narrative.
- `docs/01_final_report.md` for details.
- `data/reports/aggregate/` for measured tables.
- `data/viz/` for figures.
- `data/reports/runtime_local/` and `data/_local/poc_evidence/` only after redaction review.
