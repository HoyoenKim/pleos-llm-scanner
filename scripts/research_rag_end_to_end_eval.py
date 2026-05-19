#!/usr/bin/env python
"""Score RAG end-to-end judgment outputs against combined GT.

Expected input is one or more JSON files with:
{
  "scope": "sample19",
  "condition": "no_rag",
  "model": "...",
  "judgments": [{"finding_id": "vc-5", "verdict": "report", ...}]
}
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
LABELS = ROOT / "data" / "ground_truth" / "combined_labels.json"
OUT_DIR = ROOT / "data" / "reports" / "rag_end_to_end"


def load_gt() -> dict[str, bool]:
    data = json.loads(LABELS.read_text(encoding="utf-8"))
    return {lbl["id"]: bool(lbl["is_real"]) for lbl in data.get("labels", [])}


def load_result(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"scope": "unknown", "condition": path.stem, "model": "unknown", "judgments": data}
    judgments = data.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError(f"{path}: missing judgments list")
    return data


def score_result(data: dict[str, Any], gt: dict[str, bool]) -> dict[str, Any]:
    rows = []
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for judgment in data["judgments"]:
        fid = judgment.get("finding_id")
        verdict = judgment.get("verdict")
        if fid not in gt:
            raise ValueError(f"unknown finding_id: {fid}")
        if verdict not in {"report", "suppress"}:
            raise ValueError(f"{fid}: verdict must be report/suppress, got {verdict!r}")
        is_real = gt[fid]
        if verdict == "report" and is_real:
            bucket = "tp"
        elif verdict == "report" and not is_real:
            bucket = "fp"
        elif verdict == "suppress" and not is_real:
            bucket = "tn"
        else:
            bucket = "fn"
        counts[bucket] += 1
        rows.append({
            "finding_id": fid,
            "gt": "TP" if is_real else "FP",
            "verdict": verdict,
            "correct": bucket in {"tp", "tn"},
            "bucket": bucket.upper(),
            "confidence": judgment.get("confidence"),
            "reason": judgment.get("reason", ""),
        })

    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and (precision + recall) else None
    return {
        "scope": data.get("scope", "unknown"),
        "condition": data.get("condition", "unknown"),
        "model": data.get("model", "unknown"),
        "counts": counts,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "report_rate": (tp + fp) / len(rows) if rows else None,
        "rows": rows,
    }


def compare_conditions(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scope_model: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for item in scored:
        by_scope_model[(item["scope"], item["model"])][item["condition"]] = item

    comparisons = []
    for (scope, model), conds in by_scope_model.items():
        if "no_rag" not in conds or "with_rag" not in conds:
            continue
        a = {r["finding_id"]: r for r in conds["no_rag"]["rows"]}
        b = {r["finding_id"]: r for r in conds["with_rag"]["rows"]}
        improved = []
        regressed = []
        changed = []
        for fid, row_a in a.items():
            if fid not in b:
                continue
            row_b = b[fid]
            if row_a["verdict"] != row_b["verdict"]:
                changed.append({
                    "finding_id": fid,
                    "gt": row_a["gt"],
                    "no_rag": row_a["verdict"],
                    "with_rag": row_b["verdict"],
                    "no_rag_correct": row_a["correct"],
                    "with_rag_correct": row_b["correct"],
                })
            if not row_a["correct"] and row_b["correct"]:
                improved.append(fid)
            if row_a["correct"] and not row_b["correct"]:
                regressed.append(fid)
        comparisons.append({
            "scope": scope,
            "model": model,
            "changed": changed,
            "improved": improved,
            "regressed": regressed,
            "delta_precision": none_safe_delta(conds["with_rag"]["precision"], conds["no_rag"]["precision"]),
            "delta_recall": none_safe_delta(conds["with_rag"]["recall"], conds["no_rag"]["recall"]),
            "delta_f1": none_safe_delta(conds["with_rag"]["f1"], conds["no_rag"]["f1"]),
        })
    return comparisons


def none_safe_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.1f}%"


def write_outputs(scored: list[dict[str, Any]], comparisons: list[dict[str, Any]], name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"results": scored, "comparisons": comparisons}
    (OUT_DIR / f"{name}_metrics.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# RAG End-to-End Ablation Metrics",
        "",
        "## Per-condition results",
        "",
        "| Scope | Condition | Model | TP | FP | TN | FN | Precision | Recall | F1 | Report rate |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in scored:
        c = item["counts"]
        md.append(
            f"| {item['scope']} | {item['condition']} | {item['model']} | "
            f"{c['tp']} | {c['fp']} | {c['tn']} | {c['fn']} | "
            f"{pct(item['precision'])} | {pct(item['recall'])} | {pct(item['f1'])} | {pct(item['report_rate'])} |"
        )
    if comparisons:
        md += [
            "",
            "## Paired RAG deltas",
            "",
            "| Scope | Model | Δ Precision | Δ Recall | Δ F1 | Improved | Regressed | Changed verdicts |",
            "|---|---|---:|---:|---:|---|---|---:|",
        ]
        for comp in comparisons:
            md.append(
                f"| {comp['scope']} | {comp['model']} | {pct(comp['delta_precision'])} | "
                f"{pct(comp['delta_recall'])} | {pct(comp['delta_f1'])} | "
                f"{', '.join(comp['improved']) or '-'} | {', '.join(comp['regressed']) or '-'} | {len(comp['changed'])} |"
            )
    md.append("")
    (OUT_DIR / f"{name}_metrics.md").write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+", help="judgment JSON files to score")
    ap.add_argument("--name", default="rag_end_to_end", help="output metrics basename")
    args = ap.parse_args()

    gt = load_gt()
    scored = [score_result(load_result(Path(p)), gt) for p in args.results]
    comparisons = compare_conditions(scored)
    write_outputs(scored, comparisons, args.name)
    print(f"wrote data/reports/rag_end_to_end/{args.name}_metrics.{{md,json}}")
    for item in scored:
        print(f"{item['scope']} {item['condition']} {item['model']}: P={pct(item['precision'])} R={pct(item['recall'])} F1={pct(item['f1'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
