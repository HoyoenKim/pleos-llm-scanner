#!/usr/bin/env python
"""Summarize rabin2 metadata/imports for extracted native deep-dive targets.

Input:
  data/native_deep_dive/manifest.json

Outputs:
  data/reports/native_rabin2_summary.json
  data/reports/native_rabin2_summary.md
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


ROOT = Path(__file__).resolve().parent.parent
RABIN2 = ROOT / "tools" / "r2" / "radare2-6.1.4-w64" / "bin" / "rabin2.exe"
MANIFEST = ROOT / "data" / "native_deep_dive" / "manifest.json"
REPORTS = ROOT / "data" / "reports"
OUT_JSON = REPORTS / "native_rabin2_summary.json"
OUT_MD = REPORTS / "native_rabin2_summary.md"
KST = timezone(timedelta(hours=9))

IMPORT_GROUPS = {
    "network": {"connect", "send", "sendto", "recv", "recvfrom", "socket", "getaddrinfo", "getnameinfo", "res_search"},
    "dynamic_loading": {"dlopen", "dlsym", "dlclose"},
    "android_log": {"__android_log_print", "__android_log_write", "__android_log_vprint"},
    "exec": {"system", "execve", "popen"},
    "file_io": {"open", "openat", "read", "write", "fopen", "fread", "fwrite"},
    "memory_protection": {"mprotect", "mmap", "munmap"},
    "privilege": {"setuid", "seteuid", "setgid", "setegid", "setresuid", "setresgid"},
    "crypto_tls": {"SSL_write", "SSL_read", "SSL_connect", "EVP_EncryptInit_ex", "EVP_DecryptInit_ex"},
}


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_json_stdout(text: str) -> Any:
    text = text.strip()
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return {"_parse_error": text[:400]}
    return json.loads(text[start:end + 1])


def run_rabin2_json(flag: str, rel_path: str) -> tuple[Any, str]:
    proc = subprocess.run(
        [str(RABIN2.relative_to(ROOT)), flag, rel_path],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return {"_error": proc.stderr.strip() or proc.stdout.strip(), "_returncode": proc.returncode}, proc.stderr
    return parse_json_stdout(proc.stdout), proc.stderr


def classify_imports(imports: list[dict[str, Any]]) -> dict[str, Any]:
    names = [row.get("name", "") for row in imports]
    name_set = set(names)
    groups: dict[str, list[str]] = {}
    for group, needles in IMPORT_GROUPS.items():
        hits = sorted(name for name in name_set if name in needles)
        if hits:
            groups[group] = hits
    return {
        "n_imports": len(names),
        "groups": groups,
        "interesting_imports": sorted({name for hits in groups.values() for name in hits}),
    }


def analyze_target(target: dict[str, Any]) -> dict[str, Any]:
    rel = target["extracted_path"].replace("\\", "/")
    info_json, info_err = run_rabin2_json("-Ij", rel)
    imports_json, imports_err = run_rabin2_json("-ij", rel)
    info = info_json.get("info", {}) if isinstance(info_json, dict) else {}
    imports = imports_json.get("imports", []) if isinstance(imports_json, dict) else []
    classified = classify_imports(imports)
    return {
        **target,
        "rabin2": {
            "info": info,
            "n_imports": classified["n_imports"],
            "import_groups": classified["groups"],
            "interesting_imports": classified["interesting_imports"],
            "stderr": "\n".join(x for x in [info_err.strip(), imports_err.strip()] if x),
        },
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Native rabin2 Summary")
    lines.append("")
    lines.append(f"- Generated: {payload['generated_at']}")
    lines.append(f"- Targets: {payload['summary']['targets']}")
    lines.append(f"- Targets with network imports: {payload['summary']['with_network_imports']}")
    lines.append(f"- Targets with dynamic loading imports: {payload['summary']['with_dynamic_loading']}")
    lines.append(f"- Targets with exec imports: {payload['summary']['with_exec_imports']}")
    lines.append("")
    lines.append("## Target Table")
    lines.append("")
    lines.append("| Rank | APK | Library | ABI | Lang | NX | RELRO | Canary | Stripped | Interesting imports | Initial interpretation |")
    lines.append("|---:|---|---|---|---|---|---|---|---|---|---|")
    for row in payload["targets"]:
        info = row["rabin2"]["info"]
        groups = row["rabin2"]["import_groups"]
        imports = ", ".join(f"{k}:{len(v)}" for k, v in groups.items()) or "-"
        interp = interpret(row)
        lines.append(
            f"| {row['rank']} | `{row['apk']}` | `{row['lib_name']}` | {row['abi']} | "
            f"{info.get('lang', '?')} | {info.get('nx', '?')} | {info.get('relro', '?')} | "
            f"{info.get('canary', '?')} | {info.get('stripped', '?')} | {imports} | {interp} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `rabin2` is not a vulnerability oracle. It only shows ELF metadata and dynamic imports.")
    lines.append("- Go binaries often show network-related imports such as `getaddrinfo`/`res_search` because the Go runtime and net package are linked in.")
    lines.append("- Next evidence step is xref/runtime: confirm whether imports are reached by product paths and what data crosses Java/JNI boundaries.")
    lines.append("")
    return "\n".join(lines)


def interpret(row: dict[str, Any]) -> str:
    groups = row["rabin2"]["import_groups"]
    lib = row["lib_name"].lower()
    notes: list[str] = []
    if "exec" in groups:
        notes.append("check command execution path")
    if "network" in groups:
        notes.append("network-capable; needs endpoint/payload xref")
    if "dynamic_loading" in groups:
        notes.append("loads symbols dynamically")
    if "android_log" in groups:
        notes.append("log emission possible")
    if "gojni" in lib:
        notes.append("Go/JNI bridge candidate")
    if "airspeech" in lib or "tensorflow" in lib or "onnx" in lib:
        notes.append("ML/audio native path")
    if not notes:
        notes.append("low-signal import surface")
    return "; ".join(notes)


def main() -> int:
    if not RABIN2.is_file():
        raise SystemExit(f"missing rabin2: {RABIN2}")
    if not MANIFEST.is_file():
        raise SystemExit(f"missing manifest: {MANIFEST}")
    manifest = read_json(MANIFEST)
    targets = [analyze_target(row) for row in manifest.get("targets", [])]
    group_counts = Counter()
    for row in targets:
        for group in row["rabin2"]["import_groups"]:
            group_counts[group] += 1
    payload = {
        "generated_at": now_kst(),
        "tool": str(RABIN2.relative_to(ROOT)),
        "summary": {
            "targets": len(targets),
            "with_network_imports": group_counts.get("network", 0),
            "with_dynamic_loading": group_counts.get("dynamic_loading", 0),
            "with_exec_imports": group_counts.get("exec", 0),
            "with_android_log": group_counts.get("android_log", 0),
        },
        "targets": targets,
    }
    write_json(OUT_JSON, payload)
    OUT_MD.write_text(build_markdown(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
