# Codex Multi-Model Cross-Read Prompt

You are one Codex model participating in an independent cross-read of an existing APK
static-analysis finding. The baseline findings were produced earlier by a Claude Code
single-model multi-perspective workflow. Your job is not to discover new findings. Your
job is to re-judge each provided candidate as either reportable or suppressible.

## Decision Task

For every finding in the input JSON, return exactly one verdict:

- `report`: keep this finding in the security report.
- `suppress`: do not report this finding as a vulnerability. It may still be a
  hardening note, best-practice recommendation, blocked chain, or already-mitigated
  pattern.

Use the supplied evidence, class/line metadata, category, title, and Claude baseline
context. The Claude baseline is only a prior result for comparison; do not copy it
uncritically. Override it whenever the evidence or blocking controls do not support
the same conclusion.

## Reportability Standard

Report a finding only when there is a concrete security-relevant primitive, such as:

- externally reachable component with missing permission or caller validation
- hardcoded credential, key, token, endpoint secret, or stable device identifier
- insecure transport or absent/disabled TLS protection in an actual data path
- sensitive data exposure through logs, providers, broadcasts, WebView, or IPC
- permission grant/revoke or privileged action reachable by an untrusted caller

Suppress a finding when the evidence only shows:

- defense-in-depth hardening without an exploit or sensitive-data path
- caller chain blocked by manifest, protected broadcast, signature permission, or
  internal-only navigation
- explicit component/package targeting that prevents third-party interception
- user-confirmed navigation without automatic privileged action
- a low-severity warning whose only effect is broad API-hardening guidance

## Required Output JSON

Return JSON only. Do not include Markdown.

```json
{
  "schema_version": "codex-multimodel-verdict-v0.1",
  "run_id": "codex_multimodel_<scope>_<model_actual>_YYYYMMDD",
  "model_requested": "<requested model id>",
  "model_actual": "<actual model id used>",
  "scope": "sample19 or full47",
  "generated_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "source_input": "data/reports/local/codex_multimodel/<scope>_model_inputs.json",
  "verdicts": [
    {
      "finding_id": "vc-5",
      "verdict": "report",
      "confidence": 0.0,
      "severity": "critical|high|medium|low|none",
      "reason": "One or two concise sentences explaining the deciding evidence.",
      "blocking_control": "The concrete control that blocks exploitation, or null.",
      "evidence_used": ["short evidence reference 1", "short evidence reference 2"]
    }
  ]
}
```

## Constraints

- Return one verdict for every input finding and no extra finding IDs.
- Do not use ground-truth labels. Model-facing inputs intentionally omit them.
- Keep `reason` concise and evidence-based.
- Use `severity: "none"` when `verdict` is `suppress` and the candidate is not
  reportable. Use `low` only when it remains a reportable low-severity issue.
- If the candidate is real but the exploit is limited, prefer `report` with lower
  severity over `suppress`.
- If the candidate is a blocked chain or policy-hardening-only issue, prefer
  `suppress`.
