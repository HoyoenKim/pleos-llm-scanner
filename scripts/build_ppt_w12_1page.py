#!/usr/bin/env python
"""12주차 progress report — 1 page version.

9/10/11주차 v3 와 동일 textbox layout (Rectangle 3, 16 paragraphs).
사용자가 미리 작성한 `pptx/자율주행연구프로젝트1_12주차_*.pptx` 를 base 로 사용.

작성자/제출 파일명은 `scripts/_author.json` 에서 로드.
"""
import json
import shutil
from pathlib import Path

from pptx import Presentation


def _load_author() -> dict:
    here = Path(__file__).parent
    p = here / "_author.json"
    if not p.exists():
        p = here / "_author.example.json"
    with p.open(encoding="utf-8") as f:
        return json.load(f)


AUTHOR = _load_author()
ROOT = Path(__file__).parent.parent.parent
WEEK = "12"
PPT_BASENAME = f"자율주행연구프로젝트1_{WEEK}주차"
SRC = ROOT / "pptx" / f"{PPT_BASENAME}_{AUTHOR['student_id']}_{AUTHOR['author_name']}.pptx"
DST = ROOT / "pptx" / "v3" / f"{PPT_BASENAME}_{AUTHOR['student_id']}_{AUTHOR['author_name']}_v3.pptx"


# 16 paragraphs, indexed 0~15.
NEW_TEXTS: dict[int, str | tuple[str, str]] = {
    # 0: Progress Report (period) — keep
    # 1: 프로젝트 제목 — keep
    2: "표본 확장 (n=19 → n=28) + bootstrap CI 효과 정량 측정 + 외부 corpus boundary 6 sample 누계:",
    3: ("R1.d 강 시도로 외부 의도적 취약 corpus(InsecureBankv2) 도입 — 9 finding 모두 TP. "
        "표본 19 → 28 확장으로 Stage 1 Precision 78.9% → 85.7% / F1 0.882 → 0.922 / "
        "FP rate 21.1% → 14.3%, 동시에 bootstrap 95% CI 폭이 약 1/3 줄어듦."),
    # 4: "1) " + "R1.d 표본 확장 — 외부 corpus InsecureBankv2 도입" — keep
    5: ("외부 prebuilt APK 다운로드(github raw URL, ~5MB) → jadx 디컴파일 → priority class 5종 "
        "Stage 1 분석. 알려진 의도적 취약점이 모두 보고서 카테고리에 매핑: "
        "hardcoded AES key + zero IV + cleartext HTTP + 자격증명 logcat + exported provider/receiver"),
    6: ("9 finding 라벨링 (모두 TP, 의도된 vuln). 카테고리 분포: intent 4 / hardcoded 2 / crypto 1 / network 2. "
        "self GT 의 self-referential bias 외 외부 corpus 정답이 명확히 문서화된 corpus 로 보강"),
    7: ("combined GT n=19 → n=28 으로 갱신(`data/ground_truth/combined_labels.json`). 본 학기 처음으로 "
        "PleOS 자체 라벨 + MASTG + 외부 의도적 취약 corpus 3 source merged GT corpus 보유"),
    # 8: "2) " + "R1.b bootstrap CI — 표본 증가의 통계 효과" — keep
    9: ("Non-parametric percentile bootstrap 1000 iter, seed 42. n=19 → n=28 만으로 측정값 변화: "
        "Precision CI [57.9%, 94.7%] → [71.4%, 96.4%], F1 CI [73.3%, 97.3%] → [83.3%, 98.2%]"),
    10: ("CI 폭 정량 변화: Precision 36.8%p → 25.0%p (-32%), F1 24.0%p → 14.9%p (-38%), "
         "FP rate 36.8%p → 25.0%p (-32%). 본 학기 처음으로 'n 증가 → CI 좁힘' 직접 측정"),
    11: ("RQ1 actionable insight: 보고서의 정량 주장이 통계적으로 신뢰 가능한 corpus 크기 ≈ n=30+. "
         "다음 단계로 corpus n ≥ 40 까지 확장하면 ±5%p CI 가능 — Future Work"),
    # 12: "3) " + "외부 corpus boundary 6 sample 누계 + RQ3 강화" — keep
    13: ("MASTG 외부 corpus 6 sample 누계 — UnCrackable Level1/3 4 in-scope finding (P 100%) + "
         "Level2 / r2pay-v1.0 / HelloWord-JNI / certificatePinningXamarin 4 boundary cases (66.7%). "
         "Java/Kotlin scanner + native/non-Java binary scanner 의 분리된 stage 권고를 정량 입증"),
    14: ("R3.a corpus inventory (PleOS Connect 207 system APK 의 10.6% native lib 보유) 와 함께 "
         "한계 L1 (Java-only) 의 corpus-level + sample-level 두 axis 정량 evidence 확보"),
    15: ("향후 계획(13주차): 보고서 v0.9-r1 → v1.0 마무리 (지도교수 리뷰 반영 + 2026-05-07 새 측정값 통합), "
         "R4 real-world commercial APK 난독화 정확도 측정 시도"),
}


def update_paragraph(para, new_text: str) -> None:
    if not para.runs:
        run = para.add_run()
        run.text = new_text
        return
    para.runs[0].text = new_text
    for r in para.runs[1:]:
        r.text = ""


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"PPT base not found: {SRC}")
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC, DST)

    prs = Presentation(str(DST))
    sl = prs.slides[0]

    target = None
    for shp in sl.shapes:
        if shp.has_text_frame and shp.name == "Rectangle 3":
            target = shp
            break
    if target is None:
        target = next(s for s in sl.shapes if s.has_text_frame)

    paragraphs = list(target.text_frame.paragraphs)
    n_para = len(paragraphs)
    print(f"target shape: {target.name}, paragraphs: {n_para}")
    if n_para != 16:
        print(f"warning: expected 16 paragraphs, got {n_para} — applying best-effort")

    for idx, new in NEW_TEXTS.items():
        if idx >= n_para:
            print(f"  skip idx={idx} (out of range)")
            continue
        para = paragraphs[idx]
        if isinstance(new, tuple):
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
