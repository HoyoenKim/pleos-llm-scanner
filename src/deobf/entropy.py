#!/usr/bin/env python
"""
Shannon-entropy based obfuscation detector for jadx-decompiled Java sources.

Per-identifier metrics
----------------------
- length        : char count
- entropy_bits  : -Σ p(c) log2 p(c) over the identifier's char distribution
- pattern_class : 'jadx_short_obf' | 'jadx_long_obf' | 'short_lc' | 'normal'
- score         : composite [0, 1] — higher = more likely obfuscated

Per-class metrics (one line per .java file)
-------------------------------------------
- file_path
- class_name
- n_methods, n_fields
- mean_id_len, mean_id_entropy
- jadx_obf_ratio = (jadx_*_obf identifiers) / total identifiers
- short_lc_ratio = (length ≤ 2 lowercase identifiers) / total
- composite_obf_score [0, 1]

Heuristics (calibrated against jadx --deobf output for ProGuard'd APKs)
----------------------------------------------------------------------
- jadx renames `a`/`b`/`c`/.../`aa`/... to `Cnnnna` / `Cnnnnb` / ... (e.g. `C0000a`, `C0014b`).
- mNNNNa / mNNNNb 패턴 = 메서드. fNNNNa = 필드.
- Shannon entropy of randomly-chosen alphanumeric strings is ~5 bits/char; semantic English ≈ 4.0 bits.
- Identifier length ≤ 3 + lowercase alphanumeric → very likely obfuscated.

Usage
-----
    python src/deobf/entropy.py <decompiled_root> [--out output.json] [--md output.md]
    python src/deobf/entropy.py data/decompiled/UnCrackable-Level1 --out data/deobf/ucl1.json --md data/deobf/ucl1.md
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# JADX deobfuscated obfuscation patterns
JADX_SHORT_OBF = re.compile(r'^C[0-9]{4}[a-z]$')        # e.g. C0014b, C0000a
JADX_LONG_OBF = re.compile(r'^C[0-9]{4,}[a-zA-Z]+$')    # e.g. C00056ViewOnClickListener (jadx prefix + chunk)
JADX_METHOD_OBF = re.compile(r'^m[0-9]{1,5}[a-z]$')     # e.g. m2178a, m5a
JADX_FIELD_OBF = re.compile(r'^f[0-9]{1,5}[a-z]?$')     # e.g. f508, f509
SHORT_LC = re.compile(r'^[a-z]{1,2}$')                  # `a`, `bb`, `it`, etc.
NORMAL_CAMEL = re.compile(r'^[a-z][a-zA-Z0-9_]{3,}$')   # at least 4 chars, lowerCamel


@dataclass
class IdentifierMetric:
    name: str
    kind: str  # "class" | "method" | "field" | "param"
    length: int
    entropy_bits: float
    pattern_class: str  # "jadx_short_obf" | "jadx_long_obf" | "short_lc" | "normal"
    score: float


@dataclass
class ClassMetric:
    file_path: str
    class_name: str
    n_methods: int
    n_fields: int
    n_total_ids: int
    mean_id_len: float
    mean_id_entropy: float
    jadx_obf_ratio: float
    short_lc_ratio: float
    composite_obf_score: float
    sample_obf_ids: list[str] = field(default_factory=list)


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def classify_identifier(name: str) -> str:
    if JADX_SHORT_OBF.fullmatch(name):
        return "jadx_short_obf"
    if JADX_LONG_OBF.fullmatch(name):
        return "jadx_long_obf"
    if JADX_METHOD_OBF.fullmatch(name):
        return "jadx_short_obf"  # methods grouped with class-level for ratio
    if JADX_FIELD_OBF.fullmatch(name):
        return "jadx_short_obf"
    if SHORT_LC.fullmatch(name):
        return "short_lc"
    return "normal"


def identifier_score(name: str, pattern_class: str) -> float:
    """Composite obfuscation score for one identifier, in [0, 1]."""
    if pattern_class == "jadx_short_obf":
        return 0.95
    if pattern_class == "jadx_long_obf":
        return 0.55
    if pattern_class == "short_lc":
        return 0.50  # `it`/`ex` are common idioms, not always obfuscation
    # `normal` — penalise extremely short or extremely high-entropy
    length_factor = max(0.0, 1.0 - len(name) / 8.0) if len(name) <= 8 else 0.0
    entropy = shannon_entropy(name)
    # English-like text ≈ 4 bits/char; random ASCII alnum ≈ 5+
    entropy_factor = max(0.0, (entropy - 3.5) / 2.5)
    return min(0.4, 0.6 * length_factor + 0.4 * entropy_factor)


# -- Java source extraction (regex-based; no AST library) -------------------

CLASS_DECL = re.compile(
    r'\b(?:public|private|protected|static|final|abstract|/\*[^*]*\*/\s*)*\s*'
    r'(?:class|interface|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)\b'
)
METHOD_DECL = re.compile(
    r'\b(?:public|private|protected|static|final|abstract|synchronized|native)\s+'
    r'(?:[\w<>\[\],\s$.]+?)\s+'
    r'([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*[{;]'
)
FIELD_DECL = re.compile(
    r'^\s*(?:private|public|protected|static|final|volatile|transient)\s+'
    r'(?:[\w<>\[\],\s$.]+?)\s+'
    r'([A-Za-z_$][A-Za-z0-9_$]*)\s*[=;]',
    re.MULTILINE,
)


def extract_class_name(text: str) -> str:
    m = CLASS_DECL.search(text)
    return m.group(1) if m else "<unknown>"


def extract_identifiers(text: str) -> tuple[list[str], list[str]]:
    methods = METHOD_DECL.findall(text)
    fields = FIELD_DECL.findall(text)
    # Filter out obvious noise
    methods = [m for m in methods if m not in {"if", "for", "while", "switch", "return", "synchronized"}]
    return methods, fields


def analyze_file(path: Path) -> ClassMetric | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    if not text.strip():
        return None

    class_name = extract_class_name(text)
    methods, fields = extract_identifiers(text)
    all_ids = [class_name] + methods + fields

    if not all_ids:
        return None

    metrics: list[IdentifierMetric] = []
    for nm in all_ids:
        cls = classify_identifier(nm)
        metrics.append(
            IdentifierMetric(
                name=nm,
                kind="class" if nm == class_name else ("method" if nm in methods else "field"),
                length=len(nm),
                entropy_bits=round(shannon_entropy(nm), 3),
                pattern_class=cls,
                score=round(identifier_score(nm, cls), 3),
            )
        )

    n_total = len(metrics)
    obf_metrics = [m for m in metrics if m.pattern_class.startswith("jadx_")]
    short_lc_metrics = [m for m in metrics if m.pattern_class == "short_lc"]

    jadx_ratio = len(obf_metrics) / n_total
    short_lc_ratio = len(short_lc_metrics) / n_total

    # Class-level composite score = weighted mean of identifier scores,
    # but heavily emphasise the class identifier itself (it’s the public face).
    class_id_score = next((m.score for m in metrics if m.kind == "class"), 0.0)
    other_mean = (
        sum(m.score for m in metrics if m.kind != "class") / max(1, n_total - 1)
        if n_total > 1
        else 0.0
    )
    composite = round(0.5 * class_id_score + 0.5 * other_mean, 3)

    return ClassMetric(
        file_path=str(path),
        class_name=class_name,
        n_methods=len(methods),
        n_fields=len(fields),
        n_total_ids=n_total,
        mean_id_len=round(sum(m.length for m in metrics) / n_total, 2),
        mean_id_entropy=round(sum(m.entropy_bits for m in metrics) / n_total, 3),
        jadx_obf_ratio=round(jadx_ratio, 3),
        short_lc_ratio=round(short_lc_ratio, 3),
        composite_obf_score=composite,
        sample_obf_ids=[m.name for m in metrics if m.pattern_class.startswith("jadx_")][:5],
    )


def run(root: Path) -> list[ClassMetric]:
    results: list[ClassMetric] = []
    for java_file in root.rglob("*.java"):
        # Skip framework / library noise (heavy androidx / google / kotlin code)
        rel = java_file.relative_to(root).as_posix() if root in java_file.parents or root == java_file.parent else java_file.as_posix()
        if any(seg in rel for seg in (
            "androidx/",
            "android/arch/",  # legacy lifecycle library
            "android/support/",
            "com/google/",
            "com/squareup/",
            "com/scottyab/rootbeer/",  # 3rd party utility (UnCrackable-/r2pay-detected)
            "kotlin/",
            "kotlinx/",
            "okhttp3/",
            "okio/",
            "retrofit2/",
            "io/reactivex/",
            "rx/",
            "dagger/",
            "javax/inject/",
            "/p000/",  # jadx compat package for unobfuscated framework
        )):
            continue
        m = analyze_file(java_file)
        if m is not None:
            results.append(m)
    return results


def summarise(results: list[ClassMetric]) -> dict[str, Any]:
    if not results:
        return {"n": 0}
    n = len(results)
    high = [r for r in results if r.composite_obf_score >= 0.7]
    medium = [r for r in results if 0.4 <= r.composite_obf_score < 0.7]
    low = [r for r in results if r.composite_obf_score < 0.4]
    return {
        "n_classes": n,
        "high_obf": len(high),
        "medium_obf": len(medium),
        "low_obf": len(low),
        "high_obf_ratio": round(len(high) / n, 3),
        "mean_composite": round(sum(r.composite_obf_score for r in results) / n, 3),
        "mean_jadx_ratio": round(sum(r.jadx_obf_ratio for r in results) / n, 3),
    }


def md_table(results: list[ClassMetric], top_k: int = 30) -> str:
    sorted_r = sorted(results, key=lambda r: -r.composite_obf_score)[:top_k]
    out = [
        "| rank | class | composite | jadx_ratio | short_lc | mean_len | mean_H | n_ids | sample |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for i, r in enumerate(sorted_r, start=1):
        sample = ", ".join(r.sample_obf_ids) or "—"
        out.append(
            f"| {i} | `{r.class_name}` | {r.composite_obf_score:.3f} | "
            f"{r.jadx_obf_ratio:.2f} | {r.short_lc_ratio:.2f} | "
            f"{r.mean_id_len:.1f} | {r.mean_id_entropy:.2f} | {r.n_total_ids} | {sample} |"
        )
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("root", help="Decompiled root (e.g. data/decompiled/UnCrackable-Level1)")
    p.add_argument("--out", help="Output JSON path", default=None)
    p.add_argument("--md", help="Output Markdown path", default=None)
    p.add_argument("--top", type=int, default=30, help="Top-k classes to include in markdown table")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"error: {root} does not exist", file=sys.stderr)
        return 1

    results = run(root)
    summary = summarise(results)

    print(f"# {root.name}: {summary['n_classes']} non-framework classes")
    print(f"  HIGH (≥0.7) : {summary['high_obf']:>4}  ({summary['high_obf_ratio'] * 100:.1f}%)")
    print(f"  MEDIUM      : {summary['medium_obf']:>4}")
    print(f"  LOW         : {summary['low_obf']:>4}")
    print(f"  mean composite: {summary['mean_composite']}")
    print(f"  mean jadx_obf_ratio: {summary['mean_jadx_ratio']}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(
                {"root": str(root), "summary": summary, "results": [asdict(r) for r in results]},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"\nWrote JSON: {args.out}")

    if args.md:
        Path(args.md).parent.mkdir(parents=True, exist_ok=True)
        body = (
            f"# Obfuscation entropy — {root.name}\n\n"
            f"## Summary\n\n"
            f"- Total non-framework classes: **{summary['n_classes']}**\n"
            f"- HIGH (composite ≥ 0.7): **{summary['high_obf']}** ({summary['high_obf_ratio'] * 100:.1f}%)\n"
            f"- MEDIUM (0.4–0.7): {summary['medium_obf']}\n"
            f"- LOW (< 0.4): {summary['low_obf']}\n"
            f"- Mean composite score: {summary['mean_composite']}\n"
            f"- Mean jadx_obf_ratio: {summary['mean_jadx_ratio']}\n\n"
            f"## Top {args.top} most obfuscated classes\n\n"
            + md_table(results, args.top)
        )
        Path(args.md).write_text(body, encoding="utf-8")
        print(f"Wrote Markdown: {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
