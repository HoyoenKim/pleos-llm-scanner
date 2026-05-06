"""R1.c — Paired McNemar test for Stage 1 vs Stage 3 (n=28).

본 학기 처음으로 RQ1 의 Stage 1 → Stage 3 향상이 우연이 아닌가 통계 검정.

Per-finding paired classification (correct = matches GT label):
  Stage 1 = LLM emit 한 finding (모든 GT 라벨이 reports 에 있어 stage 1 candidate
            = TP/FP 구분은 GT is_real 이 결정)
  Stage 3 = ≥2/3 합의 reported (TP), 그 외 (1/3, 0/3) = unreported (FN against GT TP)

Outputs:
  data/reports/mcnemar_test.md
  data/reports/mcnemar_test.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GT = ROOT / "data" / "ground_truth" / "combined_labels.json"
S3 = ROOT / "data" / "reports" / "stage3_ensemble.json"
OUT = ROOT / "data" / "reports"


def stage_correct(stage_label: str, gt_is_real: object) -> int:
    """1 if the stage's verdict matches GT, else 0."""
    if stage_label == "TP" and gt_is_real is True:
        return 1
    if stage_label == "FP" and gt_is_real is False:
        return 1
    if stage_label == "FN" and gt_is_real is True:
        return 0
    return 0


