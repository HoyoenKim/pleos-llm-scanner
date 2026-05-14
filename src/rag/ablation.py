#!/usr/bin/env python
"""RAG ablation — does the retrieved context calibrate Stage 1 verdicts?

Two measurements per GT label:

1. **nearest-neighbor verdict propagation accuracy** — for each finding, query
   `finding_patterns_historical` with the finding's stage1 title/evidence,
   *excluding the finding itself*, take the top-1 hit's `verdict` (TP/FP) and
   compare with the GT label. This measures whether RAG-retrieved historical
   patterns would calibrate the Stage 1 confidence in the right direction.

2. **AAOS category alignment** — for each finding, query `aaos_guidelines` with
   the same text and compare the top-1 hit's `category` metadata with the GT
   stage1_category. Measures whether RAG produces a usable AAOS § citation.

3. **MASVS retrieval relevance** — for each finding, query `masvs_controls`
   and report whether the top-1 hit's `masvs_category` covers the relevant
   crypto / network / platform / auth / storage area.

Output: data/reports/rag_ablation.{md,json}

Usage:
    python src/rag/ablation.py [--k 1]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 stdout on Windows.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("error: chromadb not installed", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = ROOT / "data" / "rag" / "chroma"
LABELS = ROOT / "data" / "ground_truth" / "combined_labels.json"
REPORTS_GLOB = str(ROOT / "data" / "reports" / "*.json")
OUT_DIR = ROOT / "data" / "reports"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Map AAOS category labels to expected MASVS area (loose semantic alignment).
MASVS_AREA = {
    "crypto": "MASVS-CRYPTO",
    "network": "MASVS-NETWORK",
    "permission": "MASVS-PLATFORM",
    "intent": "MASVS-PLATFORM",
    "hardcoded": "MASVS-AUTH",
    "reflection_dynamic": "MASVS-PLATFORM",
}


def build_query_text(label: dict, report_finding: dict) -> str:
    """Combine GT label fields + report rationale to form a retrieval query."""
    parts = [
        f"Category: {label.get('stage1_category', '')}",
        f"Severity: {label.get('stage1_severity', '')}",
        f"Title: {report_finding.get('title', '')}",
        f"Evidence: {report_finding.get('evidence', '')[:300]}",
        f"Rationale: {report_finding.get('rationale', label.get('notes', ''))[:300]}",
    ]
    return "\n".join(p for p in parts if p.split(":", 1)[1].strip())


def load_report_findings() -> dict[tuple[str, str, int], dict]:
    import glob as _glob
    idx = {}
    for rp in _glob.glob(REPORTS_GLOB):
        try:
            r = json.loads(Path(rp).read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(r, dict) or "results" not in r:
            continue
        apk = r.get("apk")
        for cr in r.get("results", []):
            cls = cr.get("class")
            for f in cr.get("findings", []):
                try:
                    idx[(apk, cls, int(f["line"]))] = f
                except (KeyError, TypeError, ValueError):
                    continue
    return idx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3, help="top-k from finding_patterns_historical (top1 is self if present)")
    args = ap.parse_args()

    labels = json.loads(LABELS.read_text(encoding="utf-8"))["labels"]
    finding_idx = load_report_findings()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

    coll_hist = client.get_collection("finding_patterns_historical", embedding_function=ef)
    coll_aaos = client.get_collection("aaos_guidelines", embedding_function=ef)
    coll_masvs = client.get_collection("masvs_controls", embedding_function=ef)

    rows = []
    for lbl in labels:
        try:
            key = (lbl["apk"], lbl["class"], int(lbl["line"]))
        except (KeyError, TypeError, ValueError):
            continue
        rpt = finding_idx.get(key, {})
        q = build_query_text(lbl, rpt)

        # 1. historical nearest neighbor, excluding self
        hist = coll_hist.query(query_texts=[q], n_results=args.k)
        nn_verdict = None
        nn_id = None
        nn_dist = None
        for i, h_id in enumerate(hist["ids"][0]):
            md = hist["metadatas"][0][i]
            if md.get("finding_id") == lbl["id"]:
                continue
            nn_id = md.get("finding_id")
            nn_verdict = md.get("verdict")
            nn_dist = hist["distances"][0][i]
            break

        # 2. AAOS top-1 category
        aaos = coll_aaos.query(query_texts=[q], n_results=1)
        aaos_cat = aaos["metadatas"][0][0].get("category") if aaos["metadatas"][0] else None

        # 3. MASVS top-1 area
        masvs = coll_masvs.query(query_texts=[q], n_results=1)
        masvs_cat = masvs["metadatas"][0][0].get("masvs_category") if masvs["metadatas"][0] else None

        gt_verdict = "TP" if lbl.get("is_real") is True else (
            "FP" if lbl.get("is_real") is False else "uncertain"
        )
        gt_category = lbl.get("stage1_category", "")
        expected_masvs = MASVS_AREA.get(gt_category, "")

        rows.append({
            "finding_id": lbl["id"],
            "apk": lbl["apk"],
            "gt_verdict": gt_verdict,
            "gt_category": gt_category,
            "nn_finding_id": nn_id,
            "nn_verdict": nn_verdict,
            "nn_verdict_match": (nn_verdict == gt_verdict),
            "nn_distance": nn_dist,
            "aaos_top_category": aaos_cat,
            "aaos_category_match": (aaos_cat == gt_category),
            "masvs_top_category": masvs_cat,
            "masvs_area_match": (masvs_cat == expected_masvs) if expected_masvs else None,
        })

    # aggregate
    n = len(rows)
    nn_correct = sum(1 for r in rows if r["nn_verdict_match"])
    aaos_correct = sum(1 for r in rows if r["aaos_category_match"])
    masvs_correct = sum(1 for r in rows if r["masvs_area_match"])
    masvs_evaluated = sum(1 for r in rows if r["masvs_area_match"] is not None)

    nn_by_verdict = Counter((r["gt_verdict"], r["nn_verdict_match"]) for r in rows)
    aaos_by_cat = defaultdict(lambda: {"hit": 0, "total": 0})
    for r in rows:
        aaos_by_cat[r["gt_category"]]["total"] += 1
        if r["aaos_category_match"]:
            aaos_by_cat[r["gt_category"]]["hit"] += 1

    summary = {
        "n_labels": n,
        "nn_verdict_propagation": {
            "correct": nn_correct,
            "n": n,
            "accuracy": round(nn_correct / n, 4) if n else None,
            "by_gt_verdict": {
                "TP": {
                    "match": nn_by_verdict[("TP", True)],
                    "mismatch": nn_by_verdict[("TP", False)],
                },
                "FP": {
                    "match": nn_by_verdict[("FP", True)],
                    "mismatch": nn_by_verdict[("FP", False)],
                },
            },
        },
        "aaos_category_alignment": {
            "correct": aaos_correct,
            "n": n,
            "accuracy": round(aaos_correct / n, 4) if n else None,
            "by_category": {
                k: {"hit": v["hit"], "total": v["total"],
                    "accuracy": round(v["hit"] / v["total"], 4) if v["total"] else None}
                for k, v in aaos_by_cat.items()
            },
        },
        "masvs_area_match": {
            "correct": masvs_correct,
            "n_evaluated": masvs_evaluated,
            "accuracy": round(masvs_correct / masvs_evaluated, 4) if masvs_evaluated else None,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "rag_ablation.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = [
        "# RAG Ablation — Nearest-Neighbor Verdict + AAOS / MASVS Alignment",
        "",
        "_Measured: 2026-05-14 (학기 외 B 작업) / n=47 combined GT_",
        "",
        "## Methodology",
        "",
        "- **Retrieval setup**: Chroma local + sentence-transformers `all-MiniLM-L6-v2` (CPU). Four collections (`aaos_guidelines` n=6, `masvs_controls` n=99, `tara_templates` n=6, `finding_patterns_historical` n=47).",
        "- **Query construction**: per GT label, concatenate `stage1_category`, `stage1_severity`, report `title`, `evidence` (first 300 chars), `rationale` (first 300 chars).",
        "- **Three measurements**:",
        "  1. Nearest-neighbor verdict propagation: top-1 of `finding_patterns_historical` (excluding self) → does its `verdict` (TP/FP) match the query's GT?",
        "  2. AAOS category alignment: top-1 of `aaos_guidelines` → does its `category` match the query's stage1_category?",
        "  3. MASVS area match: top-1 of `masvs_controls` → does its `masvs_category` cover the expected MASVS-AREA mapping (`MASVS_AREA` table in `src/rag/ablation.py`)?",
        "",
        "## Summary",
        "",
        f"- **nearest-neighbor verdict propagation**: {summary['nn_verdict_propagation']['correct']}/{summary['nn_verdict_propagation']['n']} = **{summary['nn_verdict_propagation']['accuracy']*100:.1f}%**.",
        f"  - TP queries: {summary['nn_verdict_propagation']['by_gt_verdict']['TP']['match']} match / {summary['nn_verdict_propagation']['by_gt_verdict']['TP']['mismatch']} mismatch.",
        f"  - FP queries: {summary['nn_verdict_propagation']['by_gt_verdict']['FP']['match']} match / {summary['nn_verdict_propagation']['by_gt_verdict']['FP']['mismatch']} mismatch.",
        f"- **AAOS category alignment**: {summary['aaos_category_alignment']['correct']}/{summary['aaos_category_alignment']['n']} = **{summary['aaos_category_alignment']['accuracy']*100:.1f}%**.",
        f"- **MASVS area match**: {summary['masvs_area_match']['correct']}/{summary['masvs_area_match']['n_evaluated']} = " +
        (f"**{summary['masvs_area_match']['accuracy']*100:.1f}%**." if summary['masvs_area_match']['accuracy'] is not None else "—"),
        "",
        "## AAOS alignment by category",
        "",
        "| Category | hit | total | accuracy |",
        "|---|---:|---:|---:|",
    ]
    for cat, v in sorted(summary["aaos_category_alignment"]["by_category"].items()):
        acc = v["accuracy"]
        acc_str = f"{acc*100:.1f}%" if acc is not None else "—"
        md.append(f"| {cat} | {v['hit']} | {v['total']} | {acc_str} |")
    md += [
        "",
        "## Per-finding rows (sample, first 15 of 47)",
        "",
        "| finding_id | gt_verdict | nn_id | nn_verdict | nn_match | aaos_cat (gt → top) | masvs_match |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows[:15]:
        md.append(
            f"| {r['finding_id']} | {r['gt_verdict']} | {r['nn_finding_id']} | "
            f"{r['nn_verdict']} | {'✓' if r['nn_verdict_match'] else '✗'} | "
            f"{r['gt_category']} → {r['aaos_top_category']} "
            f"{'✓' if r['aaos_category_match'] else '✗'} | "
            f"{'✓' if r['masvs_area_match'] else ('✗' if r['masvs_area_match'] is False else '—')} |"
        )
    md += [
        "",
        "## Implication",
        "",
        "- **NN propagation accuracy** measures the *intrinsic* RAG benefit: if it is high (≥0.8), the historical-finding collection is a strong calibration signal for Stage 1. If low, the embedding model is not separating TP/FP anti-patterns in this corpus.",
        "- **AAOS alignment** measures the *citation* benefit: high accuracy means RAG can populate the `aaos_section` field of Stage 1 finding deterministically, replacing manual AAOS mapping.",
        "- **Caveat — not a Stage-1-end-to-end measurement**: this is an intrinsic retrieval-quality measurement. A full prompted-LLM ablation (with/without injecting retrieved context into the Claude Code Stage 1 prompt) is a separate study left to v1.3 § 6.",
        "",
        f"Raw rows: `data/reports/rag_ablation.json` (n={n}).",
        "",
    ]
    (OUT_DIR / "rag_ablation.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote: data/reports/rag_ablation.{{md,json}}")
    print(f"NN verdict propagation: {summary['nn_verdict_propagation']['accuracy']*100:.1f}%")
    print(f"AAOS category alignment: {summary['aaos_category_alignment']['accuracy']*100:.1f}%")
    if summary['masvs_area_match']['accuracy'] is not None:
        print(f"MASVS area match: {summary['masvs_area_match']['accuracy']*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
