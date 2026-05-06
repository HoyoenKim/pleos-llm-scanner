# configs/prompts/ — LLM Prompt Index

Prompts used at each LLM stage of the pipeline. Every prompt is invoked **inside a Claude Code session directly**; there is no separate SDK invocation code (per the project policy of using Claude Code itself as the analysis engine).

## Pipeline overview

```
                 ┌─ Stage 0 ─┐    ┌─ Stage 1 ─┐    ┌─ Stage 2 ─┐    ┌─── Stage 3 ───┐
APK ── jadx ──► obf check ──► detection ──► verification ──► ensemble ──► report
                (optional)    (LLM)         (rule + code)    (LLM × 3 + merge)
```

| Stage | Name | What it does | Has its own prompt? |
|---|---|---|---|
| 0 | **Deobfuscation** | Rename obfuscated class / method / field identifiers using semantic hints. Runs **before** Stage 1. Skipped when the class is not heavily obfuscated (composite obf score < 0.7). | Yes — `stage0_deobfuscate.md` |
| 1 | **Initial Detection** | First LLM pass over a single decompiled class. Emits candidate findings in 6 categories (crypto / network / permission / intent / hardcoded / reflection_dynamic). | Yes — `stage1_detect.md` |
| 2 | **Verification** | Caller-chain trace, manifest / Hilt graph inspection, regex + AST checks. Updates each Stage 1 finding's verdict (TP / FP / uncertain). | **No separate prompt** — rule + code analysis driven interactively. |
| 3 | **Ensemble** | Same model invoked with three perspective prompts; verdicts merged by the consensus rule. Default consensus threshold ≥ 2/3 (best F1 in ablation). | Yes — three perspective prompts + one consensus rule. |

## Files

| File | Stage | Role |
|---|---|---|
| [stage0_deobfuscate.md](stage0_deobfuscate.md) | 0 | Rename obfuscated identifiers (composite obf score ≥ 0.7) |
| [stage1_detect.md](stage1_detect.md) | 1 | First-pass detection across the 6 categories |
| [stage3_attacker.md](stage3_attacker.md) | 3 (1/3) | Attacker viewpoint — concrete exploit chain |
| [stage3_defender.md](stage3_defender.md) | 3 (2/3) | Defender viewpoint — missing controls |
| [stage3_domain_expert.md](stage3_domain_expert.md) | 3 (3/3) | IVI / vehicle-security domain viewpoint |
| [stage3_consensus.md](stage3_consensus.md) | 3 (merge) | Consensus rule (≥1/2/3 thresholds) + merged JSON schema |

## D3 mapping

- **D3 = (B) multi-prompt ensemble** — chosen due to environment constraints (single-model Claude Code session, no external paid API budget). The same Opus 4.7 model is invoked with three perspective prompts.
- Default consensus threshold = **≥ 2/3** — best F1 in Variant B ablation (combined n=19 → F1 0.966).

## Output schema

JSON output of every prompt follows `../result_schema.json`. The Stage 3 merged output lives at `data/reports/stage3_ensemble_<DATE>.json`.

## Naming convention

- `stage<N>_<role>.md` where `N ∈ {0, 1, 3}`. Stage 2 has no separate prompt.
- New perspectives at Stage 3: add `stage3_<perspective>.md` and update the threshold table inside `stage3_consensus.md`.
- All prompt bodies are in **English** for consistency across stages and reproducibility on multilingual corpora.