def main() -> None:
    gt = {lbl["id"]: lbl for lbl in json.loads(GT.read_text(encoding="utf-8"))["labels"]}
    s3 = {r["id"]: r for r in json.loads(S3.read_text(encoding="utf-8"))["results"]}

    rows = []
    for fid, lbl in gt.items():
        is_real = lbl.get("is_real")
        # Stage 1 verdict: every GT label was emitted as a candidate. Correct iff
        # GT TP (is_real=True) — Stage 1 reports it = correct identification of an
        # actual vulnerability. Stage 1 incorrect iff GT FP (false alarm).
        s1_correct = 1 if is_real is True else 0
        # Stage 3 verdict: ≥2/3 consensus = reported (TP), 1/3 or 0/3 = unreported.
        s3_entry = s3.get(fid)
        s3_count = s3_entry.get("consensus_count") if s3_entry else 0
        s3_reported = (s3_count or 0) >= 2
        # Correct iff (reported AND is_real=True) OR (unreported AND is_real=False).
        if s3_reported and is_real is True:
            s3_correct = 1
        elif (not s3_reported) and is_real is False:
            s3_correct = 1
        else:
            s3_correct = 0

        rows.append({
            "id": fid,
            "is_real": is_real,
            "s1_correct": s1_correct,
            "s3_correct": s3_correct,
            "s3_consensus": s3_count,
        })

    n = len(rows)
    a = sum(1 for r in rows if r["s1_correct"] == 1 and r["s3_correct"] == 1)
    b = sum(1 for r in rows if r["s1_correct"] == 1 and r["s3_correct"] == 0)
    c = sum(1 for r in rows if r["s1_correct"] == 0 and r["s3_correct"] == 1)
    d = sum(1 for r in rows if r["s1_correct"] == 0 and r["s3_correct"] == 0)
    assert a + b + c + d == n

    # McNemar's chi-square (uncorrected). For small b+c, exact binomial preferred.
    if (b + c) > 0:
        chi_sq = (b - c) ** 2 / (b + c)
    else:
        chi_sq = 0.0

    # Exact two-tailed binomial p-value (X ~ Bin(b+c, 0.5))
    bc = b + c
    if bc == 0:
        p_exact = 1.0
    else:
        m = min(b, c)
        # P(X <= m) under Bin(bc, 0.5)
        p_one_tail = sum(math.comb(bc, k) for k in range(0, m + 1)) / (2 ** bc)
        p_exact = min(1.0, 2 * p_one_tail)

    # McNemar's chi-square p-value (df=1) — analytical via incomplete gamma.
    # For df=1: p = erfc(sqrt(chi/2)).
    p_chi = math.erfc(math.sqrt(chi_sq / 2)) if chi_sq > 0 else 1.0

    payload = {
        "measurement_id": "R1.c",
        "description": "Paired McNemar test for Stage 1 vs Stage 3 (≥2/3 consensus) classification on combined GT (n=28).",
        "measured_at": "2026-06-07",
        "scope": f"n={n}",
        "contingency": {
            "a_s1_correct_s3_correct": a,
            "b_s1_correct_s3_incorrect": b,
            "c_s1_incorrect_s3_correct": c,
            "d_s1_incorrect_s3_incorrect": d,
        },
        "chi_sq_uncorrected": round(chi_sq, 3),
        "p_value_chi_sq_df1": round(p_chi, 4),
        "p_value_exact_binomial_two_tailed": round(p_exact, 4),
        "interpretation": (
            f"b={b}, c={c} (b+c={bc}). With small discordant pairs, exact binomial "
            f"is preferred. p_exact = {round(p_exact, 4)}. "
            f"At α=0.05, the difference between Stage 1 and Stage 3 is "
            f"{'statistically significant' if p_exact < 0.05 else 'NOT statistically significant'} "
            "— the corpus n=28 is too small to reject the null of marginal homogeneity. "
            "Sample expansion to n ≥ 50 (DIVA / additional commercial corpora) is needed for "
            "a powered test."
        ),
        "rows": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mcnemar_test.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md = [
        "# R1.c — Paired McNemar test (Stage 1 vs Stage 3, n=28)",
        "",
        f"_Measured: 2026-06-07 / scope: n={n}_",
        "",
        "## 2x2 contingency table",
        "",
        "Stage 별 'GT 와 일치 여부' 의 paired binary outcome.",
        "",
        "|  | Stage 3 correct | Stage 3 incorrect | total |",
        "|---|---:|---:|---:|",
        f"| Stage 1 correct | a = {a} | b = {b} | {a+b} |",
        f"| Stage 1 incorrect | c = {c} | d = {d} | {c+d} |",
        f"| total | {a+c} | {b+d} | **{n}** |",
        "",
        "## 검정 통계량",
        "",
        f"- McNemar's chi-square (uncorrected): χ² = {chi_sq:.3f}  (df=1)",
        f"- p-value (chi-square approximation): **{p_chi:.4f}**",
        f"- p-value (exact binomial, two-tailed): **{p_exact:.4f}**  ← b+c={bc} 작으므로 권고",
        "",
        "## 해석",
        "",
    ]
    if p_exact < 0.05:
        md.append("p < 0.05 → Stage 1 과 Stage 3 의 paired 분류 일치율 차이는 **통계적으로 유의**. Stage 3 의 향상이 우연이 아니라는 첫 증거.")
    else:
        md.append(f"p_exact = **{p_exact:.4f}** → α=0.05 기준으로 **통계적 유의성 미달**. n=28, b+c={bc} 의 표본 크기에서는 검정 power 가 부족하다. Stage 1 과 Stage 3 의 paired 차이가 우연이 아니라는 결론을 통계적으로 도출하기에는 표본이 작다.")
    md += [
        "",
        "## 한계 + Future Work",
        "",
        "- McNemar's test 는 paired discordant pair 수 (b + c) 가 작으면 power 가 낮다. 본 측정 b+c = "
        f"{bc} 로 매우 작음.",
        "- n=28 (combined GT) 까지 확장된 corpus 에서도 이 한계가 명확. 다음 단계 R1.d (n ≥ 50) "
        "확장 후 재측정 필요.",
        "- 본 측정은 단순 paired 검정. effect size (odds ratio of discordant pairs = b/c) 도 함께 보고:",
        f"  - b/c = {b}/{c} → Stage 3 가 Stage 1 의 오류를 잡은 비율이 더 큼 (c > b 이면 Stage 3 가 더 좋음).",
        "",
        "## RQ1 implication",
        "",
        f"- 본 학기 데이터에서 Stage 3 가 Stage 1 의 오류 {c} 건 ({c}/{n} = {round(100*c/n,1)}%) 을 추가로 정확히 처리.",
        f"- Stage 1 이 정답인데 Stage 3 가 누락한 케이스 b = {b} 건 ({b}/{n} = {round(100*b/n,1)}%).",
        f"- net 효과: Stage 3 가 정답 케이스를 추가로 +{c-b} 건 더 잡았으나 (n={n}, p_exact={p_exact:.4f}) 이는 통계적으로 유의하지 않다.",
        f"- 정직한 결론: bootstrap CI 좁힘 (R1.b 결과) 은 측정값의 분포를 좁혔지만, paired test 의 통계적 유의성 (R1.c) 는 본 표본 크기로 검출 불가. 본 학기의 'Stage 3 향상' 주장은 **effect size 는 양수 (Stage 3 의 net 정정 +{c-b}건) 이지만 표본 우연성 배제는 미완**.",
        "",
    ]
    (OUT / "mcnemar_test.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote: data/reports/mcnemar_test.{{md,json}}")
    print(f"contingency a={a} b={b} c={c} d={d} (n={n})")
    print(f"chi_sq={chi_sq:.3f}  p_chi={p_chi:.4f}  p_exact={p_exact:.4f}")


if __name__ == "__main__":
    main()
