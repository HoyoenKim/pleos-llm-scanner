#!/usr/bin/env python
"""
Quantitative evaluation of stage-1 vulnerability findings against ground-truth labels.

Inputs
------
- One or more report JSON files: data/reports/*.json
  (schema: see configs/result_schema.json — single-pass output produced by the LLM analyzer)
- One ground-truth JSON file: data/ground_truth/<name>.labels.json
  (schema: see data/ground_truth/self_labels.json)

Outputs
-------
- precision / FP-rate (overall + per APK + per category)
- TP / FP counts
- (optional) Recall is only meaningful when GT contains items the reports do NOT carry —
  by default this script only measures precision against the labelled superset. When the
  GT JSON includes `unmatched_in_reports` items, those are added to FN.

Usage
-----
    python src/eval.py --labels data/ground_truth/combined_labels.json \
                       --reports data/reports/*.json [--by-stage stage1|stage2]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def index_findings(report_jsons: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    """
    Index every finding by (apk, class, line) so we can match labels to findings cheaply.
    Skips JSON files that don't match the stage-1 report schema (e.g. aaos_mapping_table,
    tara_artifact, stage3_ensemble).
    """
    idx: dict[tuple[str, str, int], dict[str, Any]] = {}
    for r in report_jsons:
        if not isinstance(r, dict) or "apk" not in r or "results" not in r:
            continue
        apk = r.get("apk")
        for cls_result in r.get("results", []):
            cls = cls_result.get("class")
            for f in cls_result.get("findings", []):
                key = (apk, cls, int(f["line"]))
                idx[key] = {
                    "apk": apk,
                    "class": cls,
                    "line": int(f["line"]),
                    "category": f.get("category"),
                    "severity": f.get("severity"),
                    "confidence": f.get("confidence"),
                    "stage": cls_result.get("stage", "stage1"),
                }
    return idx


def evaluate(labels: dict[str, Any], reports_idx: dict[tuple[str, str, int], dict[str, Any]],
             stage_filter: str | None) -> dict[str, Any]:
    tp = fp = fn = unc = 0
    per_apk: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "uncertain": 0})
    per_cat: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "uncertain": 0})

    matched_keys: set[tuple[str, str, int]] = set()

    for lbl in labels.get("labels", []):
        key = (lbl["apk"], lbl["class"], int(lbl["line"]))
        finding = reports_idx.get(key)
        is_real = lbl["is_real"]
        category = (finding or lbl).get("category") or lbl.get("stage1_category")

        if finding is None:
            # The GT names a finding the reports never produced — count as FN
            fn += 1
            per_apk[lbl["apk"]]["fn"] += 1
            per_cat[category]["fn"] += 1
            continue

        if stage_filter and finding.get("stage") != stage_filter:
            continue

        matched_keys.add(key)

        if is_real is True:
            tp += 1
            per_apk[lbl["apk"]]["tp"] += 1
            per_cat[category]["tp"] += 1
        elif is_real is False:
            fp += 1
            per_apk[lbl["apk"]]["fp"] += 1
            per_cat[category]["fp"] += 1
        else:  # "uncertain" or any non-bool
            unc += 1
            per_apk[lbl["apk"]]["uncertain"] += 1
            per_cat[category]["uncertain"] += 1

    # Findings present in reports but missing from GT — informational
    unlabelled = [k for k in reports_idx if k not in matched_keys]

    # Strict view: uncertain → FP. Lenient view: uncertain excluded.
    strict_precision = tp / (tp + fp + unc) if (tp + fp + unc) else None
    lenient_precision = tp / (tp + fp) if (tp + fp) else None
    strict_fp_rate = (fp + unc) / (tp + fp + unc) if (tp + fp + unc) else None
    lenient_fp_rate = fp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None

    return {
        "stage_filter": stage_filter,
        "totals": {
            "tp": tp, "fp": fp, "uncertain": unc, "fn": fn,
            "labelled": tp + fp + unc + fn,
            "unlabelled_findings": len(unlabelled),
        },
        "metrics_lenient": {
            "precision": lenient_precision,
            "false_positive_rate": lenient_fp_rate,
            "recall": recall,
        },
        "metrics_strict": {
            "precision": strict_precision,
            "false_positive_rate": strict_fp_rate,
            "recall": recall,
        },
        "per_apk": dict(per_apk),
        "per_category": dict(per_cat),
        "unlabelled_findings_keys": [list(k) for k in unlabelled],
    }


def fmt_pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.1f}%"


def print_summary(name: str, m: dict[str, Any]) -> None:
    t = m["totals"]
    print(f"\n=== {name} ===")
    print(f"  labelled={t['labelled']}  TP={t['tp']}  FP={t['fp']}  uncertain={t['uncertain']}  FN={t['fn']}")
    print(f"  unlabelled findings (in reports, not in GT): {t['unlabelled_findings']}")
    ml, ms = m["metrics_lenient"], m["metrics_strict"]
    print(f"  precision (lenient / strict): {fmt_pct(ml['precision'])} / {fmt_pct(ms['precision'])}")
    print(f"  false-positive-rate (lenient / strict): {fmt_pct(ml['false_positive_rate'])} / {fmt_pct(ms['false_positive_rate'])}")
    print(f"  recall: {fmt_pct(ml['recall'])}")
    print("  per-APK:")
    for apk, c in m["per_apk"].items():
        print(f"    {apk:<40} TP={c['tp']:>2}  FP={c['fp']:>2}  unc={c['uncertain']:>2}  FN={c['fn']:>2}")
    print("  per-category:")
    for cat, c in m["per_category"].items():
        print(f"    {cat:<20} TP={c['tp']:>2}  FP={c['fp']:>2}  unc={c['uncertain']:>2}  FN={c['fn']:>2}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", required=True, help="Path to ground-truth labels JSON")
    p.add_argument("--reports", required=True, nargs="+",
                   help="Paths or globs to report JSONs (e.g. data/reports/*.json)")
    p.add_argument("--by-stage", default=None, choices=["stage1", "stage2", "stage3"],
                   help="Restrict matched findings to one pipeline stage")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of human summary")
    args = p.parse_args()

    labels = load_json(Path(args.labels))

    expanded: list[Path] = []
    for r in args.reports:
        matches = [Path(m) for m in glob.glob(r)]
        if not matches:
            print(f"warning: no files matched {r}", file=sys.stderr)
        expanded.extend(matches)
    reports = [load_json(p) for p in expanded]
    reports_idx = index_findings(reports)

    overall = evaluate(labels, reports_idx, args.by_stage)

    if args.json:
        print(json.dumps(overall, indent=2, ensure_ascii=False))
    else:
        scope = f"stage={args.by_stage}" if args.by_stage else "all stages"
        print(f"# Evaluation ({scope})")
        print(f"#  labels: {args.labels}")
        print(f"#  reports: {len(reports)} file(s) → {len(reports_idx)} finding(s) indexed")
        print_summary("overall", overall)

    return 0


if __name__ == "__main__":
    sys.exit(main())
