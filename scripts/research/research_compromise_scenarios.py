#!/usr/bin/env python
"""Build a compromise-scenario and PoC-feasibility report.

This script does not execute PoCs. It turns the already-validated finding set
into a defensive scenario matrix:

1. what kind of compromise the finding can trigger,
2. whether the current evidence proves an end-to-end compromise, and
3. what a safe local/owner-authorized PoC would need to verify next.

Outputs:
  data/reports/runtime_local/compromise_scenarios.json
  data/reports/runtime_local/compromise_scenarios.md
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "data" / "reports"
GT_PATH = ROOT / "data" / "ground_truth" / "combined_labels.json"
STAGE3_PATH = REPORTS_DIR / "local" / "stage3_ensemble.json"
NATIVE_FINDINGS_PATH = REPORTS_DIR / "native_local" / "native_deep_dive_findings.json"
OUT_JSON = REPORTS_DIR / "runtime_local" / "compromise_scenarios.json"
OUT_MD = REPORTS_DIR / "runtime_local" / "compromise_scenarios.md"

KST = timezone(timedelta(hours=9))

PLEOS_APK_PREFIXES = ("ai.umos.", "ai.pleos.")


SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "SC-01",
        "name": "External LLM API credential compromise",
        "trigger_findings": ["amb-1", "amb-2"],
        "compromise_level": "service credential compromise, not IVI takeover",
        "claim_status": "static exposure proven; live abuse not tested",
        "poc_feasibility": "high for safe static proof; owner-only for live-service proof",
        "attacker_position": "anyone who obtains the APK or decompiled artifact",
        "scenario": (
            "APK reverse engineering reveals an OpenAI-style API key in the "
            "AmbientAI production LLM call path and in a release-shipped test "
            "handler. If the key is valid and not scope-restricted, it can be "
            "abused outside the vehicle for billing, quota, or privacy-impacting "
            "API calls."
        ),
        "safe_poc": [
            "Keep the full secret redacted; prove only prefix, storage location, and call-site reachability.",
            "Ask the service owner to rotate the key and check provider-side logs for historical use.",
            "Use a sandbox key or mocked endpoint if request construction must be validated.",
        ],
        "blocking_unknowns": [
            "whether the shipped key is still valid",
            "whether server/provider-side restrictions prevent external use",
            "whether actual user PII reaches the same call path in runtime",
        ],
        "do_not_do": [
            "do not call the live external API with the recovered key",
            "do not publish the full key literal",
        ],
    },
    {
        "id": "SC-02",
        "name": "HMG OAuth client identity leak across AppMarket and Account",
        "trigger_findings": ["am-3", "acc-4"],
        "compromise_level": "account/service credential domain exposure",
        "claim_status": "cross-APK hardcoded-secret pattern proven; backend exploitability untested",
        "poc_feasibility": "high for static/cross-APK proof; owner-only for token-exchange proof",
        "attacker_position": "APK reverse engineer or same-device observer of exported SSO flow",
        "scenario": (
            "AppMarket contains an OAuth client_id/client_secret pair, while the "
            "Account APK passes a related user-client-secret through an exported "
            "Activity boundary. Together they form a systematic credential "
            "handling pattern rather than a single stray string."
        ),
        "safe_poc": [
            "Show both APKs reference the same credential domain with redacted values.",
            "On a local AVD, trigger the exported SSO Activity with benign extras and observe whether extras appear in dumpsys/log surfaces.",
            "Validate token exchange only in an owner-provided sandbox or by server-side log review.",
        ],
        "blocking_unknowns": [
            "backend acceptance of the extracted client identity",
            "token binding, redirect URI, or device binding controls",
            "whether production logging exposes the Intent extras",
        ],
        "do_not_do": [
            "do not attempt production OAuth token exchange",
            "do not disclose client_secret literals",
        ],
    },
    {
        "id": "SC-03",
        "name": "On-device LLM prompt/corpus disclosure and model DoS",
        "trigger_findings": ["lmp-1", "lmp-2"],
        "compromise_level": "same-device information disclosure / service disruption",
        "claim_status": "exported component primitive proven statically; runtime query/broadcast PoC pending",
        "poc_feasibility": "high on local AVD",
        "attacker_position": "malicious same-device app or adb-controlled local test harness",
        "scenario": (
            "An exported prompt ContentProvider can expose IVI LLM prompts or "
            "guardrail corpus to another app, and an exported receiver can delete "
            "or disrupt model-file state. This does not prove code execution, but "
            "it gives an attacker the material needed to prepare prompt-injection "
            "or jailbreak attempts against the IVI assistant."
        ),
        "safe_poc": [
            "Use a test app or adb content-provider query on an emulator with synthetic/non-sensitive prompts.",
            "Record only row counts, schema names, and redacted prompt excerpts.",
            "Use the existing lmp-1 Frida hook to capture caller UID and returned row count.",
        ],
        "blocking_unknowns": [
            "whether production prompt rows are populated in the current emulator image",
            "whether OEM build variants add signature permissions",
        ],
        "do_not_do": [
            "do not dump full proprietary prompt corpora into public artifacts",
        ],
    },
    {
        "id": "SC-04",
        "name": "VehicleControl same-device broadcast spoofing / state tamper",
        "trigger_findings": ["vc-5", "vc-6", "vc-7"],
        "compromise_level": "local vehicle-state tamper primitive; full vehicle control not proven",
        "claim_status": "exported/implicit intent primitives proven; actuation chain unproven",
        "poc_feasibility": "medium-high on local AVD, unsafe to claim vehicle takeover",
        "attacker_position": "malicious same-device app capable of sending intents/broadcasts",
        "scenario": (
            "VehicleControl accepts or emits vehicle-related intents across app "
            "boundaries. The strongest primitive is an exported receiver accepting "
            "a MAC-like payload that can be persisted into vehicle/Bluetooth "
            "state. This can plausibly poison pairing or control-adjacent data, "
            "but current evidence does not show a chain to physical actuation."
        ),
        "safe_poc": [
            "Send a benign, clearly fake MAC-like value on an emulator and observe only DB/preference/log state changes.",
            "Use existing vc-5/vc-6 Frida hooks to record caller UID, action, extras, and whether state mutates.",
            "Do not connect to a real vehicle or attempt actuation commands.",
        ],
        "blocking_unknowns": [
            "whether downstream vehicle services trust the persisted MAC value",
            "whether receiver actions are reachable in the production image",
            "whether signature or SELinux constraints apply outside static manifest evidence",
        ],
        "do_not_do": [
            "do not run against a real vehicle",
            "do not attempt safety-critical actuation",
        ],
    },
    {
        "id": "SC-05",
        "name": "Syslog/token/driver-PII compromise through log and network surfaces",
        "trigger_findings": ["ssl-2", "ssl-3", "ssl-4", "ssl-6"],
        "compromise_level": "privacy/telemetry compromise, not code execution",
        "claim_status": "token/log/plaintext primitives mostly proven; network endpoint reachability not fully tested",
        "poc_feasibility": "medium on local AVD or controlled network",
        "attacker_position": "local debugger/privileged log reader or network-adjacent MITM in a controlled lab",
        "scenario": (
            "Sync/syslog code can emit auth data through Kotlin data-class "
            "toString/logging paths and sends vehicle/system logs over a plaintext "
            "gRPC channel. A network-adjacent attacker in the same test network "
            "could observe telemetry if the endpoint is reachable."
        ),
        "safe_poc": [
            "Use the existing ssl-2 Frida hook to confirm token-to-log emission with synthetic credentials.",
            "Use packet capture on a local emulator network to verify plaintext framing without sending real user logs.",
            "For ssl-4, first prove an actual HmgUserInfo emission point before treating it as exploitable.",
        ],
        "blocking_unknowns": [
            "runtime endpoint reachability in the emulator",
            "whether production logs include live tokens/PII at the observed call site",
            "whether network routing or VPN/TLS wrapping outside the app changes exposure",
        ],
        "do_not_do": [
            "do not capture real driver logs or tokens",
        ],
    },
    {
        "id": "SC-06",
        "name": "All-device sync-config key reuse",
        "trigger_findings": ["ssl-1", "ssl-5"],
        "compromise_level": "offline configuration confidentiality compromise if ciphertext is obtained",
        "claim_status": "KDF root cause proven; decryption impact needs encrypted sample",
        "poc_feasibility": "medium",
        "attacker_position": "APK reverse engineer plus access to encrypted sync-config blobs",
        "scenario": (
            "A build-time constant is used as the KDF passphrase for ECC/private "
            "key derivation, making derived material effectively identical across "
            "devices. This is a strong cryptographic design flaw, but compromise "
            "of actual data requires a ciphertext/config artifact to decrypt or sign against."
        ),
        "safe_poc": [
            "Reproduce the KDF offline with a redacted BuildConfig constant and compare derived-key fingerprints.",
            "Use synthetic encrypted blobs to demonstrate impact without exposing production configs.",
            "If production config samples are available, validate only in a private report.",
        ],
        "blocking_unknowns": [
            "availability of encrypted config blobs",
            "whether server-side rotation or per-device wrapping mitigates the static key",
        ],
        "do_not_do": [
            "do not publish derived production keys or decrypted configs",
        ],
    },
    {
        "id": "SC-07",
        "name": "AppMarket suggestions/intent injection and install-lifecycle disclosure",
        "trigger_findings": ["am-1", "am-2"],
        "compromise_level": "same-device privileged-context intent primitive / information disclosure",
        "claim_status": "provider/broadcast surfaces proven; UI click path and privilege use need runtime validation",
        "poc_feasibility": "medium on local AVD",
        "attacker_position": "malicious same-device app",
        "scenario": (
            "An exported suggestions provider with an empty permission can be "
            "overwritten by another app and later surfaced through system search "
            "or AppMarket UI. A separate implicit broadcast leaks installation "
            "lifecycle details and exception information."
        ),
        "safe_poc": [
            "Insert a harmless suggestion URI in a local emulator and verify whether the UI resolves it.",
            "Observe broadcast delivery to a test receiver without installing or launching arbitrary apps.",
            "Keep payloads to benign internal test URIs.",
        ],
        "blocking_unknowns": [
            "whether the suggestion click is fired under a privileged identity",
            "whether UI interaction is required and reproducible in the emulator",
        ],
        "do_not_do": [
            "do not use payloads that install packages, launch privileged settings, or cross users",
        ],
    },
    {
        "id": "SC-08",
        "name": "Account SSO WebView and cleartext authentication exposure",
        "trigger_findings": ["acc-1", "acc-3", "acc-5"],
        "compromise_level": "account/session phishing or MITM primitive",
        "claim_status": "risky WebView/cleartext configuration proven; credential theft chain unproven",
        "poc_feasibility": "medium with test account or mocked login endpoint",
        "attacker_position": "network-adjacent MITM or same-device deep-link trigger",
        "scenario": (
            "The account APK allows cleartext traffic and has exported WebView "
            "entry points with JavaScript, popups, DOM storage, and a distinctive "
            "SDK user-agent fingerprint. These conditions can support credential "
            "phishing or MITM only if the attacker controls the URL or network path."
        ),
        "safe_poc": [
            "Use a mock login endpoint and test account; never collect real credentials.",
            "Verify whether exported Activity inputs can control the initial URL.",
            "Use local proxy/certificate instrumentation only in the emulator.",
        ],
        "blocking_unknowns": [
            "URL whitelist and redirect behavior at runtime",
            "whether production endpoints force HTTPS/HSTS outside the app setting",
            "whether login cookies are scoped and cleared correctly after the flow",
        ],
        "do_not_do": [
            "do not intercept real user credentials",
        ],
    },
    {
        "id": "SC-09",
        "name": "Maps location-history PII read",
        "trigger_findings": ["map-1"],
        "compromise_level": "same-device PII disclosure",
        "claim_status": "exported provider/no-permission primitive proven; data population needs runtime check",
        "poc_feasibility": "medium-high on local AVD",
        "attacker_position": "malicious same-device app or adb-controlled local test harness",
        "scenario": (
            "An exported maps ContentProvider has no caller signature gate and can "
            "return global-search backing data such as home/work or frequented "
            "location history if populated."
        ),
        "safe_poc": [
            "Populate emulator maps data with synthetic locations.",
            "Query only row count, column names, and redacted sample values.",
            "Confirm insert/update/delete remain blocked so the impact stays read-only.",
        ],
        "blocking_unknowns": [
            "whether production data exists in the current emulator snapshot",
            "whether a vendor build variant adds provider permissions",
        ],
        "do_not_do": [
            "do not export real location history",
        ],
    },
    {
        "id": "SC-10",
        "name": "AmbientAI deep-link state injection",
        "trigger_findings": ["amb-3"],
        "compromise_level": "same-device UI/log injection primitive",
        "claim_status": "BROWSABLE deep-link primitive proven; sensitive downstream sink unproven",
        "poc_feasibility": "medium on local AVD",
        "attacker_position": "browser/web page or malicious same-device app that can open the deep link",
        "scenario": (
            "A browser-triggerable assistant:// deep link accepts unvalidated "
            "parameters and pushes them into Settings UI state. This is a useful "
            "trigger for phishing/UI confusion or log injection, but current "
            "evidence does not show credential or code-execution impact."
        ),
        "safe_poc": [
            "Open a benign deep link with non-sensitive marker strings in the emulator.",
            "Observe UI state/logcat for marker propagation.",
            "Stop if the flow attempts external LLM calls with production credentials.",
        ],
        "blocking_unknowns": [
            "whether injected parameters reach a network, logging, or prompt-building sink",
            "whether additional validation exists after the observed state update",
        ],
        "do_not_do": [
            "do not use payloads that target real external LLM calls",
        ],
    },
    {
        "id": "SC-11",
        "name": "Native command-execution candidate in libairspeech_stt.so",
        "trigger_findings": ["native-N1"],
        "compromise_level": "candidate native command execution / destructive file deletion",
        "claim_status": "candidate only; path controllability not proven",
        "poc_feasibility": "medium after Ghidra xref and Frida system() capture",
        "attacker_position": "unknown; depends on whether Java/JNI/model/config input controls the path",
        "scenario": (
            "The native STT library imports system() and a utility function appears "
            "to construct an rm -rf command from a path argument before mkdir. If "
            "that path can be influenced by Java, downloaded model/config content, "
            "or external storage, this could become command injection or destructive "
            "file deletion. If the path is an internal constant, it is only a hardening note."
        ),
        "safe_poc": [
            "Use Ghidra/radare2 xrefs to recover callers and argument origin.",
            "Attach `src/dynamic/hooks/native-system-command-capture.js` to libc.system so commands are logged and blocked in a local emulator.",
            "Classify only after proving whether attacker-controlled input reaches the path argument.",
        ],
        "blocking_unknowns": [
            "caller of utility::make_dir(char const*)",
            "origin and controllability of the path argument",
            "whether the function is reachable in production flows",
        ],
        "do_not_do": [
            "do not execute rm -rf payloads",
            "do not test on a real vehicle or production user device",
        ],
    },
    {
        "id": "SC-12",
        "name": "Hardening-only or indirect findings without a standalone compromise trigger",
        "trigger_findings": ["acc-2"],
        "compromise_level": "hardening / maintainability / platform policy risk",
        "claim_status": "valid finding, but not a standalone compromise chain",
        "poc_feasibility": "low value as a compromise PoC",
        "attacker_position": "not directly attacker-triggered from current evidence",
        "scenario": (
            "Reflection-based hidden API access can break under platform policy "
            "changes and may bypass intended SDK boundaries, but current evidence "
            "does not show a direct attacker-controlled input or data exfiltration path."
        ),
        "safe_poc": [
            "Treat as compatibility/hardening evidence rather than exploitation evidence.",
            "Validate by running on newer platform images and checking for SecurityException or degraded behavior.",
        ],
        "blocking_unknowns": [
            "whether hidden API calls are reachable from untrusted input",
        ],
        "do_not_do": [],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_context() -> dict[str, Any]:
    gt = load_json(GT_PATH)
    stage3 = load_json(STAGE3_PATH)
    native = load_json(NATIVE_FINDINGS_PATH) if NATIVE_FINDINGS_PATH.exists() else {}

    labels = {row["id"]: row for row in gt["labels"]}
    stage3_results = {row["id"]: row for row in stage3["results"]}
    native_candidates = {
        row["id"].replace("native-candidate-1", "native-N1"): row
        for row in native.get("candidates", [])
    }

    return {
        "gt": gt,
        "stage3": stage3,
        "labels": labels,
        "stage3_results": stage3_results,
        "native": native,
        "native_candidates": native_candidates,
    }


def enrich_trigger(fid: str, ctx: dict[str, Any]) -> dict[str, Any]:
    labels = ctx["labels"]
    stage3_results = ctx["stage3_results"]
    native_candidates = ctx["native_candidates"]

    if fid in native_candidates:
        row = native_candidates[fid]
        return {
            "id": fid,
            "apk": row.get("apk"),
            "category": "native",
            "gt_is_real": None,
            "stage3_consensus": None,
            "stage3_class": row.get("status"),
            "severity": "candidate",
            "title": "libairspeech_stt.so system()/rm -rf command construction candidate",
            "notes": row.get("current_verdict"),
        }

    label = labels.get(fid)
    stage = stage3_results.get(fid)
    if not label:
        return {
            "id": fid,
            "apk": None,
            "category": None,
            "gt_is_real": None,
            "stage3_consensus": None,
            "stage3_class": "missing",
            "severity": None,
            "title": None,
            "notes": "finding id not present in current GT labels",
        }

    return {
        "id": fid,
        "apk": label.get("apk"),
        "category": label.get("stage1_category"),
        "gt_is_real": label.get("is_real"),
        "stage3_consensus": stage.get("consensus_count") if stage else None,
        "stage3_class": stage.get("consensus_class") if stage else None,
        "severity": (stage or {}).get("severity") or label.get("true_severity"),
        "title": (stage or {}).get("title") or label.get("notes", ""),
        "notes": label.get("notes", ""),
    }


def summarize_coverage(ctx: dict[str, Any], scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    labels = ctx["labels"]
    stage3_results = ctx["stage3_results"]
    covered = set()
    for scenario in scenarios:
        covered.update(fid for fid in scenario["trigger_findings"] if fid.startswith(("vc-", "ssl-", "lmp-", "acc-", "am-", "amb-", "map-")))

    pleos_real = []
    pleos_reportable = []
    for fid, label in labels.items():
        apk = label.get("apk", "")
        if not apk.startswith(PLEOS_APK_PREFIXES):
            continue
        if label.get("is_real"):
            pleos_real.append(fid)
            stage = stage3_results.get(fid, {})
            if (stage.get("consensus_count") or 0) >= 2:
                pleos_reportable.append(fid)

    return {
        "pleos_real_findings": sorted(pleos_real),
        "pleos_stage3_reportable_findings": sorted(pleos_reportable),
        "covered_pleos_real_findings": sorted(set(pleos_real) & covered),
        "covered_pleos_stage3_reportable_findings": sorted(set(pleos_reportable) & covered),
        "not_covered_pleos_real_findings": sorted(set(pleos_real) - covered),
        "external_or_benchmark_excluded": sorted(
            fid
            for fid, label in labels.items()
            if not label.get("apk", "").startswith(PLEOS_APK_PREFIXES)
            and label.get("is_real")
        ),
    }


def scenario_to_md(scenario: dict[str, Any]) -> str:
    def bullet(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- N/A"

    trigger_rows = []
    for trig in scenario["triggers_enriched"]:
        trigger_rows.append(
            "| `{id}` | `{apk}` | {category} | {stage3} | {severity} | {title} |".format(
                id=trig.get("id"),
                apk=trig.get("apk") or "N/A",
                category=trig.get("category") or "N/A",
                stage3=trig.get("stage3_class") or "N/A",
                severity=trig.get("severity") or "N/A",
                title=(trig.get("title") or "").replace("\n", " "),
            )
        )

    return f"""### {scenario['id']} — {scenario['name']}

