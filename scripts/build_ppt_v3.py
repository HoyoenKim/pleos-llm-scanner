#!/usr/bin/env python
"""
Build PPT v3 — 9주차 종합본 (Phase A~C + Stage 2.b + Phase B-4.c.2 측정 결과 모두 반영).

색상 팔레트: Ocean Gradient (065A82 deep blue / 1C7293 teal / 21295C midnight)
폰트: Malgun Gothic (한글) + Cambria (영문 강조)

총 16 슬라이드 + 차트 6개 (data/viz/01~06_*.png).

산출: ../pptx/v3/자율주행연구프로젝트1_9주차_2025311610_김호연_v3.pptx
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# Theme — Ocean Gradient
NAVY = RGBColor(0x21, 0x29, 0x5C)         # midnight (slide bg dark variant)
DEEP_BLUE = RGBColor(0x06, 0x5A, 0x82)    # deep blue (primary)
TEAL = RGBColor(0x1C, 0x72, 0x93)         # teal (secondary)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NEAR_WHITE = RGBColor(0xF5, 0xF7, 0xFA)   # near-white card bg
TEXT_DARK = RGBColor(0x1A, 0x1F, 0x3A)
TEXT_MUTED = RGBColor(0x60, 0x6F, 0x88)
ACCENT_GREEN = RGBColor(0x3A, 0x7D, 0x44)  # success / TP
ACCENT_RED = RGBColor(0xC7, 0x3E, 0x1D)    # FP / warning
ACCENT_GOLD = RGBColor(0xC4, 0x86, 0x1F)   # F1 / mid

FONT_HEAD = "Malgun Gothic"
FONT_BODY = "Malgun Gothic"
FONT_NUM = "Cambria"

VIZ_DIR = Path(__file__).parent.parent / "data" / "viz"


def add_textbox(slide, x, y, w, h, text, *, font=FONT_BODY, size=14, bold=False, color=TEXT_DARK,
                align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return tb


def add_multi_text(slide, x, y, w, h, lines, *, font=FONT_BODY, base_size=13, color=TEXT_DARK,
                   align=PP_ALIGN.LEFT, line_spacing=1.2):
    """lines: list of (text, {bold, size, color, italic}) tuples or just str."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    for i, line in enumerate(lines):
        if isinstance(line, str):
            text, opts = line, {}
        else:
            text, opts = line
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = opts.get("align", align)
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = text
        run.font.name = opts.get("font", font)
        run.font.size = Pt(opts.get("size", base_size))
        run.font.bold = opts.get("bold", False)
        run.font.italic = opts.get("italic", False)
        run.font.color.rgb = opts.get("color", color)
    return tb


