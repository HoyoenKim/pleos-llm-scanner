#!/usr/bin/env python
"""11주차 progress report — 1 page version.

9주차 / 10주차 v3 와 동일 textbox layout (Rectangle 3, 16 paragraphs).
사용자가 미리 작성한 `pptx/자율주행연구프로젝트1_11주차_*.pptx` 를 base 로 사용.

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
WEEK = "11"
PPT_BASENAME = f"자율주행연구프로젝트1_{WEEK}주차"
SRC = ROOT / "pptx" / f"{PPT_BASENAME}_{AUTHOR['student_id']}_{AUTHOR['author_name']}.pptx"
DST = ROOT / "pptx" / "v3" / f"{PPT_BASENAME}_{AUTHOR['student_id']}_{AUTHOR['author_name']}_v3.pptx"


# 16 paragraphs, indexed 0~15.
NEW_TEXTS: dict[int, str | tuple[str, str]] = {
    # 0: Progress Report (period) — keep
    # 1: 프로젝트 제목 — keep
    2: "한계 5종 근본 원인 분석 + 운영 비용 평가 + 외부 corpus boundary 추가 측정:",
    3: ("Phase A~D를 통해 드러난 본 파이프라인의 구조적 한계와 근본 원인을 5 카테고리(L1~L5)로 정리. "
        "운영 시점 시간/금전/메모리/확장성 trade-off 평가. 동시에 MASTG 외부 corpus 6 sample 누계 "
        "측정으로 boundary case 4건 정량 강화 (66.7%)."),
    # 4: "1) " + "한계 5종 근본 원인 분석" — keep
    5: ("L1 네이티브 코드 분석 불가(가장 중요): jadx = Java/Kotlin 전용 → libfoo.so / libnative-lib.so / .NET CIL "
        "안 핵심 로직 미커버. 2026-05-06 추가 측정으로 외부 corpus 6 sample 중 4건이 boundary case "
        "(MASTG-2 / r2pay / HelloWord-JNI / certificatePinningXamarin)"),
    6: ("L2 표본 크기(n=19) 통계적 약점: bootstrap CI 1000회 측정으로 정량화. Precision 95% CI [57.9%, 94.7%], "
        "F1 [73.3%, 97.3%], FP rate [5.3%, 42.1%] — ±15%p CI 폭이 표본 작음의 직접 시각화"),
    7: ("L3 멀티 모델 앙상블 미구현 → 단일 모델 + 멀티 시각으로 대체. L4 MASTG corpus 의 hand-crafted 특성으로 "
        "난독화 정확도 100% 는 upper-bound. L5 외부 corpus의 Stage 3 평가 누락은 2026-04-30 해소"),
    # 8: "2) " + "운영 비용 평가" — keep
    9: ("시간 cost: APK 1개 fully-pipeline ~40분(인터랙티브). manual baseline 6~7시간 대비 3~3.5x 단축. "
        "fully-batch 자동화 시 8~15분/APK 도달 가능 (Future Work)"),
    10: ("금전 cost: Claude Code 정액제 안에서 외부 LLM API 비용 $0. 외주 환산 기준 APK 1개당 ~₩200,000 절감 + "
         "100 APK 배치 분석 시 ~₩20M / 250 시간 절감 추정"),
    11: ("메모리 peak ~4GB (jadx 디컴파일 단계가 dominant), 산업 적용 시 enterprise plan + radare2/Ghidra 통합으로 "
         "L1 해소 필요. 처리 시간 가설 8~25분에 대해 인터랙티브 ~40분이라 fully-batch 전환 후 충족 예상"),
    # 12: "3) " + "본 학기 R1.d / RQ 진척" — keep
    13: ("MASTG 외부 corpus 6 sample 누계 — UnCrackable Level1/3 4 in-scope finding (P 100%) + "
         "Level2 / r2pay-v1.0 / HelloWord-JNI / certificatePinningXamarin 4 boundary cases (66.7%). "
         "Java/Kotlin layer scanner + native/non-Java binary scanner 의 분리된 stage 권고를 정량 입증"),
    14: ("R1.d 표본 확장 한계: MASTG 만으로는 boundary 추가만 가능. Java 측 vuln 풍부한 의도적 취약 corpus "
         "(DIVA / InsecureBankv2) 도입은 외부 다운로드 환경 제약으로 본 학기 partial. 이걸 RQ1 caveat 으로 "
         "정직히 명시 + 12주차 R4 real-world 난독화로 이어짐"),
    15: ("향후 계획(12주차): R4 real-world commercial APK 1개에 Stage 0 deobfuscation 정확도 측정 — "
         "hand-crafted MASTG 100% upper-bound 대비 real-world floor 도출. 12주차 progress PPT (통합+일반화)"),
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
