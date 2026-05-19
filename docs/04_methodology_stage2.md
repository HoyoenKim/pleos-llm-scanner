# Stage 2 Contextual Verification Methodology

Stage 2 is semi-automated contextual verification. It exists because Stage 1 intentionally over-collects suspicious API patterns, while Android exploitability depends on caller reachability, platform controls, component boundaries, and permissions.

Stage 2 is not a complete Android reachability engine. It is a structured verification layer that materially reduces false positives before Stage 3 consensus.

## 1. Purpose

Stage 2 answers a narrow question:

```text
Given a Stage 1 candidate, does Android/PleOS context support reporting it as a security finding?
```

The goal is to separate reportable findings from API-name false positives.

## 2. Inputs

| Input | Role |
|---|---|
| Stage 1 finding | Candidate category, severity, class, line, evidence, and rationale |
| `AndroidManifest.xml` | Exported state, permissions, intent filters, providers, receivers, services, and activities |
| Decompiled source | Caller chain, route binding, package/component restriction, value flow, and use site |
| Android framework semantics | Protected broadcasts, signature permissions, permission-manager ownership, and system UID assumptions |
| GT and case notes | Final validation and metric evaluation |

## 3. Verification Questions

1. Can an untrusted caller reach this component or code path?
2. Is the component exported?
3. Is a signature, privileged, or system permission required?
4. Is the intent explicit or restricted by package/component binding?
5. Is the route internal-only, such as Compose Nav state not bound to an external URI?
6. Is the broadcast protected by Android?
7. Does the sensitive value cross a process, component, or trust boundary?
8. Is this production code or a dead/dev-only artifact?
9. Does a framework guard turn the apparent vulnerability into a blocked path?

## 4. Rule Table

| Pattern | Stage 1 Risk | Stage 2 Check | Typical Stage 2 Outcome |
|---|---|---|---|
| Exported activity/service/receiver | Intent abuse | Manifest export state, permission, action, package restriction, caller path | TP if reachable by untrusted caller; FP if protected or internal-only |
| Exported provider | Data exposure or mutation | Provider export state, read/write permission, URI access, caller assumptions | TP if sensitive rows are reachable; uncertain if runtime-only |
| `grantRuntimePermission` / `revokeRuntimePermission` | Permission abuse | Caller reachability, permission-manager ownership, route binding | Often FP when route is internal-only |
| `sendBroadcast` / receiver handling | Broadcast spoofing or leak | Protected broadcast list, explicit component, package binding, sender privilege | TP only if normal caller can trigger meaningful behavior |
| `.usePlaintext()` / cleartext network | Transport risk | Production endpoint, diagnostic context, network security config, dead-code check | TP if production path remains plausible |
| WebView / JS bridge | Code or data exposure | Exported entrypoint, URL source, JS interface use, navigation constraints | TP only when untrusted content can reach sensitive bridge |
| Hardcoded credential | Secret exposure | Secret vs identifier distinction, use site, production reachability, redaction boundary | TP if credential-like material is production-relevant |
| Reflection/dynamic loading | Code integrity risk | Source of class/path, caller-controlled input, package trust boundary | TP only with controllable loading path |

## 5. Verdict Rubric

| Verdict | Meaning |
|---|---|
| TP | Context supports reporting the Stage 1 candidate as a security finding |
| FP | Context blocks the candidate or shows it is not security-relevant |
| Uncertain | Static context is insufficient; keep out of final reporting or route to runtime verification |
| Runtime follow-up | Static finding is plausible, but claim level depends on captured emulator evidence |

Stage 2 must not silently convert uncertainty into a vulnerability. If reachability cannot be established, the finding remains uncertain or is routed to dynamic verification.

## 6. Examples

### `vc-3` / `vc-4`

Stage 1 flagged permission-management APIs because they are sensitive. Stage 2 checked manifest exposure, navigation binding, and caller route.

The dangerous-looking API calls were not reachable from an untrusted external path in the final evidence package, so these rows became false positives.

### `ss-1`

Stage 1 flagged an exported receiver. Stage 2 applied Android protected-broadcast semantics: a normal third-party app cannot send `BOOT_COMPLETED`. The receiver therefore became a false positive control case.

### `lmp-1`

Stage 1 flagged a sensitive provider surface. Stage 2 kept it because provider exposure was meaningful under the IVI LLM threat model. Runtime evidence can strengthen the claim level, but the static finding remains separate from runtime capture.

## 7. Relationship To Stage 3

Stage 2 prepares evidence packages for Stage 3. It is the context-filtering layer that gathers manifest, caller-chain, permission, route, and trust-boundary evidence before the final reporting decision.

Stage 3 is the final reporting gate. It asks three calibrated perspectives to review the Stage 2 evidence:

- attacker perspective
- defender perspective
- IVI domain-expert perspective

The final reporting threshold is Stage 3 `>=2/3`. Stage 2 removes or demotes obvious context-blocked candidates before that consensus step, while Stage 3 decides whether the evidence package is strong enough to report.

The headline metric is Stage 1 vs Stage 3 because Stage 3 is the final reporting decision.

Stage 2 is not reported as a standalone automated classifier unless a separate Stage 2-only evaluation table is provided. The final `n=47` false-positive attribution table is in `docs/01_final_report.md`.

## 8. Automation Boundary

The implementation combines deterministic scripts, rule dictionaries, and human/Codex inspection. The correct final claim is:

> Stage 2 provides semi-automated contextual verification rules that materially reduce false positives on the final corpus; it is not an independent complete Android reachability engine.

This boundary matters for reporting. Stage 2 is a structured review method, not a guarantee that every possible Android call path has been exhaustively enumerated.
