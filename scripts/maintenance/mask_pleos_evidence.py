"""Mask PleOS proprietary code evidence from per-APK reports + stage3_ensemble.

Inputs (raw, gitignored):
  data/reports/per_apk_local/{ai.umos.vehiclecontrol, ai.pleos.sync.syslog,
                ai.pleos.llm.model.provider}_*.json + .md
  data/reports/local/stage3_ensemble.{json,md}

Outputs (masked, public — committed):
  data/reports/public/*.json + .md

Masking rules:
  JSON: results[*].findings[*].evidence -> "<redacted: PleOS proprietary code>"
        per_perspective[*].evidence (if any) -> same
        Stage3 ensemble: only PleOS-prefixed finding ids (vc-, ssl-, lmp-).
        MASTG ids (ucl1-, ucl3-) are public corpus -> unchanged.
  MD:   Fenced code blocks (```java/```kotlin/```) replaced with a single
        redacted comment line. Inline code (`x.y()`) untouched (it's narrative).

Other fields (class FQCN, line, category, severity, rationale, AAOS mapping,
verified_by, missing_control, attack_chain, vehicle_asset, stride, tara_impact)
are KEPT — they describe the finding shape, not the proprietary source.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "reports" / "per_apk_local"
STAGE3_SRC = ROOT / "data" / "reports" / "local"
DST = ROOT / "data" / "reports" / "public"

PLEOS_PER_APK = [
    "ai.umos.vehiclecontrol",
    "ai.pleos.sync.syslog",
    "ai.pleos.llm.model.provider",
]

REDACT_TEXT = "<redacted: PleOS proprietary code>"
REDACT_BLOCK = "// <redacted: PleOS proprietary code>"

PLEOS_FINDING_PREFIX = ("vc-", "ssl-", "lmp-")  # MASTG (ucl1-, ucl3-) is public


def is_pleos_finding(fid: str) -> bool:
    return fid.startswith(PLEOS_FINDING_PREFIX)


def mask_json_per_apk(path: Path, out_path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for cls in data.get("results", []):
        for f in cls.get("findings", []):
            if "evidence" in f and f["evidence"]:
                f["evidence"] = REDACT_TEXT
    data["_redaction_note"] = (
        "evidence fields masked — PleOS proprietary code excerpts replaced. "
        "All other metadata (class FQCN, line, category, severity, rationale, "
        "mappings) kept verbatim. Original raw report retained locally only."
    )
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def mask_json_stage3(path: Path, out_path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for f in data.get("results", []):
        if not is_pleos_finding(f.get("id", "")):
            continue
        if "evidence" in f and f["evidence"]:
            f["evidence"] = REDACT_TEXT
        for pname, pdata in (f.get("per_perspective") or {}).items():
            if isinstance(pdata, dict) and "evidence" in pdata and pdata["evidence"]:
                pdata["evidence"] = REDACT_TEXT
    data["_redaction_note"] = (
        "PleOS finding evidence (vc-/ssl-/lmp-) masked. MASTG findings (ucl1-/ucl3-) "
        "are public corpus — kept verbatim."
    )
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+\-]*)\n(.*?)\n```", re.DOTALL)


def mask_md(path: Path, out_path: Path, banner: str) -> None:
    text = path.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        lang = m.group(1) or ""
        return f"```{lang}\n{REDACT_BLOCK}\n```"

    masked = _FENCE_RE.sub(repl, text)
    out_path.write_text(banner + "\n\n" + masked, encoding="utf-8")


def find_raw_report(stem: str, suffix: str) -> Path | None:
    exact = SRC / f"{stem}{suffix}"
    if exact.exists():
        return exact
    candidates = sorted(SRC.glob(f"{stem}_*{suffix}"))
    return candidates[-1] if candidates else None


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)

    banner_per_apk = (
        "> **Public masked copy** — code evidence (fenced blocks) replaced with "
        "redaction markers under contractor IP protection. Class names, line numbers, "
        "categories, severities, rationale, and AAOS / MASVS mappings are kept verbatim. "
        "Original raw report is retained locally only.\n"
        ">\n"
        "> 본 파일은 contractor IP 보호 정책에 따라 코드 인용을 redact 한 공개용 사본이다. "
        "분석 메타데이터 (class, line, category, severity, rationale, AAOS 매핑) 는 그대로 유지."
    )
    for public_stem in PLEOS_PER_APK:
        src_json = find_raw_report(public_stem, ".json")
        src_md = find_raw_report(public_stem, ".md")
        if src_json:
            mask_json_per_apk(src_json, DST / f"{public_stem}.json")
            print(f"masked: {src_json.name} -> public/")
        if src_md:
            mask_md(src_md, DST / f"{public_stem}.md", banner_per_apk)
            print(f"masked: {src_md.name} -> public/")

    s3_json = STAGE3_SRC / "stage3_ensemble.json"
    s3_md = STAGE3_SRC / "stage3_ensemble.md"
    banner_s3 = (
        "> **Public masked copy** — only PleOS-prefixed findings (vc-/ssl-/lmp-) had their "
        "evidence redacted. MASTG findings (ucl1-/ucl3-) are public corpus and kept verbatim. "
        "Per-perspective rationales / attack chains / missing controls / vehicle assets are kept.\n"
        ">\n"
        "> 본 파일은 PleOS 코드 인용만 redact 한 공개용 사본. MASTG 외부 corpus는 그대로 유지."
    )
    if s3_json.exists():
        mask_json_stage3(s3_json, DST / "stage3_ensemble.json")
        print(f"masked: {s3_json.name} -> public/")
    if s3_md.exists():
        mask_md(s3_md, DST / "stage3_ensemble.md", banner_s3)
        print(f"masked: {s3_md.name} -> public/")

    # Index
    idx = [
        "# data/reports/public/ — Masked public copies",
        "",
        "본 디렉토리는 PleOS 자체 APK 의 per-APK 보고서 + Stage 3 ensemble 결과의 **마스킹 공개판**이다.",
        "코드 인용 (evidence / fenced code block) 만 `<redacted: PleOS proprietary code>` 로 대체했고,",
        "분석 메타데이터 (class FQCN, line, category, severity, rationale, AAOS / MASVS 매핑, attack chain,",
        "missing control, vehicle asset, STRIDE, TARA impact 등) 는 그대로 유지된다.",
        "",
        "- Original raw 보고서는 contractor IP 보호 정책에 따라 작성자 로컬에만 보관 (`data/reports/*.{json,md}`, gitignored).",
        "- 본 public 사본은 `scripts/maintenance/mask_pleos_evidence.py` 로 결정론적 생성. 재실행 시 동일 결과.",
        "- MASTG 외부 corpus 부분 (UnCrackable-Level1/3, r2pay) 은 공개 corpus 라 redact 없이 그대로 (Stage 3 ensemble 안 ucl1- / ucl3- 항목).",
        "",
        "## 파일",
        "",
    ]
    for public_stem in PLEOS_PER_APK:
        idx.append(f"- [`{public_stem}.md`]({public_stem}.md) + [`.json`]({public_stem}.json)")
    idx.append("- [`stage3_ensemble.md`](stage3_ensemble.md) + [`.json`](stage3_ensemble.json)")
    idx.append("")
    idx.append("## 재현")
    idx.append("")
    idx.append("```bash")
    idx.append("python scripts/maintenance/mask_pleos_evidence.py")
    idx.append("```")
    idx.append("")
    (DST / "README.md").write_text("\n".join(idx), encoding="utf-8")
    print(f"wrote: {DST / 'README.md'}")


if __name__ == "__main__":
    main()
