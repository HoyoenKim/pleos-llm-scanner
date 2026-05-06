"""R2.a — Multi-perspective consensus disagreement matrix.

Diversity 가 진짜인가? 시각 3종 (attacker / defender / domain_expert) 의
finding 별 flag 일치율 + Cohen's kappa 측정.

Outputs:
  data/reports/perspective_agreement.md
  data/reports/perspective_agreement.json
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "reports" / "stage3_ensemble.json"
OUT = ROOT / "data" / "reports"

PERSPECTIVES = ("attacker", "defender", "domain_expert")


def cohens_kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    p_a1 = sum(a) / n
    p_b1 = sum(b) / n
    pe = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
    if pe == 1.0:
        return 1.0
    return round((po - pe) / (1 - pe), 3)


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    findings = data["results"]
    n = len(findings)

    flag = {p: [] for p in PERSPECTIVES}
    for f in findings:
        flagged = set(f.get("consensus_perspectives") or [])
        for p in PERSPECTIVES:
            flag[p].append(1 if p in flagged else 0)

    flag_counts = {p: sum(flag[p]) for p in PERSPECTIVES}

    # Pairwise agreement + kappa
    pair_stats = {}
    for a, b in combinations(PERSPECTIVES, 2):
        agree = sum(1 for x, y in zip(flag[a], flag[b]) if x == y)
        both_flag = sum(1 for x, y in zip(flag[a], flag[b]) if x == 1 and y == 1)
        only_a = sum(1 for x, y in zip(flag[a], flag[b]) if x == 1 and y == 0)
        only_b = sum(1 for x, y in zip(flag[a], flag[b]) if x == 0 and y == 1)
        none = sum(1 for x, y in zip(flag[a], flag[b]) if x == 0 and y == 0)
        pair_stats[f"{a}-{b}"] = {
            "agree": agree,
            "agree_pct": round(100 * agree / n, 1),
            "both_flag": both_flag,
            f"only_{a}": only_a,
            f"only_{b}": only_b,
            "neither": none,
            "cohens_kappa": cohens_kappa(flag[a], flag[b]),
        }

    # Consensus distribution
    cdist = {0: 0, 1: 0, 2: 0, 3: 0}
    for f in findings:
        cdist[f.get("consensus_count", 0)] += 1

    payload = {
        "measurement_id": "R2.a",
        "description": "Per-finding flag agreement across attacker / defender / domain_expert perspectives. "
                       "Measures whether the multi-perspective ensemble produces diverse verdicts or converges trivially.",
        "measured_at": "2026-05-06",
        "scope": f"n={n} findings from data/reports/stage3_ensemble.json",
        "flag_counts_per_perspective": flag_counts,
        "consensus_count_distribution": cdist,
        "pairwise": pair_stats,
        "interpretation": {
            "kappa_scale": "κ < 0: poor / 0.0–0.20: slight / 0.21–0.40: fair / 0.41–0.60: moderate / "
                           "0.61–0.80: substantial / 0.81–1.00: almost perfect (Landis & Koch 1977)"
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "perspective_agreement.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# R2.a — Perspective disagreement matrix (multi-prompt ensemble)",
        "",
        f"_Measured: 2026-05-06 / scope: n={n} findings from `data/reports/stage3_ensemble.json`_",
        "",
        "## 시각별 flag 빈도",
        "",
        "| Perspective | flagged | flag rate |",
        "|---|---:|---:|",
    ]
    for p in PERSPECTIVES:
        lines.append(f"| {p} | {flag_counts[p]} | {round(100*flag_counts[p]/n,1)}% |")

    lines += [
        "",
        "## Consensus count 분포",
        "",
        "| consensus_count | finding 수 | 비율 |",
        "|---:|---:|---:|",
    ]
    for k in (3, 2, 1, 0):
        lines.append(f"| {k}/3 | {cdist[k]} | {round(100*cdist[k]/n,1)}% |")

    lines += [
        "",
        "## Pairwise agreement + Cohen's κ",
        "",
        "| Pair | agree | agree % | both flag | only A | only B | neither | κ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a, b in combinations(PERSPECTIVES, 2):
        s = pair_stats[f"{a}-{b}"]
        lines.append(
            f"| {a} ↔ {b} | {s['agree']} | {s['agree_pct']}% | {s['both_flag']} | "
            f"{s[f'only_{a}']} | {s[f'only_{b}']} | {s['neither']} | {s['cohens_kappa']} |"
        )

    lines += [
        "",
        "## RQ2 implication",
        "",
        "**시각 간 diversity 가 진짜인가?** Cohen's κ 가 낮을수록 시각 간 disagreement 가 많음 = "
        "perspective 다양성이 실제로 작동. 모두 동일 finding 을 flag 하면 κ → 1.0 이고 멀티 시각이 redundant 가 됨.",
        "",
        f"본 측정 (n={n}, 동일 모델 Opus 4.7) 에서:",
        f"- 평균 flag rate: attacker {round(100*flag_counts['attacker']/n,1)}% / "
        f"defender {round(100*flag_counts['defender']/n,1)}% / "
        f"domain_expert {round(100*flag_counts['domain_expert']/n,1)}%",
        f"- 만장일치 (3/3): {cdist[3]}건 ({round(100*cdist[3]/n,1)}%) / "
        f"단독 flag (1/3): {cdist[1]}건 ({round(100*cdist[1]/n,1)}%)",
        "- κ 해석은 위 표 참조. κ ≥ 0.61 (substantial) 이면 합의 임계 ≥2/3 가 reliable.",
        "",
        "**한계**: 본 측정은 동일 모델 (Opus 4.7) 에 시각 prompt 만 다르게 한 결과. "
        "외부 모델 (Sonnet / Gemini 등) cross-read 측정값 (RQ2.b) 이 추가되어야 "
        "multi-prompt 가 multi-model 의 대체재인지 판단 가능. 본 학기 환경 제약으로 RQ2.b 는 Future Work.",
        "",
    ]
    (OUT / "perspective_agreement.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote: data/reports/perspective_agreement.{md,json}")
    print(f"flag rates: {flag_counts}")
    print(f"pairwise kappa: {[(k, v['cohens_kappa']) for k, v in pair_stats.items()]}")


if __name__ == "__main__":
    main()
