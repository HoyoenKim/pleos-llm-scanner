#!/usr/bin/env python
"""Generate final report figures for the PleOS LLM scanner archive.

The main figure set explains the static-analysis experiment flow:

1. JADX output is checked for Java/Kotlin readability.
2. LLM-proposed candidate findings are filtered by Android context validation.
3. Context-aware review changes the headline scan-quality metrics.
4. Confirmed vulnerability findings are reviewed by APK and severity.
5. The candidate-acceptance rule is justified.

Appendix figures provide composition, confidence interval, obfuscation,
mapping, and cross-validation details.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["figure.dpi"] = 120
matplotlib.rcParams["savefig.dpi"] = 200
matplotlib.rcParams["savefig.bbox"] = "tight"
matplotlib.rcParams["axes.titleweight"] = "bold"
matplotlib.rcParams["font.size"] = 10

OUT_DIR = Path("data/viz")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = "#2f6f9f"
ORANGE = "#d9902f"
GREEN = "#3a7d44"
RED = "#b85c4d"
GRAY = "#6f7782"
LIGHT_GRAY = "#f3f5f7"
TEXT = "#30343b"
MUTED = "#5f6670"


def _load_json(path: str | Path) -> object:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def _caption(fig: plt.Figure, text: str, y: float = 0.065, size: float = 8.3) -> None:
    fig.text(0.5, y, text, ha="center", va="center", fontsize=size, color=MUTED)


# --------------------------------------------------------------------------- 01
def chart_category_distribution() -> None:
    """Final outcomes by candidate-finding category."""
    cats = [
        "Exported component /\nintent exposure",
        "Hardcoded\nsecret",
        "Network security\nconfig",
        "Crypto\nmisuse",
        "Permission\nhandling",
        "Dynamic code /\nreflection",
    ]
    confirmed = [13, 11, 7, 5, 0, 1]
    rejected = [4, 0, 2, 0, 3, 0]
    missed = [1, 0, 0, 0, 0, 0]
    x = np.arange(len(cats))
    width = 0.26

    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    b1 = ax.bar(x - width, confirmed, width, label="Confirmed vulnerabilities", color=BLUE)
    b2 = ax.bar(x, rejected, width, label="Rejected as false positives", color=ORANGE)
    b3 = ax.bar(x + width, missed, width, label="Missed true vulnerability", color=GRAY)

    ax.set_ylabel("Number of candidate findings")
    ax.set_title("Final Outcomes For LLM-Proposed Candidate Findings", pad=24)
    ax.text(
        0.5,
        1.03,
        "47 candidate findings: 37 confirmed, 9 rejected as false positives, and 1 low-severity true vulnerability missed.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9.5,
        color=MUTED,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_yticks(range(0, 16, 2))
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", frameon=False, fontsize=8.8)

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            if h:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.12, f"{int(h)}", ha="center", fontsize=9)

    _caption(
        fig,
        "Android context validation checks manifest exposure, caller reachability, permissions, route binding,\n"
        "and framework controls before the final multi-role decision.",
        y=0.105,
        size=8.5,
    )
    _caption(
        fig,
        "Candidate sources: PleOS-customized (30), MASTG (4), InsecureBankv2 (9), AOSP-derived (4).",
        y=0.060,
        size=8.2,
    )
    fig.subplots_adjust(bottom=0.24, top=0.82)
    fig.savefig(OUT_DIR / "02_candidate_verification_by_pattern.png")
    plt.close(fig)


# --------------------------------------------------------------------------- 02
def chart_severity_heatmap() -> None:
    """Confirmed vulnerabilities by APK and severity."""
    apks = [
        "VehicleControl [PleOS]",
        "SyncSyslog [PleOS]",
        "LLMModelProvider [PleOS]",
        "Account [PleOS]",
        "AppMarket [PleOS]",
        "AmbientAI [PleOS]",
        "Maps [PleOS]",
        "UnCrackable-L1 [MASTG]",
        "UnCrackable-L3 [MASTG]",
        "InsecureBankv2 [External]",
        "USBHandler [AOSP]",
    ]
    sev_levels = ["HIGH", "MEDIUM", "LOW"]
    verified_matrix = np.array(
        [
            [1, 1, 0],
            [5, 1, 0],
            [1, 1, 0],
            [3, 2, 0],
            [2, 1, 0],
            [2, 1, 0],
            [0, 1, 0],
            [1, 1, 1],
            [1, 0, 0],
            [7, 2, 0],
            [0, 2, 0],
        ],
        dtype=int,
    )

    fig, ax = plt.subplots(figsize=(8.4, 6.8))
    im = ax.imshow(verified_matrix, aspect="auto", cmap="Blues", vmin=0, vmax=verified_matrix.max())
    ax.set_xticks(range(len(sev_levels)))
    ax.set_xticklabels(sev_levels)
    ax.set_yticks(range(len(apks)))
    ax.set_yticklabels(apks, fontsize=9)
    ax.set_title("Confirmed Vulnerability Findings By APK And Severity", pad=30)
    ax.text(
        0.5,
        1.035,
        "37 findings confirmed by the selected >=2-role rule; PleOS entries are project targets.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )

    for i in range(len(apks)):
        for j in range(len(sev_levels)):
            v = verified_matrix[i, j]
            if v > 0:
                ax.text(
                    j,
                    i,
                    str(v),
                    ha="center",
                    va="center",
                    color="white" if v >= 4 else TEXT,
                    fontweight="bold",
                )

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.08)
    cbar.ax.set_title("Count", fontsize=8, pad=8)
    _caption(
        fig,
        "Use this as a follow-up priority map, not an ecosystem prevalence estimate.\n"
        "The one missed low-severity true vulnerability is excluded from confirmed counts.",
        y=0.075,
        size=8.2,
    )
    fig.subplots_adjust(left=0.25, bottom=0.14, top=0.84)
    fig.savefig(OUT_DIR / "04_verified_vulnerabilities_by_apk_severity.png")
    plt.close(fig)


# --------------------------------------------------------------------------- 03
def chart_fp_rate_trend() -> None:
    """Scan-quality comparison before and after context verification."""
    metrics = ["Precision", "Recall", "F1"]
    only_llm = [80.9, 100.0, 89.4]
    verified = [100.0, 97.4, 98.7]
    x = np.arange(len(metrics))
    width = 0.34

    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    b1 = ax.bar(x - width / 2, only_llm, width, label="LLM scan only", color=BLUE)
    b2 = ax.bar(x + width / 2, verified, width, label="Context validation + multi-role review", color=ORANGE)
    ax.set_ylabel("Score (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_title("Context-Aware Review Improves Precision And F1", pad=28)
    ax.text(
        0.5,
        1.035,
        "Candidate-level decisions over 47 LLM-proposed findings.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_ylim(0, 112)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2, frameon=False)

    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1.2, f"{h:.1f}", ha="center", fontsize=9)

    _caption(
        fig,
        "Context-aware review removes the measured false positives while missing one low-severity issue.\n"
        "McNemar exact p=0.0215 compares paired report/not-report decisions for the same 47 candidates.",
        y=0.075,
        size=8.4,
    )
    fig.subplots_adjust(bottom=0.18, top=0.73)
    fig.savefig(OUT_DIR / "03_scan_quality_before_after_verification.png")
    plt.close(fig)


# --------------------------------------------------------------------------- 04
def chart_deobf_accuracy_trend() -> None:
    """Obfuscation profile across sampled APKs."""
    rows = [
        ("UnCrackable-L1", "MASTG", 6, 3),
        ("UnCrackable-L2", "MASTG", 5, 2),
        ("r2pay-v1.0", "MASTG", 2, 0),
        ("NewPipe v0.27.6", "OSS", 2520, 42),
        ("VehicleControl", "PleOS", 2704, 6),
        ("SyncSyslog", "PleOS", 4555, 18),
        ("LLMModelProvider", "PleOS", 112, 0),
    ]
    colors = {"MASTG": GREEN, "OSS": ORANGE, "PleOS": BLUE}
    x = np.arange(len(rows))

    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    bars = ax.bar(x, [r[3] for r in rows], color=[colors[r[1]] for r in rows], alpha=0.78, width=0.62)
    ax.set_ylabel("Flagged classes")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{name}\n[{origin}]" for name, origin, _total, _high in rows], fontsize=8.2)
    ax.set_ylim(0, 52)
    ax.set_title("Decompiled Identifier Obfuscation Pre-Screen For Static Review", pad=26)
    ax.text(
        0.5,
        1.035,
        "Classes are flagged by high-obfuscation identifier-name patterns such as C0010a, m5a, and f2a.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    for bar, (_name, _origin, total, high) in zip(bars, rows):
        x_mid = bar.get_x() + bar.get_width() / 2
        ratio = (high / total * 100) if total else 0.0
        ax.text(
            x_mid,
            high + 1.0,
            f"{high}/{total}\n({ratio:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8.0,
            color=TEXT,
        )

    ax.legend(
        handles=[
            Patch(facecolor=GREEN, alpha=0.78, label="OWASP MASTG samples"),
            Patch(facecolor=ORANGE, alpha=0.78, label="ProGuard-obfuscated OSS sample"),
            Patch(facecolor=BLUE, alpha=0.78, label="PleOS target APKs"),
        ],
        loc="upper right",
        frameon=False,
        fontsize=8.4,
    )
    _caption(
        fig,
        "Bars use a JADX-decompiled identifier-name pattern heuristic; labels show flagged / analyzed classes.\n"
        "This is not vulnerability severity and not a final scan-quality metric.",
        y=0.075,
        size=8.2,
    )
    fig.subplots_adjust(bottom=0.20, top=0.80)
    fig.savefig(OUT_DIR / "01_obfuscation_profile_across_test_apks.png")
    plt.close(fig)


# --------------------------------------------------------------------------- 05
def chart_ablation_bars() -> None:
    """Candidate acceptance rule by three-role review."""
    labels = [
        ">=1 role\nagrees",
        ">=2 roles\nagree",
        "3/3 roles\nagree",
    ]
    precision = [84.4, 100.0, 100.0]
    recall = [100.0, 97.4, 86.8]
    f1 = [91.6, 98.7, 93.0]
    x = np.arange(len(labels))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10.8, 5.8))
    b1 = ax.bar(x - width, precision, width, label="Precision", color=BLUE)
    b2 = ax.bar(x, recall, width, label="Recall", color=GREEN)
    b3 = ax.bar(x + width, f1, width, label="F1", color=ORANGE)

    ax.set_ylabel("Precision / Recall / F1 (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 122)
    ax.set_title("Multi-Role LLM Review: Precision-Recall Trade-Off By Consensus Threshold", pad=40)
    ax.text(
        0.5,
        1.070,
        "47 candidate findings reviewed by role-prompted attacker, defender, and in-vehicle infotainment (IVI)-domain reviewers.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.035), ncol=3, frameon=False)
    ax.axvline(1, color="#111", alpha=0.08, linewidth=46, zorder=0)
    ax.text(1, 10, "selected\nthreshold", ha="center", va="center", fontsize=8.0, color=MUTED)

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 2.0, f"{h:.1f}", ha="center", fontsize=8.4)

    _caption(
        fig,
        "The >=1 threshold leaves 7 false positives; the 3/3 threshold misses 5 true vulnerabilities.\n"
        "The selected >=2 threshold confirms 37 findings with 0 false positives and 1 low-severity false negative.",
        y=0.070,
        size=8.3,
    )
    fig.subplots_adjust(bottom=0.20, top=0.68)
    fig.savefig(OUT_DIR / "05_accept_candidates_as_vulnerabilities_by_three_role_review.png")
    plt.close(fig)


# --------------------------------------------------------------------- appendix
def appendix_corpus_composition() -> None:
    labels = ["PleOS-customized", "MASTG", "InsecureBankv2", "AOSP-derived"]
    values = [30, 4, 9, 4]
    colors = [BLUE, GREEN, ORANGE, GRAY]
    total = sum(values)
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    bars = ax.barh(y, values, color=colors, alpha=0.82)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Candidate findings")
    ax.set_xlim(0, 34)
    ax.set_title("Source Composition Of The 47 Candidate Findings", pad=22)
    ax.text(
        0.5,
        1.035,
        "Each unit is one candidate finding, not one APK or an ecosystem prevalence estimate.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="x", linestyle=":", alpha=0.45)
    for bar, value in zip(bars, values):
        pct = value / total * 100
        ax.text(
            value + 0.45,
            bar.get_y() + bar.get_height() / 2,
            f"{value}/{total} ({pct:.0f}%)",
            va="center",
            fontsize=8.8,
        )

    _caption(
        fig,
        "PleOS-customized findings form the main in-vehicle infotainment (IVI) target set;\n"
        "MASTG, InsecureBankv2, and AOSP-derived findings serve as controls.",
        y=0.055,
    )
    fig.subplots_adjust(left=0.26, bottom=0.19, top=0.76)
    fig.savefig(OUT_DIR / "appendix_a1_corpus_composition.png")
    plt.close(fig)


def appendix_bootstrap_ci() -> None:
    metrics = ["Precision", "F1", "False discovery share\n(1 - precision)"]
    point = np.array([80.9, 89.4, 19.1])
    low = np.array([70.2, 82.5, 8.5])
    high = np.array([91.5, 95.6, 29.8])
    xerr = np.vstack([point - low, high - point])
    y = np.arange(len(metrics))
    colors = [BLUE, GREEN, ORANGE]

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    for i, (p, lo, hi, color) in enumerate(zip(point, low, high, colors)):
        ax.errorbar(
            p,
            i,
            xerr=np.array([[p - lo], [hi - p]]),
            fmt="o",
            markersize=8,
            color=color,
            ecolor=color,
            elinewidth=2.0,
            capsize=6,
            markeredgecolor="white",
            markeredgewidth=0.8,
        )
        ax.text(hi + 1.4, i, f"{p:.1f}% [{lo:.1f}, {hi:.1f}]", va="center", fontsize=8.6, color=TEXT)

    ax.set_xlabel("Score (%)")
    ax.set_yticks(y)
    ax.set_yticklabels(metrics, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 104)
    ax.set_title("Bootstrap Uncertainty For The LLM-Only Candidate Scan", pad=22)
    ax.text(
        0.5,
        1.035,
        "95% bootstrap intervals over the 47 candidate findings.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="x", linestyle=":", alpha=0.5)

    _caption(
        fig,
        "False discovery share is FP / (TP + FP), shown as 1 - precision to make the false-positive burden explicit.",
        y=0.065,
    )
    fig.subplots_adjust(left=0.28, bottom=0.18, top=0.76)
    fig.savefig(OUT_DIR / "appendix_a2_bootstrap_ci.png")
    plt.close(fig)


def appendix_obfuscation_score_distribution() -> None:
    apks = [
        ("UnCrackable-Level1", "UnCrackable-Level1", "MASTG"),
        ("UnCrackable-Level2", "UnCrackable-Level2", "MASTG"),
        ("r2pay-v1.0", "r2pay-v1.0", "MASTG"),
        ("NewPipe v0.27.6", "NewPipe", "OSS"),
        ("VehicleControl", "VehicleControl", "PleOS"),
        ("SyncSyslog", "SyncSyslog", "PleOS"),
        ("LLMModelProvider", "LLMModelProvider", "PleOS"),
    ]
    scores: list[list[float]] = []
    for _display, file_stem, _origin in apks:
        data = _load_json(f"data/deobf/{file_stem}.json")
        assert isinstance(data, dict)
        scores.append([r["composite_obf_score"] for r in data["results"]])

    fig, ax = plt.subplots(figsize=(11.8, 5.0))
    origin_colors = {"MASTG": GREEN, "OSS": ORANGE, "PleOS": BLUE}
    colors = [origin_colors[origin] for _display, _file_stem, origin in apks]
    bp = ax.boxplot(
        scores,
        tick_labels=[display for display, _file_stem, _origin in apks],
        patch_artist=True,
        widths=0.55,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": 5},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.58)

    ax.axhline(y=0.7, color=RED, linestyle="--", linewidth=0.9, label="High-score threshold (0.7)")
    ax.axhline(y=0.4, color=ORANGE, linestyle=":", linewidth=0.9, label="Medium-score threshold (0.4)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("Composite identifier-name score [0, 1]")
    ax.set_title("Distribution Of Heuristic Identifier-Name Obfuscation Scores", pad=22)
    ax.text(
        0.5,
        1.035,
        "Composite class-level scores from the heuristic JADX-decompiled identifier-name screen.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_xticklabels([display for display, _file_stem, _origin in apks], rotation=10, ha="right", fontsize=8.0)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.45)

    legend_handles = [
        Patch(facecolor=GREEN, alpha=0.58, label="OWASP MASTG samples"),
        Patch(facecolor=ORANGE, alpha=0.58, label="ProGuard-obfuscated OSS sample"),
        Patch(facecolor=BLUE, alpha=0.58, label="PleOS samples"),
        Line2D([0], [0], marker="D", color="black", markerfacecolor="white", markersize=5, linestyle="None", label="Mean score"),
    ] + ax.get_legend_handles_labels()[0]
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.005, 1.0), frameon=False, fontsize=8.2)

    for i, (_display, file_stem, _origin) in enumerate(apks):
        data = _load_json(f"data/deobf/{file_stem}.json")
        assert isinstance(data, dict)
        ratio = data["summary"]["high_obf_ratio"] * 100
        ax.text(i + 1, 1.02, f"score>=0.7: {ratio:.1f}%", ha="center", fontsize=7.3, color=TEXT)

    _caption(
        fig,
        "This shows the score spread behind the flagged-class screen; thresholds are heuristic readability markers,\n"
        "not an obfuscation benchmark or vulnerability metric. Diamonds mark mean class-level score.",
        y=0.055,
    )
    fig.subplots_adjust(bottom=0.22, top=0.82, right=0.78)
    fig.savefig(OUT_DIR / "appendix_a3_obfuscation_score_distribution.png")
    plt.close(fig)


def appendix_mapping_summary() -> None:
    labels = _load_json("data/ground_truth/combined_labels.json")
    assert isinstance(labels, dict)
    verified = [r for r in labels["labels"] if r.get("is_real")]
    section_by_category = {
        "crypto": "Credential and secret protection",
        "hardcoded": "Credential and secret protection",
        "intent": "Component exposure / permission enforcement",
        "permission": "Component exposure / permission enforcement",
        "network": "Network and communication security",
        "reflection_dynamic": "Dynamic code loading / reflection boundary",
    }
    counts = Counter(section_by_category.get(r["stage1_category"], "Other") for r in verified)
    order = [
        "Credential and secret protection",
        "Component exposure / permission enforcement",
        "Network and communication security",
        "Dynamic code loading / reflection boundary",
    ]
    values = [counts.get(k, 0) for k in order]

    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    bars = ax.barh(np.arange(len(order)), values, color=[BLUE, ORANGE, GREEN, GRAY], alpha=0.82)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Reference vulnerability findings")
    ax.set_title("AAOS/MASVS-Aligned Control-Area Summary", pad=22)
    ax.text(
        0.5,
        1.035,
        "38 reference vulnerability findings grouped by primary Android security control area.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_xlim(0, max(values) + 4)
    ax.set_axisbelow(True)
    ax.grid(axis="x", linestyle=":", alpha=0.45)
    for bar, value in zip(bars, values):
        ax.text(value + 0.25, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=9)

    _caption(
        fig,
        "This maps the manually verified reference set, not AAOS prevalence; the primary >=2-role rule confirms 37 of these 38.",
        y=0.045,
    )
    fig.subplots_adjust(left=0.29, bottom=0.21, top=0.76)
    fig.savefig(OUT_DIR / "appendix_a4_mapping_summary.png")
    plt.close(fig)


def appendix_validation_track_comparison() -> None:
    final_metrics = _load_json("data/reports/aggregate/final_metrics_n47.json")
    codex = _load_json("data/reports/aggregate/codex_multimodel_agreement.json")
    assert isinstance(final_metrics, dict)
    assert isinstance(codex, dict)

    main = final_metrics["stage3_verified_reporting_ge_2_of_3"]
    mcnemar = final_metrics["mcnemar"]["exact_binomial_two_tailed_p"]
    support = final_metrics["supporting_measurements"]
    native_sample = support["native_static_scan_sample"]
    rag = support["rag_intrinsic_ablation"]
    codex_2of3 = codex["metrics"]["codex_2of3_consensus"]
    codex_best = codex["metrics"]["codex_models"]["gpt-5.5"]
    rows = [
        [
            "Primary multi-role\nLLM review",
            "Candidate finding\nconfirm/reject quality",
            f"TP {main['tp']}, FP {main['fp']}, FN {main['fn']}\nagainst 38-reference set;\nF1 {main['f1'] * 100:.1f}%",
            "Main static\nresult",
        ],
        [
            "Paired\ncomparison",
            "LLM-only scan vs\ncontext-aware review",
            f"McNemar exact\np={mcnemar:.4f}",
            "Same-row\nimprovement test",
        ],
        [
            "Independent LLM\ncross-review",
            "Model/prompt\nrobustness check",
            f"2-of-3 consensus F1:\n{codex_2of3['f1'] * 100:.1f}%;\n"
            f"best single-reviewer F1:\n{codex_best['f1'] * 100:.1f}%",
            "Did not outperform\ncalibrated review",
        ],
        [
            "Native-code\nboundary scan",
            "Selected native\nboundary sample",
            f"{native_sample['n_samples']} samples;\n"
            f"{native_sample['additional_native_bound_vulnerabilities']} additional native-code-boundary\nvulnerabilities",
            "Boundary check,\nnot F1",
        ],
        [
            "Retrieval-grounded\nconsistency check",
            "Retrieval verdict\nand AAOS alignment",
            f"Verdict agreement:\n{rag['nearest_neighbor_verdict_propagation'] * 100:.1f}%;\n"
            f"category agreement:\n{rag['aaos_category_alignment'] * 100:.1f}%",
            "Intrinsic retrieval\ncheck",
        ],
    ]

    fig, ax = plt.subplots(figsize=(12.6, 5.5))
    ax.axis("off")
    ax.set_title("Supporting Validation Tracks And Their Measurement Roles", pad=22)
    ax.text(
        0.5,
        0.94,
        "Each validation track answers a different question around the main static result; the metrics should not be pooled.",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=9,
        color=MUTED,
    )

    table = ax.table(
        cellText=rows,
        colLabels=["Track", "What it checks", "Measured result", "How to read it"],
        cellLoc="left",
        colLoc="left",
        colWidths=[0.18, 0.30, 0.25, 0.27],
        bbox=[0.02, 0.14, 0.96, 0.72],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.1)
    table.scale(1, 1.30)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d7dce2")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("#e9eef4")
            cell.set_text_props(weight="bold", color=TEXT)
        elif row % 2 == 0:
            cell.set_facecolor("#f7f9fb")
        else:
            cell.set_facecolor("white")

    _caption(
        fig,
        "F1, paired-test p-values, native-boundary counts, and retrieval-alignment rates are intentionally reported separately.",
        y=0.065,
    )
    fig.subplots_adjust(bottom=0.06, top=0.86)
    fig.savefig(OUT_DIR / "appendix_a5_validation_track_comparison.png")
    plt.close(fig)


def main() -> None:
    chart_category_distribution()
    chart_severity_heatmap()
    chart_fp_rate_trend()
    chart_deobf_accuracy_trend()
    chart_ablation_bars()
    appendix_corpus_composition()
    appendix_bootstrap_ci()
    appendix_obfuscation_score_distribution()
    appendix_mapping_summary()
    appendix_validation_track_comparison()
    print(f"Wrote 10 charts to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