| Field | Assessment |
|---|---|
| Compromise level | {scenario['compromise_level']} |
| Claim status | {scenario['claim_status']} |
| PoC feasibility | {scenario['poc_feasibility']} |
| Attacker position | {scenario['attacker_position']} |

| Trigger | APK | Category | Stage 3 | Severity | Evidence title |
|---|---|---|---|---|---|
{chr(10).join(trigger_rows)}

**Scenario.** {scenario['scenario']}

**Safe PoC plan.**
{bullet(scenario['safe_poc'])}

**Blocking unknowns.**
{bullet(scenario['blocking_unknowns'])}

**Guardrails.**
{bullet(scenario.get('do_not_do', []))}
"""


def render_md(payload: dict[str, Any]) -> str:
    scenario_rows = []
    for scenario in payload["scenarios"]:
        scenario_rows.append(
            "| `{id}` | {name} | `{triggers}` | {level} | {poc} | {claim} |".format(
                id=scenario["id"],
                name=scenario["name"],
                triggers=", ".join(scenario["trigger_findings"]),
                level=scenario["compromise_level"],
                poc=scenario["poc_feasibility"],
                claim=scenario["claim_status"],
            )
        )

    coverage = payload["coverage"]
    detail = "\n\n".join(scenario_to_md(s) for s in payload["scenarios"])
    generated_at = payload["generated_at"]

    return f"""# Compromise Scenario and PoC Feasibility Matrix

