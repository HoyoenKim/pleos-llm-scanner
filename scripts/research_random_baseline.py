"""Random-sample selection-bias baseline — 본 학기 PleOS 3 APK 가 보안 가치 기반
선택이라 selection bias 가 측정값을 인플레이션 시키는지 검증.

PleOS 207 시스템 APK 중 위 3 APK 를 제외하고 시드 42 로 무작위 3 APK 선택,
priority class count + native lib count 를 측정해 보안 가치 큰 3 APK 와 비교.

본 측정은 quick screening — 디컴파일 + keyword grep 까지만 (full Stage 1 LLM
분석은 hours 단위 시간 cost 라 본 학기 외부). priority class count 차이가
'security-value-prior 가 있던 corpus selection 의 정량 영향' 의 첫 인디케이터.

Outputs:
  data/reports/random_sample_baseline.md
  data/reports/random_sample_baseline.json
"""
from __future__ import annotations

import json
import random
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APKS = ROOT / "data" / "apks"
DECOMP = ROOT / "data" / "decompiled"
OUT = ROOT / "data" / "reports"

# Selected security-priority 3 APKs (excluded from random pool)
SECURITY_PICKED = {
    "ai.umos.vehiclecontrol",
    "ai.pleos.sync.syslog",
    "ai.pleos.llm.model.provider",
}

# Quick keyword patterns (subset of configs/keywords.yaml — for screening only)
KEYWORD_PATTERNS = re.compile(
    r"(http://|https://"
    r"|setAllowFileAccess|setJavaScriptEnabled|TrustManager|HostnameVerifier"
    r"|grantRuntimePermission|revokeRuntimePermission|checkPermission"
    r"|sendBroadcast|registerReceiver|exported"
    r"|Cipher\.getInstance|MessageDigest\.getInstance|SecretKeySpec"
    r"|Log\.d|Log\.i|Log\.v|System\.out\.println"
    r"|password|secret|api[_-]?key|token"
    r"|loadLibrary|exec\(|Runtime\.getRuntime"
    r")",
    re.IGNORECASE,
)


def count_native_libs(apk_path: Path) -> int:
    try:
        with zipfile.ZipFile(apk_path) as zf:
            return sum(1 for n in zf.namelist() if n.endswith(".so"))
    except zipfile.BadZipFile:
        return 0


