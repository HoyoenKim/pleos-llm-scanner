# pleos-llm-scanner

LLM-assisted static security analysis pipeline for Android Automotive / PleOS IVI APKs.

This repository is organized as a research artifact, not as a raw working dump. The
tracked tree keeps reproducible code, prompts, labels, aggregate reports, public
external-corpus results, and masked public PleOS reports. APKs, JADX output, raw
runtime evidence, videos, vector DBs, native extracts, and portable tools live under
`data/_local/` or ignored report subdirectories.

## Current Status

- Semester work and Future Work A-E are complete as of 2026-05-14.
- The canonical final report is `docs/01_final_report.md`.
- The first-read summary is `docs/02_final_brief.md`.
- Remaining deliverable in the parent workspace: final presentation deck.

For a compact state snapshot, read `PROJECT_STATUS.md`.

## Pipeline

```text
APK
  -> scripts/apk/pull_apks.sh
  -> scripts/apk/decompile.sh
  -> configs/keywords.yaml keyword triage
  -> Stage 0 optional deobfuscation prompt
  -> Stage 1 LLM detection prompt
  -> Stage 2 deterministic contextual verification
  -> Stage 3 multi-perspective consensus
  -> evaluation / ablation / AAOS mapping / TARA / charts
```

LLM analysis is performed by Codex/Claude Code sessions directly. The repository
does not contain OpenAI, Anthropic, or other external LLM API calls for PleOS code.

## Directory Map

```text
configs/                  analysis config, schemas, prompt protocols
src/                      deterministic pipeline code
  evaluation/             precision, recall, F1, ablation
  deobf/                  entropy-based obfuscation measurement
  mapping/                AAOS / MASVS / TARA generation
  rag/                    local Chroma RAG index and retrieval helpers
  dynamic/                deterministic LangGraph state machine + Frida hooks
  native/                 native-library string/pattern scanner
  viz/                    report chart generation
scripts/                  operational and research helpers
  apk/                    APK pull/decompile wrappers
  research/               RQ measurement and corpus-expansion scripts
  runtime_poc/            runtime PoC harness and evidence capture helpers
  presentation/           local presentation/video helper scripts
  maintenance/            masking and result-maintenance scripts
docs/                     final report, brief, methodology, case studies
data/                     labels, public-safe reports, charts, local evidence
```

## Data Boundary

```text
data/ground_truth/        tracked labels
data/reports/aggregate/   tracked GT-derived aggregate reports
data/reports/external/    tracked public vulnerable-corpus reports
data/reports/public/      tracked masked PleOS public reports
data/deobf/               tracked obfuscation measurements and rename outputs
data/viz/                 tracked chart PNGs
data/_local/              ignored APKs, JADX output, raw evidence, tools, DBs
data/reports/*_local/     ignored private/generated report tracks
```

## Quickstart

```bash
# 1. Pull system APKs from an emulator into the local-only bucket.
bash scripts/apk/pull_apks.sh

# 2. Decompile one APK with jadx into the local-only bucket.
bash scripts/apk/decompile.sh data/_local/apks/<package>.apk

# 3. Evaluate reports against combined GT.
python src/evaluation/eval.py \
  --labels data/ground_truth/combined_labels.json \
  --reports 'data/reports/**/*.json'

# 4. Run stage/threshold ablation.
python src/evaluation/ablation.py \
  --labels data/ground_truth/combined_labels.json \
  --reports 'data/reports/**/*.json' \
  --stage3 data/reports/local/stage3_ensemble.json

# 5. Regenerate AAOS/TARA aggregate outputs.
python src/mapping/aaos_map.py
python src/mapping/tara_generate.py
```

## Reading Order

Start with `docs/00_reading_guide.md`. In short:

1. `docs/02_final_brief.md` for the project in one pass.
2. `docs/01_final_report.md` for the full report.
3. `docs/03_case_studies.md` and `docs/04_methodology_stage2.md` for evidence and method.
4. `data/reports/README.md` to understand what report files are public, aggregate, or local-only.

## License

MIT. See `LICENSE`.