- Generated at: {generated_at}
- Scope: PleOS-customized reportable findings plus the native deep-dive candidate
- Inputs:
  - `data/ground_truth/combined_labels.json`
  - `data/reports/local/stage3_ensemble.json`
  - `data/reports/native_local/native_deep_dive_findings.json`

## Bottom Line

현재 정적 분석 결과만으로는 **remote attacker가 곧바로 IVI/차량을 end-to-end compromise한다**는 결론은 입증되지 않는다. 대신 현재 근거는 다음 세 가지를 강하게 지지한다.

1. **Credential/service compromise primitive**: APK reverse만으로 외부 LLM API key, OAuth client identity, KDF root secret 같은 값의 노출을 증명할 수 있다. 실제 서비스 abuse 여부는 owner-side key validity, rotation, log review가 필요하다.
2. **Same-device app-to-app compromise primitive**: exported provider/receiver/activity가 LLM prompt, maps PII, AppMarket suggestion, VehicleControl state 같은 데이터를 읽거나 오염시킬 수 있는지 로컬 AVD PoC로 검증 가능하다.
3. **Native command-execution candidate**: `libairspeech_stt.so`의 `system(\"rm -rf %s\")` 계열 command construction은 후보 1건이지만, path controllability가 증명되지 않아 아직 취약점으로 보고할 수 없다.

