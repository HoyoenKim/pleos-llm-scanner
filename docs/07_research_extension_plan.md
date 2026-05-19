# Research Extension Plan — After v1.4 Supplement

_Created: 2026-05-14 / scope: post-report research expansion, not required for the current final PPT._

This document separates the completed **v1.4 supplement** conclusion from optional follow-up experiments that can strengthen the work as a longer research project.

## Bottom Line

The current research conclusion is already fixed:

- Claude Code single-model multi-perspective Stage 3 is the strongest current validation layer: `n=47`, Precision 100.0%, Recall 97.4%, F1 98.7%, McNemar `p_exact=0.0215`.
- Codex 3-model cross-read is useful as independent reproducibility evidence, but its 2/3 consensus is more conservative: Precision 100.0%, Recall 76.3%, F1 86.6%.
- The next research question is therefore not "add more models blindly"; it is **which evidence packaging or runtime signal actually changes model decisions in the right direction?**

## Priority Roadmap

| Priority | Extension | Research Question | Current Status | Done Criteria |
|---:|---|---|---|---|
| 1 | RAG end-to-end ablation | Does retrieved AAOS/MASVS/TARA/history context improve Stage 1 verdict quality? | Intrinsic retrieval measured only: NN/AAOS 85.1%, MASVS 23.4% | `no_rag` vs `with_rag` paired judgments on sample19, then full47; Precision/Recall/F1 and discordance table |
| 2 | Dynamic runtime validation | Which static findings become stronger/weaker after Frida runtime evidence? | deterministic state machine + 5 hook scripts ready | At least 3 hooks executed on PleOS AVD or emulator-equivalent target; runtime observation attached to case studies |
| 3 | Native deep dive | Are high-value native libs hiding secrets/endpoints beyond string-level analysis? | native sample n=4 static strings, 0 additional vulns | Ghidra Go plugin or equivalent symbol recovery for `libgojni.so`; use-site of UUID and MQTT payload path classified |
| 4 | Public redaction expansion | Can full n=47 evidence be safely shared? | public Stage 3 remains initial n=12 snapshot | full n=47 public masked report regenerated and reviewed for PleOS source leakage |
| 5 | n>=60 statistical expansion | Does McNemar significance remain stable with broader corpus? | n=47 significant, but discordant b+c=10 | n>=60 combined labels + Stage 3 applied to new labels + updated bootstrap/McNemar |
| 6 | True multi-vendor comparison | Does vendor diversity beat prompt diversity? | Codex-only 3-model cross-read complete | Only if IP/budget policy allows non-PleOS or redacted public-corpus prompts through external APIs |

## Priority 1 Design — RAG End-To-End Ablation

### Experiment Unit

The unit is an already discovered finding, not a new class scan. This keeps the experiment focused on **validation quality**:

- Input: one Stage 1 finding hypothesis with APK, class, line, category, severity, title, evidence, and rationale.
- Hidden GT: `is_real` from `combined_labels.json`.
- Output: `report` or `suppress`, with confidence and short reason.

### Conditions

| Condition | Context Given To Model | Purpose |
|---|---|---|
| `no_rag` | Finding only | Baseline validation prompt without retrieved domain knowledge |
| `with_rag` | Same finding + retrieved AAOS/MASVS/TARA/history context | Tests whether retrieved context improves calibration |

The model must not search for new vulnerabilities. It only decides whether the given finding should remain reportable.

Leakage control is mandatory for `with_rag`: the target finding's own historical row is removed from retrieval results, and explicit `GT verdict` / `is_real` fields are redacted from historical examples before the prompt is written.

Judgment should be run in a fresh Codex or Claude session that has not seen `combined_labels.json`, the sample composition, or the expected TP/FP split. The current planning session is not a valid judge because it has already inspected the GT and leakage checks.

### Scopes

| Scope | Findings | Purpose |
|---|---|---|
| `sample19` | strong TP 10 + uncertain/low-consensus 5 + FP controls 4 | cheap smoke test; checks whether RAG suppresses controls without losing strong TPs |
| `full47` | all combined GT findings | final measurement after sample19 passes |

### Metrics

- Per-condition Precision / Recall / F1.
- RAG delta: `with_rag - no_rag`.
- Paired discordance: no_rag wrong → with_rag correct, and no_rag correct → with_rag wrong.
- FP-control suppression rate for sample19.
- Evidence-use audit: whether the reason mentions retrieved history, AAOS, MASVS, or TARA.

### Acceptance Criteria

Sample19 can expand to full47 only if:

- `with_rag` does not lose more than one strong TP.
- At least one FP control is suppressed because of retrieved historical FP or AAOS/MASVS mismatch.
- Output JSON validates against the expected schema.
- The model does not use universal-report or universal-suppress behavior.
- No retrieved context exposes the target finding's own GT label.

## Artifacts

New deterministic tooling:

- `configs/prompts/rag_end_to_end_judge.md` — manual/Codex judgment prompt.
- `scripts/research_rag_end_to_end_pack.py` — creates paired `no_rag` / `with_rag` input packages.
- `scripts/research_rag_end_to_end_eval.py` — scores filled judgment JSON files against GT.

Generated local-only artifacts:

- `data/reports/rag_end_to_end/sample19_no_rag_input.json`
- `data/reports/rag_end_to_end/sample19_with_rag_input.json`
- `data/reports/rag_end_to_end/sample19_no_rag_results_template.json`
- `data/reports/rag_end_to_end/sample19_with_rag_results_template.json`
- `data/reports/rag_end_to_end/*_metrics.{json,md}`

These generated artifacts may include PleOS finding evidence and stay local-only.
