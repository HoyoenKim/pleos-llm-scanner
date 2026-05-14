"""R2.c Codex multi-model cross-read preparation and aggregation.

This script keeps the existing Claude Code multi-perspective result as the
baseline and adds a separate Codex multi-model validation layer.

Outputs:
  data/reports/codex_multimodel/sample19_inputs.json
  data/reports/codex_multimodel/sample19_model_inputs.json
  data/reports/codex_multimodel/full47_inputs.json
  data/reports/codex_multimodel/full47_model_inputs.json
  data/reports/codex_multimodel_agreement.{md,json}
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "data" / "reports"
OUT_DIR = REPORTS / "codex_multimodel"
STAGE3 = REPORTS / "stage3_ensemble.json"
GT = ROOT / "data" / "ground_truth" / "combined_labels.json"
AGREEMENT_JSON = REPORTS / "codex_multimodel_agreement.json"
AGREEMENT_MD = REPORTS / "codex_multimodel_agreement.md"

KST = timezone(timedelta(hours=9))

REQUESTED_MODELS = ("gpt-5.5", "gpt-5.4", "gpt-5.3-codex")
FALLBACK_MODEL = "gpt-5.4-mini"

SAMPLE19_IDS = (
    "vc-5", "vc-6", "ssl-1", "ssl-2", "ssl-5",
    "ssl-6", "lmp-1", "lmp-2", "am-3", "amb-1",
    "vc-1", "vc-2", "vc-3", "vc-4", "vc-7",
    "usb-2", "ss-1", "am-4", "amb-4",
)

FP_CONTROL_IDS = {"usb-2", "ss-1", "am-4", "amb-4"}
ALLOWED_VERDICTS = {"report", "suppress"}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low", "none"}


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pct(num: float, den: float) -> float:
    return round(100.0 * num / den, 1) if den else 0.0


def safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def f1_score(precision: float, recall: float) -> float:
    return round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0


def cohens_kappa(a: list[int], b: list[int]) -> float:
    if len(a) != len(b):
        raise ValueError("kappa inputs must have equal length")
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    p_a1 = sum(a) / n
    p_b1 = sum(b) / n
    pe = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
    if math.isclose(pe, 1.0):
        return 1.0
    return round((po - pe) / (1 - pe), 4)


def load_sources() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    stage3 = read_json(STAGE3)
    gt = read_json(GT)
    findings = {row["id"]: row for row in stage3["results"]}
    labels = {row["id"]: row for row in gt["labels"]}
    missing_gt = sorted(set(findings) - set(labels))
    missing_stage3 = sorted(set(labels) - set(findings))
    if missing_gt or missing_stage3:
        raise SystemExit(
            f"stage3/GT mismatch: missing_gt={missing_gt}, missing_stage3={missing_stage3}"
        )
    return findings, labels


def compact_finding(fid: str, finding: dict[str, Any], label: dict[str, Any], *, include_gt: bool) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": fid,
        "apk": label.get("apk"),
        "class": finding.get("class") or label.get("class"),
        "line": finding.get("line") or label.get("line"),
        "category": finding.get("category") or label.get("stage1_category"),
        "stage1_severity": finding.get("stage1_severity") or label.get("stage1_severity"),
        "candidate_title": finding.get("title"),
        "candidate_evidence": finding.get("evidence"),
        "claude_baseline": {
            "model": "claude-opus-4-7",
            "strategy": "single-model multi-perspective consensus",
            "consensus_count": finding.get("consensus_count", 0),
            "consensus_class": finding.get("consensus_class"),
            "reported_ge2of3": int(finding.get("consensus_count", 0)) >= 2,
            "perspectives": finding.get("consensus_perspectives", []),
            "rationale_merged": finding.get("rationale_merged"),
        },
    }
    if include_gt:
        row["ground_truth_for_evaluation_only"] = {
            "is_real": bool(label.get("is_real")),
            "true_severity": label.get("true_severity"),
            "source": label.get("source"),
            "notes": label.get("notes"),
            "masvs": label.get("masvs"),
        }
    return row


def build_input_payload(scope: str, ids: list[str], *, include_gt: bool) -> dict[str, Any]:
    findings, labels = load_sources()
    unknown = [fid for fid in ids if fid not in findings]
    if unknown:
        raise SystemExit(f"unknown finding ids for {scope}: {unknown}")
    return {
        "schema_version": "codex-multimodel-input-v0.1",
        "generated_at": now_kst(),
        "scope": scope,
        "model_facing": not include_gt,
        "source_files": {
            "claude_baseline": "data/reports/stage3_ensemble.json",
            "ground_truth": "data/ground_truth/combined_labels.json",
        },
        "requested_models": list(REQUESTED_MODELS),
        "fallback_model": FALLBACK_MODEL,
        "verdict_rule": "report iff the candidate remains a concrete, security-relevant vulnerability; suppress blocked chains and defense-in-depth only notes.",
        "findings": [compact_finding(fid, findings[fid], labels[fid], include_gt=include_gt) for fid in ids],
    }


def prepare_inputs() -> None:
    findings, _labels = load_sources()
    full_ids = list(findings)
    write_json(OUT_DIR / "sample19_inputs.json", build_input_payload("sample19", list(SAMPLE19_IDS), include_gt=True))
    write_json(OUT_DIR / "sample19_model_inputs.json", build_input_payload("sample19", list(SAMPLE19_IDS), include_gt=False))
    write_json(OUT_DIR / "full47_inputs.json", build_input_payload("full47", full_ids, include_gt=True))
    write_json(OUT_DIR / "full47_model_inputs.json", build_input_payload("full47", full_ids, include_gt=False))


def normalize_slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "_").replace(" ", "_")


def output_path(scope: str, model: str) -> Path:
    return OUT_DIR / f"{scope}_{normalize_slug(model)}.json"


def validate_model_payload(path: Path, expected_ids: set[str], expected_scope: str) -> dict[str, Any]:
    payload = read_json(path)
    errors: list[str] = []
    if payload.get("schema_version") != "codex-multimodel-verdict-v0.1":
        errors.append("schema_version must be codex-multimodel-verdict-v0.1")
    if payload.get("scope") != expected_scope:
        errors.append(f"scope must be {expected_scope}")
    verdicts = payload.get("verdicts")
    if not isinstance(verdicts, list):
        errors.append("verdicts must be a list")
        verdicts = []
    seen: set[str] = set()
    for idx, item in enumerate(verdicts):
        fid = item.get("finding_id")
        if fid not in expected_ids:
            errors.append(f"verdicts[{idx}] unknown finding_id={fid}")
        if fid in seen:
            errors.append(f"duplicate finding_id={fid}")
        seen.add(fid)
        if item.get("verdict") not in ALLOWED_VERDICTS:
            errors.append(f"{fid}: verdict must be one of {sorted(ALLOWED_VERDICTS)}")
        if item.get("severity") not in ALLOWED_SEVERITIES:
            errors.append(f"{fid}: severity must be one of {sorted(ALLOWED_SEVERITIES)}")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            errors.append(f"{fid}: confidence must be number in [0,1]")
        if not item.get("reason"):
            errors.append(f"{fid}: reason is required")
    missing = sorted(expected_ids - seen)
    extra = sorted(seen - expected_ids)
    if missing:
        errors.append(f"missing verdict ids: {missing}")
    if extra:
        errors.append(f"extra verdict ids: {extra}")
    if errors:
        raise SystemExit(f"{path} failed validation:\n- " + "\n- ".join(errors))
    return payload


def confusion(flags: dict[str, bool], labels: dict[str, dict[str, Any]], ids: list[str]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for fid in ids:
        pred = bool(flags[fid])
        actual = bool(labels[fid]["is_real"])
        if pred and actual:
            tp += 1
        elif pred and not actual:
            fp += 1
        elif not pred and not actual:
            tn += 1
        else:
            fn += 1
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1_score(precision, recall),
        "report_rate": safe_div(tp + fp, len(ids)),
    }


def load_model_outputs(scope: str, models: tuple[str, ...]) -> list[dict[str, Any]]:
    ids = set(SAMPLE19_IDS) if scope == "sample19" else set(load_sources()[0].keys())
    outputs = []
    for model in models:
        path = output_path(scope, model)
        if not path.exists():
            raise SystemExit(f"missing model output: {path}")
        payload = validate_model_payload(path, ids, scope)
        payload["_path"] = str(path.relative_to(ROOT))
        outputs.append(payload)
    return outputs


def aggregate(scope: str, models: tuple[str, ...]) -> dict[str, Any]:
    findings, labels = load_sources()
    ids = list(SAMPLE19_IDS) if scope == "sample19" else list(findings)
    outputs = load_model_outputs(scope, models)

    claude_flags = {fid: int(findings[fid].get("consensus_count", 0)) >= 2 for fid in ids}
    model_flags: dict[str, dict[str, bool]] = {}
    model_metrics: dict[str, Any] = {}
    model_meta: list[dict[str, Any]] = []

    for payload in outputs:
        name = payload["model_actual"]
        flags = {item["finding_id"]: item["verdict"] == "report" for item in payload["verdicts"]}
        model_flags[name] = flags
        model_metrics[name] = confusion(flags, labels, ids)
        model_meta.append({
            "model_requested": payload.get("model_requested"),
            "model_actual": name,
            "source": payload.get("_path"),
            "generated_at": payload.get("generated_at"),
        })

    codex_consensus = {}
    codex_vote_count = {}
    for fid in ids:
        votes = sum(1 for name in model_flags if model_flags[name][fid])
        codex_vote_count[fid] = votes
        codex_consensus[fid] = votes >= 2

    claude_metrics = confusion(claude_flags, labels, ids)
    codex_metrics = confusion(codex_consensus, labels, ids)

    agreement = {}
    ordered_ids = ids
    claude_vec = [1 if claude_flags[fid] else 0 for fid in ordered_ids]
    codex_vec = [1 if codex_consensus[fid] else 0 for fid in ordered_ids]
    agreement["claude_vs_codex_consensus"] = {
        "agreement_count": sum(1 for a, b in zip(claude_vec, codex_vec) if a == b),
        "agreement_pct": pct(sum(1 for a, b in zip(claude_vec, codex_vec) if a == b), len(ids)),
        "cohens_kappa": cohens_kappa(claude_vec, codex_vec),
    }
    for name, flags in model_flags.items():
        vec = [1 if flags[fid] else 0 for fid in ordered_ids]
        agree = sum(1 for a, b in zip(claude_vec, vec) if a == b)
        agreement[f"claude_vs_{name}"] = {
            "agreement_count": agree,
            "agreement_pct": pct(agree, len(ids)),
            "cohens_kappa": cohens_kappa(claude_vec, vec),
        }

    rows = []
    buckets: dict[str, list[str]] = {
        "codex_suppressed_claude_fp": [],
        "codex_recovered_claude_fn": [],
        "codex_promoted_claude_filtered_fp": [],
        "both_missed_gt_tp": [],
        "both_reported_fp": [],
        "codex_model_disagreement": [],
    }
    for fid in ids:
        actual = bool(labels[fid]["is_real"])
        claude = claude_flags[fid]
        codex = codex_consensus[fid]
        votes = codex_vote_count[fid]
        row = {
            "id": fid,
            "apk": labels[fid].get("apk"),
            "gt_is_real": actual,
            "claude_report": claude,
            "codex_votes_report": votes,
            "codex_consensus_report": codex,
            "model_votes": {name: model_flags[name][fid] for name in sorted(model_flags)},
        }
        rows.append(row)
        if claude and not codex and not actual:
            buckets["codex_suppressed_claude_fp"].append(fid)
        if not claude and codex and actual:
            buckets["codex_recovered_claude_fn"].append(fid)
        if not claude and codex and not actual:
            buckets["codex_promoted_claude_filtered_fp"].append(fid)
        if not claude and not codex and actual:
            buckets["both_missed_gt_tp"].append(fid)
        if claude and codex and not actual:
            buckets["both_reported_fp"].append(fid)
        if votes not in (0, len(model_flags)):
            buckets["codex_model_disagreement"].append(fid)

    acceptance = None
    if scope == "sample19":
        output_valid = len(outputs) == 3
        universal_flag = {
            name: metrics["report_rate"] > 0.90
            for name, metrics in model_metrics.items()
        }
        fp_control_suppressed = {
            fid: {
                name: not model_flags[name][fid]
                for name in sorted(model_flags)
            }
            for fid in sorted(FP_CONTROL_IDS)
        }
        any_fp_control_suppressed = any(any(v.values()) for v in fp_control_suppressed.values())
        any_model_difference = any(codex_vote_count[fid] not in (0, len(model_flags)) for fid in ids)
        acceptance = {
            "schema_validation_passed": output_valid,
            "no_universal_flag_model": not any(universal_flag.values()),
            "universal_flag_by_model": universal_flag,
            "fp_control_suppressed_by_any_model": any_fp_control_suppressed,
            "fp_control_suppressed": fp_control_suppressed,
            "model_difference_observed": any_model_difference,
            "full47_ready": output_valid and not any(universal_flag.values()) and any_fp_control_suppressed,
        }

    payload = {
        "schema_version": "codex-multimodel-agreement-v0.1",
        "generated_at": now_kst(),
        "scope": scope,
        "source_files": {
            "claude_baseline": "data/reports/stage3_ensemble.json",
            "ground_truth": "data/ground_truth/combined_labels.json",
            "model_outputs": [item["_path"] for item in outputs],
        },
        "models": model_meta,
        "metrics": {
            "claude_code_consensus": claude_metrics,
            "codex_models": model_metrics,
            "codex_2of3_consensus": codex_metrics,
        },
        "agreement": agreement,
        "codex_vote_distribution": dict(sorted(Counter(codex_vote_count.values()).items())),
        "discordance_buckets": buckets,
        "rows": rows,
        "sample19_acceptance": acceptance,
        "interpretation": choose_interpretation(claude_metrics, codex_metrics),
    }
    return payload


def choose_interpretation(claude_metrics: dict[str, Any], codex_metrics: dict[str, Any]) -> str:
    if codex_metrics["f1"] >= claude_metrics["f1"] - 0.01 and codex_metrics["precision"] >= claude_metrics["precision"]:
        return "Claude Code 결과의 Codex 교차 모델 재현성 확보"
    return "multi-model 자체보다 prompt calibration과 evidence packaging이 더 중요함"


def format_metric_row(name: str, metric: dict[str, Any]) -> str:
    return (
        f"| {name} | {metric['tp']} | {metric['fp']} | {metric['tn']} | {metric['fn']} | "
        f"{metric['precision']:.3f} | {metric['recall']:.3f} | {metric['f1']:.3f} | "
        f"{pct(metric['tp'] + metric['fp'], metric['tp'] + metric['fp'] + metric['tn'] + metric['fn']):.1f}% |"
    )


def markdown_for_payload(payload: dict[str, Any]) -> str:
    scope = payload["scope"]
    metrics = payload["metrics"]
    lines = [
        "# R2.c Codex multi-model cross-read",
        "",
        f"_Generated: {payload['generated_at']} / scope: `{scope}`_",
        "",
        "## Bottom line",
        "",
        f"**{payload['interpretation']}**.",
        "",
        "The Claude Code baseline is preserved as a single-model multi-perspective result. "
        "This artifact adds a separate Codex 3-model cross-read layer and compares both against the same GT labels.",
        "",
        "## Metrics",
        "",
        "| System | TP | FP | TN | FN | Precision | Recall | F1 | Report rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        format_metric_row("Claude Code consensus (>=2/3)", metrics["claude_code_consensus"]),
    ]
    for name in sorted(metrics["codex_models"]):
        lines.append(format_metric_row(f"Codex {name}", metrics["codex_models"][name]))
    lines.append(format_metric_row("Codex 2/3 consensus", metrics["codex_2of3_consensus"]))

    lines += [
        "",
        "## Claude vs Codex agreement",
        "",
        "| Pair | Agreement | Cohen's kappa |",
        "|---|---:|---:|",
    ]
    for pair, stat in payload["agreement"].items():
        lines.append(f"| {pair} | {stat['agreement_count']} ({stat['agreement_pct']}%) | {stat['cohens_kappa']:.3f} |")

    lines += [
        "",
        "## Codex vote distribution",
        "",
        "| Codex report votes | Findings |",
        "|---:|---:|",
    ]
    for votes, count in payload["codex_vote_distribution"].items():
        lines.append(f"| {votes}/3 | {count} |")

    lines += [
        "",
        "## Discordance buckets",
        "",
        "| Bucket | IDs |",
        "|---|---|",
    ]
    for bucket, ids in payload["discordance_buckets"].items():
        lines.append(f"| {bucket} | {', '.join(ids) if ids else '-'} |")

    acceptance = payload.get("sample19_acceptance")
    if acceptance:
        lines += [
            "",
            "## Sample19 acceptance",
            "",
            "| Criterion | Result |",
            "|---|---|",
            f"| Schema validation passed | {acceptance['schema_validation_passed']} |",
            f"| No universal-flag model | {acceptance['no_universal_flag_model']} |",
            f"| FP control suppressed by any model | {acceptance['fp_control_suppressed_by_any_model']} |",
            f"| Model difference observed | {acceptance['model_difference_observed']} |",
            f"| Full47 ready | **{acceptance['full47_ready']}** |",
        ]

    lines += [
        "",
        "## Per-finding table",
        "",
        "| ID | APK | GT real | Claude report | Codex votes | Codex report |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['id']} | {row['apk']} | {row['gt_is_real']} | {row['claude_report']} | "
            f"{row['codex_votes_report']}/3 | {row['codex_consensus_report']} |"
        )

    return "\n".join(lines) + "\n"


def run_aggregate(scope: str, models: tuple[str, ...]) -> None:
    payload = aggregate(scope, models)
    scoped_json = OUT_DIR / f"{scope}_agreement.json"
    scoped_md = OUT_DIR / f"{scope}_agreement.md"
    markdown = markdown_for_payload(payload)
    write_json(scoped_json, payload)
    scoped_md.write_text(markdown, encoding="utf-8")

    # Keep the latest aggregate at the historical top-level path expected by docs.
    write_json(AGREEMENT_JSON, payload)
    AGREEMENT_MD.write_text(markdown, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true", help="write model/evaluation input manifests")
    parser.add_argument("--aggregate", choices=["sample19", "full47"], help="aggregate existing model outputs")
    parser.add_argument("--models", nargs="*", default=list(REQUESTED_MODELS), help="model slugs to aggregate")
    args = parser.parse_args()

    if args.prepare:
        prepare_inputs()
        print("wrote codex_multimodel input manifests")
    if args.aggregate:
        run_aggregate(args.aggregate, tuple(args.models))
        print(f"wrote {AGREEMENT_JSON.relative_to(ROOT)} and {AGREEMENT_MD.relative_to(ROOT)}")
    if not args.prepare and not args.aggregate:
        parser.print_help()


if __name__ == "__main__":
    main()
