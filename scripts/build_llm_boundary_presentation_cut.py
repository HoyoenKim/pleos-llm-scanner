#!/usr/bin/env python3
"""Build a clean lmp-1 presentation cut from verified runtime evidence.

This script does not display raw prompt/corpus content. It reads the redacted
artifact and trace emitted by record_llm_boundary_demo.ps1, then renders a
stable explanation-first MP4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "data" / "runtime_poc_llm_boundary_demo"
SOURCE_PROMPTS = ROOT / "data" / "decompiled" / "ai.pleos.llm.model.provider" / "resources" / "assets" / "prompts.json"
FONT_REGULAR = Path("C:/Windows/Fonts/malgun.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


COLORS = {
    "bg": (10, 16, 24),
    "panel": (22, 32, 45),
    "panel_2": (18, 27, 39),
    "ink": (238, 243, 250),
    "muted": (156, 171, 190),
    "line": (61, 79, 102),
    "blue": (80, 166, 255),
    "green": (89, 201, 150),
    "amber": (255, 191, 87),
    "red": (255, 106, 106),
    "purple": (178, 132, 255),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR
    if not path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size=size)


def safe_text(value: object) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = safe_text(text).split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= max_width:
            line = candidate
            continue
        if line:
            lines.append(line)
        line = word
    if line:
        lines.append(line)
    return lines


def rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: tuple[int, int, int], outline=None, width=1):
    draw.rounded_rectangle(xy, radius=8, fill=fill, outline=outline, width=width)


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: Iterable[str],
    size: int = 38,
    color: tuple[int, int, int] = COLORS["ink"],
    bold: bool = False,
    leading: int = 12,
    max_width: int | None = None,
) -> int:
    x, y = xy
    f = font(size, bold=bold)
    for raw in lines:
        wrapped = wrap_text(draw, raw, f, max_width) if max_width else [raw]
        for line in wrapped:
            draw.text((x, y), line, fill=color, font=f)
            y += size + leading
    return y


def draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str, color=COLORS["blue"]):
    draw.rectangle((0, 0, 1920, 82), fill=(7, 11, 18))
    draw.rectangle((0, 80, 1920, 84), fill=color)
    draw.text((54, 22), title, fill=COLORS["ink"], font=font(34, bold=True))
    draw.text((1370, 24), subtitle, fill=COLORS["muted"], font=font(27))


def draw_footer(draw: ImageDraw.ImageDraw, text: str):
    draw.rectangle((0, 1004, 1920, 1080), fill=(7, 11, 18))
    draw.text((54, 1024), text, fill=COLORS["muted"], font=font(28))


def base_frame(title: str, subtitle: str, footer: str, color=COLORS["blue"]) -> Image.Image:
    img = Image.new("RGB", (1920, 1080), COLORS["bg"])
    draw = ImageDraw.Draw(img)
    draw_header(draw, title, subtitle, color)
    draw_footer(draw, footer)
    return img


def scene_threat(_: dict) -> Image.Image:
    img = base_frame("Same-Device IVI App Boundary Bypass", "Threat model", "App install is the precondition, not the exploit.", COLORS["blue"])
    draw = ImageDraw.Draw(img)
    draw_text_block(draw, (94, 166), ["This is NOT remote vehicle compromise."], 62, COLORS["red"], True)
    rounded_rect(draw, (94, 300, 902, 768), COLORS["panel"], COLORS["line"], 2)
    rounded_rect(draw, (1018, 300, 1826, 768), COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (136, 348), ["Assumption"], 42, COLORS["amber"], True)
    draw_text_block(
        draw,
        (136, 426),
        [
            "An attacker already has one untrusted app running on the IVI device.",
            "The app is same-device, not remote.",
        ],
        36,
        COLORS["ink"],
        max_width=680,
    )
    draw_text_block(draw, (1060, 348), ["Security question"], 42, COLORS["green"], True)
    draw_text_block(
        draw,
        (1060, 426),
        [
            "Can that app access IVI-internal data or components that should still be protected?",
        ],
        38,
        COLORS["ink"],
        max_width=670,
    )
    return img


def scene_boundary(_: dict) -> Image.Image:
    img = base_frame("Same-Device IVI App Boundary Bypass", "Boundary under test", "Installed apps should not automatically cross privileged component boundaries.", COLORS["purple"])
    draw = ImageDraw.Draw(img)
    rounded_rect(draw, (112, 174, 730, 792), COLORS["panel"], COLORS["line"], 2)
    rounded_rect(draw, (1190, 174, 1808, 792), COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (166, 250), ["Untrusted app"], 50, COLORS["ink"], True)
    draw_text_block(draw, (166, 348), ["org.codex.pleos.poc", "No PleOS signing key", "No signature permission"], 36, COLORS["muted"], max_width=500)
    draw_text_block(draw, (1242, 250), ["Privileged IVI data"], 50, COLORS["ink"], True)
    draw_text_block(draw, (1242, 348), ["LLM prompt/corpus provider", "Internal prompt/corpus data", "Expected to be private"], 36, COLORS["muted"], max_width=500)
    draw.line((770, 480, 1150, 480), fill=COLORS["red"], width=8)
    draw.line((960, 400, 960, 560), fill=COLORS["red"], width=8)
    draw_text_block(draw, (802, 606), ["Expected boundary: access denied"], 42, COLORS["red"], True)
    return img


def scene_identity(evidence: dict) -> Image.Image:
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Attacker app identity", "The app is the simulated same-device caller, not a privileged PleOS component.", COLORS["blue"])
    draw = ImageDraw.Draw(img)
    rows = [
        ("Package", "org.codex.pleos.poc"),
        ("Observed caller", "same-device PoC harness"),
        ("Privileged status", "not a PleOS privileged/signature app"),
        ("Platform key", "not available to attacker app"),
        ("Claim role", "untrusted caller crossing a component boundary"),
    ]
    y = 180
    for label, value in rows:
        rounded_rect(draw, (130, y, 1790, y + 92), COLORS["panel"], COLORS["line"], 1)
        draw.text((168, y + 26), label, fill=COLORS["muted"], font=font(30, bold=True))
        draw.text((520, y + 24), value, fill=COLORS["ink"], font=font(34))
        y += 112
    return img


def scene_asset(_: dict) -> Image.Image:
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Protected asset", "The protected asset is the IVI LLM prompt/corpus provider.", COLORS["green"])
    draw = ImageDraw.Draw(img)
    rounded_rect(draw, (118, 164, 1802, 842), COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (170, 224), ["Protected asset"], 48, COLORS["green"], True)
    draw_text_block(draw, (170, 304), ["IVI LLM prompt/corpus provider"], 58, COLORS["ink"], True)
    draw_text_block(
        draw,
        (170, 430),
        [
            "Authority: ai.pleos.playground.llm.model.provider.prompts",
            "Expected protection: private provider or signature permission",
            "Expected result from this app: SecurityException or permission denied",
        ],
        34,
        COLORS["muted"],
        max_width=1500,
    )
    draw_text_block(draw, (170, 686), ["This is why permission_denial=false matters."], 42, COLORS["amber"], True)
    return img


def scene_trigger(_: dict) -> Image.Image:
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Trigger", "The PoC action is one provider query. No exploit chain or backend call is hidden here.", COLORS["amber"])
    draw = ImageDraw.Draw(img)
    boxes = [
        (122, 354, 548, 590, "Untrusted App", "org.codex.pleos.poc"),
        (748, 354, 1172, 590, "ContentResolver.query()", "same-device call"),
        (1372, 354, 1798, 590, "PromptsContentProvider", "exported provider"),
    ]
    for x1, y1, x2, y2, title, sub in boxes:
        rounded_rect(draw, (x1, y1, x2, y2), COLORS["panel"], COLORS["line"], 2)
        draw.text((x1 + 34, y1 + 58), title, fill=COLORS["ink"], font=font(34, bold=True))
        draw.text((x1 + 34, y1 + 130), sub, fill=COLORS["muted"], font=font(30))
    draw.line((568, 472, 724, 472), fill=COLORS["amber"], width=6)
    draw.polygon([(724, 472), (694, 454), (694, 490)], fill=COLORS["amber"])
    draw.line((1192, 472, 1348, 472), fill=COLORS["amber"], width=6)
    draw.polygon([(1348, 472), (1318, 454), (1318, 490)], fill=COLORS["amber"])
    draw_text_block(draw, (122, 692), ["Trigger: untrusted app calls query() on the exported LLM prompt provider."], 42, COLORS["ink"], True, max_width=1650)
    return img


def scene_expected_observed(evidence: dict) -> Image.Image:
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Expected vs observed", "This is the central runtime finding.", COLORS["red"])
    draw = ImageDraw.Draw(img)
    rounded_rect(draw, (110, 166, 900, 842), COLORS["panel"], COLORS["line"], 2)
    rounded_rect(draw, (1020, 166, 1810, 842), COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (160, 220), ["Expected"], 52, COLORS["muted"], True)
    draw_text_block(draw, (160, 330), ["permission_denied=true", "or SecurityException"], 46, COLORS["red"], True, max_width=650)
    draw_text_block(draw, (160, 570), ["Reason:"], 34, COLORS["muted"], True)
    draw_text_block(draw, (160, 630), ["Untrusted apps should not read internal IVI prompt/corpus data."], 34, COLORS["muted"], max_width=650)
    draw_text_block(draw, (1070, 220), ["Observed"], 52, COLORS["amber"], True)
    observed = [
        f"permission_denial={str(evidence['permission_denial']).lower()}",
        f"cursor_null={str(evidence['cursor_null']).lower()}",
        f"rows={evidence['rows']}",
        f"chars={evidence['total_chars']}",
        f"sha256_short={evidence['sha256_short']}",
    ]
    draw_text_block(draw, (1070, 330), observed, 45, COLORS["ink"], True, max_width=650)
    draw_text_block(draw, (1070, 710), ["The provider returned data."], 38, COLORS["green"], True)
    return img


def scene_data_identity(evidence: dict) -> Image.Image:
    semantic = evidence.get("semantic_summary", {})
    scenarios = semantic.get("scenarios", [])
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "What data came out?", "This is the semantic evidence that the returned row is LLM prompt/corpus data.", COLORS["green"])
    draw = ImageDraw.Draw(img)
    rounded_rect(draw, (94, 144, 1826, 880), COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (150, 198), ["Returned payload identity"], 48, COLORS["green"], True)
    draw_text_block(
        draw,
        (150, 286),
        [
            f"JSON top-level keys: {', '.join(semantic.get('top_level_keys', []))}",
            f"Scenario count: {semantic.get('scenario_count', 'unknown')}",
            "Each scenario contains latest prompt material and one past version.",
        ],
        36,
        COLORS["ink"],
        max_width=1520,
    )
    y = 492
    for item in scenarios[:2]:
        rounded_rect(draw, (150, y, 1770, y + 134), COLORS["panel_2"], COLORS["line"], 1)
        draw.text((184, y + 28), item.get("name", "scenario"), fill=COLORS["amber"], font=font(34, bold=True))
        field_text = ", ".join(item.get("latest_fields", []))
        draw.text((560, y + 30), f"fields: {field_text}", fill=COLORS["ink"], font=font(29))
        draw.text((560, y + 78), f"latest_version={item.get('latest_version')} / past_versions={item.get('past_versions')}", fill=COLORS["muted"], font=font(27))
        y += 158
    return img


def scene_sensitivity(evidence: dict) -> Image.Image:
    semantic = evidence.get("semantic_summary", {})
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Why sensitive?", "The sensitivity is internal LLM behavior/config disclosure, not proven real-user PII.", COLORS["amber"])
    draw = ImageDraw.Draw(img)
    left = (100, 170, 900, 850)
    right = (1020, 170, 1820, 850)
    rounded_rect(draw, left, COLORS["panel"], COLORS["line"], 2)
    rounded_rect(draw, right, COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (150, 226), ["What is exposed"], 44, COLORS["amber"], True)
    bullets = [
        "prompt prefix blocks",
        "Jinja2 prompt template",
        "template variables: system_message, message",
        "rendered prompt examples",
        "scenario names and version history",
    ]
    y = 326
    for bullet in bullets:
        draw.text((168, y), "-", fill=COLORS["green"], font=font(34, bold=True))
        draw.text((210, y), bullet, fill=COLORS["ink"], font=font(31))
        y += 64
    draw_text_block(draw, (1070, 226), ["Why it matters"], 44, COLORS["green"], True)
    draw_text_block(
        draw,
        (1070, 326),
        [
            "A same-device app can reverse-engineer the IVI assistant's scenario logic and prompt shape.",
            "That can support prompt-aware manipulation or bypass research.",
            "This demo does not show raw prompt text or a live jailbreak.",
        ],
        32,
        COLORS["ink"],
        max_width=650,
    )
    if semantic.get("field_metrics"):
        draw.text((1070, 716), f"Prompt-like blocks measured: {semantic['field_metrics'].get('prompt_like_block_count')}", fill=COLORS["muted"], font=font(29))
        draw.text((1070, 758), f"Rendered-example chars: {semantic['field_metrics'].get('rendered_example_total_chars')}", fill=COLORS["muted"], font=font(29))
    return img


def scene_artifact(evidence: dict) -> Image.Image:
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Redacted evidence artifact", "The demo shows what the attacker app obtained without revealing raw prompt text.", COLORS["green"])
    draw = ImageDraw.Draw(img)
    rounded_rect(draw, (108, 146, 1812, 886), COLORS["panel_2"], COLORS["line"], 2)
    draw_text_block(draw, (160, 202), ["Collected by attacker app:"], 40, COLORS["muted"], True)
    draw_text_block(draw, (160, 266), [evidence["artifact"]], 54, COLORS["green"], True)
    keys = ", ".join(evidence.get("top_level_keys", []))
    sections = ", ".join(evidence.get("sections_detected", []))
    json_lines = [
        "{",
        '  "source": "LLM prompt provider",',
        f'  "rows": {evidence["rows"]},',
        f'  "total_chars": {evidence["total_chars"]},',
        f'  "sha256_short": "{evidence["sha256_short"]}",',
        '  "raw_text": "[REDACTED]",',
        '  "sensitive_content_redacted": true,',
        '  "data_class": "internal_llm_prompt_corpus",',
        f'  "top_level_keys": "{keys}",',
        f'  "sections_detected": "{sections}"',
        "}",
    ]
    y = 360
    code_font = font(30)
    for line in json_lines:
        draw.text((170, y), line, fill=COLORS["ink"], font=code_font)
        y += 48
    return img


def scene_impact(_: dict) -> Image.Image:
    img = base_frame("lmp-1: LLM Prompt/Corpus Disclosure", "Impact", "The impact is a protected-data read primitive, not vehicle actuation.", COLORS["amber"])
    draw = ImageDraw.Draw(img)
    draw_text_block(draw, (118, 190), ["Impact"], 60, COLORS["amber"], True)
    draw_text_block(
        draw,
        (118, 310),
        [
            "An unprivileged same-device app can read internal IVI LLM prompt/corpus data.",
            "That crosses an IVI app/component boundary that should protect the LLM asset.",
        ],
        48,
        COLORS["ink"],
        True,
        max_width=1600,
    )
    rounded_rect(draw, (118, 680, 1802, 828), COLORS["panel"], COLORS["line"], 2)
    draw_text_block(draw, (164, 718), ["Exact claim: LLM prompt/corpus disclosure primitive is runtime confirmed for lmp-1."], 38, COLORS["green"], True, max_width=1540)
    return img


def scene_appendix(_: dict) -> Image.Image:
    img = base_frame("Additional primitives", "Appendix only", "These do not replace the main lmp-1 impact claim.", COLORS["purple"])
    draw = ImageDraw.Draw(img)
    rows = [
        ("vc-6", "receiver reachability; state pollution only if DB before/after proves mutation"),
        ("am-1", "suggestion provider write accepted; UI poisoning only if marker appears in UI"),
        ("acc-4", "SSO client parameter boundary surface; runtime secret leak unconfirmed"),
        ("static", "credential-shaped APK exposure; live backend abuse untested"),
    ]
    y = 200
    for fid, text in rows:
        rounded_rect(draw, (120, y, 1800, y + 118), COLORS["panel"], COLORS["line"], 1)
        draw.text((166, y + 34), fid, fill=COLORS["purple"], font=font(38, bold=True))
        draw_text_block(draw, (330, y + 34), [text], 32, COLORS["ink"], max_width=1360)
        y += 142
    return img


def scene_not_claimed(evidence: dict) -> Image.Image:
    img = base_frame("Scope control", "Not claimed", "This keeps the demo honest and prevents vehicle-compromise overclaiming.", COLORS["red"])
    draw = ImageDraw.Draw(img)
    draw_text_block(draw, (118, 170), ["Not demonstrated"], 58, COLORS["red"], True)
    claims = [
        "No remote vehicle compromise",
        "No vehicle takeover",
        "No vehicle actuation",
        "No safety-critical control",
        "No jailbreak demonstrated",
        "No live backend abuse",
        "No raw prompt or secret disclosure in the video",
    ]
    y = 294
    for claim in claims:
        draw.text((150, y), "X", fill=COLORS["red"], font=font(38, bold=True))
        draw.text((210, y), claim, fill=COLORS["ink"], font=font(38))
        y += 74
    return img


SCENES = [
    ("threat", 16, scene_threat),
    ("boundary", 14, scene_boundary),
    ("identity", 18, scene_identity),
    ("asset", 18, scene_asset),
    ("trigger", 18, scene_trigger),
    ("expected_observed", 30, scene_expected_observed),
    ("data_identity", 30, scene_data_identity),
    ("sensitivity", 34, scene_sensitivity),
    ("artifact", 34, scene_artifact),
    ("impact", 24, scene_impact),
    ("appendix", 18, scene_appendix),
    ("not_claimed", 28, scene_not_claimed),
]


def parse_preview_hash(trace_path: Path) -> str | None:
    if not trace_path.exists():
        return None
    text = trace_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"preview_hash=([a-f0-9]{16})", text)
    return match.group(1) if match else None


def load_evidence(output_dir: Path) -> dict:
    artifact = output_dir / "redacted_evidence_bundle" / "prompt_corpus_bundle.redacted.json"
    data = json.loads(artifact.read_text(encoding="utf-8-sig"))
    preview_hash = parse_preview_hash(output_dir / "record_llm_boundary_trace.txt")
    if preview_hash:
        data["preview_hash"] = preview_hash
    semantic = build_semantic_summary()
    if semantic:
        data["semantic_summary"] = semantic
        out = output_dir / "redacted_evidence_bundle" / "prompt_corpus_semantic_summary.redacted.json"
        out.write_text(json.dumps(semantic, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def summarize_block(value: str) -> dict:
    variables = sorted(set(re.findall(r"\{\{\s*([a-zA-Z0-9_.-]+)", value or "")))
    tags = sorted(set(re.findall(r"\{%\s*([a-zA-Z_]+)", value or "")))
    return {
        "chars": len(value or ""),
        "sha8": hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:8],
        "template_variables": variables,
        "template_tags": tags,
        "raw_text": "[REDACTED]",
    }


def build_semantic_summary() -> dict:
    if not SOURCE_PROMPTS.exists():
        return {}
    raw = SOURCE_PROMPTS.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    scenarios = []
    rendered_chars = 0
    prompt_like_blocks = 0
    for scenario in parsed.get("scenarios", []):
        latest = scenario.get("latest", {})
        blocks = {}
        for field in ["description", "prefix", "jinja2_template", "rendered_example"]:
            blocks[field] = summarize_block(str(latest.get(field, "") or ""))
        rendered_chars += blocks["rendered_example"]["chars"]
        prompt_like_blocks += sum(1 for field in ["prefix", "jinja2_template", "rendered_example"] if blocks[field]["chars"] > 0)
        scenarios.append(
            {
                "name": scenario.get("name"),
                "latest_version": latest.get("version"),
                "latest_timestamp": latest.get("timestamp"),
                "latest_fields": list(latest.keys()),
                "past_versions": len(scenario.get("past_version", [])),
                "field_summaries": blocks,
            }
        )
    return {
        "data_class": "internal_llm_prompt_corpus",
        "raw_text": "[REDACTED]",
        "source_file": "assets/prompts.json",
        "total_chars": len(raw),
        "source_file_sha256_short": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],
        "top_level_keys": list(parsed.keys()),
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "field_metrics": {
            "prompt_like_block_count": prompt_like_blocks,
            "rendered_example_total_chars": rendered_chars,
        },
        "sensitivity_reason": [
            "internal prompt prefix blocks",
            "prompt template variables",
            "rendered LLM examples",
            "scenario and version metadata",
            "assistant behavior/config disclosure",
        ],
        "not_claimed": [
            "not proof of real-user PII disclosure",
            "not a live jailbreak demonstration",
            "not a remote vehicle compromise",
        ],
    }


def write_storyboard(output_dir: Path, evidence: dict, video_name: str) -> None:
    lines = [
        "# LLM Boundary Presentation Cut",
        "",
        f"- Video: `{video_name}`",
        f"- Source artifact: `redacted_evidence_bundle/{evidence['artifact']}`",
        "- Semantic summary: `redacted_evidence_bundle/prompt_corpus_semantic_summary.redacted.json`",
        f"- Runtime evidence: `permission_denial={str(evidence['permission_denial']).lower()}`, `rows={evidence['rows']}`, `chars={evidence['total_chars']}`, `sha256_short={evidence['sha256_short']}`",
        "- Returned-data identity shown: `metadata`, `scenarios`, `phone_call_scenario`, `text_message_scenario`, `prefix`, `jinja2_template`, `rendered_example`.",
        "- Raw prompt/corpus text is not displayed.",
        "",
        "| Time | Scene | Evidence / Claim |",
        "|---:|---|---|",
    ]
    t = 0
    for name, duration, _ in SCENES:
        lines.append(f"| {t:02d}s | {name} | lmp-1 boundary-bypass story card |")
        t += duration
    lines.extend(
        [
            "",
            "## Exact Main Claim",
            "",
            "Under a same-device untrusted app threat model, lmp-1 confirms that the PoC app can query the exported IVI LLM prompt/corpus provider and receive data where access should be denied.",
            "",
            "## Not Claimed",
            "",
            "- No remote vehicle compromise",
            "- No vehicle takeover",
            "- No vehicle actuation",
            "- No safety-critical control",
            "- No jailbreak demonstrated",
            "- No live backend abuse",
            "- No raw prompt or secret disclosure in the video",
        ]
    )
    (output_dir / "presentation_cut_README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_video(output_dir: Path, fps: int) -> Path:
    evidence = load_evidence(output_dir)
    video_path = output_dir / "llm_prompt_boundary_presentation_cut.mp4"
    writer = imageio.get_writer(
        str(video_path),
        fps=fps,
        codec="libx264",
        quality=8,
        macro_block_size=1,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    try:
        for _name, duration, maker in SCENES:
            frame = np.asarray(maker(evidence))
            for _ in range(duration * fps):
                writer.append_data(frame)
    finally:
        writer.close()
    write_storyboard(output_dir, evidence, video_path.name)
    return video_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--fps", type=int, default=8)
    args = parser.parse_args()
    video = build_video(args.output_dir, args.fps)
    print(f"PRESENTATION_CUT={video}")


if __name__ == "__main__":
    main()
