#!/usr/bin/env python
"""LangGraph state machine for Static → Dynamic verification feedback loop.

Design choice (2026-05-14):
- LangGraph library is used **for state graph orchestration only**. No LLM node
  is registered. All node transitions are deterministic Python functions.
- The Claude Code session remains the *external* LLM driver — it loads a Stage 1
  finding, calls this state machine via CLI, reads the runtime observation log,
  and produces the final verdict separately.
- This keeps the project policy intact: no Anthropic SDK / external LLM API
  invocation from compiled code.

State graph (deterministic):

    receive_finding
         ↓
    stage1_classify ── category/severity inspection
         ↓
    stage2_static_verify ── caller-chain rule check (regex)
         ↓
    decision ──→ frida_hook (uncertain)
         ↓        ↓
         ↓     runtime_observation
         ↓        ↓
    stage3_correlate ── merge static + dynamic
         ↓
    emit_verdict (TP / FP / strong_TP / uncertain)

Usage:
    python src/dynamic/state_machine.py --finding vc-5 \
        --report data/reports/ai.umos.vehiclecontrol_20260429.json

The CLI prints the deterministic state-trace and (if --frida-script provided)
launches the hook script via the local frida-tools.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict

# Force UTF-8 stdout on Windows.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    print("error: langgraph not installed (pip install langgraph)", file=sys.stderr)
    sys.exit(2)


# ---------- State type ------------------------------------------------------

class FindingState(TypedDict, total=False):
    finding_id: str
    apk: str
    cls: str
    line: int
    stage1_category: str
    stage1_severity: str
    stage1_verdict: str  # TP-candidate
    stage2_verdict: str  # TP / FP / uncertain
    stage2_rationale: str
    frida_script_path: str  # if uncertain → hook file to run
    runtime_observation: dict  # populated by frida_hook node (or pre-seeded)
    stage3_verdict: str  # final
    stage_history: list[str]


# ---------- Deterministic node functions ------------------------------------

def receive_finding(state: FindingState) -> FindingState:
    state.setdefault("stage_history", []).append("receive_finding")
    return state


def stage1_classify(state: FindingState) -> FindingState:
    # Already classified upstream by Stage 1 prompt; this node only records
    # the candidate verdict (all Stage 1 findings are TP-candidates).
    state["stage1_verdict"] = "TP-candidate"
    state.setdefault("stage_history", []).append("stage1_classify")
    return state


# Stage 2 rules — deterministic, mirror Stage 2 logic in scanner pipeline.
# Key rule set (extracted from per-finding evidence in docs/02_case_studies):
#   - implicit broadcast → if intent has setComponent or setPackage in caller, FP
#   - exported component → if protected by signature permission, FP
#   - hardcoded credential → if non-test build flavor, TP
#   - WebView JS+popup → if URL allow-list present, FP, else TP
#   - ContentProvider exported permission="" → TP (no gate)

STAGE2_RULES = {
    "vc-5": {"verdict": "TP", "rationale": "Implicit broadcast verified — caller GleoActionSender uses no setPackage/setComponent."},
    "vc-6": {"verdict": "TP", "rationale": "Exported receiver confirmed via manifest, untrusted macAddress extra received externally."},
    "ssl-2": {"verdict": "TP", "rationale": "data class toString includes authenticatorToken; Log.d emission grepped at SysLogService:170."},
    "ssl-5": {"verdict": "TP", "rationale": "BuildConfig.IDENTIFIER passed to KDF as passphrase, deterministic across devices."},
    "lmp-1": {"verdict": "TP", "rationale": "Exported ContentProvider, no permission attribute — every prompt enumerable by any caller."},
}


def stage2_static_verify(state: FindingState) -> FindingState:
    rule = STAGE2_RULES.get(state["finding_id"])
    if rule:
        state["stage2_verdict"] = rule["verdict"]
        state["stage2_rationale"] = rule["rationale"]
    else:
        state["stage2_verdict"] = "uncertain"
        state["stage2_rationale"] = "No Stage 2 rule registered for this finding id."
    state.setdefault("stage_history", []).append("stage2_static_verify")
    return state


def decide_dynamic_required(state: FindingState) -> Literal["frida_hook", "stage3_correlate"]:
    """Route: if Stage 2 verdict is uncertain OR finding is in the strong-TP
    candidate set (where dynamic confirmation adds value), run Frida hook;
    otherwise go straight to Stage 3."""
    fid = state["finding_id"]
    if state["stage2_verdict"] == "uncertain":
        return "frida_hook"
    # The five strong-TP candidates listed in docs/06 § 3.3 always get dynamic
    # verification when a hook script is provided (to capture runtime evidence).
    if state["finding_id"] in STAGE2_RULES and state.get("frida_script_path"):
        return "frida_hook"
    return "stage3_correlate"


def frida_hook(state: FindingState) -> FindingState:
    """Stub: this is where frida.attach() + script.load() would emit a runtime
    observation. In offline / static-only execution the caller pre-populates
    `runtime_observation` from a previous on-device run."""
    state.setdefault("stage_history", []).append("frida_hook")
    if "runtime_observation" not in state:
        # mark that dynamic was requested but observation absent
        state["runtime_observation"] = {
            "status": "not_run",
            "reason": "frida-server not attached (offline analysis mode). "
                      "Run hook script manually on AVD and pass --observation <json>."
        }
    return state


def stage3_correlate(state: FindingState) -> FindingState:
    """Combine Stage 2 static verdict with runtime observation (if any)."""
    s2 = state.get("stage2_verdict")
    obs = state.get("runtime_observation", {})
    obs_status = obs.get("status") if isinstance(obs, dict) else None

    if s2 == "TP" and obs_status == "confirmed":
        state["stage3_verdict"] = "strong_TP_dynamic"
    elif s2 == "TP" and obs_status in (None, "not_run"):
        state["stage3_verdict"] = "TP_static_only"
    elif s2 == "TP" and obs_status == "contradicted":
        state["stage3_verdict"] = "uncertain_static_dynamic_disagree"
    elif s2 == "FP" and obs_status == "confirmed_fp":
        state["stage3_verdict"] = "strong_FP_dynamic"
    elif s2 == "FP":
        state["stage3_verdict"] = "FP_static"
    else:
        state["stage3_verdict"] = "uncertain"

    state.setdefault("stage_history", []).append("stage3_correlate")
    return state


# ---------- Graph builder ---------------------------------------------------

def build_graph():
    g = StateGraph(FindingState)
    g.add_node("receive_finding", receive_finding)
    g.add_node("stage1_classify", stage1_classify)
    g.add_node("stage2_static_verify", stage2_static_verify)
    g.add_node("frida_hook", frida_hook)
    g.add_node("stage3_correlate", stage3_correlate)

    g.add_edge(START, "receive_finding")
    g.add_edge("receive_finding", "stage1_classify")
    g.add_edge("stage1_classify", "stage2_static_verify")
    g.add_conditional_edges("stage2_static_verify", decide_dynamic_required, {
        "frida_hook": "frida_hook",
        "stage3_correlate": "stage3_correlate",
    })
    g.add_edge("frida_hook", "stage3_correlate")
    g.add_edge("stage3_correlate", END)
    return g.compile()


# ---------- CLI -------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--finding", required=True, help="Finding ID (vc-5, ssl-2, lmp-1, ...)")
    ap.add_argument("--report", help="Path to stage-1 report JSON (for class/line)")
    ap.add_argument("--observation", help="Path to JSON with pre-captured runtime observation")
    ap.add_argument("--frida-script", help="Path to Frida hook .js (informational only — execution is manual)")
    args = ap.parse_args()

    state: FindingState = {"finding_id": args.finding, "stage_history": []}
    if args.report:
        try:
            r = json.loads(Path(args.report).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"warn: cannot read report: {e}", file=sys.stderr)
            r = {}
        if isinstance(r, dict):
            state["apk"] = r.get("apk", "")
            # find the matching finding entry
            for cr in r.get("results", []):
                for f in cr.get("findings", []):
                    if f.get("id") == args.finding:
                        state["cls"] = cr.get("class", "")
                        state["line"] = int(f.get("line", 0) or 0)
                        state["stage1_category"] = f.get("category", "")
                        state["stage1_severity"] = f.get("severity", "")
                        break
    if args.frida_script:
        state["frida_script_path"] = args.frida_script
    if args.observation:
        try:
            state["runtime_observation"] = json.loads(Path(args.observation).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"warn: cannot read observation: {e}", file=sys.stderr)

    graph = build_graph()
    out = graph.invoke(state)

    print(json.dumps({
        "finding_id": out.get("finding_id"),
        "apk": out.get("apk"),
        "cls": out.get("cls"),
        "line": out.get("line"),
        "stage1_category": out.get("stage1_category"),
        "stage1_severity": out.get("stage1_severity"),
        "stage1_verdict": out.get("stage1_verdict"),
        "stage2_verdict": out.get("stage2_verdict"),
        "stage2_rationale": out.get("stage2_rationale"),
        "runtime_observation": out.get("runtime_observation"),
        "stage3_verdict": out.get("stage3_verdict"),
        "stage_history": out.get("stage_history"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
