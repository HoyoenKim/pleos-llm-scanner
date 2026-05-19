"""AAOS / MASVS / TARA mapper.

Reads:
  - configs/aaos_mapping.yaml (category -> AAOS/MASVS/TARA mapping)
  - data/ground_truth/combined_labels.json (combined GT, n=19)

Writes:
  - data/reports/aggregate/aaos_mapping_table.{md,json}  (overwritten each run; the md
    body carries `_Generated: <ISO date>_` so the measurement date is preserved).

Deterministic only. No LLM calls.
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


def _load() -> tuple[dict[str, Any], dict[str, Any]]:
    with CFG.open("r", encoding="utf-8") as f:
        mapping = yaml.safe_load(f)
    with GT.open("r", encoding="utf-8") as f:
        gt = json.load(f)
    return mapping, gt


def _row(label: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    cat = label["stage1_category"]
    cat_map = mapping["mappings"].get(cat, {})
    fid = label["id"]
    tara = mapping.get("finding_tara_assignments", {}).get(fid, {})
    asset_key = tara.get("asset")
    asset_meta = mapping.get("tara", {}).get("asset_categories", {}).get(asset_key, {}) if asset_key else {}
    threat_ids = tara.get("threats", []) or []
    threat_table = {t["id"]: t["label"] for t in mapping.get("tara", {}).get("threat_categories", [])}
    threat_labels = [f"{tid} ({threat_table.get(tid, '?')})" for tid in threat_ids]

    return {
        "id": fid,
        "apk": label["apk"],
        "class": label["class"],
        "line": label["line"],
        "stage1_severity": label["stage1_severity"],
        "stage1_category": cat,
        "is_real": label["is_real"],
        "true_severity": label.get("true_severity"),
        "source": label.get("source"),
        "aaos_section": cat_map.get("aaos_section"),
        "aaos_url": cat_map.get("aaos_url"),
        "masvs_categories": cat_map.get("masvs_categories", []),
        "masvs_external": label.get("masvs"),  # MASTG label may carry per-finding MASVS
        "tara_asset": asset_meta.get("label", asset_key or "n/a"),
        "tara_threats": threat_labels,
        "tara_threat_class_default": cat_map.get("tara_threat_class"),
        "tara_impact_default": cat_map.get("tara_impact"),
        "note": tara.get("note", ""),
    }


def build_rows() -> list[dict[str, Any]]:
    mapping, gt = _load()
    return [_row(lbl, mapping) for lbl in gt["labels"]]


def to_md(rows: list[dict[str, Any]]) -> str:
    lines = []
    lines.append("# AAOS / MASVS / TARA Mapping Table\n")
    lines.append(f"_Generated: {date.today().isoformat()} (deterministic from `configs/aaos_mapping.yaml` + GT)_\n")
    lines.append(f"**n = {len(rows)}** (PleOS self {sum(1 for r in rows if r['source']=='self')} + MASTG {sum(1 for r in rows if r['source']=='mastg')})\n")

    # Section 1: Per-finding mapping
    lines.append("## 1. Finding-level Mapping\n")
    lines.append("| ID | APK | Cat | Sev | TP | AAOS | MASVS | TARA Asset | Threats |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        masvs = ", ".join(r["masvs_categories"]) if r["masvs_categories"] else "—"
        masvs_ext = f" ({r['masvs_external']})" if r["masvs_external"] else ""
        threats = ", ".join(r["tara_threats"]) if r["tara_threats"] else "—"
        tp = "✓" if r["is_real"] else "FP"
        lines.append(
            f"| {r['id']} | {r['apk'].split('.')[-1]} | {r['stage1_category']} | "
            f"{r['stage1_severity']} | {tp} | {r['aaos_section']} | "
            f"{masvs}{masvs_ext} | {r['tara_asset']} | {threats} |"
        )

    # Section 2: AAOS section coverage
    lines.append("\n## 2. AAOS Section Coverage\n")
    sec_counts: dict[str, dict[str, int]] = {}
    for r in rows:
        sec = r["aaos_section"] or "(unmapped)"
        d = sec_counts.setdefault(sec, {"total": 0, "tp": 0, "high": 0})
        d["total"] += 1
        if r["is_real"]:
            d["tp"] += 1
        if r["stage1_severity"] == "high":
            d["high"] += 1
    lines.append("| AAOS Section | Findings | TP | HIGH |")
    lines.append("|---|---|---|---|")
    for sec, d in sorted(sec_counts.items(), key=lambda x: -x[1]["total"]):
        lines.append(f"| {sec} | {d['total']} | {d['tp']} | {d['high']} |")

    # Section 3: TARA asset × threat matrix
    lines.append("\n## 3. TARA Asset × Threat Matrix (TP only)\n")
    matrix: dict[tuple[str, str], int] = {}
    assets_seen: set[str] = set()
    threats_seen: set[str] = set()
    for r in rows:
        if not r["is_real"]:
            continue
        a = r["tara_asset"]
        assets_seen.add(a)
        for t in r["tara_threats"]:
            tid = t.split(" ")[0]  # "S (Spoofing)" -> "S"
            threats_seen.add(tid)
            matrix[(a, tid)] = matrix.get((a, tid), 0) + 1
    threats_order = ["S", "T", "I", "D", "E"]
    threats_used = [t for t in threats_order if t in threats_seen]
    if not threats_used:
        threats_used = sorted(threats_seen)
    header = "| Asset \\ Threat | " + " | ".join(threats_used) + " |"
    sep = "|---|" + "|".join(["---"] * len(threats_used)) + "|"
    lines.append(header)
    lines.append(sep)
    for a in sorted(assets_seen):
        row_vals = [str(matrix.get((a, t), 0)) for t in threats_used]
        lines.append(f"| {a} | " + " | ".join(row_vals) + " |")

    # Section 4: Notes
    lines.append("\n## 4. Notes per Finding\n")
    for r in rows:
        if r["note"]:
            lines.append(f"- **{r['id']}** — {r['note']}")

    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    md_path = OUT_DIR / "aaos_mapping_table.md"
    json_path = OUT_DIR / "aaos_mapping_table.json"
    md_path.write_text(to_md(rows), encoding="utf-8")
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote: {md_path}")
    print(f"wrote: {json_path}")


if __name__ == "__main__":
    main()
