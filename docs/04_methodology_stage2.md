# Stage 2 Contextual Verification Methodology

Stage 2 exists because Stage 1 intentionally over-collects suspicious API patterns. Android security findings are rarely valid from an API name alone; reachability and platform controls decide exploitability.

## Inputs

| Input | Role |
|---|---|
| Stage 1 finding | candidate category, severity, class, line, evidence |
| `AndroidManifest.xml` | exported state, permissions, intent filters |
| Decompiled source | caller chain, route binding, package/component restriction |
| Framework semantics | protected broadcasts, signature permissions, system UID assumptions |
| GT and case notes | final validation and metric evaluation |

## Verification Questions

Stage 2 asks:

1. Can an untrusted caller reach this component or code path?
2. Is the component exported?
3. Is a signature/system permission required?
4. Is the intent explicit or package/component-restricted?
5. Is the route internal-only, such as Compose Nav state not bound to external URI?
6. Is the broadcast protected by Android?
7. Does the sensitive value cross a process/component boundary?
8. Is this production code or a dead/dev-only artifact?

## Common Rules

| Pattern | Stage 1 Risk | Stage 2 Check |
|---|---|---|
| `grantRuntimePermission` / `revokeRuntimePermission` | permission abuse | caller reachability, permission manager ownership, route binding |
| exported `Activity` / `Receiver` / `Provider` | component exposure | manifest export, permission gate, caller control |
| `BOOT_COMPLETED` receiver | broadcast spoofing | protected broadcast semantics |
| WebView URL/content path | network/content injection | external deep link, trusted data source, sanitization |
| implicit broadcast | spoofing/tampering | package restriction, target binding, receiver permission |
| hardcoded credential | credential exposure | use site, production reachability, secret vs identifier distinction |
| plaintext transport | network exposure | API-level transport setting, endpoint role, prod/dev separation |

## Verdicts

| Verdict | Meaning |
|---|---|
| TP | exploitable or security-relevant under project threat model |
| FP | blocked by platform/app control or not security-relevant |
| uncertain | insufficient evidence; requires runtime or owner validation |

Stage 2 should not silently convert uncertainty into a vulnerability. If reachability cannot be established, the finding remains uncertain or goes to dynamic verification.

## Example: `vc-3` / `vc-4`

Stage 1 flagged permission grant/revoke calls in `AppPermissionManager`. Stage 2 found:

- no external URI route to the path
- Compose navigation was internal-only
- caller-controlled path did not bind to privileged operation
- app-level permission manager logic did not expose arbitrary third-party grant/revoke

Final verdict: FP. This case is the main evidence that the pipeline is not just keyword scanning.

## Example: `ss-1`

Stage 1 flagged an exported `BOOT_COMPLETED` receiver. Stage 2 applied Android protected-broadcast semantics: normal third-party apps cannot spoof `BOOT_COMPLETED`.

Final verdict: FP.

## Relationship To Stage 3

Stage 2 produces grounded context. Stage 3 then re-reads the finding from three perspectives:

- attacker: can this be abused?
- defender: what existing control blocks it?
- IVI domain expert: does it matter for vehicle/IVI assets?

The final reporting threshold is Stage 3 `>=2/3`.

## Automation Boundary

The current Stage 2 implementation combines deterministic scripts, rule dictionaries, and human/Codex inspection. It is not a full general-purpose Android static analyzer. The correct final claim is:

> Stage 2 provides contextual verification rules that materially reduce false positives on the final corpus; it is not an independent complete Android reachability engine.
