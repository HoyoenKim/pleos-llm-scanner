#!/usr/bin/env python
"""
9주차 progress report v3 — **1 page** version aligned with current measurements.

수업개요 (PDF):
- 매주 progress report PPT 1장
- 맨위에 연구진행 기간

기존 v1 (2026-04-29 작성, n=12 시점)을 base로 사용 — 동일 폰트/레이아웃 유지.
2026-04-30 시점 측정값 (combined n=18 + Phase B-4.c.2 + Phase C entropy)을 반영.

산출: ../pptx/v3/자율주행연구프로젝트1_9주차_2025311610_김호연_v3.pptx
"""
import shutil
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).parent.parent.parent
SRC = ROOT / "pptx" / "자율주행연구프로젝트1_9주차_2025311610_김호연.pptx"
DST = ROOT / "pptx" / "v3" / "자율주행연구프로젝트1_9주차_2025311610_김호연_v3.pptx"


# 16 paragraphs, indexed 0~15. v1 keeps numbered headers as two runs ("1) " + title).
NEW_TEXTS: dict[int, str | tuple[str, str]] = {
    # 0: Progress Report (period) — keep
    # 1: 프로젝트 제목 — keep
    2: "최종 파이프라인 성능 평가 + 베이스라인 비교 + 시각화 (Combined GT n=18)",
    3: ("self GT (PleOS 3종 n=15) + MASTG 외부 GT (UnCrackable-Level1 n=3) = combined n=18 기준으로 "
        "9주차 시점 최종 성능 지표 확정. Ablation A·B 변형 + 기존 4 도구 베이스라인 비교 + 시각화 6 차트로 정량 우위 입증."),
    # 4: "1) " + "최종 파이프라인 성능 재측정" — keep
    5: "측정 방법: src/eval.py 자동 측정 (P/R/F1, per-APK·per-category). 합의 임계 sensitivity는 src/ablation.py 별도 측정",
    6: ("측정 대상: PleOS 3종 (VehicleControl + sync.syslog + llm.model.provider) n=15 + "
        "MASTG UnCrackable-Level1 n=3 = combined n=18. Level2/r2pay는 native 의존 boundary case 별도 보고"),
    7: ("결과: 가설(1차 25% / 3차 7% / P 0.93) 대비 — 1차 오탐률 22.2% (-2.8%p 충족), Stage 1 F1 0.875 / MASTG-only P 100%. "
        "Stage 3 D3=B 합의 (공격자/방어자/도메인전문가) ≥2/3에서 P 100% / R 90.9% / F1 0.952 — 가설 0.93 도달·초과. "
        "Strong TP 9건. Stage 2.b deep-link 4중 차단으로 vc-1~4 FP 4건 CONFIRMED"),
    # 8: "2) " + "Ablation Study 수행" — keep
    9: ("방법: A 변형 (stage1 only / +stage2 caller / +stage3 ≥3/3) + "
        "B 변형 (합의 임계 ≥1/3 / ≥2/3 / ≥3/3) — src/ablation.py 자동 측정"),
    10: "목적: 각 단계의 P/R/F1 기여도 분리 정량화 + 합의 임계 default(≥2/3)의 정당성 확인",
    11: ("결과: A.1 F1=0.875 → A.2 F1=1.000 (P-ceiling) → A.3 ≥3/3 F1=0.783*. "
         "B ≥1/3 → ≥2/3 → ≥3/3: F1 0.846 → 0.952 → 0.900 — ≥2/3 최적. "
         "Phase C entropy로 PleOS HIGH 난독화 0.2~0.4% (가정과 다름) 발견"),
    # 12: "3) " + "베이스라인 도구 비교 실험" — keep
    13: ("비교 대상: ① JADX + 수동 ② 단일 LLM 1-pass ③ android-scanner-ai (Gemini key) ④ Androidmeda (Apache 2.0). "
         "환경 제약으로 ③/④는 정성 비교"),
    14: ("결과: ③/④ 모두 README에 자체 P/R/F1 측정 부재 — 본 연구의 차별 gap. "
         "시간 cost ① 6~7h vs 본 파이프라인 ~2h (3x 단축). ② 단일 LLM P 77.8% → multi-stage 거치며 P 100% (+22.2%p)"),
    15: ("향후 계획: Phase D (10주차) — AAOS 매핑 (§3.7/§4.2/§5.1) + TARA 산출물 + 사례 연구 5건 + 보고서 v0.9. "
         "시각화 6 차트 data/viz/, 16-슬라이드 중간정리 별도 파일"),
}


def update_paragraph(para, new_text: str) -> None:
    """Replace paragraph text in-place — preserves font / level / alignment of run 0."""
    if not para.runs:
        # No runs — create one with theme-default font (rare)
        run = para.add_run()
        run.text = new_text
        return
    para.runs[0].text = new_text
    # Wipe runs 1..N (keep their <r> elements but blank text) so visual stays clean.
    for r in para.runs[1:]:
        r.text = ""


def main() -> None:
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC, DST)

    prs = Presentation(str(DST))
    sl = prs.slides[0]
    # The single PLACEHOLDER (Rectangle 3) holds all 16 paragraphs.
    target = None
    for shp in sl.shapes:
        if shp.has_text_frame and shp.name == "Rectangle 3":
            target = shp
            break
    if target is None:
        # Fallback — first text-bearing shape
        target = next(s for s in sl.shapes if s.has_text_frame)

    paragraphs = list(target.text_frame.paragraphs)
    assert len(paragraphs) == 16, f"expected 16 paragraphs, got {len(paragraphs)}"

    for idx, new in NEW_TEXTS.items():
        para = paragraphs[idx]
        if isinstance(new, tuple):
            # Two-run paragraph — preserve numbering on run 0, set title on run 1
            num, title = new
            if len(para.runs) >= 2:
                para.runs[0].text = num
                para.runs[1].text = title
                for r in para.runs[2:]:
                    r.text = ""
            else:
                update_paragraph(para, num + title)
        else:
            update_paragraph(para, new)

    prs.save(str(DST))
    print(f"Wrote: {DST}")
    print(f"Size: {DST.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