즉 결론은 **\"full vehicle takeover는 아직 아니다. 하지만 각 finding은 credential theft, same-device data disclosure/state tamper, telemetry MITM, native command execution candidate 같은 부분 compromise trigger로 정리할 수 있고, 대부분은 안전한 로컬 PoC가 가능하다\"** 이다.

## Compromise Level Definition

| Level | Meaning | Current project status |
|---|---|---|
| Static exposure | APK reverse/decompile만으로 secret, config, exported surface를 증명 | 여러 finding에서 이미 달성 |
| Same-device compromise | 악성 로컬 앱/adb test harness가 exported component를 trigger해 data read/state tamper 수행 | AVD PoC 가능, 일부 hook ready |
| Service/backend compromise | 노출된 credential이 실제 외부 서비스/API에 통함 | owner-side sandbox/log review 필요 |
| Network telemetry compromise | 로컬 네트워크/MITM에서 plaintext log/token/PII 관찰 | controlled network PoC 가능 |
| Native code execution | native input controllability가 `system()` 등 위험 sink에 도달 | 현재 candidate only |
| Full vehicle/IVI takeover | remote-to-vehicle actuation 또는 persistent device takeover까지 연결 | 현재 근거로는 미입증 |

## Summary Table

| ID | Scenario | Trigger findings | Compromise level | PoC feasibility | Claim status |
|---|---|---|---|---|---|
{chr(10).join(scenario_rows)}

