#!/usr/bin/env python
"""Generate final report figures for the PleOS LLM scanner archive.

The main figure set explains the static-analysis experiment flow:

1. JADX output is checked for Java/Kotlin readability.
2. LLM candidates are filtered by Android context verification.
3. Verification changes the headline scan-quality metrics.
4. Verified vulnerabilities are reviewed by APK and severity.
5. The consensus threshold is justified.
6. Supporting validation tracks define robustness and boundaries.

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
    """Candidate verification by vulnerability pattern."""
    cats = [
        "Intent /\nexported component",
        "Hardcoded\nsecret",
        "Network\nconfig",
        "Crypto\nmisuse",
        "Permission\nexposure",
        "Dynamic code /\nreflection",
    ]
    kept = [14, 11, 7, 5, 0, 1]
    rejected = [4, 0, 2, 0, 3, 0]
    x = np.arange(len(cats))
    width = 0.42

    fig, ax = plt.subplots(figsize=(10.4, 5.2))
    b1 = ax.bar(x - width / 2, kept, width, label="Kept for reporting (TP)", color=BLUE)
    b2 = ax.bar(x + width / 2, rejected, width, label="Rejected after context check (FP)", color=ORANGE)

    ax.set_ylabel("Number of LLM-proposed candidates")
    ax.set_title("LLM Security Candidates After Context Verification", pad=24)
    ax.text(
        0.5,
        1.03,
        "47 candidates proposed from decompiled APK code; 38 kept for reporting, 9 rejected after Android context checks.",
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
    ax.legend(loc="upper right", frameon=False)

    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            if h:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.12, f"{int(h)}", ha="center", fontsize=9)

    _caption(
        fig,
        "Context verification checked manifest exposure, caller reachability, permission gates, route binding,\n"
        "and Android framework controls before deciding whether each candidate should remain reportable.",
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
    """Verified vulnerabilities by APK and severity."""
    apks = [
        "VehicleControl [PleOS]",
        "sync.syslog [PleOS]",
        "llm.model.provider [PleOS]",
        "account [PleOS]",
        "appmarket [PleOS]",
        "ambientai [PleOS]",
        "maps [PleOS]",
        "UnCrackable-L1 [MASTG]",
        "UnCrackable-L3 [MASTG]",
        "InsecureBankv2 [External]",
        "usb.handler [AOSP]",
        "statementservice [AOSP]",
    ]
    sev_levels = ["HIGH", "MEDIUM", "LOW"]
    verified_matrix = np.array(
        [
            [1, 1, 1],
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
            [0, 0, 0],
        ],
        dtype=int,
    )

    fig, ax = plt.subplots(figsize=(8.4, 6.8))
    im = ax.imshow(verified_matrix, aspect="auto", cmap="Blues", vmin=0, vmax=verified_matrix.max())
    ax.set_xticks(range(len(sev_levels)))
    ax.set_xticklabels(sev_levels)
    ax.set_yticks(range(len(apks)))
    ax.set_yticklabels(apks, fontsize=9)
    ax.set_title("Verified Security Vulnerabilities By APK And Severity", pad=30)
    ax.text(
        0.5,
        1.035,
        "38 verified vulnerabilities by final severity; PleOS rows are marked for project-target context.",
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
        "Rows marked [PleOS] are the project target apps; HIGH cells indicate priority targets for follow-up analysis.\n"
        "Runtime PoC tracks focus on selected PleOS rows, including VehicleControl and maps.",
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
    b1 = ax.bar(x - width / 2, only_llm, width, label="LLM Scan", color=BLUE)
    b2 = ax.bar(x + width / 2, verified, width, label="LLM Scan + Context Verification", color=ORANGE)
    ax.set_ylabel("Score (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_title("Scan Quality Before And After Verification", pad=28)
    ax.text(
        0.5,
        1.035,
        "Context verification removes measured false positives with a small recall trade-off.",
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
        "Verification checked manifest exposure, caller reachability, permission gates, route binding, and framework controls.\n"
        "McNemar exact p=0.0215 on 47 candidates.",
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
    ax.set_ylabel("HIGH-obfuscation classes (count)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{name}\n[{origin}]" for name, origin, _total, _high in rows], fontsize=8.2)
    ax.set_ylim(0, 52)
    ax.set_title("JADX Identifier-Pattern Obfuscation Screen", pad=26)
    ax.text(
        0.5,
        1.035,
        "HIGH classes are counted by a heuristic screen over JADX-style identifiers such as C0010a, m5a, and f2a.",
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
            Patch(facecolor=GREEN, alpha=0.78, label="MASTG obfuscation samples"),
            Patch(facecolor=ORANGE, alpha=0.78, label="Open-source ProGuard sample"),
            Patch(facecolor=BLUE, alpha=0.78, label="PleOS target APKs"),
        ],
        loc="upper right",
        frameon=False,
        fontsize=8.4,
    )
    _caption(
        fig,
        "Bars count classes scored as HIGH by a heuristic identifier-pattern screen; labels show HIGH / analyzed classes.\n"
        "This is a readability screen for static analysis, not a validated obfuscation benchmark or vulnerability metric.",
        y=0.075,
        size=8.2,
    )
    fig.subplots_adjust(bottom=0.20, top=0.80)
    fig.savefig(OUT_DIR / "01_obfuscation_profile_across_test_apks.png")
    plt.close(fig)


# --------------------------------------------------------------------------- 05
def chart_ablation_bars() -> None:
    """Consensus threshold trade-off."""
    labels = ["Any flag\n(>=1/3)", "Majority\n(>=2/3)", "Unanimous\n(>=3/3)"]
    precision = [84.4, 100.0, 100.0]
    recall = [100.0, 97.4, 86.8]
    f1 = [91.6, 98.7, 93.0]
    x = np.arange(len(labels))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9.3, 5.1))
    b1 = ax.bar(x - width, precision, width, label="Precision", color=BLUE)
    b2 = ax.bar(x, recall, width, label="Recall", color=GREEN)
    b3 = ax.bar(x + width, f1, width, label="F1", color=ORANGE)

    ax.set_ylabel("Score (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 112)
    ax.set_title("Consensus Threshold Trade-Off", pad=26)
    ax.text(
        0.5,
        1.035,
        "Majority consensus keeps precision at 100.0% while retaining 97.4% recall.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=3, frameon=False)
    ax.axvline(1, color="#111", alpha=0.08, linewidth=46, zorder=0)
    ax.text(1, 8, "final\nthreshold", ha="center", va="center", fontsize=8.0, color=MUTED)

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1.2, f"{h:.1f}", ha="center", fontsize=8.4)

    _caption(
        fig,
        "Any-flag consensus keeps every true issue but admits more false-positive candidates.\n"
        "Unanimous consensus is stricter but drops too many verified vulnerabilities.",
        y=0.070,
        size=8.3,
    )
    fig.subplots_adjust(bottom=0.18, top=0.74)
    fig.savefig(OUT_DIR / "05_consensus_threshold_tradeoff.png")
    plt.close(fig)


# --------------------------------------------------------------------------- 06
def chart_supporting_validation_summary() -> None:
    """Supporting validation tracks that bound the main static result."""
    rows = [
        {
            "track": "Corpus/statistics",
            "check": "Expanded candidate set\nand paired test",
            "result": "47 candidates;\nMcNemar p=0.0215",
            "meaning": "Verification improves\npaired decisions.",
        },
        {
            "track": "Local RAG",
            "check": "Nearest-neighbor verdict\nand AAOS alignment",
            "result": "85.1% / 85.1%",
            "meaning": "Useful retrieval signal;\nnot an end-to-end gain claim.",
        },
        {
            "track": "Native static scan",
            "check": "Selected .so boundary review",
            "result": "4 samples;\n0 extra native-bound\nvulnerabilities",
            "meaning": "Reduces one blind spot\nin the sampled set.",
        },
        {
            "track": "Codex cross-read",
            "check": "3-model comparison\nagainst calibrated baseline",
            "result": "Did not beat\nfinal consensus",
            "meaning": "Evidence packaging mattered\nmore than model count.",
        },
    ]

    fig, ax = plt.subplots(figsize=(12.4, 5.1))
    ax.axis("off")
    ax.set_title("Supporting Validation Tracks", pad=24)
    ax.text(
        0.5,
        0.94,
        "These checks support the final static-analysis result; they are not separate vulnerability-count sources.",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=9,
        color=MUTED,
    )

    col_labels = ["Track", "What was checked", "Result", "How to read it"]
    cell_text = [[r["track"], r["check"], r["result"], r["meaning"]] for r in rows]
    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc="left",
        colLoc="left",
        colWidths=[0.16, 0.30, 0.22, 0.32],
        bbox=[0.02, 0.17, 0.96, 0.68],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.0)
    table.scale(1, 1.62)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d8dde4")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("#e8eef5")
            cell.set_text_props(weight="bold", color=TEXT)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else LIGHT_GRAY)
            if col == 0:
                cell.set_text_props(weight="bold", color=TEXT)
            else:
                cell.set_text_props(color=TEXT)

    _caption(
        fig,
        "Main precision/recall numbers still come from the 47-candidate static evaluation.\n"
        "Runtime PoC evidence remains a separate local-evidence track.",
        y=0.065,
        size=8.2,
    )
    fig.subplots_adjust(bottom=0.06, top=0.86)
    fig.savefig(OUT_DIR / "06_supporting_validation_tracks.png")
    plt.close(fig)


# --------------------------------------------------------------------- appendix
def appendix_corpus_composition() -> None:
    labels = ["PleOS-customized", "MASTG", "InsecureBankv2", "AOSP-derived"]
    values = [30, 4, 9, 4]
    colors = [BLUE, GREEN, ORANGE, GRAY]

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    wedges, _texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct=lambda pct: f"{pct:.0f}%",
        startangle=90,
        colors=colors,
        wedgeprops={"linewidth": 1.0, "edgecolor": "white"},
        textprops={"color": "white", "fontsize": 9, "weight": "bold"},
    )
    ax.legend(
        wedges,
        [f"{label} ({value})" for label, value in zip(labels, values)],
        loc="center left",
        bbox_to_anchor=(0.92, 0.5),
        frameon=False,
        fontsize=9,
    )
    for t in autotexts:
        t.set_color("white")
    ax.set_title("Candidate Source Composition", pad=18)
    _caption(
        fig,
        "The evaluation uses 47 candidates from PleOS-customized APKs, public vulnerable apps, and AOSP-derived samples.",
        y=0.055,
    )
    fig.subplots_adjust(left=0.05, right=0.78, bottom=0.10, top=0.86)
    fig.savefig(OUT_DIR / "appendix_a1_corpus_composition.png")
    plt.close(fig)


def appendix_bootstrap_ci() -> None:
    metrics = ["Precision", "F1", "False-positive\nrate"]
    point = np.array([80.9, 89.4, 19.1])
    low = np.array([70.2, 82.5, 8.5])
    high = np.array([91.5, 95.6, 29.8])
    yerr = np.vstack([point - low, high - point])
    x = np.arange(len(metrics))

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    bars = ax.bar(x, point, color=[BLUE, GREEN, ORANGE], alpha=0.82, width=0.58)
    ax.errorbar(x, point, yerr=yerr, fmt="none", ecolor=TEXT, elinewidth=1.2, capsize=5)
    ax.set_ylabel("Score (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 110)
    ax.set_title("Bootstrap Confidence Intervals For Candidate Scan", pad=22)
    ax.text(
        0.5,
        1.035,
        "95% percentile intervals from the final 47-candidate evaluation.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    for bar, p, lo, hi in zip(bars, point, low, high):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            hi + 2.0,
            f"{p:.1f}\n[{lo:.1f}, {hi:.1f}]",
            ha="center",
            va="bottom",
            fontsize=8.2,
            color=TEXT,
        )

    _caption(
        fig,
        "The intervals describe candidate-generation uncertainty; verified reporting is summarized in the main metric chart.",
        y=0.065,
    )
    fig.subplots_adjust(bottom=0.18, top=0.76)
    fig.savefig(OUT_DIR / "appendix_a2_bootstrap_ci.png")
    plt.close(fig)


def appendix_obfuscation_score_distribution() -> None:
    apks = [
        ("UnCrackable-Level1", "MASTG"),
        ("UnCrackable-Level2", "MASTG"),
        ("r2pay-v1.0", "MASTG"),
        ("VehicleControl", "PleOS"),
        ("SyncSyslog", "PleOS"),
        ("LLMModelProvider", "PleOS"),
    ]
    scores: list[list[float]] = []
    for name, _origin in apks:
        data = _load_json(f"data/deobf/{name}.json")
        assert isinstance(data, dict)
        scores.append([r["composite_obf_score"] for r in data["results"]])

    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    colors = [GREEN if origin == "MASTG" else BLUE for _name, origin in apks]
    bp = ax.boxplot(
        scores,
        tick_labels=[name for name, _origin in apks],
        patch_artist=True,
        widths=0.55,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": 5},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.58)

    ax.axhline(y=0.7, color=RED, linestyle="--", linewidth=0.9, label="HIGH threshold (0.7)")
    ax.axhline(y=0.4, color=ORANGE, linestyle=":", linewidth=0.9, label="MEDIUM threshold (0.4)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("Composite obfuscation score [0, 1]")
    ax.set_title("Obfuscation Score Distribution", pad=22)
    ax.set_xticklabels([name for name, _origin in apks], rotation=10, ha="right", fontsize=8.3)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.45)

    legend_handles = [
        Patch(facecolor=GREEN, alpha=0.58, label="MASTG samples"),
        Patch(facecolor=BLUE, alpha=0.58, label="PleOS samples"),
    ] + ax.get_legend_handles_labels()[0]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=8.2)

    for i, (name, _origin) in enumerate(apks):
        data = _load_json(f"data/deobf/{name}.json")
        assert isinstance(data, dict)
        ratio = data["summary"]["high_obf_ratio"] * 100
        ax.text(i + 1, 1.02, f"HIGH={ratio:.1f}%", ha="center", fontsize=7.5, color=TEXT)

    _caption(
        fig,
        "This appendix keeps the full score distribution; the main obfuscation figure uses the simpler HIGH-ratio view.",
        y=0.055,
    )
    fig.subplots_adjust(bottom=0.22, top=0.82)
    fig.savefig(OUT_DIR / "appendix_a3_obfuscation_score_distribution.png")
    plt.close(fig)


def appendix_mapping_summary() -> None:
    labels = _load_json("data/ground_truth/combined_labels.json")
    assert isinstance(labels, dict)
    verified = [r for r in labels["labels"] if r.get("is_real")]
    section_by_category = {
        "crypto": "Credential protection",
        "hardcoded": "Credential protection",
        "intent": "Permission / component exposure",
        "permission": "Permission / component exposure",
        "network": "Communication security",
        "reflection_dynamic": "Dynamic code boundary",
    }
    counts = Counter(section_by_category.get(r["stage1_category"], "Other") for r in verified)
    order = [
        "Credential protection",
        "Permission / component exposure",
        "Communication security",
        "Dynamic code boundary",
    ]
    values = [counts.get(k, 0) for k in order]

    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    bars = ax.barh(np.arange(len(order)), values, color=[BLUE, ORANGE, GREEN, GRAY], alpha=0.82)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Verified vulnerabilities")
    ax.set_title("AAOS / MASVS Mapping Summary", pad=22)
    ax.text(
        0.5,
        1.035,
        "Verified vulnerabilities are grouped by the Android security control area they primarily exercise.",
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
        "This is a control-mapping view of the 38 verified vulnerabilities, not a prevalence claim about AAOS overall.",
        y=0.065,
    )
    fig.subplots_adjust(left=0.29, bottom=0.16, top=0.76)
    fig.savefig(OUT_DIR / "appendix_a4_mapping_summary.png")
    plt.close(fig)


def appendix_validation_track_comparison() -> None:
    final_metrics = _load_json("data/reports/aggregate/final_metrics_n47.json")
    codex = _load_json("data/reports/aggregate/codex_multimodel_agreement.json")
    native = _load_json("data/reports/aggregate/native_lib_inventory.json")
    assert isinstance(final_metrics, dict)
    assert isinstance(codex, dict)
    assert isinstance(native, dict)

    rows = [
        ("Final consensus", final_metrics["stage3_verified_reporting_ge_2_of_3"]["f1"] * 100, "Main result"),
        ("Codex 2/3 cross-read", codex["metrics"]["codex_2of3_consensus"]["f1"] * 100, "Support check"),
        ("Best Codex single model", codex["metrics"]["codex_models"]["gpt-5.5"]["f1"] * 100, "Support check"),
        ("Native APKs with .so", native["overall"]["pct"], "Boundary inventory"),
    ]
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    colors = [BLUE, ORANGE, ORANGE, GRAY]

    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    bars = ax.barh(np.arange(len(labels)), values, color=colors, alpha=0.82)
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Percent")
    ax.set_title("Cross-Validation Track Comparison", pad=22)
    ax.text(
        0.5,
        1.035,
        "Comparison tracks contextualize the main result but use different measurement meanings.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    ax.set_axisbelow(True)
    ax.grid(axis="x", linestyle=":", alpha=0.45)

    for bar, (_label, value, note) in zip(bars, rows):
        ax.text(value + 1.0, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%  {note}", va="center", fontsize=8.6)

    _caption(
        fig,
        "F1 rows are scan-quality metrics; the native row is inventory coverage and should not be read as F1.",
        y=0.065,
    )
    fig.subplots_adjust(left=0.28, bottom=0.16, top=0.76)
    fig.savefig(OUT_DIR / "appendix_a5_validation_track_comparison.png")
    plt.close(fig)


def main() -> None:
    chart_category_distribution()
    chart_severity_heatmap()
    chart_fp_rate_trend()
    chart_deobf_accuracy_trend()
    chart_ablation_bars()
    chart_supporting_validation_summary()
    appendix_corpus_composition()
    appendix_bootstrap_ci()
    appendix_obfuscation_score_distribution()
    appendix_mapping_summary()
    appendix_validation_track_comparison()
    print(f"Wrote 11 charts to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
