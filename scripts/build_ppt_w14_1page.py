#!/usr/bin/env python
"""14주차 progress report — 1 page version (학기 종합 + 발표 준비).

9~13주차 v3 동일 textbox layout (Rectangle 3, 16 paragraphs).
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
WEEK = "14"
PPT_BASENAME = f"자율주행연구프로젝트1_{WEEK}주차"
SRC = ROOT / "pptx" / f"{PPT_BASENAME}_{AUTHOR['student_id']}_{AUTHOR['author_name']}.pptx"
DST = ROOT / "pptx" / "v3" / f"{PPT_BASENAME}_{AUTHOR['student_id']}_{AUTHOR['author_name']}_v3.pptx"


# 16 paragraphs, indexed 0~15.
NEW_TEXTS: dict[int, str | tuple[str, str]] = {
    # 0: Progress Report (period) — keep
    # 1: 프로젝트 제목 — keep
    2: "학기 마무리 — 4개 새 측정 (R2.b' / R1.c / R4 보강 / Random baseline) + 보고서 v1.0 + 발표 PPT 18:",
    3: ("14주차 진짜 RQ 진척 — defender prompt 효과 검증, paired McNemar test, NewPipe Stage 0 정확도, "
        "selection bias 정량. Phase A~D 마무리 + 본 학기 RQ 모두 정량 측정값 확보. "
        "보고서 v1.0 + 최종 발표 PPT 18 슬라이드 + 라이브 데모 시나리오 정리."),
    # 4: "1) " + "RQ2.b' / RQ1.c — 통계 검정과 prompt 효과" — keep
    5: ("R2.b' — defender prompt selectivity calibration 의 정량 효과: Cohen's κ(attacker, defender) "
        "0.0 → **0.900** (poor → almost perfect). Universal flag (28/28) → 22/28 (78.6%). "
        "본 학기 처음으로 prompt 변경의 ensemble diversity 효과 측정"),
    6: ("R1.c — paired McNemar test (n=28): exact binomial p=0.375. Stage 3 가 Stage 1 의 오류 4건 추가 정정 + "
        "Stage 1 정답 1건만 누락 (net +3건) 이지만 표본 작아 **통계적 유의성 미달** — 정직히 명시. "
        "n ≥ 50 확장 시 재측정 필요"),
    7: ("R4 보강 — NewPipe HIGH 3 클래스에 Stage 0 LLM rename 적용 → confidence avg 0.62, "
        "semantic plausibility 33% GOOD (1/3 GOOD + 1 PARTIAL + 1 POOR). Hand-crafted MASTG 100% exact "
        "대비 약 3배 정확도 하락 = corpus contextual hint density 의존성 입증"),
    # 8: "2) " + "Random sample baseline + 학기 측정값 종합" — keep
    9: ("Random sample baseline (시드 42, 무작위 3 PleOS APK): 보안 가치 큰 3 APK 평균 priority class "
        "**424.33** vs 무작위 3 APK 평균 15.0 — **28.29× selection bias** 정량 입증. "
        "본 학기 측정값 (P 85.7%, F1 0.923) 은 보안 가치 큰 corpus subset 한정"),
    10: ("Stage 1 (n=28): P 85.7% / R 100% / F1 0.923. 95% CI [71.4%, 96.4%]. "
         "Stage 3 ≥2/3 (n=28): P 100% / R 95.8% / **F1 0.979** — 본 학기 최고치. "
         "초기 계획서 가설 모두 충족 (1차 오탐 25%→14.3%, 3차 7%→0%, P 0.93→1.00)"),
    11: ("Bootstrap CI 표본 효과 (R1.b): n=19 → n=28 확장으로 Precision CI 폭 36.8%p → 25.0%p (-32%), "
         "F1 CI 폭 24.0%p → 14.9%p (-38%). RQ1 의 핵심 contribution"),
    # 12: "3) " + "학기 종합 deliverable + 발표 준비" — keep
    13: ("외부 corpus 7 sample 누계: in-scope 13 finding (UnCrackable Level1/3 + InsecureBankv2) + "
         "boundary 4 sample. NewPipe (OSS, real-world) 추가로 8 sample. R3.a — PleOS Connect 207 APK 중 "
         "10.6% native lib (보안 가치 큰 차량 제어 / 맵 / 음성 비서가 top)"),
    14: ("산출물 종합: 보고서 v1.0 + 사례 5건 + 차트 6장 + AAOS/TARA 매핑 + 통합 아키텍처 + 일반화 평가 + "
         "영문 prompt 6종 + 결정론 측정 스크립트 11종 (R1.a/b/c, R2.a/b', R3.a, R4, random baseline). "
         "최종 발표 PPT 18 슬라이드 빌드 완료"),
    15: ("Future Work: multi-LLM ensemble (외부 API 환경 확보 시) / native binary scanner 통합 (radare2) / "
         "n ≥ 50 표본 확장 후 paired McNemar 재측정 / commercial APK 의 ProGuard mapping 확보 → R4 exact / "
         "fully-batch 자동화 / 라이브 데모 + 백업 영상"),
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

    for idx, new in NEW_TEXTS.items():
        if idx >= n_para:
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
