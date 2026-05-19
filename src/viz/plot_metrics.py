#!/usr/bin/env python
"""
Generate publication-quality charts from the GT + ablation + entropy measurements.

Outputs (data/viz/*.png):
- 01_category_distribution.png   : finding 카테고리 분포 (combined n=47)
- 02_apk_severity_heatmap.png    : APK × severity 히트맵 (12 APK, n=47)
- 03_fp_rate_trend.png           : 1차/2차/3차 오탐률 (PPT 가설 vs 실측 n=18/n=47)
- 04_deobf_accuracy_trend.png    : Corpus별 난독화 분포 + LLM rename 정확도 (단일 측정, 시간축 아님)
- 05_ablation_bars.png           : A 변형 + B threshold sensitivity (combined n=47)
- 06_entropy_distribution.png    : 6 APK 의 obfuscation composite score 분포 (live data/deobf)

데이터: charts 01-05 는 combined_labels.json n=47 기준 하드코딩 갱신 (2026-05-14),
chart 06 은 data/deobf/*.json 라이브 로드. 갱신 시 본 스크립트 재실행.

Usage
-----
    python src/viz/plot_metrics.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Patch

# Korean font
matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["figure.dpi"] = 120
matplotlib.rcParams["savefig.dpi"] = 200
matplotlib.rcParams["savefig.bbox"] = "tight"
matplotlib.rcParams["axes.titleweight"] = "bold"
matplotlib.rcParams["font.size"] = 10

OUT_DIR = Path("data/viz")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- 01 category distribution
def chart_category_distribution() -> None:
    # combined_labels.json n=47 기준 (is_real → TP/FP, stage1_category 그룹)
    cats = ["intent", "hardcoded", "network", "crypto", "permission", "reflection_dynamic"]
    tp = [14, 11, 7, 5, 0, 1]
    fp = [4, 0, 2, 0, 3, 0]
    x = np.arange(len(cats))
    width = 0.42
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    b1 = ax.bar(x - width / 2, tp, width, label="True Positive", color="#3a7d44")
    b2 = ax.bar(x + width / 2, fp, width, label="False Positive", color="#c73e1d")
    ax.set_ylabel("개수 (n=47)")
    ax.set_title("Stage 1 카테고리별 정·오탐 분포 (combined n=47)")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_yticks(range(0, 16, 2))
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", frameon=False)
    for bars in (b1, b2):
        for b in bars:
            h = b.get_height()
            if h:
                ax.text(b.get_x() + b.get_width() / 2, h + 0.12, f"{int(h)}", ha="center", fontsize=9)
    ax.text(
        0.99, -0.18,
        "combined GT n=47 — PleOS-customized 30 + MASTG 4 + InsecureBankv2 9 + AOSP-derived 4 (TP 38 / FP 9)",
        transform=ax.transAxes, ha="right", va="center", fontsize=8, color="#666",
    )
    fig.savefig(OUT_DIR / "01_category_distribution.png")
    plt.close(fig)


# ---------------------------------------------------------------- 02 severity heatmap
def chart_severity_heatmap() -> None:
    # combined_labels.json n=47 기준 — apk × true_severity TP count + FP 별도 annotation
    apks = [
        "VehicleControl", "sync.syslog", "llm.model.provider", "account",
        "appmarket", "ambientai", "maps", "UnCrackable-L1", "UnCrackable-L3",
        "InsecureBankv2", "usb.handler", "statementservice",
    ]
    sev_levels = ["HIGH", "MEDIUM", "LOW"]
    tp_matrix = np.array(
        [
            [1, 1, 1],   # VehicleControl  — vc-5/6/7
            [5, 1, 0],   # sync.syslog     — ssl-1/2/4/5/6 HIGH, ssl-3 MED
            [1, 1, 0],   # llm.model.provider — lmp-1 HIGH, lmp-2 MED
            [3, 2, 0],   # account (R1.d.4) — acc-1/3/4 HIGH, acc-2/5 MED
            [2, 1, 0],   # appmarket (R1.d.5) — am-1/3 HIGH, am-2 MED
            [2, 1, 0],   # ambientai (R1.d.5) — amb-1/2 HIGH, amb-3 MED
            [0, 1, 0],   # maps (R1.d.5)   — map-1 MED
            [1, 1, 1],   # UnCrackable-L1  — ucl1-1/2/3
            [1, 0, 0],   # UnCrackable-L3  — ucl3-1 HIGH
            [7, 2, 0],   # InsecureBankv2  — 9 finding 모두 TP
            [0, 2, 0],   # usb.handler (R1.d.2) — usb-1/3 MED
            [0, 0, 0],   # statementservice (R1.d.3) — ss-1 은 FP
        ],
        dtype=int,
    )
    fp_per_apk = np.array([4, 0, 0, 0, 1, 2, 0, 0, 0, 0, 1, 1])  # 합계 9 FP

    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    im = ax.imshow(tp_matrix, aspect="auto", cmap="Blues", vmin=0, vmax=tp_matrix.max())
    ax.set_xticks(range(len(sev_levels)))
    ax.set_xticklabels(sev_levels)
    ax.set_yticks(range(len(apks)))
    ax.set_yticklabels(apks, fontsize=9)
    ax.set_title("APK × Severity — True Positive (n=38 TP) + FP 표시 (combined n=47)")

    for i in range(len(apks)):
        for j in range(len(sev_levels)):
            v = tp_matrix[i, j]
            if v > 0:
                ax.text(j, i, str(v), ha="center", va="center",
                        color="white" if v >= 4 else "#222", fontweight="bold")

    # FP annotation column on the right
    ax2 = ax.twinx()
    ax2.set_yticks(range(len(apks)))
    ax2.set_yticklabels([f"FP={n}" for n in fp_per_apk])
    ax2.set_ylim(ax.get_ylim())
    ax2.tick_params(axis="y", labelsize=8, labelcolor="#c73e1d")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.20)
    cbar.set_label("True Positive count", fontsize=9)
    ax.text(
        0.5, -0.10,
        "FP 9건 — VehicleControl 4 (vc-1~4 deep-link FP) + ambientai 2 + appmarket/usb.handler/statementservice 각 1",
        transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color="#666",
    )
    fig.savefig(OUT_DIR / "02_apk_severity_heatmap.png")
    plt.close(fig)


# ---------------------------------------------------------------- 03 FP rate trend
def chart_fp_rate_trend() -> None:
    stages = ["Stage 1\n(LLM 1차)", "Stage 2\n(caller 검증)", "Stage 3\n(≥2/3 합의)"]
    ppt_hyp = [25.0, 12.0, 7.0]
    actual_n18 = [22.2, 0.0, 0.0]   # combined n=18 (초기 측정)
    actual_n47 = [19.1, 0.0, 0.0]   # combined n=47 (학기 외 A 최종)
    x = np.arange(len(stages))
    width = 0.27
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    b1 = ax.bar(x - width, ppt_hyp, width, label="PPT 가설", color="#a0a0a0")
    b2 = ax.bar(x, actual_n18, width, label="실측 combined n=18 (초기)", color="#3673a4")
    b3 = ax.bar(x + width, actual_n47, width, label="실측 combined n=47 (최종)", color="#3a7d44")
    ax.set_ylabel("False Positive Rate (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_title("Stage별 오탐률 — PPT 가설 vs 실측 (x축은 검증 단계, 시간 아님)")
    ax.set_ylim(0, 30)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", frameon=False)
    for bars in (b1, b2, b3):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 0.5, f"{h:.1f}%", ha="center", fontsize=9)
    ax.text(
        0.99, -0.16,
        "Stage 3 (≥2/3 합의) — combined n=47 측정 (P 100% / R 97.4% / F1 0.987). "
        "McNemar p_exact=0.0215 < α=0.05 통계적 유의.",
        transform=ax.transAxes, ha="right", va="center", fontsize=7.5, color="#666",
    )
    fig.savefig(OUT_DIR / "03_fp_rate_trend.png")
    plt.close(fig)


# ---------------------------------------------------------------- 04 deobf accuracy by corpus
def chart_deobf_accuracy_trend() -> None:
    """
    이전 버전은 시간축(5/6/8주차)에 단일 측정값(2026-04-30 n=17)을 세 번 그려
    추이가 있는 것처럼 보이게 하는 misleading 시각화였다 (사용자 지적, 2026-05-06).
    재설계: corpus별 HIGH 난독화 비율 + 측정된 corpus의 LLM rename 정확도 annotation.
    PPT 가설 78%는 caption에만 명시 — 측정값과 다른 축이라 같이 막대로 그리지 않음.
    """
    apks = [
        # (label, HIGH ratio %, origin, rename n, accuracy %, accuracy kind)
        ("UnCrackable-L1\n(MASTG)",        50.0, "MASTG", 11,   100.0, "exact"),
        ("UnCrackable-L2\n(MASTG)",        40.0, "MASTG",  6,   100.0, "exact"),
        ("r2pay-v1.0\n(MASTG)",             0.0, "MASTG", None, None,  None),
        ("NewPipe v0.27.6\n(OSS ProGuard)", 1.7, "OSS",    6,    67.0, "GOOD+"),
        ("VehicleControl\n(PleOS)",         0.2, "PleOS", None, None,  None),
        ("SyncSyslog\n(PleOS)",             0.4, "PleOS", None, None,  None),
        ("LLMModelProvider\n(PleOS)",       0.0, "PleOS", None, None,  None),
    ]
    x = np.arange(len(apks))
    fig, ax = plt.subplots(figsize=(10.0, 4.8))
    _palette = {"MASTG": "#3a7d44", "OSS": "#c4861f", "PleOS": "#3673a4"}
    colors = [_palette[a[2]] for a in apks]
    ax.bar(x, [a[1] for a in apks], color=colors, alpha=0.75, width=0.65)
    ax.set_ylabel("HIGH 난독화 클래스 비율 (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([a[0] for a in apks], fontsize=8.5)
    ax.set_ylim(0, 70)
    ax.set_title("Corpus별 난독화 분포 + LLM 이름 복원 정확도 (측정된 corpus만)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    for i, (_, ratio, _origin, n, acc, kind) in enumerate(apks):
        ax.text(i, ratio + 1.5, f"{ratio:.1f}%", ha="center", fontsize=9, color="#333")
        if n is None:
            ax.text(i, ratio + 7, "정확도\n측정 X", ha="center", va="bottom",
                    fontsize=8, color="#888", style="italic")
        else:
            ax.text(i, ratio + 7, f"rename n={n}\n{kind} {acc:.0f}%",
                    ha="center", va="bottom", fontsize=8.5,
                    bbox=dict(boxstyle="round,pad=0.28", fc="#fff7da",
                              ec="#c4861f", lw=0.7))

    legend_handles = [
        Patch(facecolor="#3a7d44", alpha=0.75, label="MASTG (OWASP, hand-crafted) — exact match"),
        Patch(facecolor="#c4861f", alpha=0.75, label="OSS ProGuard (NewPipe) — semantic plausibility"),
        Patch(facecolor="#3673a4", alpha=0.75, label="PleOS (실제 IVI APK)"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=8.5)

    ax.text(
        0.5, -0.22,
        "단일 측정 (시간 추이 아님). hand-crafted MASTG n=17 exact 100% = upper-bound. "
        "real-world OSS NewPipe n=6 GOOD+ 67% = real-world floor (ProGuard mapping 부재로 exact 불가, plausibility 평가). "
        "PleOS는 HIGH 0.2~0.4%로 측정 대상 자체가 거의 없음. PPT 가설 5/6/8주차 40→65→78%는 reference.",
        transform=ax.transAxes, ha="center", va="center", fontsize=7.6, color="#666",
        wrap=True,
    )
    fig.savefig(OUT_DIR / "04_deobf_accuracy_trend.png")
    plt.close(fig)


# ---------------------------------------------------------------- 05 ablation bars
def chart_ablation_bars() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))

    # --- Variant A — stage ablation (combined n=47, 학기 외 A) ---
    a_labels = ["A.1\nstage 1", "A.2\n+stage 2", "A.3\n+stage 3 ≥3/3"]
    a_p = [80.9, 100.0, 100.0]
    a_r = [100.0, 100.0, 86.8]
    a_f1 = [0.894, 1.000, 0.930]
    x = np.arange(len(a_labels))
    width = 0.27
    ax = axes[0]
    b1 = ax.bar(x - width, a_p, width, label="Precision", color="#3673a4")
    b2 = ax.bar(x, a_r, width, label="Recall", color="#3a7d44")
    b3 = ax.bar(x + width, [v * 100 for v in a_f1], width, label="F1 ×100", color="#c4861f")
    ax.set_ylim(0, 110)
    ax.set_xticks(x)
    ax.set_xticklabels(a_labels)
    ax.set_ylabel("값 (%)")
    ax.set_title("Variant A — Stage Ablation (combined n=47)")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for bars in (b1, b2, b3):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 1.5, f"{h:.1f}", ha="center", fontsize=8)

    # --- Variant B — consensus threshold (combined n=47, 학기 외 A) ---
    b_labels = ["≥1/3\n(any flag)", "≥2/3\n(default)", "≥3/3\n(unanimous)"]
    b_p = [84.4, 100.0, 100.0]
    b_r = [100.0, 97.4, 86.8]
    b_f1 = [0.916, 0.987, 0.930]
    x = np.arange(len(b_labels))
    ax = axes[1]
    b1 = ax.bar(x - width, b_p, width, label="Precision", color="#3673a4")
    b2 = ax.bar(x, b_r, width, label="Recall", color="#3a7d44")
    b3 = ax.bar(x + width, [v * 100 for v in b_f1], width, label="F1 ×100", color="#c4861f")
    ax.set_ylim(0, 110)
    ax.set_xticks(x)
    ax.set_xticklabels(b_labels)
    ax.set_ylabel("값 (%)")
    ax.set_title("Variant B — 멀티 프롬프트 합의 임계 sensitivity (combined n=47)")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for bars in (b1, b2, b3):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 1.5, f"{h:.1f}", ha="center", fontsize=8)

    fig.suptitle("Ablation Results — Stage + Consensus 변형", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "05_ablation_bars.png")
    plt.close(fig)


# ---------------------------------------------------------------- 06 entropy distribution
def chart_entropy_distribution() -> None:
    apks = [
        ("UnCrackable-Level1", "MASTG"),
        ("UnCrackable-Level2", "MASTG"),
        ("r2pay-v1.0", "MASTG"),
        ("VehicleControl", "PleOS"),
        ("SyncSyslog", "PleOS"),
        ("LLMModelProvider", "PleOS"),
    ]
    scores: list[list[float]] = []
    for name, _ in apks:
        path = Path(f"data/deobf/{name}.json")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        scores.append([r["composite_obf_score"] for r in data["results"]])

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    colors = ["#3a7d44" if origin == "MASTG" else "#3673a4" for _, origin in apks]
    bp = ax.boxplot(
        scores,
        tick_labels=[name for name, _ in apks],
        patch_artist=True,
        widths=0.55,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": 6},
    )
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.55)
    ax.axhline(y=0.7, color="#c73e1d", linestyle="--", linewidth=0.9, label="HIGH 임계 (0.7)")
    ax.axhline(y=0.4, color="#c4861f", linestyle=":", linewidth=0.9, label="MEDIUM 임계 (0.4)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("composite obfuscation score [0, 1]")
    ax.set_title("Obfuscation Composite Score 분포 (6 APK, 비-framework 클래스)")
    ax.set_xticklabels([name for name, _ in apks], rotation=10, ha="right")
    legend_handles = [
        Patch(facecolor="#3a7d44", alpha=0.55, label="MASTG corpus"),
        Patch(facecolor="#3673a4", alpha=0.55, label="PleOS corpus"),
    ] + ax.get_legend_handles_labels()[0]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=8)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    # annotate HIGH ratios
    for i, (name, _) in enumerate(apks):
        path = Path(f"data/deobf/{name}.json")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        ratio = data["summary"]["high_obf_ratio"] * 100
        ax.text(i + 1, 1.02, f"HIGH={ratio:.1f}%", ha="center", fontsize=7.5, color="#444")

    ax.text(
        0.5, -0.22,
        "PleOS 3종 HIGH 0.2~0.4% — PPT 가정 '고난독화 IVI 코드'와 정량적으로 다름.  MASTG (OWASP) 는 hand-crafted obfuscation",
        transform=ax.transAxes, ha="center", va="center", fontsize=8, color="#666",
    )
    fig.savefig(OUT_DIR / "06_entropy_distribution.png")
    plt.close(fig)


def main() -> None:
    chart_category_distribution()
    chart_severity_heatmap()
    chart_fp_rate_trend()
    chart_deobf_accuracy_trend()
    chart_ablation_bars()
    chart_entropy_distribution()
    print(f"Wrote 6 charts to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