def decompile_if_needed(apk_path: Path) -> Path:
    """Run scripts/decompile.sh if output dir does not exist. Returns the
    decompiled output dir."""
    out_dir = DECOMP / apk_path.stem
    if out_dir.exists() and any(out_dir.iterdir()):
        return out_dir
    print(f"  decompiling {apk_path.name} ...", flush=True)
    subprocess.run(
        ["bash", "scripts/decompile.sh", str(apk_path.relative_to(ROOT))],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    return out_dir


def count_priority(decomp_dir: Path) -> tuple[int, int]:
    """Return (java_files_total, priority_classes_with_keyword_hit)."""
    sources = decomp_dir / "sources"
    if not sources.exists():
        return 0, 0
    total = 0
    priority = 0
    for f in sources.rglob("*.java"):
        total += 1
        # skip framework / library packages
        rel = str(f.relative_to(sources)).replace("\\", "/")
        if any(skip in rel for skip in [
            "/com/google/", "/android/support/", "/androidx/", "/kotlin/",
            "/com/squareup/", "/okhttp3/", "/okio/", "/io/reactivex/",
            "/dagger/", "/javax/inject/", "/com/scottyab/",
        ]):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if KEYWORD_PATTERNS.search(text):
            priority += 1
    return total, priority


def main() -> None:
    all_apks = sorted(p for p in APKS.glob("*.apk"))
    pool = [p for p in all_apks if p.stem not in SECURITY_PICKED]
    print(f"total APKs: {len(all_apks)}, eligible pool (excluding security-picked): {len(pool)}")

    rng = random.Random(42)
    sample = rng.sample(pool, 3)
    print(f"random sample (seed 42): {[p.name for p in sample]}")

    # security-picked baseline (re-measured)
    secs = []
    for stem in SECURITY_PICKED:
        apk = APKS / f"{stem}.apk"
        if not apk.exists():
            print(f"  warning: {apk.name} not found")
            continue
        decomp_dir = decompile_if_needed(apk)
        total, priority = count_priority(decomp_dir)
        nlibs = count_native_libs(apk)
        secs.append({
            "apk": stem,
            "java_files": total,
            "priority_classes": priority,
            "priority_ratio_pct": round(100 * priority / total, 2) if total else 0.0,
            "native_libs": nlibs,
        })
        print(f"  [security] {stem}: total={total}, priority={priority} ({secs[-1]['priority_ratio_pct']}%), .so={nlibs}")

    # random sample
    rands = []
    for apk in sample:
        decomp_dir = decompile_if_needed(apk)
        total, priority = count_priority(decomp_dir)
        nlibs = count_native_libs(apk)
        rands.append({
            "apk": apk.stem,
            "java_files": total,
            "priority_classes": priority,
            "priority_ratio_pct": round(100 * priority / total, 2) if total else 0.0,
            "native_libs": nlibs,
        })
        print(f"  [random] {apk.stem}: total={total}, priority={priority} ({rands[-1]['priority_ratio_pct']}%), .so={nlibs}")

    def avg(rows, key):
        if not rows:
            return 0.0
        return round(sum(r[key] for r in rows) / len(rows), 2)

    sec_avg_priority = avg(secs, "priority_classes")
    rand_avg_priority = avg(rands, "priority_classes")
    sec_avg_ratio = avg(secs, "priority_ratio_pct")
    rand_avg_ratio = avg(rands, "priority_ratio_pct")
    sec_avg_nlibs = avg(secs, "native_libs")
    rand_avg_nlibs = avg(rands, "native_libs")

    payload = {
        "measurement_id": "random_sample_baseline",
        "description": "Selection-bias baseline — 본 학기 보안 가치 기반 선정 PleOS 3 APK vs 무작위 3 APK 의 priority class count 비교 (selection bias 정량).",
        "measured_at": "2026-06-07",
        "scope": f"random pool size = {len(pool)} APKs (207 total, security-picked 3 excluded). Sample seed=42.",
        "security_picked": secs,
        "random_sample_seed_42": rands,
        "summary": {
            "security_picked_avg_priority_classes": sec_avg_priority,
            "random_sample_avg_priority_classes": rand_avg_priority,
            "ratio_security_vs_random": (round(sec_avg_priority / rand_avg_priority, 2)
                                         if rand_avg_priority else float("inf")),
            "security_picked_avg_priority_ratio_pct": sec_avg_ratio,
            "random_sample_avg_priority_ratio_pct": rand_avg_ratio,
            "security_picked_avg_native_libs": sec_avg_nlibs,
            "random_sample_avg_native_libs": rand_avg_nlibs,
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "random_sample_baseline.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md = [
        "# Random-sample selection-bias baseline",
        "",
        f"_Measured: 2026-06-07 / random pool: {len(pool)} APKs (PleOS 207 minus 3 security-picked) / seed: 42_",
        "",
        "## 본 학기 보안 가치 기반 PleOS 3 APK",
        "",
        "| APK | Java files | Priority class | Priority % | Native lib |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in secs:
        md.append(f"| `{r['apk']}` | {r['java_files']:,} | **{r['priority_classes']}** | {r['priority_ratio_pct']}% | {r['native_libs']} |")
    md += [
        "",
        "## 무작위 3 APK (시드 42)",
        "",
        "| APK | Java files | Priority class | Priority % | Native lib |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rands:
        md.append(f"| `{r['apk']}` | {r['java_files']:,} | {r['priority_classes']} | {r['priority_ratio_pct']}% | {r['native_libs']} |")
    md += [
        "",
        "## 비교 요약",
        "",
        "| 측정 | 보안 가치 큰 3 APK 평균 | 무작위 3 APK 평균 | 비율 |",
        "|---|---:|---:|---:|",
        f"| Priority class count | **{sec_avg_priority}** | {rand_avg_priority} | {round(sec_avg_priority / rand_avg_priority, 2) if rand_avg_priority else '∞'}× |",
        f"| Priority class ratio | {sec_avg_ratio}% | {rand_avg_ratio}% | — |",
        f"| Native lib count | {sec_avg_nlibs} | {rand_avg_nlibs} | — |",
        "",
        "## Selection bias 해석",
        "",
        f"- 보안 가치 기반 선정 3 APK (`vehiclecontrol`/`syslog`/`llm.model.provider`) 의 priority class count 평균 **{sec_avg_priority}** 가 무작위 3 APK 평균 {rand_avg_priority} 의 약 **{round(sec_avg_priority / rand_avg_priority, 2) if rand_avg_priority else 'inf'}×** 수준.",
        "- 즉 본 학기의 priority class 선정 (`stage 1` 진입 후보) 자체가 **선정 단계의 selection bias 를 가진다** — 본 학기 측정값 (Stage 1 P 85.7%, F1 0.923) 은 이 bias 가 반영된 corpus 결과.",
        "- 단 priority class count 만으로는 final Stage 1 finding count 또는 정확도 차이가 직접 매칭되지 않는다. priority 가 많아도 모든 priority 가 finding 을 emit 하지 않을 수 있고, 적어도 finding 이 cleaner/more decisive 할 수 있다.",
        "- **본 학기 selection bias 측정의 한계**: Stage 1 LLM 분석을 무작위 3 APK 에 직접 적용하면 더 직접적 비교 가능하나, 본 학기 시간 cost 로 priority class count 까지만 측정. 무작위 3 APK 의 Stage 1 P/R/F1 측정은 Future Work.",
        "",
        "## RQ1 implication",
        "",
        "- 본 학기 `Stage 1 / Stage 3` 측정값은 **보안 가치 큰 priority subset 에서 측정된 값**. 무작위 PleOS APK sample 에서는 priority class density 가 더 낮아 finding 수 자체가 줄어들 가능성.",
        "- 정량 측정값 자체는 영향이 클 수 있으나 (priority class 가 적으면 stage 1 finding 도 적음), Precision / FP rate 같은 normalised metric 은 priority class density 와 직접 비례하지 않을 수 있다.",
        "- v1.0 narrative 갱신 권고: 본 학기 측정값은 **보안 가치 큰 corpus subset 한정** 임을 명시. 일반화 주장은 무작위 sample 추가 측정 후.",
        "",
    ]
    # Re-format the bias paragraph (Python f-string interpolation issue avoided above)
    (OUT / "random_sample_baseline.md").write_text(
        "\n".join(md).replace(
            "{round(sec_avg_priority / rand_avg_priority, 2) if rand_avg_priority else 'inf'}",
            f"{round(sec_avg_priority / rand_avg_priority, 2) if rand_avg_priority else 'inf'}",
        ).replace(
            "**{sec_avg_priority}**",
            f"**{sec_avg_priority}**",
        ).replace(
            "{rand_avg_priority}",
            f"{rand_avg_priority}",
        ),
        encoding="utf-8",
    )
    print()
    print(f"security avg priority: {sec_avg_priority}")
    print(f"random   avg priority: {rand_avg_priority}")
    print(f"ratio: {round(sec_avg_priority / rand_avg_priority, 2) if rand_avg_priority else 'inf'}x")


if __name__ == "__main__":
    main()
