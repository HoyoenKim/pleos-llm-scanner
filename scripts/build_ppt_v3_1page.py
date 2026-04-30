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
    3: ("8주차까지 고도화 완료된 전체 파이프라인을 7주차 정량 평가 프레임워크로 재측정하여 9주차 시점 최종 성능 지표를 확정한다. "
        "자체 라벨링한 PleOS 앱 3종(15건)에 OWASP 표준 모바일 보안 테스트 가이드(MASTG)의 UnCrackable-Level1(3건)을 합산한 "
        "정답 라벨 총 18건을 기준으로 측정하며, 각 분석 단계의 기여도를 분리하는 ablation 실험과 기존 도구 4종과의 베이스라인 "
        "비교 실험을 수행하여 본 연구의 우위를 정량 입증한다."),
    # 4: "1) " + "최종 파이프라인 성능 재측정" — keep
    5: ("측정 방법: 7주차에 수립한 정량 평가 프레임워크(Precision/Recall/F1, 처리 시간, 오탐률)를 자동 측정하는 코드로 일괄 적용. "
        "카테고리별·APK별 세부 분석을 동시 산출"),
    6: ("측정 대상: 자체 라벨링 PleOS 앱 3종 — 차량 제어 앱(VehicleControl), 시스템 로그 동기화 앱(sync.syslog), 온디바이스 LLM "
        "모델 제공 앱(llm.model.provider) — 의 취약점 후보 15건과, OWASP MASTG의 UnCrackable-Level1 챌린지 앱에서 정답이 알려진 "
        "취약점 3건을 합쳐 총 18건. UnCrackable-Level2 및 r2pay-v1.0은 핵심 보안 로직이 네이티브 라이브러리(.so) 안에 있어 "
        "자바 정적 분석 파이프라인의 범위 밖 사례로 별도 보고"),
    7: ("결과(9주차 시점): 가설(최종 오탐률 7%·난독화 정확도 78%·Precision 0.93) 대비 실측 — 1차 오탐률 22.2%로 가설 25%에 "
        "근접 충족, 1차 단계 Precision 77.8%·Recall 100%·F1 0.875. OWASP 표준 데이터셋만 떼어 측정하면 Precision 100%. "
        "다중 시각(공격자·방어자·도메인 전문가) 합의 단계에서 2/3 이상 일치 기준 적용 시 Precision 100%·Recall 90.9%·F1 0.952로 "
        "가설 0.93을 초과. 합의 만장일치로 확정된 진성 양성 9건. 1차 단계의 잠정 오탐 4건은 외부 진입 경로 4중 차단(매니페스트 "
        "URI / 네비게이션 / 라우팅 / 의존성) 분석을 거쳐 모두 오탐 확정"),
    # 8: "2) " + "Ablation Study 수행" — keep
    9: ("방법: 분석 단계별 변형(1차만 / 1+2차 / 1+2+3차) 3종과, 다중 시각 합의 임계 변형(1·2·3 시각 중 몇 시각 일치를 "
        "양성으로 채택할지) 3종을 자동 측정 코드로 일괄 비교"),
    10: ("목적: 각 분석 단계가 Precision·Recall·F1에 기여하는 정도를 분리 정량화하고, 다중 시각 합의 임계값의 기본값을 "
         "데이터로 확정"),
    11: ("결과: 단계 변형은 1차만 F1 0.875 → 2차 caller 검증 추가 시 F1 1.000(상한) → 3차 만장일치 추가 시 F1 0.783으로 "
         "변화(만장일치는 외부 데이터셋 미평가에 따른 인위적 하락). 합의 임계 변형은 1/3 → 2/3 → 3/3에서 F1 0.846 → 0.952 → "
         "0.900 — 2/3 임계가 정밀도와 재현율의 균형이 가장 좋음. 추가 발견: 식별자 엔트로피로 측정한 PleOS 앱 3종의 난독화 "
         "비율은 0.2~0.4%로 가정 '고난독화 IVI 코드'와 다름 — PleOS 코드는 의미적 클래스명을 유지(빌드 정책상 가독성 보존)"),
    # 12: "3) " + "베이스라인 도구 비교 실험" — keep
    13: ("비교 대상: ① JADX 디컴파일 + 사람 직접 분석 ② 단일 LLM 1회 분석(검증 단계 없음) ③ android-scanner-ai(Google "
         "Gemini API 키 필수) ④ Androidmeda(Apache 2.0, 난독화 풀이 위주). 외부 유료 API 미사용 정책으로 ③·④는 정성 비교"),
    14: ("결과: ③·④ 모두 자체 Precision·Recall·F1 측정값을 README/논문에 발표한 사례가 없음 — 정량 비교 가능한 기존 도구의 "
         "부재 자체가 본 연구의 차별점. 처리 시간은 ① 사람 직접 6~7시간 vs 본 파이프라인 약 2시간(3배 단축). ② 단일 LLM 1회 "
         "분석은 정밀도 77.8%이며 본 파이프라인 다단계 검증을 거치면 100%로 향상(+22.2%p)"),
    15: ("향후 계획(10주차): 자동차 안드로이드(AAOS) 보안 가이드라인의 권한·자격증명 보호·통신 보안 항목과 본 파이프라인 결과의 "
         "매핑 표 작성, TARA(위협 분석·위험 평가) 산출물 자동 생성, 대표 취약점 사례 연구 5건 작성, 중간 보고서 v0.9 초안 작성. "
         "본 주에 산출한 시각화 차트 6종과 16슬라이드 종합 정리본은 별도 파일로 첨부"),
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
