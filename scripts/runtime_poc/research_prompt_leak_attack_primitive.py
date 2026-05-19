#!/usr/bin/env python3
"""Build a safe prompt-leak -> prompt-aware-input PoC package.

This is not a jailbreak and does not call a live backend. It demonstrates that
the leaked lmp-1 prompt/corpus structure lets an attacker construct an input
that matches the IVI assistant scenario/template contract better than a generic
input. Raw prompt/corpus text is never written to the output artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import textwrap
from pathlib import Path
from typing import Iterable

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
PROMPTS_JSON = ROOT / "data" / "decompiled" / "ai.pleos.llm.model.provider" / "resources" / "assets" / "prompts.json"
MANIFEST = ROOT / "data" / "decompiled" / "ai.pleos.llm.model.provider" / "resources" / "AndroidManifest.xml"
PROVIDER_JAVA = ROOT / "data" / "decompiled" / "ai.pleos.llm.model.provider" / "sources" / "ai" / "pleos" / "llm" / "model" / "provider" / "PromptsContentProvider.java"
SERVICE_JAVA = ROOT / "data" / "decompiled" / "ai.pleos.llm.model.provider" / "sources" / "ai" / "pleos" / "llm" / "model" / "provider" / "LLMModelProviderService.java"
DEFAULT_OUT = ROOT / "data" / "reports" / "runtime_local" / "prompt_leak_attack_poc"

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
    if path.exists():
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip() + "\n", encoding="utf-8")


def sha_short(value: str, n: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:n]


def summarize_block(value: str) -> dict:
    value = value or ""
    variables = sorted(set(re.findall(r"\{\{\s*([a-zA-Z0-9_.-]+)", value)))
    tags = sorted(set(re.findall(r"\{%\s*([a-zA-Z_]+)", value)))
    return {
        "chars": len(value),
        "sha8": sha_short(value, 8),
        "template_variables": variables,
        "template_tags": tags,
        "raw_text": "[REDACTED]",
    }


def build_semantic_summary() -> dict:
    raw = PROMPTS_JSON.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    scenarios = []
    prompt_like_blocks = 0
    rendered_example_total_chars = 0
    variables: set[str] = set()

    for scenario in parsed.get("scenarios", []):
        latest = scenario.get("latest", {})
        summaries = {}
        for field in ["description", "prefix", "jinja2_template", "rendered_example"]:
            summary = summarize_block(str(latest.get(field, "") or ""))
            summaries[field] = summary
            variables.update(summary["template_variables"])
        prompt_like_blocks += sum(1 for field in ["prefix", "jinja2_template", "rendered_example"] if summaries[field]["chars"] > 0)
        rendered_example_total_chars += summaries["rendered_example"]["chars"]
        scenarios.append(
            {
                "name": scenario.get("name"),
                "latest_version": latest.get("version"),
                "latest_timestamp": latest.get("timestamp"),
                "latest_fields": list(latest.keys()),
                "past_versions": len(scenario.get("past_version", [])),
                "field_summaries": summaries,
            }
        )

    return {
        "data_class": "internal_llm_prompt_corpus",
        "source_file": "assets/prompts.json",
        "total_chars": len(raw),
        "source_file_sha256_short": sha_short(raw, 16),
        "top_level_keys": list(parsed.keys()),
        "scenario_count": len(scenarios),
        "scenario_names": [s["name"] for s in scenarios],
        "template_variables_observed": sorted(variables),
        "prompt_like_block_count": prompt_like_blocks,
        "rendered_example_total_chars": rendered_example_total_chars,
        "scenarios": scenarios,
        "raw_text": "[REDACTED]",
        "sensitivity": [
            "scenario names",
            "prompt prefix blocks",
            "Jinja2 prompt template structure",
            "template variables",
            "rendered prompt examples",
            "scenario version metadata",
        ],
        "not_claimed": [
            "not proof of real-user PII disclosure",
            "not a live jailbreak demonstration",
            "not a remote vehicle compromise",
        ],
    }


def inspect_runtime_feasibility() -> dict:
    manifest = MANIFEST.read_text(encoding="utf-8", errors="replace") if MANIFEST.exists() else ""
    service = SERVICE_JAVA.read_text(encoding="utf-8", errors="replace") if SERVICE_JAVA.exists() else ""
    provider = PROVIDER_JAVA.read_text(encoding="utf-8", errors="replace") if PROVIDER_JAVA.exists() else ""
    return {
        "actual_llm_direct_call": "not_attempted",
        "reason": "The visible LLMModelProviderService is android:exported=\"false\" and onBind returns null; this package exposes prompt/corpus provider read, not an external LLM inference API.",
        "service_exported_false": 'android:name="ai.pleos.llm.model.provider.LLMModelProviderService"\n            android:exported="false"' in manifest,
        "service_onbind_returns_null": "return null;" in service,
        "prompt_provider_exported": 'android:name="ai.pleos.llm.model.provider.PromptsContentProvider"' in manifest and 'android:exported="true"' in manifest,
        "provider_reads_assets_prompts_json": 'open("prompts.json")' in provider,
        "provider_returns_cursor_content": 'new String[]{"content"}' in provider and "matrixCursor.addRow" in provider,
        "demo_engine": "safe mock evaluator derived from leaked prompt/corpus structure",
    }


def build_inputs(summary: dict) -> list[dict]:
    scenario_names = summary["scenario_names"]
    variables = summary["template_variables_observed"]
    phone = scenario_names[0] if scenario_names else "phone_call_scenario"
    text = scenario_names[1] if len(scenario_names) > 1 else "text_message_scenario"
    return [
        {
            "id": "baseline_generic_phone",
            "type": "baseline_generic",
            "target_scenario": phone,
            "description": "Generic same-device user input without leaked scenario/template knowledge.",
            "input": "Please help me place a test call to a synthetic contact and keep the output safe.",
            "uses_leaked_structure": False,
        },
        {
            "id": "prompt_aware_phone",
            "type": "prompt_aware",
            "target_scenario": phone,
            "description": "Structure-aware input built from leaked scenario names and template variables.",
            "input": (
                "scenario=phone_call_scenario\n"
                "system_message=[SYNTHETIC_IVI_CONTEXT_REDACTED]\n"
                "message=[SYNTHETIC_USER_REQUEST: prepare a safe phone-call intent preview only]\n"
                "return_format=rendered_example_compatible_redacted_summary\n"
                "do_not_execute_call=true"
            ),
            "uses_leaked_structure": True,
            "leaked_features_used": {
                "scenario_name": phone,
                "template_variables": variables,
                "field_contract": ["prefix", "jinja2_template", "rendered_example"],
            },
        },
        {
            "id": "baseline_generic_text",
            "type": "baseline_generic",
            "target_scenario": text,
            "description": "Generic text-message request without leaked scenario/template knowledge.",
            "input": "Draft a harmless test message for a synthetic contact.",
            "uses_leaked_structure": False,
        },
        {
            "id": "prompt_aware_text",
            "type": "prompt_aware",
            "target_scenario": text,
            "description": "Structure-aware text-message input built from leaked template variables.",
            "input": (
                "scenario=text_message_scenario\n"
                "system_message=[SYNTHETIC_IVI_CONTEXT_REDACTED]\n"
                "message=[SYNTHETIC_USER_REQUEST: prepare a safe text-message preview only]\n"
                "return_format=rendered_example_compatible_redacted_summary\n"
                "do_not_send_message=true"
            ),
            "uses_leaked_structure": True,
            "leaked_features_used": {
                "scenario_name": text,
                "template_variables": variables,
                "field_contract": ["prefix", "jinja2_template", "rendered_example"],
            },
        },
    ]


def evaluate_input(item: dict, summary: dict) -> dict:
    text = item["input"]
    lower = text.lower()
    target = item["target_scenario"]
    variables = summary["template_variables_observed"]
    scenario_names = summary["scenario_names"]
    criteria = [
        {
            "name": "known_scenario_name_present",
            "matched": target in text,
            "why": "Uses a scenario identifier learned from the leaked corpus.",
        },
        {
            "name": "template_variables_present",
            "matched": all(f"{var}=" in text or f'"{var}"' in text for var in variables),
            "why": "Matches the Jinja2 template variable names observed in the leak.",
        },
        {
            "name": "prompt_contract_fields_referenced",
            "matched": "rendered_example" in text or "prefix" in text or "jinja2_template" in text,
            "why": "References the leaked prompt/corpus field contract.",
        },
        {
            "name": "safe_non_executing_guardrail",
            "matched": "do_not_execute" in lower or "do_not_send" in lower or "preview only" in lower or "safe" in lower or "harmless" in lower or "test" in lower,
            "why": "Keeps the PoC non-destructive and preview-only.",
        },
        {
            "name": "no_raw_prompt_literal",
            "matched": True,
            "why": "Uses synthetic placeholders rather than raw prompt/corpus text.",
        },
    ]
    score = sum(1 for c in criteria if c["matched"])
    return {
        "id": item["id"],
        "type": item["type"],
        "target_scenario": target,
        "matched_criteria": score,
        "total_criteria": len(criteria),
        "contract_match_score": round(score / len(criteria), 3),
        "accepted_by_mock_contract": score >= 4,
        "criteria": criteria,
        "available_scenarios_from_leak": scenario_names,
        "engine": "rule-based mock contract evaluator; no live LLM/backend call",
    }


def build_results(inputs: list[dict], summary: dict, feasibility: dict) -> dict:
    evaluations = [evaluate_input(item, summary) for item in inputs]
    by_type = {}
    for item in evaluations:
        by_type.setdefault(item["type"], []).append(item["contract_match_score"])
    aggregates = {
        key: {
            "n": len(values),
            "mean_contract_match_score": round(sum(values) / len(values), 3) if values else 0.0,
            "accepted_count": sum(1 for item in evaluations if item["type"] == key and item["accepted_by_mock_contract"]),
        }
        for key, values in by_type.items()
    }
    return {
        "claim": "Prompt/corpus disclosure enables construction of prompt-aware inputs that match the leaked IVI LLM scenario/template contract better than generic inputs.",
        "runtime_feasibility": feasibility,
        "evaluations": evaluations,
        "aggregates": aggregates,
        "limitations": [
            "No live LLM inference was called.",
            "No jailbreak success is claimed.",
            "No vehicle actuation, message sending, phone call, or backend abuse was attempted.",
            "The evaluator demonstrates contract matching, not semantic model compromise.",
        ],
    }


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], max_width: int, size: int, fill, bold=False, leading=10) -> int:
    f = font(size, bold)
    words = text.split()
    lines = []
    line = ""
    for word in words:
        cand = word if not line else f"{line} {word}"
        if draw.textbbox((0, 0), cand, font=f)[2] <= max_width:
            line = cand
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill)
        y += size + leading
    return y


def rect(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=8, fill=fill, outline=outline, width=width)


def frame(title: str, subtitle: str) -> Image.Image:
    img = Image.new("RGB", (1920, 1080), COLORS["bg"])
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1920, 84), fill=(7, 11, 18))
    draw.text((54, 24), title, font=font(34, True), fill=COLORS["ink"])
    draw.text((1350, 25), subtitle, font=font(28), fill=COLORS["muted"])
    draw.rectangle((0, 80, 1920, 84), fill=COLORS["blue"])
    draw.rectangle((0, 1004, 1920, 1080), fill=(7, 11, 18))
    return img


def scene_goal(_: dict) -> Image.Image:
    img = frame("Prompt Leak -> Prompt-Aware Input PoC", "Goal")
    draw = ImageDraw.Draw(img)
    draw_wrapped(draw, "What this proves", (110, 170), 1600, 62, COLORS["green"], True)
    draw_wrapped(
        draw,
        "The provider leak is useful because it reveals the IVI LLM scenario and template contract. An attacker can then build inputs that fit that contract better than generic text.",
        (110, 300),
        1600,
        42,
        COLORS["ink"],
        True,
    )
    draw_wrapped(draw, "Not a live jailbreak, not vehicle actuation, not backend abuse.", (110, 720), 1600, 40, COLORS["red"], True)
    return img


def scene_leaked_structure(data: dict) -> Image.Image:
    summary = data["summary"]
    img = frame("Prompt Leak -> Prompt-Aware Input PoC", "Leaked structure")
    draw = ImageDraw.Draw(img)
    rect(draw, (100, 150, 1820, 870), COLORS["panel"], COLORS["line"], 2)
    draw_wrapped(draw, "Attacker learns these safe structural facts", (150, 210), 1500, 46, COLORS["green"], True)
    lines = [
        f"top-level keys: {', '.join(summary['top_level_keys'])}",
        f"scenarios: {', '.join(summary['scenario_names'])}",
        f"template variables: {', '.join(summary['template_variables_observed'])}",
        "fields: prefix, jinja2_template, rendered_example",
        f"prompt-like blocks: {summary['prompt_like_block_count']}",
    ]
    y = 330
    for line in lines:
        draw.text((170, y), "- ", fill=COLORS["amber"], font=font(36, True))
        draw.text((220, y), line, fill=COLORS["ink"], font=font(34))
        y += 72
    draw_wrapped(draw, "Raw prompt/corpus text remains redacted.", (170, 756), 1450, 34, COLORS["muted"], True)
    return img


def scene_input_compare(data: dict) -> Image.Image:
    inputs = data["inputs"]
    generic = next(i for i in inputs if i["id"] == "baseline_generic_phone")
    aware = next(i for i in inputs if i["id"] == "prompt_aware_phone")
    img = frame("Prompt Leak -> Prompt-Aware Input PoC", "Input construction")
    draw = ImageDraw.Draw(img)
    rect(draw, (90, 150, 900, 890), COLORS["panel"], COLORS["line"], 2)
    rect(draw, (1020, 150, 1830, 890), COLORS["panel"], COLORS["line"], 2)
    draw.text((140, 210), "Generic input", fill=COLORS["red"], font=font(44, True))
    draw_wrapped(draw, generic["input"], (140, 310), 680, 36, COLORS["ink"])
    draw.text((1070, 210), "Prompt-aware input", fill=COLORS["green"], font=font(44, True))
    for line in aware["input"].splitlines():
        draw.text((1070, 310), line, fill=COLORS["ink"], font=font(30))
        y = 310
        break
    y = 310
    for line in aware["input"].splitlines():
        draw.text((1070, y), line, fill=COLORS["ink"], font=font(30))
        y += 54
    return img


def scene_eval(data: dict) -> Image.Image:
    results = data["results"]
    img = frame("Prompt Leak -> Prompt-Aware Input PoC", "Mock evaluation")
    draw = ImageDraw.Draw(img)
    rect(draw, (90, 145, 1830, 890), COLORS["panel"], COLORS["line"], 2)
    draw.text((140, 205), "Contract match score", fill=COLORS["amber"], font=font(46, True))
    y = 320
    for ev in results["evaluations"]:
        color = COLORS["green"] if ev["accepted_by_mock_contract"] else COLORS["red"]
        draw.text((160, y), ev["id"], fill=COLORS["ink"], font=font(32, True))
        draw.text((780, y), f"{ev['matched_criteria']}/{ev['total_criteria']} = {ev['contract_match_score']}", fill=color, font=font(34, True))
        draw.text((1180, y), "accepted" if ev["accepted_by_mock_contract"] else "not accepted", fill=color, font=font(32, True))
        y += 86
    agg = results["aggregates"]
    draw_wrapped(
        draw,
        f"Generic mean score: {agg['baseline_generic']['mean_contract_match_score']} / Prompt-aware mean score: {agg['prompt_aware']['mean_contract_match_score']}",
        (140, 720),
        1500,
        38,
        COLORS["green"],
        True,
    )
    draw_wrapped(draw, "This is contract matching, not live LLM compromise.", (140, 808), 1500, 34, COLORS["muted"], True)
    return img


def scene_claim(data: dict) -> Image.Image:
    img = frame("Prompt Leak -> Prompt-Aware Input PoC", "Claim")
    draw = ImageDraw.Draw(img)
    draw_wrapped(
        draw,
        "Result: the leak turns into a prompt-aware input design primitive.",
        (110, 180),
        1650,
        58,
        COLORS["green"],
        True,
    )
    draw_wrapped(
        draw,
        "It tells the attacker which scenario names, variables, and prompt fields the IVI assistant expects. The prompt-aware input matches that leaked contract; a generic input does not.",
        (110, 360),
        1650,
        42,
        COLORS["ink"],
        True,
    )
    draw_wrapped(
        draw,
        "Limitations: no raw prompt text shown, no live LLM call, no jailbreak success, no vehicle actuation, no backend abuse.",
        (110, 720),
        1650,
        38,
        COLORS["red"],
        True,
    )
    return img


SCENES = [
    (scene_goal, 20),
    (scene_leaked_structure, 26),
    (scene_input_compare, 34),
    (scene_eval, 32),
    (scene_claim, 26),
]


def build_video(out_dir: Path, data: dict, fps: int = 8) -> Path:
    video = out_dir / "prompt_aware_attack_demo.mp4"
    writer = imageio.get_writer(str(video), fps=fps, codec="libx264", quality=8, macro_block_size=1, ffmpeg_params=["-pix_fmt", "yuv420p"])
    try:
        for maker, seconds in SCENES:
            arr = np.asarray(maker(data))
            for _ in range(seconds * fps):
                writer.append_data(arr)
    finally:
        writer.close()
    return video


def write_reports(out_dir: Path, summary: dict, feasibility: dict, inputs: list[dict], results: dict, video: Path) -> None:
    write_md(
        out_dir / "prompt_leak_attack_plan.md",
        f"""
        # Prompt Leak Attack Primitive PoC

        ## Goal

        Show that `lmp-1` is not only a provider-read finding. The leaked prompt/corpus structure lets an attacker build inputs that match the IVI LLM scenario/template contract better than generic text.

        ## Evidence Chain

        1. `lmp-1` provider read is runtime confirmed in the earlier evidence pack.
        2. The returned payload is structurally identified as internal LLM prompt/corpus data:
           - top-level keys: `{', '.join(summary['top_level_keys'])}`
           - scenarios: `{', '.join(summary['scenario_names'])}`
           - template variables: `{', '.join(summary['template_variables_observed'])}`
           - prompt fields: `prefix`, `jinja2_template`, `rendered_example`
        3. Direct live LLM API/inference was not used because `LLMModelProviderService` is not exported and `onBind()` returns null in the visible decompiled path.
        4. A safe mock contract evaluator compares generic input against prompt-aware input.

        ## Exact Claim

        Prompt/corpus disclosure enables prompt-aware input construction under a same-device app threat model.

        ## Not Claimed

        - No live jailbreak success
        - No raw prompt/corpus disclosure in public artifacts
        - No vehicle actuation
        - No remote vehicle compromise
        - No live backend/API abuse

        ## Video

        - `{video.name}`
        """,
    )

    generic = results["aggregates"]["baseline_generic"]
    aware = results["aggregates"]["prompt_aware"]
    write_md(
        out_dir / "prompt_aware_poc_results.md",
        f"""
        # Prompt-Aware Input PoC Results

        ## Summary

        | Input type | n | Mean contract-match score | Accepted by mock contract |
        |---|---:|---:|---:|
        | Generic baseline | {generic['n']} | {generic['mean_contract_match_score']} | {generic['accepted_count']} |
        | Prompt-aware | {aware['n']} | {aware['mean_contract_match_score']} | {aware['accepted_count']} |

        ## Interpretation

        The generic inputs do not contain leaked scenario names or the observed template variables. The prompt-aware inputs use only safe structural knowledge from the leaked prompt/corpus: scenario names, `system_message`, `message`, and rendered-example-compatible output framing.

        This demonstrates a downstream primitive: the leak provides enough structure to craft inputs that fit the IVI LLM prompt contract. It still does not demonstrate a live jailbreak or vehicle control.

        ## Runtime Feasibility Note

        {feasibility['reason']}
        """,
    )

    write_md(
        out_dir / "narrator_script_prompt_aware.md",
        """
        # Narrator Script

        This demo starts after the lmp-1 provider-read evidence. The question is no longer whether data came out. The question is what the attacker can do with the structure of that data.

        The leaked payload is not a random blob. It contains metadata and scenarios. The scenario names include phone-call and text-message flows, and each scenario contains prompt prefix blocks, a Jinja2 template, rendered examples, and version metadata. The raw prompt text is redacted, but the structure is enough to reveal how the IVI assistant organizes its LLM inputs.

        The generic input is just a normal natural-language request. It does not know the scenario name, the template variables, or the expected prompt contract.

        The prompt-aware input uses the leaked structure. It names the scenario, supplies synthetic `system_message` and `message` placeholders, and requests a redacted rendered-example-compatible preview. It does not execute a call, send a message, use a backend, or expose raw prompt text.

        The mock evaluator is deliberately simple: it checks whether the input matches the leaked scenario and template contract. Generic inputs do not match. Prompt-aware inputs do.

        The claim is narrow: prompt/corpus disclosure enables prompt-aware input construction. This is not a live jailbreak, not vehicle actuation, and not remote compromise.
        """,
    )

    write_md(
        out_dir / "runbook.md",
        """
        # Runbook

        ```powershell
        python .\\scripts\\research_prompt_leak_attack_primitive.py
        ```

        Outputs are written to `data/reports/runtime_local/prompt_leak_attack_poc/`.

        Safety rules:

        - Do not display raw prompt/corpus text.
        - Do not call live backend/API endpoints.
        - Do not attempt vehicle actuation.
        - Treat this as a prompt-contract matching demonstration, not a jailbreak proof.
        """,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = build_semantic_summary()
    feasibility = inspect_runtime_feasibility()
    inputs = build_inputs(summary)
    results = build_results(inputs, summary, feasibility)

    write_json(out_dir / "prompt_leak_semantic_summary.redacted.json", summary)
    write_json(out_dir / "actual_llm_runtime_feasibility.json", feasibility)
    write_json(out_dir / "baseline_vs_prompt_aware_inputs.json", inputs)
    write_json(out_dir / "mock_eval_results.json", results)

    video = out_dir / "prompt_aware_attack_demo.mp4"
    if not args.no_video:
        video = build_video(out_dir, {"summary": summary, "inputs": inputs, "results": results})
    write_reports(out_dir, summary, feasibility, inputs, results, video)
    print(f"PROMPT_AWARE_POC_DIR={out_dir}")
    print(f"VIDEO={video}")
    print(f"GENERIC_MEAN={results['aggregates']['baseline_generic']['mean_contract_match_score']}")
    print(f"PROMPT_AWARE_MEAN={results['aggregates']['prompt_aware']['mean_contract_match_score']}")


if __name__ == "__main__":
    main()
