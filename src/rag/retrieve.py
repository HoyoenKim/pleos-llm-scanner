#!/usr/bin/env python
"""Retrieve top-k chunks per collection for a Stage 1 prompt query.

Usage:
    python src/rag/retrieve.py --query "WebView setJavaScriptEnabled exported activity" \
                               [--k 3] [--collections aaos_guidelines,masvs_controls,...] \
                               [--json]

By default queries all four collections, k=3 each. Output is a structured retrieval
record that the Stage 1 prompt can inline as context.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows (cp949 default chokes on em-dashes / korean).
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
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_COLLECTIONS = (
    "aaos_guidelines",
    "masvs_controls",
    "tara_templates",
    "finding_patterns_historical",
)


def retrieve(query: str, k: int, collections: list[str]) -> dict:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    out: dict = {"query": query, "k": k, "collections": {}}
    for name in collections:
        try:
            coll = client.get_collection(name=name, embedding_function=ef)
        except Exception as e:
            out["collections"][name] = {"error": str(e), "hits": []}
            continue
        res = coll.query(query_texts=[query], n_results=k)
        hits = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for i, _id in enumerate(ids):
            hits.append({
                "id": _id,
                "distance": dists[i] if i < len(dists) else None,
                "metadata": metas[i] if i < len(metas) else {},
                "document": docs[i] if i < len(docs) else "",
            })
        out["collections"][name] = {"hits": hits}
    return out


def format_for_prompt(retrieved: dict, max_chars_per_hit: int = 500) -> str:
    """Render retrieval into a single prompt-friendly markdown block."""
    lines = ["## Retrieved domain context\n"]
    for name, payload in retrieved["collections"].items():
        if "error" in payload:
            continue
        hits = payload.get("hits", [])
        if not hits:
            continue
        lines.append(f"### {name}")
        for h in hits:
            md = h.get("metadata") or {}
            tag = md.get("category") or md.get("section_title") or md.get("finding_id") or md.get("source") or h.get("id")
            doc = (h.get("document") or "")[:max_chars_per_hit].replace("\n", " ")
            lines.append(f"- **{tag}**  (dist {h.get('distance'):.3f})\n  {doc}…")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Stage 1 prompt query text (code snippet / finding hypothesis)")
    ap.add_argument("--k", type=int, default=3, help="Top-k per collection (default 3)")
    ap.add_argument("--collections", default=",".join(DEFAULT_COLLECTIONS),
                    help="Comma-separated collection names")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of prompt-formatted markdown")
    args = ap.parse_args()

    colls = [c.strip() for c in args.collections.split(",") if c.strip()]
    res = retrieve(args.query, args.k, colls)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(format_for_prompt(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