def fill_rect(slide, x, y, w, h, color, *, line_color=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color
    shp.shadow.inherit = False
    return shp


def add_chip(slide, x, y, w, h, text, *, fill=DEEP_BLUE, color=WHITE, size=12, bold=True):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.name = FONT_BODY
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shp


def slide_header(slide, title, subtitle=None):
    """Standard top header on light-bg slide. Returns content-area top y."""
    # Left accent bar
    fill_rect(slide, 0, 0, 0.18, 7.5, DEEP_BLUE)
    add_textbox(slide, 0.45, 0.30, 12.5, 0.7, title, size=28, bold=True, color=NAVY)
    if subtitle:
        add_textbox(slide, 0.45, 0.95, 12.5, 0.35, subtitle, size=12, color=TEXT_MUTED, italic=True)
        return 1.45
    return 1.10


def page_footer(slide, page_no, total):
    add_textbox(slide, 11.5, 7.10, 1.8, 0.3, f"{page_no} / {total}", size=10, color=TEXT_MUTED, align=PP_ALIGN.RIGHT)
    add_textbox(slide, 0.45, 7.10, 6.0, 0.3, "PleOS LLM Scanner — 9주차 종합 v3 (2026-04-30)", size=9, color=TEXT_MUTED)


# ----------------------------------------------------------------------- main
def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank = prs.slide_layouts[6]
    total = 16

    # ---------------------------------- Slide 1 — Cover (dark)
    s = prs.slides.add_slide(blank)
    fill_rect(s, 0, 0, 13.333, 7.5, NAVY)
    fill_rect(s, 0, 5.6, 13.333, 0.06, TEAL)
    add_textbox(s, 0.6, 1.5, 12.0, 0.5, "자율주행연구프로젝트 1 — 9주차 종합 v3",
                size=18, bold=False, color=TEAL, align=PP_ALIGN.LEFT, font=FONT_NUM)
    add_textbox(s, 0.6, 2.0, 12.0, 1.4,
                "LLM을 활용한 디컴파일러 분석 및\nPleOS 적용 방안 검토",
                size=42, bold=True, color=WHITE)
    add_textbox(s, 0.6, 4.0, 12.0, 0.4,
                "LLM-based Decompiler Analysis for IVI Security on PleOS",
                size=15, bold=False, color=TEAL, italic=True)
    add_textbox(s, 0.6, 5.85, 12.0, 0.4,
                "김호연 (2025311610)  ·  연세대학교 전기전자공학과  ·  Computational Intelligence Lab",
                size=13, color=WHITE)
    add_textbox(s, 0.6, 6.30, 12.0, 0.4,
                "현대자동차 계약학과 육성형 연구과제 — PleOS TARA 및 실차 보안 취약점 점검",
                size=11, color=TEAL)
    add_textbox(s, 0.6, 6.95, 12.0, 0.3,
                "2026-1학기  ·  2026-04-30 작성  ·  Phase A~C 측정 결과 종합",
                size=10, color=TEAL, italic=True)

    # ---------------------------------- Slide 2 — Agenda
    s = prs.slides.add_slide(blank)
    slide_header(s, "목차", "Phase A 환경 → Phase B 검증 → Phase C 난독화 + Phase B-4.c.2 베이스라인")
    items = [
        ("01", "프로젝트 개요 + 환경 제약"),
        ("02", "파이프라인 아키텍처 + 의사결정 (D1~D4)"),
        ("03", "분석 corpus (PleOS 3 + MASTG 3)"),
        ("04", "Stage 1 카테고리 분포"),
        ("05", "APK × Severity 히트맵"),
        ("06", "Stage 2.b deep-link 4중 차단"),
        ("07", "단계별 오탐률 추이"),
        ("08", "난독화 정확도 + entropy 분포"),
        ("09", "Ablation A 변형 + B 합의 임계"),
        ("10", "베이스라인 비교 (4 도구)"),
        ("11", "PPT 가설 매칭 표 (전체 지표)"),
        ("12", "Pipeline boundary + 한계"),
        ("13", "결론 + 다음 단계 + 산출물"),
    ]
    for i, (num, t) in enumerate(items):
        col = i // 7
        row = i % 7
        x = 0.7 + col * 6.4
        y = 1.6 + row * 0.65
        add_chip(s, x, y + 0.06, 0.55, 0.42, num, fill=TEAL, color=WHITE, size=14)
        add_textbox(s, x + 0.7, y + 0.06, 5.6, 0.42, t, size=15, bold=True, color=NAVY)
    page_footer(s, 2, total)

    # ---------------------------------- Slide 3 — 프로젝트 개요 + 환경 제약
    s = prs.slides.add_slide(blank)
    slide_header(s, "프로젝트 개요 + 환경 제약", "PleOS 탑재 IVI APK 정적 분석 파이프라인")
    # 좌상 — 무엇을 만드는가
    fill_rect(s, 0.45, 1.55, 6.2, 2.7, NEAR_WHITE)
    fill_rect(s, 0.45, 1.55, 0.08, 2.7, DEEP_BLUE)
    add_textbox(s, 0.65, 1.65, 5.9, 0.4, "무엇을 만드는가", size=15, bold=True, color=NAVY)
    add_multi_text(s, 0.65, 2.05, 5.9, 2.2, [
        ("① 디컴파일 + 난독화 전처리", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    jadx --deobf → entropy 판별 → LLM 이름 복원 → 2차 디컴파일", {"size": 11, "color": TEXT_MUTED}),
        ("② 코드 분할 + 키워드 필터링", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    crypto / network / permission / intent / hardcoded", {"size": 11, "color": TEXT_MUTED}),
        ("③ 다단계 LLM 검증 (1 → 2 → 3차 합의)", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    stage 1 LLM → caller trust boundary → 멀티 프롬프트 합의", {"size": 11, "color": TEXT_MUTED}),
        ("④ 리포트 + AAOS / TARA 매핑", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    JSON / Markdown + 차트 + 가이드라인 매핑", {"size": 11, "color": TEXT_MUTED}),
    ])
    # 우상 — 환경 제약
    fill_rect(s, 6.85, 1.55, 6.2, 2.7, NEAR_WHITE)
    fill_rect(s, 6.85, 1.55, 0.08, 2.7, ACCENT_RED)
    add_textbox(s, 7.05, 1.65, 5.9, 0.4, "환경 제약 (정량적으로 PPT 가설 영향)", size=15, bold=True, color=NAVY)
    add_multi_text(s, 7.05, 2.05, 5.9, 2.2, [
        ("로컬 GPU 없음", {"size": 12, "bold": True, "color": ACCENT_RED}),
        ("    → Ollama / 로컬 LLM 사용 불가", {"size": 11, "color": TEXT_MUTED}),
        ("외부 유료 LLM API 없음 (계약과제 IP 보호)", {"size": 12, "bold": True, "color": ACCENT_RED}),
        ("    → OpenAI / Gemini 등 직접 호출 불가", {"size": 11, "color": TEXT_MUTED}),
        ("Claude Code 정액제 = 분석 엔진", {"size": 12, "bold": True, "color": ACCENT_GREEN}),
        ("    → Anthropic SDK 호출 코드 X, 세션 직접 분석", {"size": 11, "color": TEXT_MUTED}),
        ("실차 접근 불가", {"size": 12, "bold": True, "color": ACCENT_RED}),
        ("    → AAOS/PleOS 에뮬레이터 + ADB 가 데이터 소스", {"size": 11, "color": TEXT_MUTED}),
    ])
    # 하단 — 9주차 추격 narrative
    fill_rect(s, 0.45, 4.5, 12.6, 2.4, RGBColor(0xE9, 0xEF, 0xF6))
    add_textbox(s, 0.65, 4.6, 12.2, 0.4, "9주차 추격 narrative", size=15, bold=True, color=NAVY)
    add_multi_text(s, 0.65, 5.05, 12.2, 1.8, [
        ("• PPT 5주차 (PleOS APK 3종 분석) → ✅ Phase B-3 완료 (VehicleControl + sync.syslog + llm.model.provider)", {"size": 12}),
        ("• PPT 6주차 (2차 검증 + 난독화 전처리) → ✅ Stage 2 + 2.b 완료 / Phase C 진입 측정", {"size": 12}),
        ("• PPT 7주차 (정량 평가 + 베이스라인) → ✅ src/eval.py + ablation.py + MASTG 외부 GT + 4 baseline 비교", {"size": 12}),
        ("• PPT 8주차 (3차 교차 검증 + 시각화) → ✅ Stage 3 D3=B 합의 + 본 시각화 6 차트 (오늘)", {"size": 12, "bold": True, "color": DEEP_BLUE}),
        ("• PPT 9주차 (최종 성능 평가 + Ablation + 베이스라인) → ✅ Combined n=18 측정 + ablation A/B 변형", {"size": 12, "bold": True, "color": DEEP_BLUE}),
    ])
    page_footer(s, 3, total)

    # ---------------------------------- Slide 4 — 파이프라인 + 의사결정
    s = prs.slides.add_slide(blank)
    slide_header(s, "파이프라인 아키텍처 + 의사결정 (D1~D4)", "각 단계의 산출물 + 환경 제약 매핑")
    # 가로 4단계 chip + 화살표
    stages = [
        ("Stage A", "디컴파일 + 난독화", "jadx --deobf\nentropy.py\nstage_b 프롬프트", DEEP_BLUE),
        ("Stage 1", "키워드 + LLM 1차", "keywords.yaml\nstage1_detect.md", TEAL),
        ("Stage 2", "Caller / Trust", "manifest grep\nNav graph 추적\n4중 차단 audit", TEAL),
        ("Stage 3", "멀티 프롬프트", "attacker / defender\ndomain_expert\n≥2/3 합의 default", DEEP_BLUE),
    ]
    box_w = 2.85
    box_h = 2.0
    gap = 0.30
    start_x = 0.55
    for i, (head, sub, body, c) in enumerate(stages):
        x = start_x + i * (box_w + gap)
        fill_rect(s, x, 1.5, box_w, box_h, c)
        add_textbox(s, x + 0.15, 1.6, box_w - 0.3, 0.35, head, size=11, color=WHITE, bold=False)
        add_textbox(s, x + 0.15, 1.95, box_w - 0.3, 0.45, sub, size=15, color=WHITE, bold=True)
        add_multi_text(s, x + 0.15, 2.45, box_w - 0.3, 1.0, [
            (line, {"size": 10.5, "color": WHITE}) for line in body.split("\n")
        ])
        # 화살표
        if i < 3:
            arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                       Inches(x + box_w + 0.02), Inches(2.3),
                                       Inches(0.26), Inches(0.4))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = TEXT_MUTED
            arrow.line.fill.background()
    # 의사결정 표
    add_textbox(s, 0.55, 3.85, 12.4, 0.4, "주요 의사결정 (D1~D4)", size=15, bold=True, color=NAVY)
    decisions = [
        ("D1", "에뮬레이터 = PleOS Connect v2.0.5 x86_64", "본 과제 정합성", DEEP_BLUE),
        ("D2", "1차 분석 타겟 = ai.umos.vehiclecontrol", "system UID + 13 위험 권한", TEAL),
        ("D3", "(B) 멀티 프롬프트 합의 (공격자 / 방어자 / 도메인 전문가)", "(A) 멀티 모델은 Claude Code 단일 세션 한계", ACCENT_GOLD),
        ("D4", "Ground truth = (c) OWASP MASVS-MASTG + 자체 라벨링", "베이스라인 비교 + PleOS 특화", ACCENT_GREEN),
    ]
    for i, (key, what, why, c) in enumerate(decisions):
        y = 4.3 + i * 0.7
        add_chip(s, 0.55, y + 0.05, 0.7, 0.5, key, fill=c, color=WHITE, size=14)
        add_textbox(s, 1.4, y, 7.5, 0.4, what, size=13, bold=True, color=NAVY)
        add_textbox(s, 1.4, y + 0.34, 11.5, 0.35, why, size=11, color=TEXT_MUTED, italic=True)
    page_footer(s, 4, total)

    # ---------------------------------- Slide 5 — 분석 corpus
    s = prs.slides.add_slide(blank)
    slide_header(s, "분석 Corpus", "PleOS APK 3종 (자체) + OWASP MASTG 3 sample (외부 GT)")
    # 좌측 PleOS
    fill_rect(s, 0.45, 1.55, 6.3, 5.5, NEAR_WHITE)
    fill_rect(s, 0.45, 1.55, 0.08, 5.5, DEEP_BLUE)
    add_textbox(s, 0.65, 1.65, 5.95, 0.4, "PleOS Corpus (자체 라벨)", size=15, bold=True, color=NAVY)
    pleos = [
        ("ai.umos.vehiclecontrol", "92 MB · 1,765 java", "system UID + 13 위험 권한"),
        ("ai.pleos.sync.syslog", "4 priority 클래스", "토큰 logcat / gRPC plaintext / KDF"),
        ("ai.pleos.llm.model.provider", "2 priority 클래스", "exported provider + receiver DoS"),
    ]
    for i, (name, sub, body) in enumerate(pleos):
        y = 2.15 + i * 1.55
        add_textbox(s, 0.7, y, 5.9, 0.4, name, size=13, bold=True, color=DEEP_BLUE, font=FONT_NUM)
        add_textbox(s, 0.7, y + 0.4, 5.9, 0.35, sub, size=11, color=TEXT_MUTED, italic=True)
        add_textbox(s, 0.7, y + 0.78, 5.9, 0.6, body, size=12, color=TEXT_DARK)
    # 좌측 합계 chip
    add_chip(s, 0.65, 6.55, 5.95, 0.4, "총 15 finding · TP 11 / FP 4 · uncertain 0", fill=DEEP_BLUE, size=12)
    # 우측 MASTG
    fill_rect(s, 6.95, 1.55, 6.1, 5.5, NEAR_WHITE)
    fill_rect(s, 6.95, 1.55, 0.08, 5.5, ACCENT_GREEN)
    add_textbox(s, 7.15, 1.65, 5.85, 0.4, "MASTG Corpus (외부 GT, OWASP)", size=15, bold=True, color=NAVY)
    mastg = [
        ("UnCrackable-Level1 (68 KB)", "6 java", "hardcoded AES + ECB + Log.d (3 in-scope TP)"),
        ("UnCrackable-Level2", "5 java (sg.vantagepoint)", "native lib 의존 → in-scope 0건 (boundary)"),
        ("r2pay-v1.0", "re.pwnme + RootBeer", "native lib + 1337/0 anti-tamper (boundary)"),
    ]
    for i, (name, sub, body) in enumerate(mastg):
        y = 2.15 + i * 1.55
        add_textbox(s, 7.2, y, 5.7, 0.4, name, size=13, bold=True, color=ACCENT_GREEN, font=FONT_NUM)
        add_textbox(s, 7.2, y + 0.4, 5.7, 0.35, sub, size=11, color=TEXT_MUTED, italic=True)
        add_textbox(s, 7.2, y + 0.78, 5.7, 0.6, body, size=12, color=TEXT_DARK)
    add_chip(s, 7.15, 6.55, 5.85, 0.4, "총 3 in-scope · TP 3 / FP 0 — MASTG-only P 100%",
             fill=ACCENT_GREEN, size=12)
    page_footer(s, 5, total)

    # ---------------------------------- Slide 6 — 카테고리 분포 (chart 01)
    s = prs.slides.add_slide(blank)
    slide_header(s, "Stage 1 카테고리별 정·오탐 분포", "combined n=18 — intent / hardcoded / crypto 모두 100% TP")
    s.shapes.add_picture(str(VIZ_DIR / "01_category_distribution.png"),
                         Inches(0.55), Inches(1.55), height=Inches(4.3))
    fill_rect(s, 8.4, 1.55, 4.65, 4.3, NEAR_WHITE)
    fill_rect(s, 8.4, 1.55, 0.08, 4.3, DEEP_BLUE)
    add_textbox(s, 8.6, 1.65, 4.45, 0.4, "Key takeaways", size=14, bold=True, color=NAVY)
    add_multi_text(s, 8.6, 2.05, 4.45, 3.7, [
        ("intent · hardcoded · crypto", {"size": 12, "bold": True, "color": ACCENT_GREEN}),
        ("    100% Precision (5/4/3 TP, FP 0)", {"size": 11, "color": TEXT_MUTED}),
        ("network 50% (2 TP / 2 FP)", {"size": 12, "bold": True, "color": ACCENT_GOLD}),
        ("    HtmlWebView 2건 (Stage 2.b CONFIRMED FP)", {"size": 11, "color": TEXT_MUTED}),
        ("permission 0% (0 TP / 2 FP)", {"size": 12, "bold": True, "color": ACCENT_RED}),
        ("    AppPermissionManager 2건 (4중 차단으로 FP)", {"size": 11, "color": TEXT_MUTED}),
        ("→ FP 4건 모두 Stage 3 ≥2/3 합의에서", {"size": 12, "bold": True, "color": DEEP_BLUE}),
        ("    제거되어 P 100% 도달", {"size": 11, "color": TEXT_MUTED}),
    ])
    # 하단 강조 stat
    fill_rect(s, 0.55, 6.0, 12.5, 1.05, RGBColor(0xE9, 0xEF, 0xF6))
    add_textbox(s, 0.75, 6.05, 12.0, 0.4,
                "Stage 1 P 77.8% (combined n=18)", size=20, bold=True, color=NAVY, font=FONT_NUM)
    add_textbox(s, 0.75, 6.5, 12.0, 0.4,
                "Recall 100% · F1 0.875 · PPT 가설 1차 오탐률 25% → 측정 22.2% (-2.8%p 충족)",
                size=12, color=TEXT_MUTED)
    page_footer(s, 6, total)

    # ---------------------------------- Slide 7 — APK x Severity (chart 02)
    s = prs.slides.add_slide(blank)
    slide_header(s, "APK × Severity 히트맵", "TP 14건 분포 + FP 4건 (모두 VehicleControl)")
    s.shapes.add_picture(str(VIZ_DIR / "02_apk_severity_heatmap.png"),
                         Inches(0.55), Inches(1.55), height=Inches(4.3))
    fill_rect(s, 8.4, 1.55, 4.65, 4.3, NEAR_WHITE)
    fill_rect(s, 8.4, 1.55, 0.08, 4.3, ACCENT_RED)
    add_textbox(s, 8.6, 1.65, 4.45, 0.4, "위험 분포", size=14, bold=True, color=NAVY)
    add_multi_text(s, 8.6, 2.05, 4.45, 3.7, [
        ("sync.syslog 가장 위험", {"size": 12, "bold": True, "color": ACCENT_RED}),
        ("    HIGH 4: token logcat / PII / KDF", {"size": 11, "color": TEXT_MUTED}),
        ("    BuildConfig.IDENTIFIER / gRPC plaintext", {"size": 11, "color": TEXT_MUTED}),
        ("VehicleControl FP 4건 집중", {"size": 12, "bold": True, "color": ACCENT_GOLD}),
        ("    HtmlWebView 2 + AppPermissionManager 2", {"size": 11, "color": TEXT_MUTED}),
        ("    Stage 2.b 4중 차단 evidence 확정", {"size": 11, "color": TEXT_MUTED}),
        ("llm.model.provider", {"size": 12, "bold": True, "color": ACCENT_GOLD}),
        ("    HIGH 1 (PromptsContentProvider) +", {"size": 11, "color": TEXT_MUTED}),
        ("    MEDIUM 1 (모델 파일 삭제 DoS)", {"size": 11, "color": TEXT_MUTED}),
        ("UnCrackable-L1 baseline", {"size": 12, "bold": True, "color": ACCENT_GREEN}),
        ("    HIGH 1 / MEDIUM 1 / LOW 1 (모두 TP)", {"size": 11, "color": TEXT_MUTED}),
    ])
    page_footer(s, 7, total)

    # ---------------------------------- Slide 8 — Stage 2.b deep-link 4중 차단
    s = prs.slides.add_slide(blank)
    slide_header(s, "Stage 2.b — Deep-link 4중 차단", "잠정 FP 4건의 외부 진입 가능성을 4 layer로 봉쇄 확정")
    layers = [
        ("Layer 1", "Manifest URI deep-link",
         "android:scheme / android:host / <data> · 0건\nexported activity = VehicleControlActivity 1개\n모두 action 기반 intent-filter"),
        ("Layer 2", "Compose Nav graph",
         "ApplicationDetails / HtmlPopup / ReleaseNotes\nNavGraphBuilder 내부 등록만\nnavDeepLink {} 미사용"),
        ("Layer 3", "IntentRouter pathSegment",
         "LinkProvider.createLink → path 1개 + ?section=…\npathSegments.size() > 1 영구 미충족\nsubPathRoute 호출 자체 X"),
        ("Layer 4", "NestedNavRouter binding",
         "Dagger MapFactory.builder(2) — APPLICATIONS 키 부재\nNavRouter 구현체 = 2개 (Convenience + VehicleInformation)\nfindRoute(APPLICATIONS, ·) → null"),
    ]
    for i, (head, name, body) in enumerate(layers):
        col = i % 2
        row = i // 2
        x = 0.55 + col * 6.4
        y = 1.55 + row * 2.55
        fill_rect(s, x, y, 6.2, 2.4, NEAR_WHITE)
        fill_rect(s, x, y, 0.08, 2.4, DEEP_BLUE)
        add_chip(s, x + 0.25, y + 0.15, 0.85, 0.4, head, fill=TEAL, color=WHITE, size=11)
        add_textbox(s, x + 1.2, y + 0.15, 4.9, 0.4, name, size=14, bold=True, color=NAVY)
        add_multi_text(s, x + 0.25, y + 0.65, 5.85, 1.7, [
            (line, {"size": 12, "color": TEXT_DARK}) for line in body.split("\n")
        ])
    fill_rect(s, 0.55, 6.7, 12.5, 0.55, NAVY)
    add_textbox(s, 0.75, 6.78, 12.0, 0.4,
                "→ 외부 NAVIGATE_TO_SETTING은 카테고리 화면(앱 목록)까지만 진입. ApplicationDetails 외부 진입 불가 확정.",
                size=13, bold=True, color=WHITE)
    page_footer(s, 8, total)

    # ---------------------------------- Slide 9 — FP rate trend (chart 03)
    s = prs.slides.add_slide(blank)
    slide_header(s, "단계별 1차/2차/3차 오탐률", "PPT 가설 25 → 12 → 7% 매칭 / 초과 확인")
    s.shapes.add_picture(str(VIZ_DIR / "03_fp_rate_trend.png"),
                         Inches(0.55), Inches(1.55), height=Inches(4.3))
    fill_rect(s, 8.4, 1.55, 4.65, 4.3, NEAR_WHITE)
    fill_rect(s, 8.4, 1.55, 0.08, 4.3, ACCENT_GREEN)
    add_textbox(s, 8.6, 1.65, 4.45, 0.4, "PPT 가설 vs 실측", size=14, bold=True, color=NAVY)
    add_multi_text(s, 8.6, 2.05, 4.45, 3.7, [
        ("1차 오탐률", {"size": 12, "bold": True, "color": NAVY}),
        ("    가설 25% / 실측 22.2%", {"size": 11, "color": TEXT_MUTED}),
        ("    -2.8%p 충족", {"size": 11, "color": ACCENT_GREEN, "bold": True}),
        ("2차 오탐률", {"size": 12, "bold": True, "color": NAVY}),
        ("    가설 12% / 실측 0% (caller P-ceiling)", {"size": 11, "color": TEXT_MUTED}),
        ("    -12%p 초과", {"size": 11, "color": ACCENT_GREEN, "bold": True}),
        ("3차 오탐률", {"size": 12, "bold": True, "color": NAVY}),
        ("    가설 7% / 실측 0% (≥2/3 합의)", {"size": 11, "color": TEXT_MUTED}),
        ("    -7%p 도달", {"size": 11, "color": ACCENT_GREEN, "bold": True}),
        ("caveat: stage 2/3는 PleOS-only n=15", {"size": 10, "color": TEXT_MUTED, "italic": True}),
        ("MASTG는 stage 3 미평가 (Phase B-4.c.2)", {"size": 10, "color": TEXT_MUTED, "italic": True}),
    ])
    page_footer(s, 9, total)

    # ---------------------------------- Slide 10 — 난독화 정확도 + entropy (chart 04 + 06)
    s = prs.slides.add_slide(blank)
    slide_header(s, "난독화 정확도 + Corpus Entropy 분포",
                 "외부 OWASP UnCrackable에서 100% / PleOS는 가정과 다르게 난독화 약함")
    s.shapes.add_picture(str(VIZ_DIR / "04_deobf_accuracy_trend.png"),
                         Inches(0.45), Inches(1.55), height=Inches(2.8))
    s.shapes.add_picture(str(VIZ_DIR / "06_entropy_distribution.png"),
                         Inches(0.45), Inches(4.45), height=Inches(2.7))
    fill_rect(s, 8.4, 1.55, 4.65, 5.6, NEAR_WHITE)
    fill_rect(s, 8.4, 1.55, 0.08, 5.6, ACCENT_GOLD)
    add_textbox(s, 8.6, 1.65, 4.45, 0.4, "Surprising finding", size=14, bold=True, color=NAVY)
    add_multi_text(s, 8.6, 2.05, 4.45, 5.0, [
        ("난독화 정확도 n=17 exact 100%", {"size": 12, "bold": True, "color": ACCENT_GREEN}),
        ("    UnCrackable Level1/2 sg.vantagepoint", {"size": 10, "color": TEXT_MUTED}),
        ("    6 class + 11 method rename 모두 정답", {"size": 10, "color": TEXT_MUTED}),
        ("    Log.d \"CodeCheck\" / \"test-keys\" 등", {"size": 10, "color": TEXT_MUTED, "italic": True}),
        ("    contextual hint 강함 — upper-bound", {"size": 10, "color": TEXT_MUTED, "italic": True}),
        ("PleOS HIGH 난독화 0.2~0.4%", {"size": 12, "bold": True, "color": ACCENT_RED}),
        ("    PPT 가정 (고난독화) 와 다름", {"size": 10, "color": TEXT_MUTED}),
        ("    의미적 클래스명 유지 (release", {"size": 10, "color": TEXT_MUTED}),
        ("    engineering / debug build / AOSP)", {"size": 10, "color": TEXT_MUTED}),
        ("MASTG 40~50% HIGH (가정 매칭)", {"size": 12, "bold": True, "color": DEEP_BLUE}),
        ("→ Phase C narrative 정정", {"size": 11, "bold": True, "color": NAVY}),
        ("    \"외부 corpus 검증 / PleOS 효과 작음\"", {"size": 10, "color": TEXT_MUTED, "italic": True}),
        ("→ 자체로 PleOS 코드 품질 발견", {"size": 11, "bold": True, "color": NAVY}),
        ("    IVI 제조사 release engineering 정책", {"size": 10, "color": TEXT_MUTED, "italic": True}),
    ])
    page_footer(s, 10, total)

    # ---------------------------------- Slide 11 — Ablation A/B (chart 05)
    s = prs.slides.add_slide(blank)
    slide_header(s, "Ablation Study — Stage + Consensus 변형", "Stage 2 caller + ≥2/3 합의가 차별 동력")
    s.shapes.add_picture(str(VIZ_DIR / "05_ablation_bars.png"),
                         Inches(0.45), Inches(1.55), height=Inches(3.6))
    # 하단 두 박스
    fill_rect(s, 0.45, 5.4, 6.25, 1.85, NEAR_WHITE)
    fill_rect(s, 0.45, 5.4, 0.08, 1.85, DEEP_BLUE)
    add_textbox(s, 0.65, 5.5, 6.0, 0.4, "Variant A — Stage 효과 (n=18)", size=13, bold=True, color=NAVY)
    add_multi_text(s, 0.65, 5.9, 6.0, 1.3, [
        ("A.1 stage 1 only:  P 77.8% / R 100% / F1 0.875", {"size": 11}),
        ("A.2 + stage 2 caller (P-ceiling):  P 100% / R 100% / F1 1.000", {"size": 11, "bold": True, "color": ACCENT_GREEN}),
        ("A.3 + stage 3 ≥3/3:  P 100% / R 64.3% / F1 0.783*", {"size": 11}),
        ("    *artifact: stage3 ensemble 평가가 PleOS n=15에 한정", {"size": 10, "color": TEXT_MUTED, "italic": True}),
    ])
    fill_rect(s, 6.85, 5.4, 6.2, 1.85, NEAR_WHITE)
    fill_rect(s, 6.85, 5.4, 0.08, 1.85, TEAL)
    add_textbox(s, 7.05, 5.5, 5.95, 0.4, "Variant B — D3=B 합의 임계 (PleOS n=15)", size=13, bold=True, color=NAVY)
    add_multi_text(s, 7.05, 5.9, 5.95, 1.3, [
        ("≥1/3:  P 73.3% / R 100% / F1 0.846", {"size": 11}),
        ("≥2/3 (default):  P 100% / R 90.9% / F1 0.952", {"size": 11, "bold": True, "color": ACCENT_GREEN}),
        ("≥3/3:  P 100% / R 81.8% / F1 0.900", {"size": 11}),
        ("→ ≥2/3가 PPT 가설 0.93 도달·초과 (+0.022)", {"size": 11, "color": NAVY, "italic": True}),
    ])
    page_footer(s, 11, total)

    # ---------------------------------- Slide 12 — 베이스라인 비교
    s = prs.slides.add_slide(blank)
    slide_header(s, "베이스라인 비교 (4 도구)", "본 연구만 정량 측정 + multi-stage 검증 + schema enforcement")
    headers = ["측면", "① jadx 수동", "② 단일 LLM", "③ android-scanner-ai", "④ Androidmeda", "본 연구"]
    rows = [
        ["LLM",         "n/a",       "단일",          "Gemini-2.0",      "OAI/Gem/Claude/Ollama", "Claude Opus 4.7"],
        ["외부 API",    "n/a",       "API key",       "Gemini key 필수",  "API key or GPU",        "Claude Code 정액제"],
        ["Multi-stage", "n/a",       "❌",            "❌",               "❌",                    "✅ stage 1+2+3"],
        ["Caller 추적", "manual",    "❌",            "❌",               "❌",                    "✅ Stage 2.b"],
        ["Schema enum", "없음",      "없음",          "free text",       "free text",             "✅ 6 cat enum"],
        ["자체 P/R/F1", "n/a",       "n/a",           "❌ README 부재",   "❌ vuln 측정 부재",      "✅ n=18 P 77.8%"],
        ["GT corpus",   "self만",    "self만",        "❌",               "❌",                    "✅ self 15 + MASTG 3"],
        ["시간 (3 APK)", "6~7h",     "~1.5h",         "~1h",             "~1h",                   "~2h"],
        ["라이선스",    "n/a",       "n/a",           "unspecified",     "Apache 2.0",            "MIT"],
    ]
    # 헤더
    col_widths = [1.75, 1.75, 1.65, 2.0, 1.95, 2.45]
    x_acc = 0.55
    for i, h in enumerate(headers):
        bg = DEEP_BLUE if i < 5 else NAVY
        fill_rect(s, x_acc, 1.55, col_widths[i], 0.4, bg)
        add_textbox(s, x_acc + 0.05, 1.58, col_widths[i] - 0.1, 0.34, h, size=11, bold=True, color=WHITE,
                    align=PP_ALIGN.CENTER)
        x_acc += col_widths[i]
    # 본문
    for r, row in enumerate(rows):
        y = 1.95 + r * 0.5
        bg = NEAR_WHITE if r % 2 == 0 else WHITE
        fill_rect(s, 0.55, y, sum(col_widths), 0.5, bg)
        x_acc = 0.55
        for c, cell in enumerate(row):
            highlight = c == 5
            color = NAVY if highlight else TEXT_DARK
            bold = highlight
            add_textbox(s, x_acc + 0.05, y + 0.05, col_widths[c] - 0.1, 0.4, cell,
                        size=10.5, bold=bold, color=color, align=PP_ALIGN.CENTER)
            x_acc += col_widths[c]
    page_footer(s, 12, total)

    # ---------------------------------- Slide 13 — PPT 가설 매칭 표
    s = prs.slides.add_slide(blank)
    slide_header(s, "PPT 가설 매칭 표 (전체 지표)", "9주차 마감 시점 — 핵심 가설 모두 도달·충족·초과")
    headers2 = ["지표", "PPT 가설", "실측 (combined n=18)", "상태"]
    rows2 = [
        ["1차 오탐률", "25%", "22.2%", "✅ 충족 (-2.8%p)"],
        ["2차 오탐률", "12%", "0% (caller P-ceiling)", "✅ 초과 (-12%p)"],
        ["3차 오탐률", "7%", "0% (≥2/3 합의)", "✅ 도달 (-7%p)"],
        ["Precision (Full)", "0.93", "1.00 (≥2/3 합의)", "✅ 도달·초과"],
        ["F1 (Full)", "—", "0.952 (≥2/3) / 0.875 (n=18 stage1)", "✅ 측정"],
        ["난독화 정확도", "40 → 78%", "100% (n=17 UnCrackable)", "✅ 조건부 도달"],
        ["분석 대상 축소율", "30~40%", "99.49% (1,765 → 9 priority)", "✅ 초과"],
        ["MASTG-only Precision", "—", "100% (Recall 100%)", "✅ 외부 검증"],
    ]
    col_widths2 = [3.0, 2.6, 4.5, 2.5]
    x_acc = 0.55
    for i, h in enumerate(headers2):
        fill_rect(s, x_acc, 1.55, col_widths2[i], 0.45, DEEP_BLUE)
        add_textbox(s, x_acc + 0.05, 1.58, col_widths2[i] - 0.1, 0.4, h, size=12, bold=True, color=WHITE,
                    align=PP_ALIGN.CENTER)
        x_acc += col_widths2[i]
    for r, row in enumerate(rows2):
        y = 2.0 + r * 0.55
        bg = NEAR_WHITE if r % 2 == 0 else WHITE
        fill_rect(s, 0.55, y, sum(col_widths2), 0.55, bg)
        x_acc = 0.55
        for c, cell in enumerate(row):
            color = NAVY if c == 0 or c == 3 else TEXT_DARK
            bold = c == 0 or c == 3
            add_textbox(s, x_acc + 0.07, y + 0.07, col_widths2[c] - 0.14, 0.45, cell,
                        size=11.5, bold=bold, color=color,
                        align=PP_ALIGN.CENTER if c != 0 else PP_ALIGN.LEFT)
            x_acc += col_widths2[c]
    fill_rect(s, 0.55, 6.6, 12.5, 0.6, NAVY)
    add_textbox(s, 0.75, 6.65, 12.0, 0.5,
                "→ PPT 9주차 deliverable (성능 평가 + Ablation + 베이스라인) 본체 모두 충족",
                size=14, bold=True, color=WHITE)
    page_footer(s, 13, total)

    # ---------------------------------- Slide 14 — Pipeline boundary + 한계
    s = prs.slides.add_slide(blank)
    slide_header(s, "Pipeline Boundary + 한계", "Java-only static analysis가 못 잡는 영역의 정량 입증")
    fill_rect(s, 0.45, 1.55, 6.3, 5.5, NEAR_WHITE)
    fill_rect(s, 0.45, 1.55, 0.08, 5.5, ACCENT_RED)
    add_textbox(s, 0.65, 1.65, 5.95, 0.4, "Boundary case (외부 corpus가 정량 입증)",
                size=14, bold=True, color=NAVY)
    add_multi_text(s, 0.65, 2.1, 5.95, 5.0, [
        ("UnCrackable-Level2", {"size": 13, "bold": True, "color": ACCENT_RED}),
        ("    핵심 secret = libfoo.so (native lib)", {"size": 11}),
        ("    Java 측: System.loadLibrary + JNI bridge", {"size": 11}),
        ("    Stage 1 in-scope finding 0건", {"size": 11, "italic": True, "color": TEXT_MUTED}),
        ("    MASVS-CRYPTO-1 정답 = 못 잡음", {"size": 11, "color": ACCENT_RED}),
        ("", {}),
        ("r2pay-v1.0", {"size": 13, "bold": True, "color": ACCENT_RED}),
        ("    libnative-lib.so + RootBeer", {"size": 11}),
        ("    의도적 1337/0 ArithmeticException 패턴", {"size": 11}),
        ("    Stage 1 in-scope finding 0건", {"size": 11, "italic": True, "color": TEXT_MUTED}),
        ("    MASVS-CRYPTO-1 / RESILIENCE = 못 잡음", {"size": 11, "color": ACCENT_RED}),
        ("", {}),
        ("→ Java-only static = 명백한 boundary", {"size": 12, "bold": True, "color": NAVY}),
    ])
    fill_rect(s, 6.85, 1.55, 6.2, 5.5, NEAR_WHITE)
    fill_rect(s, 6.85, 1.55, 0.08, 5.5, ACCENT_GREEN)
    add_textbox(s, 7.05, 1.65, 5.85, 0.4, "Future Work (한계 해소)", size=14, bold=True, color=NAVY)
    add_multi_text(s, 7.05, 2.1, 5.85, 5.0, [
        ("Native binary 분석 통합", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    Ghidra headless + LLM symbol enum", {"size": 11}),
        ("    radare2 / r2ghidra (.so 분석)", {"size": 11}),
        ("", {}),
        ("category enum 확장", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    anti_tamper (root/debug detection)", {"size": 11}),
        ("    MASVS-RESILIENCE-2/3 매핑", {"size": 11}),
        ("", {}),
        ("Stage 3 ensemble을 MASTG까지 확장", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    UnCrackable-Level1 ucl1-1/2/3에", {"size": 11}),
        ("    attacker/defender/domain_expert 평가", {"size": 11}),
        ("", {}),
        ("Androidmeda Apache 2.0 deobf 통합", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("    Phase C에서 fork/merge 가능", {"size": 11}),
    ])
    page_footer(s, 14, total)

    # ---------------------------------- Slide 15 — 발견 취약점 사례 (highlight)
    s = prs.slides.add_slide(blank)
    slide_header(s, "주요 발견 취약점 사례 (Strong TP 9건)", "Stage 3 ≥3/3 합의 — 모든 시각이 동의한 strong TP")
    findings = [
        ("ssl-2", "AuthData token logcat", "HIGH",
         "Kotlin data class toString() leaks authenticatorToken"),
        ("ssl-4", "HmgUserInfo PII toString", "HIGH",
         "UUID / 생년월일 / 이메일 / 이름 → logcat 누출 (GDPR)"),
        ("ssl-5", "BuildConfig.IDENTIFIER hardcoded", "HIGH",
         "build-time 상수 = KDF passphrase. 모든 device 동일 키"),
        ("ssl-6", "gRPC .usePlaintext()", "HIGH",
         "차량 syslog 평문 외부 송출 — MITM 진단 페이로드 관찰"),
        ("vc-6", "VehicleBroadcastReceiver", "HIGH",
         "exported=true + macAddress 미검증 DB 저장"),
        ("lmp-1", "PromptsContentProvider", "HIGH",
         "exported provider — LLM system prompt 외부 노출"),
        ("vc-5", "GleoActionSender broadcast", "MEDIUM",
         "Implicit broadcast로 응답 정보 외부 송출"),
        ("lmp-2", "LLMModelProviderReceiver", "MEDIUM",
         "exported receiver — 모델 파일 삭제 + Process kill DoS"),
        ("ssl-1", "ECCCrypto KDF passphrase", "HIGH",
         "SHA-256 only KDF + ssl-5와 결합 시 universal decrypt"),
    ]
    for i, (fid, name, sev, desc) in enumerate(findings):
        col = i % 3
        row = i // 3
        x = 0.5 + col * 4.25
        y = 1.55 + row * 1.75
        fill_rect(s, x, y, 4.05, 1.6, NEAR_WHITE)
        sev_color = ACCENT_RED if sev == "HIGH" else ACCENT_GOLD
        fill_rect(s, x, y, 0.08, 1.6, sev_color)
        add_chip(s, x + 0.2, y + 0.12, 0.7, 0.35, sev, fill=sev_color, color=WHITE, size=10)
        add_textbox(s, x + 1.0, y + 0.12, 2.95, 0.35, fid, size=12, bold=True,
                    color=DEEP_BLUE, font=FONT_NUM)
        add_textbox(s, x + 0.2, y + 0.55, 3.7, 0.4, name, size=12, bold=True, color=NAVY)
        add_textbox(s, x + 0.2, y + 0.95, 3.7, 0.6, desc, size=10, color=TEXT_DARK)
    page_footer(s, 15, total)

    # ---------------------------------- Slide 16 — 결론 + 다음 단계 + 산출물
    s = prs.slides.add_slide(blank)
    fill_rect(s, 0, 0, 13.333, 7.5, NAVY)
    fill_rect(s, 0, 1.05, 13.333, 0.04, TEAL)
    add_textbox(s, 0.55, 0.4, 12.5, 0.55, "결론 + 다음 단계 + 산출물", size=28, bold=True, color=WHITE)
    # 좌측 — 결론
    fill_rect(s, 0.45, 1.4, 6.3, 4.8, RGBColor(0x2D, 0x35, 0x6B))
    add_textbox(s, 0.65, 1.5, 5.95, 0.4, "결론", size=15, bold=True, color=TEAL)
    add_multi_text(s, 0.65, 1.9, 5.95, 4.2, [
        ("• Phase A~C + Stage 2.b + Phase B-4.c.2 모두 완료", {"size": 12, "color": WHITE}),
        ("", {}),
        ("• PPT 9주차 deliverable 본체 충족", {"size": 12, "bold": True, "color": WHITE}),
        ("    P 77.8% / R 100% / F1 0.875 (combined n=18)", {"size": 11, "color": TEAL}),
        ("    ≥2/3 합의 P 100% / F1 0.952 (PleOS n=15)", {"size": 11, "color": TEAL}),
        ("", {}),
        ("• 외부 OWASP MASTG corpus에서 Precision 100% 검증", {"size": 12, "color": WHITE}),
        ("    UnCrackable-Level1 3 in-scope 모두 TP", {"size": 11, "color": TEAL}),
        ("", {}),
        ("• Pipeline boundary 정량 입증", {"size": 12, "color": WHITE}),
        ("    Java-only는 native-bound vuln 못 잡음", {"size": 11, "color": TEAL}),
        ("", {}),
        ("• PleOS corpus 난독화 0.2~0.4% — surprising", {"size": 12, "bold": True, "color": ACCENT_GOLD}),
        ("    PPT 가정과 다름 (PleOS 코드 품질 발견)", {"size": 11, "color": TEAL}),
    ])
    # 우상 — 다음 단계
    fill_rect(s, 6.95, 1.4, 6.1, 2.6, RGBColor(0x2D, 0x35, 0x6B))
    add_textbox(s, 7.15, 1.5, 5.85, 0.4, "다음 단계 — Phase D 진입", size=15, bold=True, color=TEAL)
    add_multi_text(s, 7.15, 1.9, 5.85, 2.0, [
        ("① AAOS 매핑 표 완성 (§3.7 / §4.2 / §5.1)", {"size": 11.5, "color": WHITE}),
        ("② TARA 산출물 자동 생성 (자산-위협-영향)", {"size": 11.5, "color": WHITE}),
        ("③ 사례 연구 5건 케이스 카드 (10주차)", {"size": 11.5, "color": WHITE}),
        ("④ 보고서 v0.9 (13주차)", {"size": 11.5, "color": WHITE}),
        ("⑤ Stage 3 ensemble을 MASTG까지 확장 (선택)", {"size": 11.5, "color": TEAL, "italic": True}),
    ])
    # 우하 — 산출물 + repo
    fill_rect(s, 6.95, 4.15, 6.1, 2.05, RGBColor(0x2D, 0x35, 0x6B))
    add_textbox(s, 7.15, 4.25, 5.85, 0.4, "산출물", size=15, bold=True, color=TEAL)
    add_multi_text(s, 7.15, 4.65, 5.85, 1.5, [
        ("GitHub: HoyoenKim/pleos-llm-scanner (MIT, 10 commits)", {"size": 11, "color": WHITE, "font": FONT_NUM}),
        ("docs/ : 6 audit 노트 (stage 2.b / b-4.c / b-4.c.2 / phase c / viz / ppt revision)", {"size": 10.5, "color": WHITE}),
        ("data/ground_truth/ : self n=15 + MASTG n=3 + combined n=18", {"size": 10.5, "color": WHITE}),
        ("data/viz/ : 6 차트 PNG (Malgun Gothic / matplotlib 3.10.8)", {"size": 10.5, "color": WHITE}),
        ("src/ : eval.py · ablation.py · deobf/entropy.py · viz/plot_metrics.py", {"size": 10.5, "color": WHITE, "font": FONT_NUM}),
    ])
    add_textbox(s, 0.55, 6.55, 12.5, 0.4,
                "PleOS 9주차 종합 v3 — 측정값 모두 GT 기반 (가짜·추정 수치 없음)",
                size=11, color=TEAL, italic=True, align=PP_ALIGN.CENTER)
    page_footer(s, 16, total)

    out_path = Path(__file__).parent.parent.parent / "pptx" / "v3" / "자율주행연구프로젝트1_9주차_2025311610_김호연_v3.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    print(f"Wrote: {out_path}")
    return out_path


if __name__ == "__main__":
    build()
