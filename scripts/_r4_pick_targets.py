"""Pick NewPipe business-package HIGH-obfuscation classes for R4 Stage 0 sample."""
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "data" / "deobf" / "NewPipe.json").read_text(encoding="utf-8"))

NEEDLE = "org/schabi/newpipe"


def is_business(r):
    p = r["file_path"].replace("\\", "/").lower()
    return NEEDLE in p


business = [r for r in d["results"] if is_business(r)]
print(f"NewPipe business (org.schabi.newpipe.*) classes: {len(business)}")

high = sorted(
    [r for r in business if r["composite_obf_score"] >= 0.5],
    key=lambda r: -r["composite_obf_score"],
)[:15]
print(f"top 15 HIGH composite (>=0.5):")
for r in high:
    p = r["file_path"].replace("\\", "/")
    short = p[p.find(NEEDLE):]
    print(f"  {r['composite_obf_score']:.3f}  jadx={r['jadx_obf_ratio']:.2f}  "
          f"{r['class_name']}  ({r['n_total_ids']} ids)  {short}")
print()
print(f"Top 5 sample for R4:")
for r in high[:5]:
    p = r["file_path"].replace("\\", "/")
    print(f"  - {r['class_name']}  ({r['n_total_ids']} ids, composite {r['composite_obf_score']:.3f})")
    print(f"    path: {p}")
    print(f"    sample ids: {r['sample_obf_ids'][:8]}")
