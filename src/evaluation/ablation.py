#!/usr/bin/env python
"""
Ablation harness - measures the contribution of each pipeline stage and the
sensitivity of the stage-3 consensus threshold.

Variants
--------
A. Stage ablation
   A.1 stage 1 only          : every keyword-filtered finding accepted
   A.2 stage 1 + stage 2     : caller-traced TPs only (== self GT 'is_real==true')
   A.3 stage 1+2+3 (full)    : stage 3 strong-TP (consensus ≥ 3) only

B. Consensus-threshold sensitivity (multi-prompt ensemble)
   B.1 threshold ≥ 1/3 - accept anything any perspective flags
   B.2 threshold ≥ 2/3 - accept majority
   B.3 threshold ≥ 3/3 - accept only unanimous

Usage
-----
    python src/evaluation/ablation.py \
        --labels data/ground_truth/combined_labels.json \
        --reports 'data/reports/**/*.json' \
        --stage3  data/reports/local/stage3_ensemble.json

Output is a markdown table on stdout. Add `--json` for machine-readable form.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any


def load_json(p: Path) -> dict[str, Any]:
    with p.open(encoding="utf-8") as f:
        return json.load(f)


Key = tuple[str, str, int]  # (apk, class, line)


def index_stage1_findings(reports: list[dict[str, Any]]) -> dict[Key, dict[str, Any]]:
    idx: dict[Key, dict[str, Any]] = {}
    for r in reports:
        if not isinstance(r, dict) or "apk" not in r or "results" not in r:
            continue
        apk = r.get("apk")
        for cr in r.get("results", []):
            cls = cr.get("class")
            for f in cr.get("findings", []):
                idx[(apk, cls, int(f["line"]))] = {
                    "category": f.get("category"),
                    "severity": f.get("severity"),
                }
    return idx


def index_labels(labels_doc: dict[str, Any]) -> dict[Key, dict[str, Any]]:
    return {
        (l["apk"], l["class"], int(l["line"])): l
        for l in labels_doc.get("labels", [])
    }


def id_to_key_map(labels_doc: dict[str, Any]) -> dict[str, Key]:
    return {l["id"]: (l["apk"], l["class"], int(l["line"])) for l in labels_doc.get("labels", [])}


def stage3_keys_at_threshold(
    stage3: dict[str, Any],
    id_to_key: dict[str, Key],
    threshold: int,
) -> set[Key]:
    keys: set[Key] = set()
    for e in stage3.get("results", []):
        if e.get("consensus_count", 0) >= threshold:
            k = id_to_key.get(e["id"])
            if k is not None:
                keys.add(k)
    return keys


def measure(
    accepted: set[Key],
    labels: dict[Key, dict[str, Any]],
) -> dict[str, Any]:
    """Compute TP / FP / uncertain / FN against the GT labels.

    - GT TP not in `accepted` → FN
    - GT FP in `accepted` → FP
    - GT TP in `accepted` → TP
    - GT uncertain in `accepted` → uncertain bucket
    """
    tp = fp = fn = unc = 0
    for k, lbl in labels.items():
        is_real = lbl["is_real"]
        in_accepted = k in accepted
        if is_real is True and in_accepted:
            tp += 1
        elif is_real is True and not in_accepted:
            fn += 1
        elif is_real is False and in_accepted:
            fp += 1
        elif is_real is False and not in_accepted:
            pass  # correctly rejected
        else:  # uncertain
            if in_accepted:
                unc += 1

    precision_lenient = tp / (tp + fp) if (tp + fp) else None
    precision_strict = tp / (tp + fp + unc) if (tp + fp + unc) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    fp_rate = fp / (tp + fp) if (tp + fp) else None
    f1 = (
        2 * precision_lenient * recall / (precision_lenient + recall)
        if precision_lenient and recall and (precision_lenient + recall) > 0
        else None
    )
    return {
        "accepted": len(accepted),
        "tp": tp, "fp": fp, "fn": fn, "uncertain": unc,
        "precision_lenient": precision_lenient,
        "precision_strict": precision_strict,
        "fp_rate_lenient": fp_rate,
        "recall": recall,
        "f1_lenient": f1,
    }


def fmt_pct(x: float | None) -> str:
    return "-" if x is None else f"{100 * x:.1f}%"


def fmt_num(x: float | None) -> str:
    return "-" if x is None else f"{x:.3f}"


def md_table(rows: list[dict[str, Any]], cols: list[tuple[str, str]]) -> str:
    """rows = list of dict, cols = [(header, key), ...]. Returns markdown table."""
    headers = [h for h, _ in cols]
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(k, "")) for _, k in cols) + " |")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", required=True)
    p.add_argument("--reports", required=True, nargs="+")
    p.add_argument("--stage3", required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    labels_doc = load_json(Path(args.labels))
    labels = index_labels(labels_doc)
    id2key = id_to_key_map(labels_doc)

    expanded = []
    for r in args.reports:
        expanded.extend([Path(m) for m in glob.glob(r, recursive=True)])
    if not expanded:
        print(f"warning: no report files matched {args.reports}", file=sys.stderr)
    reports = [load_json(p) for p in expanded]

    stage1_idx = index_stage1_findings(reports)
    stage3 = load_json(Path(args.stage3))

    # Variant A: stage ablation
    rows_A = []
    # A.1 stage 1 only
    accepted_A1 = set(stage1_idx.keys())
    m = measure(accepted_A1, labels)
    rows_A.append({"variant": "A.1 stage 1 only",
                   "accepted": m["accepted"],
                   "TP": m["tp"], "FP": m["fp"], "FN": m["fn"], "unc": m["uncertain"],
                   "P (lenient)": fmt_pct(m["precision_lenient"]),
                   "FP-rate": fmt_pct(m["fp_rate_lenient"]),
                   "Recall": fmt_pct(m["recall"]),
                   "F1": fmt_num(m["f1_lenient"])})

    # A.2 stage 1 + stage 2 = caller-traced TPs (self GT is_real=True)
    accepted_A2 = {k for k, lbl in labels.items() if lbl["is_real"] is True}
    m = measure(accepted_A2, labels)
    rows_A.append({"variant": "A.2 + stage 2 (caller)",
                   "accepted": m["accepted"],
                   "TP": m["tp"], "FP": m["fp"], "FN": m["fn"], "unc": m["uncertain"],
                   "P (lenient)": fmt_pct(m["precision_lenient"]),
                   "FP-rate": fmt_pct(m["fp_rate_lenient"]),
                   "Recall": fmt_pct(m["recall"]),
                   "F1": fmt_num(m["f1_lenient"])})

    # A.3 full pipeline = stage 3 strong TP (consensus ≥ 3)
    accepted_A3 = stage3_keys_at_threshold(stage3, id2key, 3)
    m = measure(accepted_A3, labels)
    rows_A.append({"variant": "A.3 + stage 3 (≥3/3)",
                   "accepted": m["accepted"],
                   "TP": m["tp"], "FP": m["fp"], "FN": m["fn"], "unc": m["uncertain"],
                   "P (lenient)": fmt_pct(m["precision_lenient"]),
                   "FP-rate": fmt_pct(m["fp_rate_lenient"]),
                   "Recall": fmt_pct(m["recall"]),
                   "F1": fmt_num(m["f1_lenient"])})

    # Variant B: consensus threshold sensitivity
    rows_B = []
    for th in [1, 2, 3]:
        acc = stage3_keys_at_threshold(stage3, id2key, th)
        m = measure(acc, labels)
        rows_B.append({"threshold": f"≥ {th}/3",
                       "accepted": m["accepted"],
                       "TP": m["tp"], "FP": m["fp"], "FN": m["fn"], "unc": m["uncertain"],
                       "P (lenient)": fmt_pct(m["precision_lenient"]),
                       "FP-rate": fmt_pct(m["fp_rate_lenient"]),
                       "Recall": fmt_pct(m["recall"]),
                       "F1": fmt_num(m["f1_lenient"])})

    if args.json:
        print(json.dumps({"variant_A_stage_ablation": rows_A,
                          "variant_B_consensus_threshold": rows_B},
                         indent=2, ensure_ascii=False))
        return 0

    print("# Ablation Results\n")
    print(f"## Inputs")
    print(f"- labels: {args.labels} (n={len(labels)})")
    print(f"- reports: {len(reports)} files → {len(stage1_idx)} stage-1 findings indexed")
    print(f"- stage3: {args.stage3} (n={len(stage3.get('results', []))} entries)\n")

    print("## A - Stage ablation\n")
    cols_A = [("variant", "variant"), ("accepted", "accepted"),
              ("TP", "TP"), ("FP", "FP"), ("FN", "FN"), ("unc", "unc"),
              ("P (lenient)", "P (lenient)"), ("FP-rate", "FP-rate"),
              ("Recall", "Recall"), ("F1", "F1")]
    print(md_table(rows_A, cols_A))

    print("\n## B - Consensus-threshold sensitivity (multi-prompt ensemble)\n")
    cols_B = [("threshold", "threshold"), ("accepted", "accepted"),
              ("TP", "TP"), ("FP", "FP"), ("FN", "FN"), ("unc", "unc"),
              ("P (lenient)", "P (lenient)"), ("FP-rate", "FP-rate"),
              ("Recall", "Recall"), ("F1", "F1")]
    print(md_table(rows_B, cols_B))

    print("\n## Notes")
    print("- A.2 simulates 'stage 2 caller analysis' by using self-GT `is_real==true` as the accepted set. The Recall is 100% by construction (every GT TP is accepted), so A.2 is a P-ceiling rather than a realistic ablation; useful as an upper bound for the caller-trace step in isolation.")
    print("- B threshold curve shows the FP/Recall trade-off of the multi-prompt ensemble. Sample is small; OWASP MASTG corpus is needed for statistical significance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
