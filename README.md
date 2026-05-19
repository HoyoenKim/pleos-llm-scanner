# pleos-llm-scanner

LLM-assisted static security analysis pipeline for Android Automotive / PleOS IVI APKs.

This repository is the **final 15-week research artifact** for the 2026-1 autonomous-driving research project. It should be read as a completed archive, not as an in-progress work log. Late-stage reinforcement experiments A-E are completed and integrated into the final results.

## Final Result

The project built and evaluated a pipeline that combines deterministic Android APK analysis with LLM-based reasoning:

```text
APK
  -> jadx decompile
  -> keyword triage
  -> Stage 0 obfuscation check
  -> Stage 1 LLM finding proposal
  -> Stage 2 contextual verification
  -> Stage 3 multi-perspective consensus
  -> AAOS / MASVS / TARA mapping
  -> final reports and public-safe artifacts
```

Final measured corpus:

| Metric | Result |
|---|---:|
| Combined GT | 47 labelled findings |
| Stage 1 precision / recall / F1 | 80.9% / 100.0% / 0.894 |
| Stage 3 `>=2/3` precision / recall / F1 | 100.0% / 97.4% / 0.987 |
| Stage 1 vs Stage 3 McNemar exact test | `p=0.0215` |
| Native static sample | 4 `.so` samples, 0 additional native-bound vulnerabilities |
| RAG intrinsic ablation | NN verdict 85.1%, AAOS category 85.1% |

The main conclusion is not that an LLM alone is a security scanner. The useful design is to place an LLM as a reasoning layer between deterministic triage and domain-specific verification.

## What Was Completed

The 15-week final scope includes:

| Area | Completed Work |
|---|---|
| APK collection/decompile | ADB extraction wrapper and `jadx --deobf` wrapper |
| Stage 0 | Obfuscation entropy and rename plausibility checks |
| Stage 1 | Six-category vulnerability candidate detection |
| Stage 2 | Manifest/caller/permission/route based contextual verification |
| Stage 3 | Single-model multi-perspective consensus |
| GT expansion | PleOS-customized, OWASP MASTG, InsecureBankv2, AOSP-derived samples |
| Statistics | Bootstrap CI, stage ablation, McNemar paired test |
| Mapping | AAOS/MASVS mapping and TARA artifact generation |
| Reinforcement A | Corpus expansion to `n=47` |
| Reinforcement B | Local RAG knowledge base and intrinsic retrieval evaluation |
| Reinforcement C | Native binary static scan track |
| Reinforcement D | Dynamic verification state machine and Frida hooks |
| Reinforcement E | Codex 3-model cross-read |

## Directory Map

```text
configs/                  keyword rules, schemas, prompt protocols
src/                      deterministic pipeline code
  evaluation/             metrics, ablation, bootstrap support
  deobf/                  obfuscation and rename support
  mapping/                AAOS / MASVS / TARA generation
  rag/                    local Chroma retrieval helpers
  dynamic/                state machine and Frida hook scripts
  native/                 native `.so` scanner
  viz/                    chart generation
scripts/                  orchestration and one-off research helpers
  apk/                    APK pull/decompile wrappers
  research/               RQ measurement and packaging scripts
  runtime_poc/            runtime PoC and recording helpers
  presentation/           deck/video helper scripts
  maintenance/            masking and result maintenance
docs/                     final report, brief, methodology, cases, limits
data/                     labels, public-safe reports, charts, local evidence boundary
```

## Data Boundary

Tracked public-safe artifacts:

```text
data/ground_truth/        final labels and merged GT
data/reports/aggregate/   aggregate measurements and tables
data/reports/external/    public vulnerable-corpus reports
data/reports/public/      masked PleOS public reports
data/deobf/               obfuscation measurements and rename outputs
data/viz/                 final chart PNGs
```

Local-only or generated evidence:

```text
data/_local/              APKs, JADX output, raw evidence, tools, DBs
data/reports/local/       unmasked Stage 3 and model outputs
data/reports/per_apk_local/
data/reports/runtime_local/
data/reports/native_local/
data/reports/rag_local/
```

PleOS proprietary code excerpts must stay redacted in public-facing files.

## Quickstart

Run commands from the repository root.

```bash
# Pull system APKs from an emulator into the local-only bucket.
bash scripts/apk/pull_apks.sh

# Decompile one APK with jadx into the local-only bucket.
bash scripts/apk/decompile.sh data/_local/apks/<package>.apk

# Evaluate report JSONs against the final combined GT.
python src/evaluation/eval.py \
  --labels data/ground_truth/combined_labels.json \
  --reports 'data/reports/**/*.json'

# Run stage/threshold ablation.
python src/evaluation/ablation.py \
  --labels data/ground_truth/combined_labels.json \
  --reports 'data/reports/**/*.json' \
  --stage3 data/reports/local/stage3_ensemble.json

# Regenerate AAOS/TARA aggregate outputs when labels or mappings change.
python src/mapping/aaos_map.py
python src/mapping/tara_generate.py
```

## Reading Order

1. `docs/00_reading_guide.md`
2. `docs/02_final_brief.md`
3. `docs/01_final_report.md`
4. `docs/03_case_studies.md`
5. `docs/04_methodology_stage2.md`
6. `docs/06_limitations_and_costs.md`
7. `docs/08_completed_reinforcements.md`

## License

MIT. See `LICENSE`.
