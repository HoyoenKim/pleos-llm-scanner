"""R3.a — count native (.so) entries across all extracted APKs.

Reproducibility: deterministic. No LLM calls.
Outputs:
  data/reports/native_lib_inventory.md
  data/reports/native_lib_inventory.json
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APKS = ROOT / "data" / "apks"
OUT = ROOT / "data" / "reports"


def classify(name: str) -> str:
    if name.startswith("ai.umos.") or name.startswith("ai.pleos."):
        return "PleOS"
    if name.startswith("com.android.") or name.startswith("android.") or name.startswith("com.google."):
        return "AOSP"
    return "third-party"


def count_so(apk: Path) -> int:
    try:
        with zipfile.ZipFile(apk) as zf:
            return sum(1 for n in zf.namelist() if n.endswith(".so"))
    except zipfile.BadZipFile:
        return 0


def main() -> None:
    rows = []
    for apk in sorted(APKS.glob("*.apk")):
        name = apk.stem
        rows.append({"apk": name, "so_count": count_so(apk), "origin": classify(name)})

    def stats(group):
        n = len(group)
        wn = sum(1 for r in group if r["so_count"] > 0)
        return {
            "n": n,
            "with_native": wn,
            "pct": round(100 * wn / n, 1) if n else 0.0,
            "total_so": sum(r["so_count"] for r in group),
        }

    bucket = {"PleOS": [], "AOSP": [], "third-party": []}
    for r in rows:
        bucket[r["origin"]].append(r)
    overall = stats(rows)
    by_origin = {k: stats(v) for k, v in bucket.items()}
    top = sorted([r for r in rows if r["so_count"] > 0], key=lambda r: -r["so_count"])[:15]

    payload = {
        "measurement_id": "R3.a",
        "description": "Native lib (.so) inventory across 207 system APKs extracted from PleOS Connect v2.0.5 emulator",
        "measured_at": "2026-05-06",
        "overall": overall,
        "by_origin": by_origin,
        "top_native_apks": top,
        "methodology": (
            "zipfile namelist filter on '.so'. APK origin classified by package prefix "
            "(ai.umos.* / ai.pleos.* = PleOS; com.android.* / android.* / com.google.* = AOSP; other = third-party)."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "native_lib_inventory.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# R3.a — Native lib inventory across PleOS Connect APKs",
        "",
        "_Measured: 2026-05-06 / scope: 207 system APKs from PleOS Connect v2.0.5 emulator_",
        "",
        "## Overall",
        "",
        "| 지표 | 값 |",
        "|---|---|",
        f"| Total APKs | {overall['n']} |",
        f"| APKs with at least one native lib | {overall['with_native']} ({overall['pct']}%) |",
        f"| Total .so files | {overall['total_so']} |",
        "",
        "## By origin",
        "",
        "| Origin | n | with native | % | total .so |",
        "|---|---|---|---|---|",
    ]
    for k in ("PleOS", "AOSP", "third-party"):
        s = by_origin[k]
        lines.append(f"| {k} | {s['n']} | {s['with_native']} | {s['pct']}% | {s['total_so']} |")
    lines += ["", "## Top 15 APKs by .so count", "",
              "| Rank | APK | .so count | Origin |", "|---|---|---:|---|"]
    for i, r in enumerate(top, 1):
        lines.append(f"| {i} | `{r['apk']}` | {r['so_count']} | {r['origin']} |")
    lines += [
        "",
        "## RQ3 implication",
        "",
        f"PleOS Connect 시스템 APK 중 native lib 보유 비율은 **{overall['pct']}%** "
        f"({overall['with_native']}/{overall['n']}). PleOS 자체 패키지 한정으로는 "
        f"**{by_origin['PleOS']['pct']}%** ({by_origin['PleOS']['with_native']}/{by_origin['PleOS']['n']}). "
        "본 파이프라인은 Java-only 정적 분석이라 native 부분 (MASVS-CRYPTO / RESILIENCE 일부 위반 가능성) 미커버 — "
        "한계 L1 의 corpus-level 인덱스. 차량 제어 / map navigation / 음성 비서 등 보안 가치가 큰 컴포넌트가 "
        "native 비중이 높은 점 (top 3: PleOS playground caas / maps navigation / ambientai) 은 추가 보강 필요성을 시사.",
        "",
    ]
    (OUT / "native_lib_inventory.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote: data/reports/native_lib_inventory.{md,json}")
    print(f"overall: {overall}")


if __name__ == "__main__":
    main()