## Coverage Check

| Item | Count | IDs |
|---|---:|---|
| PleOS real findings | {len(coverage['pleos_real_findings'])} | `{', '.join(coverage['pleos_real_findings'])}` |
| PleOS Stage 3 reportable findings | {len(coverage['pleos_stage3_reportable_findings'])} | `{', '.join(coverage['pleos_stage3_reportable_findings'])}` |
| Covered by scenario matrix | {len(coverage['covered_pleos_real_findings'])} | `{', '.join(coverage['covered_pleos_real_findings'])}` |
| Not covered by scenario matrix | {len(coverage['not_covered_pleos_real_findings'])} | `{', '.join(coverage['not_covered_pleos_real_findings']) or 'none'}` |
| External/benchmark real findings excluded from PleOS compromise claims | {len(coverage['external_or_benchmark_excluded'])} | `{', '.join(coverage['external_or_benchmark_excluded'])}` |

External benchmark findings such as MASTG/InsecureBankv2 are kept out of PleOS compromise claims because they validate the scanner, not PleOS product risk.

## Scenario Details

{detail}

## PoC Queue

1. **High-value local PoC first**: `lmp-1`, `map-1`, `vc-6`, `am-1`, `acc-4`. These are same-device component-boundary checks and can be run on AVD with synthetic data.
2. **Dynamic evidence next**: run existing Frida hooks for `vc-5`, `vc-6`, `ssl-2`, `ssl-5`, `lmp-1` to turn static findings into runtime observations.
3. **Owner-only checks**: `amb-1/2` and `am-3` service abuse should be validated by key rotation, sandbox credentials, or provider/server logs, not by live API calls from the recovered secret.
4. **Native candidate validation**: recover `libairspeech_stt.so` caller xrefs and attach `src/dynamic/hooks/native-system-command-capture.js` before any runtime test.
5. **Do not claim** full remote vehicle compromise until a concrete chain crosses all boundaries: attacker entry point → trigger → persisted state/data/control sink → security impact → no platform/server mitigation.
"""


def main() -> int:
    ctx = build_context()
    generated_at = datetime.now(KST).isoformat(timespec="seconds")

    scenarios: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        enriched = dict(scenario)
        enriched["triggers_enriched"] = [
            enrich_trigger(fid, ctx) for fid in scenario["trigger_findings"]
        ]
        scenarios.append(enriched)

    payload = {
        "generated_at": generated_at,
        "inputs": {
            "ground_truth": str(GT_PATH.relative_to(ROOT)),
            "stage3": str(STAGE3_PATH.relative_to(ROOT)),
            "native_findings": str(NATIVE_FINDINGS_PATH.relative_to(ROOT)),
        },
        "verdict": {
            "full_end_to_end_vehicle_or_ivi_compromise_proven": False,
            "reason": (
                "Current evidence proves multiple compromise primitives, but does "
                "not connect them into a remote-to-vehicle actuation or persistent "
                "device-takeover chain."
            ),
            "strongest_supported_claims": [
                "shipped credential/static secret exposure",
                "same-device exported component data disclosure/state tamper",
                "plaintext telemetry/token/PII exposure candidate paths",
                "native command-execution candidate requiring controllability proof",
            ],
        },
        "coverage": summarize_coverage(ctx, scenarios),
        "scenarios": scenarios,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(payload), encoding="utf-8")

    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
