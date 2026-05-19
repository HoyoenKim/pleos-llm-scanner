#!/usr/bin/env python
"""Build Chroma vector index for RAG-enhanced Stage 1 prompt.

Four collections (docs/06 § 4.1 schema):
- aaos_guidelines:           AAOS § 매핑 (configs/aaos_mapping.yaml)
- masvs_controls:            OWASP MASTG Document/*.md per-section chunks
- tara_templates:            TARA artifact (data/reports/aggregate/tara_artifact*.{md,json}) + aaos_mapping tara fields
- finding_patterns_historical: combined GT findings + reports rationale (n=47, R1.d.5 포함)

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (22M params, CPU推論, 영어 corpus).
Persistence: data/_local/rag_db/chroma/ (deterministic, local-only).

Environment policy: no external embedding API. Hugging Face download is one-shot
to local cache (~/.cache/huggingface/), then offline inference.

Usage:
    python src/rag/build_index.py [--reset] [--limit-mastg N]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("error: chromadb not installed. Run: pip install chromadb sentence-transformers", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = ROOT / "data" / "_local" / "rag_db" / "chroma"
AAOS_YAML = ROOT / "configs" / "aaos_mapping.yaml"
MASTG_DIR = ROOT / "data" / "_local" / "apks" / "_mastg" / "owasp-mastg" / "Document"
TARA_GLOB = str(ROOT / "data" / "reports" / "aggregate" / "tara_artifact*.md")
LABELS = ROOT / "data" / "ground_truth" / "combined_labels.json"
REPORTS_GLOB = str(ROOT / "data" / "reports" / "**" / "*.json")

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def short_id(text: str, prefix: str) -> str:
    """Deterministic id for chunk dedup across rebuilds."""
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{h}"


# ----- collection 1: aaos_guidelines ----------------------------------------

def load_aaos_guidelines() -> list[dict[str, Any]]:
    data = yaml.safe_load(AAOS_YAML.read_text(encoding="utf-8"))
    out = []
    for category, info in data.get("mappings", {}).items():
        text = (
            f"AAOS Section: {info.get('aaos_section', '')}\n"
            f"Category: {category}\n"
            f"Description: {info.get('description', '')}\n"
            f"Related findings:\n"
            + "\n".join(f"- {x}" for x in info.get("related_findings", []))
            + f"\nTARA threat class: {info.get('tara_threat_class', '')}\n"
            f"TARA impact: {info.get('tara_impact', '')}"
        )
        out.append({
            "id": short_id(text, f"aaos_{category}"),
            "document": text,
            "metadata": {
                "category": category,
                "aaos_section": info.get("aaos_section", ""),
                "masvs_categories": ",".join(info.get("masvs_categories", [])),
                "aaos_url": info.get("aaos_url", ""),
            },
        })
    return out


# ----- collection 2: masvs_controls -----------------------------------------

SECTION_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def parse_mastg_doc(md_path: Path) -> list[dict[str, Any]]:
    """Chunk MASTG doc by top-level H2 sections (## ... ). Keep YAML front-matter masvs_category."""
    raw = md_path.read_text(encoding="utf-8", errors="ignore")
    fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if fm_match:
        try:
            front = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            front = {}
        body = fm_match.group(2)
    else:
        front, body = {}, raw

    masvs_cat = (front.get("masvs_category") or "").strip()
    platform = (front.get("platform") or "").strip()

    chunks = []
    # split by H2 (## ...) — coarse enough for retrieval, keeps semantic boundary
    parts = re.split(r"\n## ", body)
    title = md_path.stem
    for i, part in enumerate(parts):
        if i == 0:
            content = part.strip()
            section_title = title
        else:
            split = part.split("\n", 1)
            section_title = split[0].strip()
            content = (split[1] if len(split) > 1 else "").strip()
        if len(content) < 100:  # skip stubs
            continue
        # cap chunk to ~2000 chars to keep retrieval focused
        text = f"# {title} — {section_title}\n\n{content[:2000]}"
        chunks.append({
            "id": short_id(text, f"masvs_{md_path.stem}_{i}"),
            "document": text,
            "metadata": {
                "source_file": md_path.name,
                "masvs_category": masvs_cat,
                "platform": platform,
                "section_title": section_title,
                "chunk_index": i,
            },
        })
    return chunks


def load_masvs_controls(limit: int | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    files = sorted(MASTG_DIR.glob("0x0*.md"))  # Document chapters, skip CHANGELOG/SUMMARY
    if limit:
        files = files[:limit]
    for p in files:
        out.extend(parse_mastg_doc(p))
    return out


# ----- collection 3: tara_templates -----------------------------------------

def load_tara_templates() -> list[dict[str, Any]]:
    out = []
    # aaos_mapping yaml's tara fields → per-category template
    data = yaml.safe_load(AAOS_YAML.read_text(encoding="utf-8"))
    for category, info in data.get("mappings", {}).items():
        text = (
            f"TARA template — category: {category}\n"
            f"Threat class (STRIDE): {info.get('tara_threat_class', '')}\n"
            f"Impact: {info.get('tara_impact', '')}\n"
            f"AAOS link: {info.get('aaos_section', '')}\n"
            f"Treatment defaults: Mitigate (default), Avoid (high asset), Accept (low feasibility)"
        )
        out.append({
            "id": short_id(text, f"tara_yaml_{category}"),
            "document": text,
            "metadata": {
                "source": "aaos_mapping.yaml",
                "category": category,
                "stride": info.get("tara_threat_class", ""),
            },
        })
    # tara_artifact reports (markdown) — section chunks
    for p in glob.glob(TARA_GLOB):
        raw = Path(p).read_text(encoding="utf-8", errors="ignore")
        parts = re.split(r"\n## ", raw)
        for i, part in enumerate(parts):
            if len(part) < 200:
                continue
            text = ("## " if i > 0 else "") + part[:2000]
            out.append({
                "id": short_id(text, f"tara_md_{Path(p).stem}_{i}"),
                "document": text,
                "metadata": {
                    "source": Path(p).name,
                    "chunk_index": i,
                },
            })
    return out


# ----- collection 4: finding_patterns_historical ----------------------------

def load_finding_patterns() -> list[dict[str, Any]]:
    """One document per GT finding, enriched with rationale from matching report."""
    labels = json.loads(LABELS.read_text(encoding="utf-8"))

    # index reports by (apk, class, line) for cross-lookup
    finding_idx: dict[tuple[str, str, int], dict[str, Any]] = {}
    for rp in glob.glob(REPORTS_GLOB, recursive=True):
        try:
            r = json.loads(Path(rp).read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(r, dict) or "apk" not in r or "results" not in r:
            continue
        apk = r.get("apk")
        for cr in r.get("results", []):
            cls = cr.get("class")
            for f in cr.get("findings", []):
                try:
                    key = (apk, cls, int(f["line"]))
                except (KeyError, TypeError, ValueError):
                    continue
                finding_idx[key] = f

    out = []
    for lbl in labels.get("labels", []):
        try:
            key = (lbl["apk"], lbl["class"], int(lbl["line"]))
        except (KeyError, TypeError, ValueError):
            continue
        rpt = finding_idx.get(key, {})
        verdict = "TP" if lbl.get("is_real") is True else (
            "FP" if lbl.get("is_real") is False else "uncertain"
        )
        text = (
            f"Finding ID: {lbl['id']}\n"
            f"APK: {lbl['apk']}\n"
            f"Class: {lbl['class']}:{lbl['line']}\n"
            f"Category: {lbl.get('stage1_category', rpt.get('category', ''))}\n"
            f"Stage 1 severity: {lbl.get('stage1_severity', rpt.get('severity', ''))}\n"
            f"GT verdict: {verdict} (true_severity: {lbl.get('true_severity', '')})\n"
            f"Title: {rpt.get('title', '')}\n"
            f"Evidence: {rpt.get('evidence', '')[:600]}\n"
            f"Rationale: {rpt.get('rationale', lbl.get('notes', ''))[:800]}"
        )
        out.append({
            "id": short_id(text, f"hist_{lbl['id']}"),
            "document": text,
            "metadata": {
                "finding_id": lbl["id"],
                "apk": lbl["apk"],
                "category": lbl.get("stage1_category", rpt.get("category", "")),
                "is_real": str(lbl.get("is_real")),
                "verdict": verdict,
                "source": lbl.get("source", ""),
            },
        })
    return out


# ----- driver ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="Drop and rebuild all collections")
    ap.add_argument("--limit-mastg", type=int, default=None, help="Limit MASTG doc count (debug)")
    args = ap.parse_args()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

    if args.reset:
        for name in ("aaos_guidelines", "masvs_controls", "tara_templates", "finding_patterns_historical"):
            try:
                client.delete_collection(name)
                print(f"  dropped: {name}")
            except Exception:
                pass

    plans = [
        ("aaos_guidelines", load_aaos_guidelines()),
        ("masvs_controls", load_masvs_controls(args.limit_mastg)),
        ("tara_templates", load_tara_templates()),
        ("finding_patterns_historical", load_finding_patterns()),
    ]

    for name, docs in plans:
        if not docs:
            print(f"  skip (empty): {name}")
            continue
        coll = client.get_or_create_collection(name=name, embedding_function=ef)
        ids = [d["id"] for d in docs]
        documents = [d["document"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        # add in batches of 64 to keep memory bounded on CPU
        BATCH = 64
        added = 0
        for i in range(0, len(ids), BATCH):
            coll.upsert(
                ids=ids[i:i + BATCH],
                documents=documents[i:i + BATCH],
                metadatas=metadatas[i:i + BATCH],
            )
            added += len(ids[i:i + BATCH])
        print(f"  {name:<32} {added:>4} chunks  (total in coll: {coll.count()})")

    print(f"\npersisted at: {CHROMA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
