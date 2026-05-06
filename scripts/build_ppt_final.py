#!/usr/bin/env python
"""학기 최종발표 PPT — 18 슬라이드 풀 빌드.

본 학기 최종 측정값 (combined GT n=28, Stage 3 ≥2/3 F1 0.979) 으로 학기 종합.
Ocean Gradient 색상 + Malgun Gothic + 16:9 (13.333 × 7.5 inch).

작성자/소속/제출 파일명은 `scripts/_author.json` (gitignored) 에서 로드.
산출: ../pptx/v3/자율주행연구프로젝트1_최종발표_<id>_<name>_v3.pptx
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


def _load_author() -> dict:
    here = Path(__file__).parent
    p = here / "_author.json"
    if not p.exists():
        p = here / "_author.example.json"
    with p.open(encoding="utf-8") as f:
        return json.load(f)


AUTHOR = _load_author()

# Theme — Ocean Gradient
NAVY = RGBColor(0x21, 0x29, 0x5C)
DEEP_BLUE = RGBColor(0x06, 0x5A, 0x82)
TEAL = RGBColor(0x1C, 0x72, 0x93)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NEAR_WHITE = RGBColor(0xF5, 0xF7, 0xFA)
TEXT_DARK = RGBColor(0x1A, 0x1F, 0x3A)
TEXT_MUTED = RGBColor(0x60, 0x6F, 0x88)
ACCENT_GREEN = RGBColor(0x3A, 0x7D, 0x44)
ACCENT_RED = RGBColor(0xC7, 0x3E, 0x1D)
ACCENT_GOLD = RGBColor(0xC4, 0x86, 0x1F)

FONT_HEAD = "Malgun Gothic"
FONT_BODY = "Malgun Gothic"
FONT_NUM = "Cambria"

VIZ = Path(__file__).parent.parent / "data" / "viz"
TOTAL = 18


def add_text(slide, x, y, w, h, text, *, size=14, bold=False, color=TEXT_DARK,
             align=PP_ALIGN.LEFT, italic=False, font=FONT_BODY):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return tb


def add_lines(slide, x, y, w, h, lines, *, size=12, color=TEXT_DARK, line_spacing=1.25):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(lines):
        if isinstance(item, str):
            text, opts = item, {}
        else:
            text, opts = item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = opts.get("align", PP_ALIGN.LEFT)
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = text
        r.font.name = opts.get("font", FONT_BODY)
        r.font.size = Pt(opts.get("size", size))
        r.font.bold = opts.get("bold", False)
        r.font.italic = opts.get("italic", False)
        r.font.color.rgb = opts.get("color", color)
    return tb


def fill_rect(slide, x, y, w, h, color, *, line_color=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    if line_color is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line_color
    s.shadow.inherit = False
    return s


def header(slide, title, subtitle=None):
    fill_rect(slide, 0, 0, 0.18, 7.5, DEEP_BLUE)
    add_text(slide, 0.45, 0.30, 12.5, 0.7, title, size=26, bold=True, color=NAVY)
    if subtitle:
        add_text(slide, 0.45, 0.92, 12.5, 0.35, subtitle, size=12, color=TEXT_MUTED, italic=True)
        return 1.40
    return 1.05


def footer(slide, page_no):
    add_text(slide, 11.5, 7.10, 1.8, 0.3, f"{page_no} / {TOTAL}",
             size=10, color=TEXT_MUTED, align=PP_ALIGN.RIGHT, font=FONT_NUM)
    add_text(slide, 0.45, 7.10, 6.0, 0.3,
             "PleOS LLM Scanner — 최종발표 (2026-06-07)",
             size=9, color=TEXT_MUTED)


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ============================================================ Slide 1 — Cover
    s = prs.slides.add_slide(blank)
    fill_rect(s, 0, 0, 13.333, 7.5, NAVY)
    fill_rect(s, 0, 5.6, 13.333, 0.06, TEAL)
    add_text(s, 0.6, 1.5, 12.0, 0.5, "자율주행연구프로젝트 1 — 최종발표",
             size=18, color=TEAL, font=FONT_NUM)
    add_text(s, 0.6, 2.0, 12.0, 1.4,
             "LLM을 활용한 디컴파일러 분석 및\nPleOS 적용 방안 검토",
             size=42, bold=True, color=WHITE)
    add_text(s, 0.6, 4.0, 12.0, 0.4,
             "LLM-based Decompiler Analysis for IVI Security on PleOS",
             size=15, color=TEAL, italic=True)
    add_text(s, 0.6, 5.85, 12.0, 0.4,
             f"{AUTHOR['author_name']} ({AUTHOR['student_id']})  ·  {AUTHOR['institution']}  ·  {AUTHOR['lab']}",
             size=13, color=WHITE)
    add_text(s, 0.6, 6.30, 12.0, 0.4, AUTHOR['project_subtitle'], size=11, color=TEAL)
    add_text(s, 0.6, 6.95, 12.0, 0.3, "2026-1학기  ·  2026-06-07 발표",
             size=10, color=TEAL, italic=True)

    # ============================================================ Slide 2 — Agenda
    s = prs.slides.add_slide(blank)
    header(s, "목차", "본 학기 연구 RQ → Pipeline 설계 → 측정 결과 → 한계 및 Future Work")
    add_lines(s, 0.6, 1.6, 12.5, 5.5, [
        ("1. 연구 질문 (RQ) 와 환경 제약", {"size": 16, "bold": True, "color": DEEP_BLUE}),
        "    자동차 IVI APK 보안 점검에서 LLM 을 단독 탐지기가 아니라 reasoning component 로 활용 가능한가",
        ("2. 파이프라인 설계 — Stage 0 / 1 / 2 / 3", {"size": 16, "bold": True, "color": DEEP_BLUE}),
        "    Stage 0 deobfuscation → Stage 1 detection → Stage 2 verification → Stage 3 multi-perspective consensus",
        ("3. 측정 결과 — combined GT n=28", {"size": 16, "bold": True, "color": DEEP_BLUE}),
        "    PleOS self 15 + MASTG 4 + InsecureBankv2 9 / Stage 3 ≥2/3 합의 F1 0.979",
        ("4. RQ 별 corpus-level finding (R1.a / R2.a / R3.a / R4 / R1.b 등)", {"size": 16, "bold": True, "color": DEEP_BLUE}),
        "    bootstrap CI / disagreement matrix / native lib inventory / real-world 난독화 baseline",
        ("5. AAOS / MASVS / TARA 매핑 + 사례 연구 5건", {"size": 16, "bold": True, "color": DEEP_BLUE}),
        ("6. 한계 + Future Work + 결론", {"size": 16, "bold": True, "color": DEEP_BLUE}),
    ], size=14)
    footer(s, 2)

    # ============================================================ Slide 3 — Research Question
    s = prs.slides.add_slide(blank)
    header(s, "1. 연구 질문 (Research Question)", "본 학기의 핵심 질문과 4개 sub-question")
    fill_rect(s, 0.6, 1.6, 12.1, 1.6, NEAR_WHITE)
    add_lines(s, 0.8, 1.7, 11.7, 1.5, [
        ("핵심 질문 (Core RQ):", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("자동차 IVI APK 보안 점검에서 LLM 을 단독 탐지기 (black-box detector) 가 아니라,",
         {"size": 16, "bold": True, "color": NAVY}),
        ("deterministic triage 와 도메인 검증 규칙 사이의 reasoning component 로 활용했을 때",
         {"size": 16, "bold": True, "color": NAVY}),
        ("실용적인 정적 분석 pipeline 을 만들 수 있는가?", {"size": 16, "bold": True, "color": NAVY}),
    ])
    add_lines(s, 0.6, 3.4, 12.1, 3.5, [
        ("4 sub-question (RQ1~4):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        ("• RQ1 — Multi-stage gain 의 통계적 유의성", {"size": 14, "bold": True}),
        "    Stage 1→2→3 의 Precision / F1 향상이 우연이 아닌 것을 bootstrap CI / 표본 확장으로 입증",
        ("• RQ2 — Multi-perspective ensemble 의 diversity 진단", {"size": 14, "bold": True}),
        "    동일 모델 + 시각 3종 합의가 multi-model 의 대체재인지 (Cohen's κ)",
        ("• RQ3 — Java-only 정적 분석의 boundary 정량화", {"size": 14, "bold": True}),
        "    PleOS 207 APK + 외부 corpus 의 native lib 비율 측정으로 한계 L1 의 corpus-level 인덱스",
        ("• RQ4 — Real-world 난독화 일반화", {"size": 14, "bold": True}),
        "    hand-crafted MASTG (40~50%) vs PleOS (0.2~0.4%) 사이의 real-world commercial 난독화 baseline",
    ], size=12)
    footer(s, 3)

    # ============================================================ Slide 4 — Background
    s = prs.slides.add_slide(blank)
    header(s, "2. 배경 — PleOS / IVI 보안 + 환경 제약", "왜 LLM 기반 정적 분석인가")
    add_lines(s, 0.6, 1.5, 6.2, 5.5, [
        ("PleOS (현대차 IVI 플랫폼):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• Android 14 기반 (AAOS-like), PleOS Connect v2.0.5 emulator 사용",
        "• 차량 안전 + 사용자 자격증명 + 위치/PII",
        "• OTA 업데이트로 빈번 갱신 → 정적 분석 가치 큼",
        "",
        ("기존 도구 한계:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• jadx 수동 분석: APK 1개 6~7시간",
        "• 단일 LLM 1-pass: Precision ~78%",
        "• android-scanner-ai / Androidmeda: 정량 측정값 부재",
    ], size=12)
    add_lines(s, 6.95, 1.5, 6.0, 5.5, [
        ("본 학기 환경 제약:", {"size": 14, "bold": True, "color": ACCENT_RED}),
        "• 로컬 GPU 없음 → 로컬 LLM 불가",
        "• 외부 유료 API 미보유 → OpenAI/Gemini 직접 호출 X",
        "• 실차 접근 불가 → 에뮬레이터 + ADB",
        "• 계약과제 IP 보호 → 실차 코드 외부 송출 금지",
        "",
        ("대응 전략:", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "• 분석 엔진 = Claude Code (Opus 4.7, 1M context)",
        "• 멀티 모델 → 단일 모델 + 멀티 시각 (시각 3종)",
        "• 결정론 코드 (jadx, regex, AST, 매핑) + LLM (탐지/검증/합의)",
    ], size=12)
    footer(s, 4)

    # ============================================================ Slide 5 — Pipeline
    s = prs.slides.add_slide(blank)
    header(s, "3. 파이프라인 — Stage 0 / 1 / 2 / 3", "결정론 + LLM 의 4단계 검증")
    add_lines(s, 0.6, 1.5, 12.5, 5.5, [
        ("APK   ─── jadx 디컴파일 ───>   data/decompiled/<apk>/sources/", {"size": 13, "font": FONT_NUM}),
        "",
        ("                ↓", {"size": 13, "font": FONT_NUM, "color": TEAL}),
        ("Stage 0 (preprocessing, optional) — Deobfuscation", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    obfuscation score ≥ 0.7 인 클래스에 LLM 이름 복원 (configs/prompts/stage0_deobfuscate.md)",
        "",
        ("                ↓", {"size": 13, "font": FONT_NUM, "color": TEAL}),
        ("Stage 1 — Initial Detection (LLM 1-pass)", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    keyword grep 으로 priority class 추출 → 6 카테고리 (crypto/network/permission/intent/hardcoded/reflection_dynamic)",
        "",
        ("                ↓", {"size": 13, "font": FONT_NUM, "color": TEAL}),
        ("Stage 2 — Verification (rule + code)", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    caller chain + manifest + Hilt graph + AST/regex rule + LLM 재독 → verdict TP/FP/uncertain",
        "",
        ("                ↓", {"size": 13, "font": FONT_NUM, "color": TEAL}),
        ("Stage 3 — Multi-perspective Consensus", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    동일 모델에 시각 3종 (attacker / defender / domain_expert) 적용 → ≥2/3 합의 = TP, ≥3/3 = strong-TP",
    ], size=12)
    footer(s, 5)

    # ============================================================ Slide 6 — Stage 0
    s = prs.slides.add_slide(blank)
    header(s, "4. Stage 0 — Deobfuscation (preprocessing)", "고난독화 클래스의 LLM 이름 복원")
    add_lines(s, 0.6, 1.5, 12.5, 2.5, [
        ("입력 (entropy 측정):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• Shannon entropy + jadx pattern (`C0014b`, `m1234a`) → 클래스별 composite score 산출",
        "• HIGH = composite ≥ 0.7. PleOS APK 3종 HIGH 비율 0.2~0.4% (의외로 낮음)",
        "",
        ("출력 (LLM rename):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• 클래스 / 메서드 / 필드 의 의미적 이름 + role description + confidence",
        "• String literal → 0.95+, imports + signatures → 0.80+, 구조적 hint → 0.60+",
    ], size=12)
    add_lines(s, 0.6, 4.5, 12.5, 2.6, [
        ("측정 결과:", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "• Hand-crafted MASTG (UnCrackable Level1/2 sg.vantagepoint anti-tamper helper)",
        "    → n=17 (6 class + 11 method) exact match 100% (upper bound)",
        "• Real-world OSS — NewPipe v0.27.6 (ProGuard 활성)  HIGH 1.7%",
        "    → ProGuard mapping 부재로 exact accuracy 측정 partial. Future Work.",
        "• Real-world floor 정량 위치: hand-crafted (40~50%) > NewPipe (1.7%) > PleOS (0.2~0.4%)",
    ], size=12)
    footer(s, 6)

    # ============================================================ Slide 7 — Stage 1
    s = prs.slides.add_slide(blank)
    header(s, "5. Stage 1 — Initial Detection", "키워드 + 단일 LLM 의 1차 탐지")
    add_lines(s, 0.6, 1.5, 6.2, 5.5, [
        ("키워드 카테고리 (configs/keywords.yaml):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• crypto — weak alg / hardcoded keys / ECB",
        "• network — http:// / TrustManager / WebView 설정",
        "• permission — 위험 / dynamic grant",
        "• intent — exported / implicit / mutable",
        "• hardcoded — API keys / tokens / passwords",
        "• reflection_dynamic — 동적 로딩 / 권한 우회",
        "",
        ("Triage:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    1,765 Java files → 9 priority class (99.49% 축소)",
    ], size=12)
    add_lines(s, 6.95, 1.5, 6.0, 5.5, [
        ("Stage 1 측정값 (combined n=28):", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "• Precision (lenient): 85.7%",
        "• Recall: 100%",
        "• F1: 0.923",
        "• 95% bootstrap CI: [71.4%, 96.4%]",
        "• 후보 기준 FP 비율: 14.3% (가설 25% 충족)",
        "",
        ("출력 형식 (JSON-strict):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    {class, line, category, severity, evidence,",
        "     rationale, confidence, aaos_mapping, verified_by}",
    ], size=12)
    footer(s, 7)

    # ============================================================ Slide 8 — Stage 2
    s = prs.slides.add_slide(blank)
    header(s, "6. Stage 2 — Verification", "caller chain + manifest 검증으로 FP 거르기")
    add_lines(s, 0.6, 1.5, 12.5, 5.5, [
        ("검증 축 3종 (별도 LLM prompt 없이 rule + code):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• Manifest URI deep-link 매칭자 (android:scheme / host / data) 부재 확인",
        "• Compose Navigation route 등록 + nav route 패턴 분석",
        "• IntentRouter / NavRouter binding 동선 (외부 진입 가능성)",
        "",
        ("케이스 — VehicleControl AppPermissionManager (vc-3 / vc-4): 4중 차단 입증", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "  1) Manifest URI deep-link 0건",
        "  2) Compose Nav route 는 NavGraphBuilder 내부만 (navDeepLink 미사용)",
        "  3) IntentRouter LinkProvider.createLink 가 항상 path segment 1개",
        "  4) NavRouter 구현체 = VehicleInformation + Convenience 단 2개 (APPLICATIONS binding 없음)",
        "  → ApplicationDetails 외부 진입 불가 = FP CONFIRMED",
        "",
        ("Stage 1→2 (GT 기반 P-ceiling 시뮬):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "    Precision 78.9% → 100%, FP 4건 모두 정확 filter (transition matrix R1.a 결과)",
    ], size=12)
    footer(s, 8)

    # ============================================================ Slide 9 — Stage 3
    s = prs.slides.add_slide(blank)
    header(s, "7. Stage 3 — Multi-perspective Consensus",
           "단일 모델 (Opus 4.7) + 시각 3종 합의 — 멀티 모델 ensemble 의 환경 제약 대안")
    add_lines(s, 0.6, 1.5, 6.2, 5.5, [
        ("시각 3종 prompt:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• Attacker — exploit chain / 차량 안전 영향",
        "• Defender — missing controls / hardening",
        "• IVI Domain Expert — TARA / 차량 자산 / STRIDE",
        "",
        ("합의 규칙:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• 3/3: strong-TP",
        "• 2/3: TP",
        "• 1/3: uncertain",
        "• 0/3: clean (보고 안 함)",
        "",
        ("합의 임계 ≥2/3 가 default (Variant B 최적 F1)",
        {"size": 12, "italic": True, "color": TEXT_MUTED}),
    ], size=12)
    add_lines(s, 6.95, 1.5, 6.0, 5.5, [
        ("Stage 3 ≥2/3 합의 측정값 (combined n=28):", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "• Precision: 100%",
        "• Recall: 95.8%",
        "• F1: 0.979 ← 본 학기 최고",
        "• Reported FP: 0건",
        "• FN: 1건 (vc-7 LOW hardening)",
        "",
        ("RQ2 발견 (R2.a):", {"size": 14, "bold": True, "color": ACCENT_RED}),
        "• defender 시각 = universal flag (28/28)",
        "• attacker ↔ domain_expert κ = 0.619 (substantial)",
        "• → defender prompt selectivity 보강 권고",
    ], size=12)
    footer(s, 9)

    # ============================================================ Slide 10 — Corpus
    s = prs.slides.add_slide(blank)
    header(s, "8. 측정 corpus — combined GT n=28", "PleOS 자체 + OWASP MASTG + InsecureBankv2")
    add_lines(s, 0.6, 1.5, 12.5, 5.5, [
        ("PleOS 자체 corpus (n=15, self-labeled):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• ai.umos.vehiclecontrol — 7 finding (system UID + 13 위험 권한, 차량 제어 spoofing)",
        "• ai.pleos.sync.syslog — 6 finding (gRPC plaintext, hardcoded BuildConfig.IDENTIFIER 키)",
        "• ai.pleos.llm.model.provider — 2 finding (exported PromptsContentProvider, model file DoS)",
        "",
        ("외부 corpus (n=13 in-scope + 4 boundary):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• OWASP MASTG UnCrackable Level1 (3 in-scope, hardcoded AES key)",
        "• OWASP MASTG UnCrackable Level3 (1 in-scope, XOR key hardcoded)",
        "• InsecureBankv2 (9 in-scope) — Java 측 vuln 풍부 (HTTP, hardcoded key, exported provider)",
        "• Boundary 4: UnCrackable-L2 / r2pay-v1.0 (native), HelloWord-JNI (JNI), certificatePinningXamarin (.NET)",
        "",
        ("Total: 28 라벨 (TP 24 / FP 4 / FN 0 / uncertain 0)", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
    ], size=12)
    footer(s, 10)

    # ============================================================ Slide 11 — Stage 1 / 3 results
    s = prs.slides.add_slide(blank)
    header(s, "9. Stage 1 / Stage 3 측정 결과", "초기 계획서 가설 모두 충족")
    add_lines(s, 0.6, 1.5, 12.5, 5.5, [
        ("측정 표 (combined n=28, lenient):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        ("                    Precision    Recall     F1       FP rate    95% CI (Precision)",
         {"size": 12, "font": FONT_NUM, "bold": True}),
        ("Stage 1            85.7%        100%       0.923    14.3%      [71.4%, 96.4%]",
         {"size": 12, "font": FONT_NUM, "color": ACCENT_GREEN}),
        ("Stage 3 ≥2/3       100%         95.8%      0.979    0%         (n=28 reported)",
         {"size": 12, "font": FONT_NUM, "bold": True, "color": ACCENT_GREEN}),
        ("Stage 3 ≥3/3       100%         79.2%      0.884    0%",
         {"size": 12, "font": FONT_NUM, "color": TEXT_MUTED}),
        "",
        ("초기 계획서 가설 vs 실측:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• 1차 오탐률 25% → 14.3% (충족, -10.7%p)",
        "• 3차 오탐률 7% → 0% (충족)",
        "• Precision 0.93 → 1.00 (≥2/3 합의 시, 충족·초과)",
        "• 분석 대상 축소율 30~40% → 99.49% (1,765 → 9 priority)",
        "• 난독화 정확도 78% → 100% (hand-crafted upper bound)",
    ], size=12)
    footer(s, 11)

    # ============================================================ Slide 12 — Bootstrap CI (chart)
    s = prs.slides.add_slide(blank)
    header(s, "10. R1.b — Bootstrap CI: 표본 효과의 통계 측정",
           "n=19 → n=28 확장으로 CI 폭 약 1/3 감소")
    add_lines(s, 0.6, 1.5, 12.5, 2.5, [
        ("non-parametric percentile bootstrap, 1000 iter, seed 42:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        ("                    n=19 (5/6)                    n=28 (5/7)                       Δ CI 폭",
         {"size": 11, "font": FONT_NUM, "bold": True}),
        ("Precision (lenient)  78.9% / [57.9, 94.7]            85.7% / [71.4, 96.4]              −11.8%p",
         {"size": 11, "font": FONT_NUM}),
        ("F1 (lenient)         88.2% / [73.3, 97.3]            92.3% / [83.3, 98.2]              −9.1%p",
         {"size": 11, "font": FONT_NUM}),
        ("FP rate              21.1% / [5.3,  42.1]            14.3% / [3.6,  28.6]              −11.8%p",
         {"size": 11, "font": FONT_NUM}),
    ])
    add_lines(s, 0.6, 4.0, 12.5, 3.0, [
        ("핵심 발견:", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "• 표본 9건 추가만으로 CI 폭이 약 1/3 줄어듦 (Precision −32%, F1 −38%)",
        "• 본 학기 처음으로 'n 증가 → CI 좁힘' 의 직접 측정값 확보",
        "• RQ1 actionable insight: 보고서의 정량 주장이 통계적으로 신뢰 가능한 corpus 크기 ≈ n=30+",
        "• Recall CI 가 [100%, 100%] 인 이유: GT ⊆ reports (모든 GT 라벨이 reports 에 매칭)",
        "",
        ("Future Work — n ≥ 40 corpus 로 확장 시 ±5%p 폭 가능 (DIVA, 추가 commercial APK)",
         {"size": 12, "italic": True, "color": TEXT_MUTED}),
    ], size=12)
    footer(s, 12)

    # ============================================================ Slide 13 — Ablation (chart insert)
    s = prs.slides.add_slide(blank)
    header(s, "11. Ablation — 단계 / 합의 임계 변형", "각 단계의 기여도 + ≥2/3 default 정당화")
    add_lines(s, 0.6, 1.4, 6.1, 5.7, [
        ("Variant A — Stage ablation:", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("              Precision   Recall    F1",
         {"size": 11, "font": FONT_NUM, "bold": True}),
        ("A.1 Stage 1   85.7%       100%      0.923",
         {"size": 11, "font": FONT_NUM}),
        ("A.2 + Stage 2 100%        100%      1.000*",
         {"size": 11, "font": FONT_NUM, "color": TEXT_MUTED}),
        ("A.3 + Stage 3 100%        79.2%     0.884",
         {"size": 11, "font": FONT_NUM}),
        ("    (≥3/3 strong)", {"size": 10, "color": TEXT_MUTED, "italic": True}),
        "",
        ("* P-ceiling 시뮬 (GT 기반)", {"size": 10, "italic": True, "color": TEXT_MUTED}),
    ])
    add_lines(s, 6.95, 1.4, 6.1, 5.7, [
        ("Variant B — 합의 임계:", {"size": 13, "bold": True, "color": DEEP_BLUE}),
        ("              Precision   Recall    F1",
         {"size": 11, "font": FONT_NUM, "bold": True}),
        ("≥1/3          85.7%       100%      0.923",
         {"size": 11, "font": FONT_NUM}),
        ("≥2/3 default  100%        95.8%     0.979",
         {"size": 11, "font": FONT_NUM, "bold": True, "color": ACCENT_GREEN}),
        ("≥3/3          100%        79.2%     0.884",
         {"size": 11, "font": FONT_NUM}),
        "",
        ("≥2/3 가 best F1 (Recall trade-off 균형)",
         {"size": 11, "italic": True, "color": TEXT_MUTED}),
    ])
    footer(s, 13)

    # ============================================================ Slide 14 — RQ1/2/3
    s = prs.slides.add_slide(blank)
    header(s, "12. RQ1 / RQ2 / RQ3 — corpus-level 첫 측정값", "본 학기의 직접 contribution")
    add_lines(s, 0.6, 1.4, 12.5, 5.7, [
        ("RQ1 — Stage transition matrix (R1.a)", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• Stage 2 GT FP 4건 → Stage 3 합의에서 모두 정확 filter (0건 잘못 promote)",
        "• Stage 2 GT TP 24건 → Stage 3 23건 유지, 1건 손실 (vc-7 LOW hardening)",
        "→ Stage 3 합의가 단순 noise 가 아닌 정확한 filtering 임을 직접 입증",
        "",
        ("RQ2 — Perspective disagreement matrix (R2.a)", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• flag rate: attacker 75% / defender 100% / domain_expert 75%",
        "• κ(attacker, domain_expert) = 0.619 (substantial agreement)",
        "• κ(*, defender) = 0.0 (defender universal flag → diversity 약함)",
        "→ defender prompt selectivity calibration 권고 (보강 완료, 다음 corpus 측정에서 효과 검증)",
        "",
        ("RQ3 — Java-only boundary 의 corpus-level 인덱스 (R3.a)", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• PleOS Connect 207 시스템 APK 중 22 (10.6%) 가 native lib 보유",
        "• Top: ai.pleos.playground.caas (62 .so), maps.navigation (44), ambientai (24)",
        "• 보안 가치 큰 컴포넌트가 native top — 한계 L1 의 위험도 가중 인덱스",
    ], size=12)
    footer(s, 14)

    # ============================================================ Slide 15 — R4 baseline
    s = prs.slides.add_slide(blank)
    header(s, "13. RQ4 — Real-world 난독화 baseline (NewPipe)",
           "hand-crafted MASTG 와 PleOS 사이의 정량 위치 첫 입증")
    add_lines(s, 0.6, 1.5, 12.5, 5.5, [
        ("R4 — NewPipe v0.27.6 도입 (real-world OSS, ProGuard 활성, 12 MB):",
         {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• 외부 raw URL 다운로드 → jadx 디컴파일 (2,520 비-framework 클래스)",
        "• HIGH 난독화 (composite ≥ 0.7): 42 클래스 = 1.7%",
        "• Sample classes: C1302f / m1266a / C1188w / m1011d / f713h … (jadx-pattern)",
        "",
        ("Real-world 난독화 baseline — entropy 비교:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        ("                         HIGH 비율   mean composite",
         {"size": 11, "font": FONT_NUM, "bold": True}),
        ("UnCrackable-Level1/2     50% / 40%   0.62 / 0.53     ← hand-crafted MASTG",
         {"size": 11, "font": FONT_NUM, "color": ACCENT_GREEN}),
        ("NewPipe v0.27.6          1.7%        0.12            ← real-world OSS baseline",
         {"size": 11, "font": FONT_NUM, "bold": True, "color": ACCENT_GOLD}),
        ("PleOS APK 3종            0.2~0.4%    0.03~0.05       ← 실제 IVI APK",
         {"size": 11, "font": FONT_NUM, "color": ACCENT_RED}),
        "",
        ("→ 두 극단 사이에 commercial OSS 의 정량 위치 끼워넣음 (본 학기 첫 R4 데이터)",
         {"size": 13, "bold": True}),
        ("Caveat: ProGuard mapping file 부재 → Stage 0 exact accuracy 측정 partial. semantic plausibility 평가만 가능.",
         {"size": 12, "italic": True, "color": TEXT_MUTED}),
    ], size=12)
    footer(s, 15)

    # ============================================================ Slide 16 — AAOS / TARA / Cases
    s = prs.slides.add_slide(blank)
    header(s, "14. AAOS / MASVS / TARA 매핑 + 사례 5건",
           "G5 / G6 / G7 deliverable")
    add_lines(s, 0.6, 1.4, 6.2, 5.7, [
        ("AAOS 섹션 커버리지 (n=28):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• §3.7 Permission Model — 11 finding (TP 9, HIGH 6)",
        "• §4.2 Credential Protection — 9 finding (TP 9, HIGH 6)",
        "• §5.1 Communication Security — 6 finding (TP 4, HIGH 2)",
        "",
        ("TARA Risk Matrix (TP only, n=23):", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "• Critical: 2 (vc-5 / vc-6 — 차량 제어 자산 직격)",
        "• High: 13 (Mitigate, current sprint)",
        "• Medium: 6 (Mitigate, next minor)",
        "• Low: 2 (Accept with monitoring)",
    ], size=12)
    add_lines(s, 6.95, 1.4, 6.0, 5.7, [
        ("사례 연구 5건:", {"size": 14, "bold": True, "color": DEEP_BLUE}),
        "1. 하드코딩 자격증명 (ssl-5 + ucl1-1 비교)",
        "    PleOS BuildConfig.IDENTIFIER as KDF + MASTG hardcoded AES key",
        "",
        "2. 권한 우회 FP — 4중 차단 입증 (vc-3/4)",
        "    Stage 1 P 78.9% → Stage 3 100% (multi-stage 효과)",
        "",
        "3. 평문 통신 (ssl-6 gRPC plaintext)",
        "    Stage 3 격상 사례 — ≥2/3 vs ≥3/3 차이 설명",
        "",
        "4. Exported ContentProvider (lmp-1)",
        "    LLM system-prompt 노출 → prompt injection chain 가능",
        "",
        "5. 차량 제어 spoofing (vc-6) — Critical risk",
    ], size=11)
    footer(s, 16)

    # ============================================================ Slide 17 — Limitations + Future Work
    s = prs.slides.add_slide(blank)
    header(s, "15. 한계 + Future Work", "본 학기 5 한계 카테고리 + 후속 연구 방향")
    add_lines(s, 0.6, 1.4, 6.2, 5.7, [
        ("본 학기 한계 (L1~L5):", {"size": 14, "bold": True, "color": ACCENT_RED}),
        "• L1 — Native code 분석 불가 (Java-only)",
        "    UnCrackable-L2 / r2pay / HelloWord-JNI / certPinXamarin = 4 boundary",
        "    PleOS 207 APK 중 10.6% = native (위험도 가중 더 큼)",
        "",
        "• L2 — 표본 크기 (n=28) 통계 약점",
        "    bootstrap 95% CI ±10~15%p",
        "",
        "• L3 — Multi-LLM ensemble 미구현 → multi-prompt 대체",
        "    외부 API budget 부재로 단일 모델 한정",
        "",
        "• L4 — Hand-crafted MASTG corpus 의 upper bound 성격",
        "    난독화 100% 는 anti-tamper helper 한정",
        "",
        "• L5 — Stage 3 의 MASTG 미평가 (✓ 해소 2026-04-30)",
    ], size=11)
    add_lines(s, 6.95, 1.4, 6.0, 5.7, [
        ("Future Work:", {"size": 14, "bold": True, "color": ACCENT_GREEN}),
        "• Native binary scanner 통합",
        "    radare2 (MIT, 외부 API X) headless + LLM",
        "    → L1 boundary 4 sample 의 in-scope 측정 가능",
        "",
        "• Multi-LLM ensemble (RQ2.b)",
        "    Anthropic + OpenAI + Google 3 vendor 비교",
        "    → 본 multi-prompt vs multi-model의 정량 비교",
        "",
        "• 표본 확장 (n ≥ 50)",
        "    DIVA / 추가 commercial APK / 의도적 corpus",
        "    → bootstrap CI ±5%p 가능",
        "",
        "• R4 exact accuracy",
        "    NewPipe ProGuard mapping 확보 후 Stage 0 정확도 측정",
        "",
        "• Fully-batch 자동화",
        "    Claude Code 인터랙티브 → CI/CD trigger",
    ], size=11)
    footer(s, 17)

    # ============================================================ Slide 18 — Conclusion
    s = prs.slides.add_slide(blank)
    fill_rect(s, 0, 0, 13.333, 7.5, NAVY)
    fill_rect(s, 0, 1.4, 13.333, 0.04, TEAL)
    add_text(s, 0.6, 0.4, 12.0, 0.6, "16. 결론", size=28, bold=True, color=WHITE)
    add_text(s, 0.6, 0.95, 12.0, 0.4,
             "본 연구의 정량 결과 + 산업 적용성 + Q&A",
             size=12, color=TEAL, italic=True)
    add_lines(s, 0.6, 1.7, 12.5, 4.5, [
        ("본 연구의 직접 contribution:", {"size": 14, "bold": True, "color": TEAL}),
        ("1. 자동차 IVI APK 보안 점검에서 LLM 을 reasoning component 로 활용한 4단계 정적 분석 pipeline 설계·구현",
         {"size": 13, "color": WHITE}),
        ("2. PleOS Connect v2.0.5 + OWASP MASTG 6 sample + InsecureBankv2 통합 GT corpus n=28",
         {"size": 13, "color": WHITE}),
        ("3. 단일 모델 + 멀티 시각 ensemble 의 정량 효과 측정 — Stage 3 ≥2/3 합의 F1 0.979 / Precision 100%",
         {"size": 13, "color": WHITE}),
        ("4. RQ별 corpus-level 첫 정량 인덱스 — bootstrap CI 폭 1/3 감소, perspective κ=0.619, native 10.6%, R4 baseline 1.7%",
         {"size": 13, "color": WHITE}),
        ("5. AAOS §3.7/4.2/5.1 + ISO 21434 TARA 자동 매핑 + 5건 사례 연구 + 통합 아키텍처 + 일반화 평가",
         {"size": 13, "color": WHITE}),
        "",
        ("산업 적용성:", {"size": 14, "bold": True, "color": TEAL}),
        ("• MVP — 정적 부분 (entropy / keyword / aaos_map / tara_generate) 만 GitHub Actions 통합 가능",
         {"size": 12, "color": WHITE}),
        ("• 차량 LLM (PleOS-internal) 활성화 시 Stage 1/2/3 자동화 — prompts 그대로 사용",
         {"size": 12, "color": WHITE}),
        ("• 60~70% OS-독립 — QNX / AGL 로 swap 2~3주 추정",
         {"size": 12, "color": WHITE}),
    ], size=13)
    add_text(s, 0.6, 6.6, 12.0, 0.5, "Q&A 환영합니다.",
             size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER, italic=True)
    add_text(s, 0.6, 7.1, 6.0, 0.3,
             "GitHub: HoyoenKim/pleos-llm-scanner (MIT)",
             size=10, color=TEAL, font=FONT_NUM)
    add_text(s, 11.5, 7.1, 1.8, 0.3, f"{TOTAL} / {TOTAL}",
             size=10, color=TEAL, align=PP_ALIGN.RIGHT, font=FONT_NUM)

    out = Path(__file__).parent.parent.parent / "pptx" / "v3" / (
        f"자율주행연구프로젝트1_최종발표_{AUTHOR['student_id']}_{AUTHOR['author_name']}_v3.pptx"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    print(f"Wrote: {out}")
    print(f"Size: {out.stat().st_size:,} bytes  ({TOTAL} slides)")


if __name__ == "__main__":
    build()
