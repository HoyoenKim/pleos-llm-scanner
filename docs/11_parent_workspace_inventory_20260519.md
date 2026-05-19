# Parent Workspace Inventory And Cleanup Policy

_Date: 2026-05-19_

This note covers files outside the `pleos-llm-scanner/` git repository, under the parent course workspace.

## Key Finding

The parent workspace is not a git repository. The only git repositories found under it are:

| Path | Meaning | Cleanup policy |
|---|---|---|
| `pleos-llm-scanner/.git` | Main public project repository | Pushable source of truth |
| `pleos-llm-scanner/data/apks/_mastg/owasp-mastg/.git` | Local OWASP MASTG input clone under ignored data | Local-only reference corpus; do not push as part of this repo |

Because the parent workspace contains submitted PPT/PDF files, APK inputs, and runtime PoC artifacts, do not initialize or push it as a new repository without a separate redaction pass.

## Parent Directory Classification

| Path | Current role | Action |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md` | Project/session operating instructions | Keep in parent workspace |
| `progress.md`, `next.md` | Local canonical progress and next-action notes | Keep in parent workspace; mirror only public-safe summaries into repo docs |
| `.claude/` | Local Claude/session settings (`settings.local.json`, lock file) | Keep local; never push |
| `pptx/` | Weekly decks, final deck versions, course overview PDF | Keep local. Do not overwrite submitted files; create new versions if needed |
| `scripts/` | Parent-level PPT helper scripts (`build_ppt_w11_v4_*`) | Keep local unless a rebuild path must be made public |
| `data/apks/_external/` | External APK inputs (`NewPipe.apk`, `InsecureBankv2.apk`) | Keep local-only as benchmark inputs |
| `data/runtime_poc_harness/` | Generated runtime PoC harness source/build outputs | Treat as local-only generated evidence; do not push APK/dex/keystore/class outputs |
| `tmp_pentest_report.docx` | Unclassified old document | Leave untouched until provenance is confirmed |

## Notable Files Observed

| Group | Files |
|---|---|
| Final deck | `pptx/v5/*_v5.pptx` |
| Earlier final deck versions | `pptx/v4/*_v4.pptx`, `pptx/v3/*_v3.pptx` |
| Weekly decks | `pptx/*_{2..14}*.pptx` and v3 revisions for weeks 12-14 |
| Course overview | `pptx/*.pdf` |
| Parent helper scripts | `scripts/build_ppt_w11_v4_plain.py`, `scripts/build_ppt_w11_v4_readable.py` |
| External APK inputs | `data/apks/_external/NewPipe.apk`, `data/apks/_external/InsecureBankv2.apk` |
| Runtime harness outputs | `data/runtime_poc_harness/*.apk`, `*.idsig`, `debug.keystore`, `classes.jar`, `dex/classes.dex`, compiled classes |

## Cleanup Plan

1. Keep the parent workspace as a local course/submission workspace, not a pushed repository.
2. Keep all submitted or submission-adjacent `.pptx` and `.pdf` files under `pptx/`; create new versioned files instead of overwriting.
3. Keep APKs and runtime PoC harness outputs local-only. Public commits should contain only deterministic scripts and sanitized summary docs.
4. If the harness source is needed later, regenerate it from the tracked repo scripts instead of treating parent `data/runtime_poc_harness/` as the canonical source.
5. After the final presentation, archive parent generated outputs in a local archive folder or zip, but do not delete them before final deck/video QA is complete.
6. Do a separate provenance check before moving or deleting `tmp_pentest_report.docx`.

## Push Boundary

Only `pleos-llm-scanner/` can be pushed in the current workspace layout. This document is the public-safe record of the parent workspace cleanup decision.
