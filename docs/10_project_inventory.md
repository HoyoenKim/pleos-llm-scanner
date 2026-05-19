# Project Inventory And Disclosure Boundary

This document states what belongs in the public repository and what stays local-only. It is the disclosure inventory for the final 15-week archive.

## Scope Split

| Scope | Role | Policy |
|---|---|---|
| parent workspace | course materials, PPT/PDF submissions, and local progress notes outside this git repo | not part of the public artifact |
| `pleos-llm-scanner/` | source, configs, public-safe docs, labels, aggregate artifacts, and redacted reports | public repo source of truth |
| `data/_local/` | APKs, JADX output, raw evidence, tools, vector DBs, and local scratch | ignored local-only data |

## Canonical Public Files

| File | Role |
|---|---|
| `README.md` | repo map and quickstart |
| `docs/00_reading_guide.md` | reading paths |
| `docs/01_final_report.md` | measured-claim source of truth |
| `docs/02_final_brief.md` | one-page evaluator brief |
| `docs/03_case_studies.md` | representative findings and claim levels |
| `docs/04_methodology_stage2.md` | contextual verification method |
| `docs/05_charts.md` | chart source and interpretation boundary |
| `docs/06_limitations_and_costs.md` | limits and operating cost |
| `docs/07_remaining_work.md` | remaining work after final scope |
| `docs/08_completed_reinforcements.md` | completed reinforcement experiments A-E |
| `docs/09_research_extension_plan.md` | future experiment designs |
| `docs/10_project_inventory.md` | disclosure inventory |

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
| `data/reports/local/` | local Stage 3 and intermediate evidence |
| `data/reports/per_apk_local/` | unmasked per-APK reports |
| `data/reports/runtime_local/` | runtime evidence and PoC records |
| `data/reports/native_local/` | native scan scratch and local details |
| `data/reports/rag_local/` | local RAG ablation and judgment packages |

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
- raw screenshots, logcat, or window dumps
- videos
- unredacted reports
- generated vector DBs
- portable binary tools
- generated runtime harness outputs unless explicitly redacted and reviewed

## Redaction Rule

Public PleOS reports may keep metadata such as class name, line number, category, severity, rationale, AAOS/MASVS/TARA mapping, and high-level attack chain. They must not include proprietary code excerpts, secret literals, raw runtime logs, videos, or unredacted local evidence.

## Public Archive Rule

The public docs should explain what was measured and how to reproduce public-safe checks. Internal workspace cleanup notes, course submission logistics, parent-directory file inventories, and temporary local artifacts are intentionally excluded from `docs/`.
