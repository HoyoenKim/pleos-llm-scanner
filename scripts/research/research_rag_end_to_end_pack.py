#!/usr/bin/env python
"""Build paired no-RAG / with-RAG judgment packages for manual LLM validation.

This script does not call any LLM API. It packages existing findings so a Codex
or Claude Code session can judge the same finding under two conditions:

- no_rag: finding evidence only
- with_rag: finding evidence + retrieved AAOS/MASVS/TARA/history context

Generated artifacts are local-only because they may contain PleOS evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
LABELS = ROOT / "data" / "ground_truth" / "combined_labels.json"
REPORTS_DIR = ROOT / "data" / "reports"
OUT_DIR = REPORTS_DIR / "rag_local" / "rag_end_to_end"
PROMPT_PATH = ROOT / "configs" / "prompts" / "rag_end_to_end_judge.md"
GT_VERDICT_RE = re.compile(r"(?im)^GT verdict:.*(?:\r?\n)?")

SAMPLE19_IDS = [
    "vc-5", "vc-6", "ssl-1", "ssl-2", "ssl-5", "ssl-6", "lmp-1", "lmp-2", "am-3", "amb-1",
    "vc-1", "vc-2", "vc-3", "vc-4", "vc-7",
    "usb-2", "ss-1", "am-4", "amb-4",
]


def load_labels() -> list[dict[str, Any]]:
    data = json.loads(LABELS.read_text(encoding="utf-8"))
    labels = data.get("labels", [])
    return labels


def load_report_findings() -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for path in REPORTS_DIR.glob("**/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or "results" not in data:
            continue
        apk = data.get("apk") or data.get("package")
        for class_result in data.get("results", []):
            cls = class_result.get("class")
            source_file = class_result.get("source_file")
            for finding in class_result.get("findings", []):
                fid = finding.get("id") or finding.get("finding_id")
                if not fid:
                    continue
                enriched = dict(finding)
                enriched.setdefault("apk", apk)
                enriched.setdefault("class", cls)
                enriched.setdefault("source_file", source_file)
                enriched.setdefault("report_file", str(path.relative_to(ROOT)))
                by_id[fid] = enriched
    return by_id


def make_query(label: dict[str, Any], finding: dict[str, Any]) -> str:
    parts = [
        f"Finding ID: {label.get('id')}",
        f"APK: {label.get('apk')}",
        f"Class: {label.get('class')}",
        f"Line: {label.get('line')}",
        f"Category: {label.get('stage1_category')}",
        f"Severity: {label.get('stage1_severity')}",
        f"Title: {finding.get('title', '')}",
        f"Evidence: {finding.get('evidence', '')[:800]}",
        f"Rationale: {finding.get('rationale', '')[:800]}",
    ]
    return "\n".join(p for p in parts if p.rsplit(":", 1)[-1].strip())


def retrieve_context(query: str, k: int) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from src.rag.retrieve import DEFAULT_COLLECTIONS, retrieve

    return retrieve(query=query, k=k, collections=list(DEFAULT_COLLECTIONS))


def redact_historical_document(document: str) -> str:
    """Remove explicit GT labels from historical examples before judgment."""
    return GT_VERDICT_RE.sub("", document)


def trim_retrieval(
    retrieved: dict[str, Any],
    max_chars: int,
    target_finding_id: str,
    k: int,
) -> dict[str, Any]:
    """Keep retrieval compact while preventing target-label leakage."""
    out = {
        "query": retrieved.get("query"),
        "k": k,
        "leakage_control": "target historical self-match removed; explicit label metadata redacted",
        "collections": {},
    }
    for name, payload in retrieved.get("collections", {}).items():
        hits = []
        for hit in payload.get("hits", []):
            metadata = dict(hit.get("metadata") or {})
            doc = hit.get("document") or ""
            if name == "finding_patterns_historical":
                if metadata.get("finding_id") == target_finding_id:
                    continue
                metadata.pop("is_real", None)
                metadata.pop("verdict", None)
                doc = redact_historical_document(doc)
            doc = doc[:max_chars]
            hits.append({
                "id": hit.get("id"),
                "distance": hit.get("distance"),
                "metadata": metadata,
                "document": doc,
            })
            if len(hits) >= k:
                break
        out["collections"][name] = {"hits": hits}
    return out


def build_case(label: dict[str, Any], finding: dict[str, Any], condition: str, k: int, max_chars: int) -> dict[str, Any]:
    fid = label["id"]
    case = {
        "finding_id": fid,
        "condition": condition,
        "apk": label.get("apk"),
        "class": label.get("class"),
        "line": label.get("line"),
        "stage1_category": label.get("stage1_category"),
        "stage1_severity": label.get("stage1_severity"),
        "title": finding.get("title", ""),
        "evidence": finding.get("evidence", ""),
        "rationale": finding.get("rationale", ""),
        "report_file": finding.get("report_file", ""),
    }
    if condition == "with_rag":
        query = make_query(label, finding)
        # Retrieve one extra hit so historical self-match removal still leaves
        # the requested top-k context in the common case.
        retrieved = retrieve_context(query, k=k + 1)
        case["retrieved_context"] = trim_retrieval(
            retrieved,
            max_chars=max_chars,
            target_finding_id=fid,
            k=k,
        )
    return case


def write_prompt_markdown(scope: str, condition: str, cases: list[dict[str, Any]]) -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    lines = [
        prompt.rstrip(),
        "",
        "---",
        "",
        f"# Input Package: {scope} / {condition}",
        "",
        "Return one JSON object following the schema above. Ground truth is intentionally omitted.",
        "",
        "```json",
        json.dumps({"scope": scope, "condition": condition, "findings": cases}, indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    (OUT_DIR / f"{scope}_{condition}_prompt.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["sample19", "full47"], default="sample19")
    ap.add_argument("--condition", choices=["no_rag", "with_rag", "both"], default="both")
    ap.add_argument("--k", type=int, default=3, help="top-k retrieval per collection")
    ap.add_argument("--max-context-chars", type=int, default=700, help="max chars per retrieved hit")
    ap.add_argument("--no-md", action="store_true", help="only write JSON packages")
    args = ap.parse_args()

    labels = load_labels()
    by_id = load_report_findings()
    selected_ids = SAMPLE19_IDS if args.scope == "sample19" else [lbl["id"] for lbl in labels]
    labels_by_id = {lbl["id"]: lbl for lbl in labels}

    missing = [fid for fid in selected_ids if fid not in labels_by_id]
    if missing:
        raise SystemExit(f"missing labels: {', '.join(missing)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conditions = ["no_rag", "with_rag"] if args.condition == "both" else [args.condition]

    template = {
        "scope": args.scope,
        "model": "<fill actual model/session>",
        "judgments": [
            {
                "finding_id": fid,
                "verdict": "<report|suppress>",
                "confidence": None,
                "severity": "<critical|high|medium|low|none>",
                "reason": "",
                "blocking_control": "unknown",
                "evidence_used": [],
            }
            for fid in selected_ids
        ],
    }

    for condition in conditions:
        cases = []
        for fid in selected_ids:
            label = labels_by_id[fid]
            finding = by_id.get(fid, {})
            cases.append(build_case(label, finding, condition, args.k, args.max_context_chars))

        package = {
            "schema_version": "rag_end_to_end_input_v0.1",
            "scope": args.scope,
            "condition": condition,
            "n": len(cases),
            "prompt": str(PROMPT_PATH.relative_to(ROOT)),
            "gt_hidden": True,
            "findings": cases,
        }
        out_json = OUT_DIR / f"{args.scope}_{condition}_input.json"
        out_json.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.no_md:
            write_prompt_markdown(args.scope, condition, cases)
        print(f"wrote {out_json.relative_to(ROOT)} ({len(cases)} findings)")

    for condition in conditions:
        t = dict(template)
        t["condition"] = condition
        (OUT_DIR / f"{args.scope}_{condition}_results_template.json").write_text(
            json.dumps(t, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
