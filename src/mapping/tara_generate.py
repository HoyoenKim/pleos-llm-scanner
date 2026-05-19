"""TARA (Threat Analysis and Risk Assessment) artifact generator.

ISO/SAE 21434 흐름을 단순화한 자동 생성기:
  Item Definition (asset) -> Threat Scenarios -> Impact -> Attack Feasibility -> Risk

입력:
  - configs/aaos_mapping.yaml (asset/threat 카테고리 + finding 매핑)
  - data/ground_truth/combined_labels.json (ground truth, TP only)

출력:
  - data/reports/aggregate/tara_artifact.{md,json}  (overwritten each run; 본문에 generated date 메타 포함)

본 산출물은 PleOS 계약과제의 TARA 단계와 본 정적 분석 파이프라인을 연결하는
정량 근거 자료로 활용. Attack Feasibility 등급은 정적 분석 단계의 추정치이며
실차/실측 후 갱신 필요.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    raise


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "configs" / "aaos_mapping.yaml"
GT = ROOT / "data" / "ground_truth" / "combined_labels.json"
OUT_DIR = ROOT / "data" / "reports" / "aggregate"


# Severity → ISO/SAE 21434 Impact rating
SEV_TO_IMPACT = {
    "high": "Major",
    "medium": "Moderate",
    "low": "Negligible",
    "none": "Negligible",
}

# Asset criticality (vehicle safety > credential > pii > telemetry > model)
ASSET_CRITICALITY = {
    "vehicle_control": "Severe",  # safety-critical
    "user_credentials": "Major",
    "pii": "Major",
    "vehicle_identifier": "Moderate",
    "diagnostic_data": "Moderate",
    "llm_corpus": "Moderate",
}

# Attack feasibility — 정적 분석 단계 추정 기준:
#   exported component / no permission gate -> High
#   caller-controlled (in same process / via known route) -> Medium
#   privileged context only -> Low
ATTACK_FEASIBILITY_RULES = {
    # by category × component-export pattern (rough heuristics)
    "intent_high_exported": "High",      # exported provider/receiver, no gate
    "network_plaintext": "High",          # MITM on shared network
    "hardcoded_in_apk": "High",           # APK reverse trivial
    "crypto_weak_kdf": "Medium",          # need device-side data
    "permission_caller_controlled": "Medium",
    "low_default": "Low",
}


def _load() -> tuple[dict[str, Any], dict[str, Any]]:
    with CFG.open("r", encoding="utf-8") as f:
        mapping = yaml.safe_load(f)
    with GT.open("r", encoding="utf-8") as f:
        gt = json.load(f)
    return mapping, gt


def _classify_attack_feasibility(label: dict[str, Any], note: str) -> str:
    cat = label["stage1_category"]
    sev = label["stage1_severity"]
    note_l = (note or "").lower()
    if cat == "intent" and ("exported" in note_l or "external app" in note_l or "외부" in note_l):
        return ATTACK_FEASIBILITY_RULES["intent_high_exported"]
    if cat == "network" and ("plaintext" in note_l or "usePlaintext" in note_l or "평문" in note_l or "MITM" in note_l):
        return ATTACK_FEASIBILITY_RULES["network_plaintext"]
    if cat == "hardcoded":
        return ATTACK_FEASIBILITY_RULES["hardcoded_in_apk"]
    if cat == "crypto":
        return ATTACK_FEASIBILITY_RULES["crypto_weak_kdf"]
    if cat == "permission":
        return ATTACK_FEASIBILITY_RULES["permission_caller_controlled"]
    if sev == "low":
        return ATTACK_FEASIBILITY_RULES["low_default"]
    return ATTACK_FEASIBILITY_RULES["low_default"]


def _risk_level(impact: str, feasibility: str) -> str:
    """ISO/SAE 21434-style 5-tier risk matrix (simplified to 4 tiers)."""
    matrix = {
        ("Severe", "High"): "Critical",
        ("Severe", "Medium"): "High",
        ("Severe", "Low"): "Medium",
        ("Major", "High"): "High",
        ("Major", "Medium"): "Medium",
        ("Major", "Low"): "Low",
        ("Moderate", "High"): "Medium",
        ("Moderate", "Medium"): "Low",
        ("Moderate", "Low"): "Low",
        ("Negligible", "High"): "Low",
        ("Negligible", "Medium"): "Low",
        ("Negligible", "Low"): "Negligible",
    }
    return matrix.get((impact, feasibility), "Low")


def _treatment(risk: str) -> str:
    return {
        "Critical": "Avoid (must fix before release)",
        "High": "Mitigate (fix in current sprint)",
        "Medium": "Mitigate (next minor release) or Transfer",
        "Low": "Accept with monitoring",
        "Negligible": "Accept",
    }.get(risk, "Accept")


def build_threat_scenarios(mapping: dict[str, Any], gt: dict[str, Any]) -> list[dict[str, Any]]:
    finding_tara = mapping.get("finding_tara_assignments", {})
    asset_meta = mapping.get("tara", {}).get("asset_categories", {})
    threat_table = {t["id"]: t["label"] for t in mapping.get("tara", {}).get("threat_categories", [])}

    scenarios: list[dict[str, Any]] = []
    for label in gt["labels"]:
        if not label.get("is_real"):
            continue  # TARA — TP only
        fid = label["id"]
        tara = finding_tara.get(fid, {})
        asset_key = tara.get("asset")
        asset_label = asset_meta.get(asset_key, {}).get("label", asset_key or "n/a")
        asset_impact = ASSET_CRITICALITY.get(asset_key, "Moderate")
        # Per-finding impact = max(severity-based, asset-based)
        sev_impact = SEV_TO_IMPACT.get(label["true_severity"] or label["stage1_severity"], "Negligible")
        impact_rank = ["Negligible", "Moderate", "Major", "Severe"]
        impact = impact_rank[max(impact_rank.index(asset_impact), impact_rank.index(sev_impact))]
        feasibility = _classify_attack_feasibility(label, tara.get("note", ""))
        risk = _risk_level(impact, feasibility)
        threat_ids = tara.get("threats", [])
        threats = [f"{tid} ({threat_table.get(tid, '?')})" for tid in threat_ids]

        scenarios.append({
            "scenario_id": f"TS-{fid.upper()}",
            "finding_id": fid,
            "apk": label["apk"],
            "asset": asset_label,
            "asset_key": asset_key,
            "asset_criticality": asset_impact,
            "stage1_category": label["stage1_category"],
            "stage1_severity": label["stage1_severity"],
            "true_severity": label.get("true_severity"),
            "threats": threats,
            "impact": impact,
            "attack_feasibility": feasibility,
            "risk_level": risk,
            "treatment": _treatment(risk),
            "source": label.get("source", "self"),
            "note": tara.get("note", ""),
        })
    return scenarios


def to_md(scenarios: list[dict[str, Any]], asset_meta: dict[str, Any]) -> str:
    today = date.today().isoformat()
    lines = []
    lines.append("# TARA Artifact — PleOS IVI APK Static Analysis\n")
    lines.append(f"_Generated: {today} (auto from `configs/aaos_mapping.yaml` + GT, TP-only)_\n")
    lines.append("> ISO/SAE 21434 흐름을 정적 분석 결과에 매핑한 산출물. Attack Feasibility 등급은 정적\n"
                 "> 분석 단계의 추정치이며, 실차 시나리오 측정 후 갱신 필요.\n")

    # 1. Item Definition (자산 정의)
    lines.append("## 1. Item Definition (Asset Catalog)\n")
    lines.append("| Asset | Examples | Criticality | Impact if compromised |")
    lines.append("|---|---|---|---|")
    for key, meta in asset_meta.items():
        crit = ASSET_CRITICALITY.get(key, "Moderate")
        ex = ", ".join(meta.get("examples", [])[:3])
        lines.append(f"| {meta.get('label', key)} | {ex} | {crit} | {meta.get('impact_if_compromised', '')} |")

    # 2. Threat Scenarios (위협 시나리오)
    lines.append("\n## 2. Threat Scenarios (n = " + str(len(scenarios)) + ", TP only)\n")
    lines.append("| ID | APK | Asset | Threats (STRIDE) | Impact | Feasibility | Risk | Treatment |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for s in scenarios:
        threats = ", ".join([t.split(" ")[0] for t in s["threats"]]) or "—"
        lines.append(
            f"| {s['scenario_id']} | {s['apk'].split('.')[-1]} | {s['asset']} | "
            f"{threats} | {s['impact']} | {s['attack_feasibility']} | "
            f"**{s['risk_level']}** | {s['treatment']} |"
        )

    # 3. Risk Matrix
    lines.append("\n## 3. Risk Matrix (count of scenarios per cell)\n")
    impact_order = ["Severe", "Major", "Moderate", "Negligible"]
    feas_order = ["High", "Medium", "Low"]
    matrix: dict[tuple[str, str], int] = {}
    for s in scenarios:
        matrix[(s["impact"], s["attack_feasibility"])] = (
            matrix.get((s["impact"], s["attack_feasibility"]), 0) + 1
        )
    header = "| Impact \\ Feasibility | " + " | ".join(feas_order) + " |"
    sep = "|---|" + "|".join(["---"] * len(feas_order)) + "|"
    lines.append(header)
    lines.append(sep)
    for imp in impact_order:
        row = [str(matrix.get((imp, f), 0)) for f in feas_order]
        lines.append(f"| {imp} | " + " | ".join(row) + " |")

    # 4. Risk distribution
    risk_counts: dict[str, int] = {}
    for s in scenarios:
        risk_counts[s["risk_level"]] = risk_counts.get(s["risk_level"], 0) + 1
    lines.append("\n## 4. Risk Distribution\n")
    lines.append("| Risk Level | Count | Treatment |")
    lines.append("|---|---|---|")
    for risk in ["Critical", "High", "Medium", "Low", "Negligible"]:
        if risk in risk_counts:
            lines.append(f"| **{risk}** | {risk_counts[risk]} | {_treatment(risk)} |")

    # 5. Top concerns (Critical / High only)
    top = [s for s in scenarios if s["risk_level"] in ("Critical", "High")]
    if top:
        lines.append("\n## 5. Top Concerns (Critical / High)\n")
        for s in top:
            lines.append(f"### {s['scenario_id']} — {s['asset']} ({s['risk_level']})")
            lines.append(f"- **APK**: `{s['apk']}`")
            lines.append(f"- **Category**: {s['stage1_category']} ({s['stage1_severity']} → {s['true_severity']})")
            lines.append(f"- **Threats**: {', '.join(s['threats'])}")
            lines.append(f"- **Impact / Feasibility**: {s['impact']} / {s['attack_feasibility']}")
            lines.append(f"- **Treatment**: {s['treatment']}")
            if s["note"]:
                lines.append(f"- **Note**: {s['note']}")
            lines.append("")

    # 6. Methodology footnote
    lines.append("\n## 6. Methodology\n")
    lines.append("- **Impact**: max(asset_criticality, severity_to_impact). 자산 본질적 가치와 finding 심각도 중 큰 값.")
    lines.append("- **Attack Feasibility**: category + note 기반 룰. exported intent / hardcoded in APK / plaintext network → High.")
    lines.append("- **Risk Matrix**: ISO/SAE 21434 단순화 4-tier (Critical / High / Medium / Low / Negligible).")
    lines.append("- **Treatment**: Critical=Avoid, High=Mitigate(현 sprint), Medium=Mitigate(차 minor) 또는 Transfer, Low=Accept w/ monitoring.")
    lines.append("- **Caveat**: Attack Feasibility는 정적 분석 단계 추정. 실차 시나리오 (네트워크 위치, 권한 grant 경로) 측정 후 재평가 필요.")

    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping, gt = _load()
    asset_meta = mapping.get("tara", {}).get("asset_categories", {})
    scenarios = build_threat_scenarios(mapping, gt)
    md = OUT_DIR / "tara_artifact.md"
    js = OUT_DIR / "tara_artifact.json"
    md.write_text(to_md(scenarios, asset_meta), encoding="utf-8")
    js.write_text(
        json.dumps({"scenarios": scenarios, "generated": str(date.today())}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote: {md}")
    print(f"wrote: {js}")


if __name__ == "__main__":
    main()
