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
    2: "최종 파이프라인 종합 성능 평가, 베이스라인 도구 비교, 결과 시각화:",
    3: ("8주차까지 완성한 파이프라인을 정답 라벨 18건(자체 PleOS 앱 3종 15건 + OWASP MASTG 표준 샘플 3건)에 적용해 9주차 "
        "최종 성능을 확정. Ablation 실험 + 기존 도구 4종과의 비교 + 시각화 6 차트로 정량 우위 입증."),
    # 4: "1) " + "최종 파이프라인 성능 재측정" — keep
    5: "측정 방법: 7주차 정량 평가 프레임워크(Precision/Recall/F1, 오탐률)를 자동 측정 코드로 일괄 적용",
    6: ("측정 대상: PleOS 앱 3종(차량 제어·로그 동기화·온디바이스 LLM 제공) 15건 + OWASP MASTG UnCrackable-Level1 3건 "
        "= 총 18건. UnCrackable-Level2와 r2pay는 핵심 로직이 네이티브 라이브러리(.so)에 있어 별도 보고"),
    7: ("결과: 가설(1차 오탐률 25%·3차 7%·Precision 0.93) 대비 — 1차 오탐률 22.2%(충족), 1차 F1 0.875. "
        "다중 시각(공격자·방어자·도메인 전문가) 합의 2/3 일치 기준 적용 시 Precision 100%·Recall 90.9%·F1 0.952로 가설 초과. "
        "만장일치 확정 진성 양성 9건. 잠정 오탐 4건은 외부 진입 경로 4중 차단 분석으로 모두 오탐 확정"),
    # 8: "2) " + "Ablation Study 수행" — keep
    9: "방법: 단계별 변형(1차만/1+2차/1+2+3차) + 합의 임계 변형(1·2·3 시각 중 N개 일치) 자동 비교",
    10: "목적: 각 단계 기여도 분리 정량화 + 합의 임계 기본값 확정",
    11: ("결과: 단계 변형 F1 0.875 → 1.000(상한) → 0.783. 합의 임계 1/3 → 2/3 → 3/3 F1 0.846 → 0.952 → 0.900 "
         "— 2/3가 최적. 추가 발견: PleOS 앱 난독화 비율 0.2~0.4%로 가정 '고난독화 IVI 코드'와 달리 가독성 유지"),
    # 12: "3) " + "베이스라인 도구 비교 실험" — keep
    13: ("비교 대상: ① JADX + 사람 직접 ② 단일 LLM 1회 ③ android-scanner-ai(Gemini API 키 필수) "
         "④ Androidmeda(Apache 2.0, 난독화 풀이). 외부 유료 API 미사용 정책으로 ③·④는 정성 비교"),
    14: ("결과: ③·④ 모두 자체 Precision·Recall·F1 미발표 — 정량 비교 가능 도구의 부재 자체가 본 연구의 차별점. "
         "처리 시간 ① 6~7시간 vs 본 파이프라인 약 2시간(3배 단축). ② 단일 LLM 정밀도 77.8% → 다단계 검증 시 100%(+22.2%p)"),
    15: "향후 계획(10주차): 자동차 안드로이드(AAOS) 보안 가이드라인의 권한·자격증명 보호·통신 보안 항목과 본 파이프라인 결과의 매핑 표 작성",
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
