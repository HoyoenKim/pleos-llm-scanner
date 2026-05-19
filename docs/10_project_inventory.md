# Project Inventory

This document records the final repository organization after the 15-week research artifact cleanup.

## Scope Split

| Scope | Role | Policy |
|---|---|---|
| parent workspace | course materials, PPT/PDF submissions, local progress notes | local workspace, not a pushed git repo |
| `pleos-llm-scanner/` | source, configs, public-safe docs, aggregate artifacts | public repo source of truth |
| `data/_local/` | APKs, JADX output, raw evidence, tools, vector DBs | ignored local-only data |

## Canonical Public Files

| File | Role |
|---|---|
| `README.md` | repo map and quickstart |
| `PROJECT_STATUS.md` | compact final state |
| `docs/01_final_report.md` | full final report |
| `docs/02_final_brief.md` | first-read summary |
| `docs/03_case_studies.md` | representative findings |
| `docs/04_methodology_stage2.md` | contextual verification method |
| `docs/06_limitations_and_costs.md` | limits and operating cost |
| `docs/08_completed_reinforcements.md` | completed reinforcement experiments A-E |

## Tracked Data

| Path | Meaning |
|---|---|
| `data/ground_truth/` | final labels and merged GT |
| `data/reports/aggregate/` | aggregate metrics and mapping tables |
| `data/reports/external/` | public vulnerable-corpus reports |
| `data/reports/public/` | masked PleOS public reports |
| `data/deobf/` | obfuscation and rename measurements |
| `data/viz/` | final chart images |

## Local-Only Data

| Path | Meaning |
|---|---|
| `data/_local/apks/` | APK inputs |
| `data/_local/decompiled/` | JADX output |
| `data/_local/poc_evidence/` | raw runtime evidence |
| `data/_local/runtime_videos/` | videos and previews |
| `data/_local/native_extracts/` | native extracted binaries and analysis scratch |
| `data/_local/rag_db/` | Chroma vector DB |
| `data/_local/tools/` | portable binary tools |
| `data/reports/*_local/` | unmasked or generated report tracks |

## Final Timeline Markers

| Date | Meaning |
|---|---|
| 2026-04-29 | repo scaffold, APK extraction/decompile, initial self-label |
| 2026-04-30 | Stage 2 verification, MASTG baseline, Stage 0, AAOS/TARA first pass |
| 2026-05-06 | evaluation scripts, baseline comparison, early RQ measurements |
| 2026-05-11 | broader corpus, report/brief consolidation |
| 2026-05-14 | reinforcement experiments A-E integrated into final results |
| 2026-05-19 | repo structure cleanup and final-document rewrite policy |

## Commit Policy

Commit:

- deterministic source code
- prompt/config files without secrets
- final docs
- GT labels
- aggregate/public-safe reports
- redacted public copies

Do not commit:

- APKs
- decompiled PleOS code
- raw screenshots/logcat/window dumps
- videos
- unredacted reports
- generated vector DBs
- binary tools

## Redaction Rule

Public PleOS reports may keep metadata such as class name, line number, category, severity, rationale, AAOS/MASVS/TARA mapping, and high-level attack chain. They must not include proprietary code excerpts or secret literals.
