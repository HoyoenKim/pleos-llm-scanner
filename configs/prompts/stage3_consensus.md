# Stage 3 — Consensus Rule (Multi-Perspective Ensemble)

The same model (Claude Opus 4.7) is invoked with three perspective prompts (`stage3_attacker.md`, `stage3_defender.md`, `stage3_domain_expert.md`) and their verdicts are merged by this rule. Diversity comes from the prompts (different analytical stances), not from different models.

## Consensus rule (TP determination)

For each `(class, line)` location, compare the three perspective verdicts:

| Agreement | Class | Treatment |
|---|---|---|
| 3/3 | **strong TP** | severity = max of the three; report with confidence ≥ 0.9. Top candidate for case-study card. |
| 2/3 | **TP** | severity = majority (max on tie); confidence = mean. |
| 1/3 | **uncertain → re-verify at Stage 2** | Keep the single-perspective result in a separate file; revisit via Stage 2 caller analysis or manual review. |
| 0/3 | clean | Not reported. |

## Merged output schema

```json
{
  "class": "...",
  "stage": "stage3",
  "ensemble_strategy": "multi-prompt-D3-B",
  "perspectives_run": ["attacker", "defender", "domain_expert"],
  "findings": [
    {
      "line": <int>,
      "category": "...",
      "consensus_count": <0~3>,
      "consensus_perspectives": ["attacker", "defender"],
      "severity": "...",
      "title": "...",
      "evidence": "...",
      "rationale_merged": "<one paragraph merging the three rationales>",
      "per_perspective": {
        "attacker": { "severity": "...", "rationale": "...", "attack_chain": [...] },
        "defender": { "severity": "...", "rationale": "...", "missing_control": "..." },
        "domain_expert": { "severity": "...", "vehicle_asset": "...", "stride": "...", "tara_impact": "..." }
      },
      "confidence": <0.0~1.0>
    }
  ]
}
```

## Operational procedure

1. **Stage 1**: run `stage1_detect.md` on each priority class (already done).
2. **Stage 2**: caller-chain trace + regex / AST verification (already in place; no separate prompt — rule + code analysis).
3. **Stage 3 entry condition**: candidates left at confidence 0.55~0.75 after Stage 2 are fed into Stage 3.
4. **Stage 3 run**: apply the three perspective prompts to the same class → three perspective verdicts → apply the consensus rule above.
5. **Stage 3 output path**: `data/reports/<apk>_<YYYYMMDD>_stage3.json`, stored separately from the Stage 1 / 2 reports.

## Multi-prompt vs multi-model — alternative considered

A multi-model ensemble (e.g. Opus + Sonnet + Haiku, or Claude + GPT-4) was considered first but ruled out by environment constraints. The trade-off:

| Property | Multi-model ensemble (alternative) | Multi-prompt ensemble (current) |
|---|---|---|
| Model diversity | Opus / Sonnet / Haiku, or different vendors | All Opus 4.7 |
| Automation | Not possible inside a single Claude Code session — manual cross-reading required | **Automatable in one session** |
| Source of perspective diversity | Training-data and architecture differences | Explicit role prompts (attacker / defender / domain expert) |
| Reporting honesty | Must disclose the manual workflow | Documents the environment limit and the chosen substitute |

## Future work

- Switching to a multi-model ensemble requires an external SDK / API budget; this is left as future work.
- A different model family (GPT-4, Gemini, etc.) can be plugged in later — the consensus rule above is reusable as-is.
