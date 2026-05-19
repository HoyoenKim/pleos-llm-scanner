#!/usr/bin/env python
"""Plan the next native deep-dive pass.

This script does not decompile native code and does not call any LLM API. It
builds an actionable target list for a deeper native pass by:

1. enumerating .so entries in high-value APKs,
2. deduplicating them by SHA-256,
3. scanning JADX Java output for Java->native boundary hints, and
4. producing a redacted local report with ranked next targets.

Outputs:
  data/reports/native_local/native_deep_dive_targets.json
  data/reports/native_local/native_deep_dive_targets.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


ROOT = Path(__file__).resolve().parents[2]
APKS_DIR = ROOT / "data" / "_local" / "apks"
DECOMPILED_DIR = ROOT / "data" / "_local" / "decompiled"
REPORTS_DIR = ROOT / "data" / "reports"
INVENTORY_JSON = REPORTS_DIR / "aggregate" / "native_lib_inventory.json"
OUT_JSON = REPORTS_DIR / "native_local" / "native_deep_dive_targets.json"
OUT_MD = REPORTS_DIR / "native_local" / "native_deep_dive_targets.md"
EXTRACT_DIR = ROOT / "data" / "_local" / "native_extracts" / "deep_dive" / "libs"
EXTRACT_MANIFEST = ROOT / "data" / "_local" / "native_extracts" / "deep_dive" / "manifest.json"

KST = timezone(timedelta(hours=9))

LOAD_LIBRARY_RE = re.compile(r"System\.loadLibrary\(\s*\"([^\"]+)\"\s*\)")
SYSTEM_LOAD_RE = re.compile(r"System\.load\(")
NATIVE_METHOD_RE = re.compile(
    r"(?P<prefix>(?:public|private|protected)?\s*(?:static\s+)?)"
    r"native\s+(?P<ret>[\w.$<>\[\]?]+)\s+(?P<name>\w+)\s*\((?P<args>[^)]*)\)"
)

ASCII_RE = re.compile(rb"[\x20-\x7e]{6,}")
URL_RE = re.compile(r"^https?://[A-Za-z0-9.\-:/_?=&%#@~+]+$")
SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?i:api[_-]?key|access[_-]?token|client[_-]?secret|bearer)[\s:=]+[A-Za-z0-9_./+=-]{16,})"
)
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
TLS_RE = re.compile(
    r"(?i)(TrustManager|HostnameVerifier|usePlaintext|CertificatePinner|x509|"
    r"tls_no_verify|verify_peer|setHostnameVerifier|insecureChannel|SSL_write|mbedtls)"
)

NOISE_URL_PARTS = (
    "schemas.android.com",
    "schema.org",
    "w3.org",
    "json-schema.org",
    "github.com",
    "go.dev",
    "golang.org",
    "example.com",
    "github.io",
)

SECURITY_APK_KEYWORDS = (
    "caas",
    "maps",
    "navigation",
    "ambient",
    "vehicle",
    "sync",
    "syslog",
    "appmarket",
    "account",
    "driving",
    "call",
    "message",
    "inputmethod",
)

SECURITY_LIB_KEYWORDS = (
    "gojni",
    "mapbox",
    "speech",
    "stt",
    "voice",
    "onnx",
    "crypto",
    "ssl",
    "tls",
    "vehicle",
    "nav",
    "gleo",
    "mqtt",
)

LOW_VALUE_LIB_PATTERNS = (
    "androidx.graphics.path",
)

ABI_PRIORITY = {
    "arm64-v8a": 4,
    "armeabi-v7a": 3,
    "x86_64": 2,
    "x86": 1,
}


@dataclass
class NativeOccurrence:
    apk: str
    origin: str
    abi: str
    entry: str
    lib_name: str
    size_bytes: int
    apk_path: str


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def origin_for(apk: str) -> str:
    if apk.startswith(("ai.umos.", "ai.pleos.")):
        return "PleOS"
    if apk.startswith(("android.", "com.android.", "com.google.")):
        return "AOSP"
    return "third-party"


def apk_name_from_path(path: Path) -> str:
    return path.name.removesuffix(".apk")


def lib_to_load_name(lib_name: str) -> str:
    name = lib_name
    if name.startswith("lib"):
        name = name[3:]
    if name.endswith(".so"):
        name = name[:-3]
    return name


def redact(value: str) -> str:
    value = re.sub(
        r"(https?://http-intake\.logs\.datadoghq\.com/v1/input/)[A-Za-z0-9._-]+",
        r"\1<REDACTED>",
        value,
    )
    value = re.sub(
        r"([?&](?:api[_-]?key|access[_-]?token|client[_-]?secret|token|key|secret)=)[^&#\s]+",
        r"\1<REDACTED>",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"sk-[A-Za-z0-9_-]{6,}", "sk-<REDACTED>", value)
    value = re.sub(r"AKIA[A-Z0-9]{8,}", "AKIA<REDACTED>", value)
    value = UUID_RE.sub("<UUID-REDACTED>", value)
    value = re.sub(
        r"(?i)((?:api[_-]?key|access[_-]?token|client[_-]?secret|bearer)[\s:=]+)[A-Za-z0-9_./+=-]{8,}",
        r"\1<REDACTED>",
        value,
    )
    return value


def clip(value: str, limit: int = 180) -> str:
    value = value.replace("\r", " ").replace("\n", " ").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def inventory_top_apks(top_n: int) -> list[str]:
    if not INVENTORY_JSON.is_file():
        return []
    data = read_json(INVENTORY_JSON)
    rows = data.get("top_native_apks", [])
    return [row["apk"] for row in rows[:top_n] if row.get("apk")]


def choose_apks(top_apks: int, scan_all: bool) -> list[Path]:
    all_apks = {apk_name_from_path(path): path for path in APKS_DIR.glob("*.apk")}
    if scan_all:
        return sorted(all_apks.values(), key=lambda p: p.name)

    wanted = set(inventory_top_apks(top_apks))
    # Keep high-value packages even when they were not in the top inventory list.
    for name in all_apks:
        if any(k in name.lower() for k in SECURITY_APK_KEYWORDS):
            wanted.add(name)
    return [all_apks[name] for name in sorted(wanted) if name in all_apks]


def sha256_zip_entry(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    h = hashlib.sha256()
    with zf.open(info) as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def enumerate_native_libs(apk_paths: list[Path]) -> tuple[dict[str, list[NativeOccurrence]], list[dict[str, Any]]]:
    by_hash: dict[str, list[NativeOccurrence]] = defaultdict(list)
    apk_summary: list[dict[str, Any]] = []
    for apk_path in apk_paths:
        apk = apk_name_from_path(apk_path)
        origin = origin_for(apk)
        so_count = 0
        total_bytes = 0
        errors: list[str] = []
        try:
            with zipfile.ZipFile(apk_path) as zf:
                infos = [
                    info for info in zf.infolist()
                    if info.filename.startswith("lib/") and info.filename.endswith(".so")
                ]
                for info in infos:
                    parts = info.filename.split("/")
                    if len(parts) < 3:
                        continue
                    abi = parts[1]
                    lib_name = parts[-1]
                    digest = sha256_zip_entry(zf, info)
                    occ = NativeOccurrence(
                        apk=apk,
                        origin=origin,
                        abi=abi,
                        entry=info.filename,
                        lib_name=lib_name,
                        size_bytes=info.file_size,
                        apk_path=str(apk_path.relative_to(ROOT)),
                    )
                    by_hash[digest].append(occ)
                    so_count += 1
                    total_bytes += info.file_size
        except Exception as exc:
            errors.append(str(exc))
        apk_summary.append({
            "apk": apk,
            "origin": origin,
            "apk_size_bytes": apk_path.stat().st_size if apk_path.is_file() else 0,
            "so_count": so_count,
            "total_native_bytes": total_bytes,
            "errors": errors,
        })
    return by_hash, apk_summary


def analyzed_hashes_from_extracted() -> dict[str, list[str]]:
    roots = [
        ROOT / "data" / "_local" / "native_extracts" / "native",
        ROOT / "data" / "_local" / "native_extracts" / "native_libs",
    ]
    out: dict[str, list[str]] = defaultdict(list)
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.so"):
            h = hashlib.sha256()
            with path.open("rb") as fp:
                for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                    h.update(chunk)
            out[h.hexdigest()].append(str(path.relative_to(ROOT)))
    return dict(out)


def scan_java_boundary(apk: str, max_hits: int = 40) -> dict[str, Any]:
    src_root = DECOMPILED_DIR / apk / "sources"
    if not src_root.exists():
        return {
            "apk": apk,
            "decompiled_sources": False,
            "load_libraries": [],
            "system_load_calls": [],
            "native_methods": [],
            "files_scanned": 0,
        }

    load_libraries: list[dict[str, Any]] = []
    system_load_calls: list[dict[str, Any]] = []
    native_methods: list[dict[str, Any]] = []
    files_scanned = 0
    for path in src_root.rglob("*.java"):
        files_scanned += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            for match in LOAD_LIBRARY_RE.finditer(line):
                if len(load_libraries) < max_hits:
                    load_libraries.append({
                        "library": match.group(1),
                        "file": str(path.relative_to(ROOT)),
                        "line": idx,
                        "snippet": redact(line.strip())[:240],
                    })
            if SYSTEM_LOAD_RE.search(line) and len(system_load_calls) < max_hits:
                system_load_calls.append({
                    "file": str(path.relative_to(ROOT)),
                    "line": idx,
                    "snippet": redact(line.strip())[:240],
                })
            for match in NATIVE_METHOD_RE.finditer(line):
                if len(native_methods) < max_hits:
                    native_methods.append({
                        "method": match.group("name"),
                        "return": match.group("ret"),
                        "args": redact(match.group("args"))[:240],
                        "file": str(path.relative_to(ROOT)),
                        "line": idx,
                        "snippet": redact(line.strip())[:240],
                    })
    return {
        "apk": apk,
        "decompiled_sources": True,
        "files_scanned": files_scanned,
        "load_libraries": load_libraries,
        "system_load_calls": system_load_calls,
        "native_methods": native_methods,
    }


def strings_from_zip_entry(zf: zipfile.ZipFile, entry: str, max_bytes: int = 64 * 1024 * 1024) -> list[str]:
    info = zf.getinfo(entry)
    if info.file_size > max_bytes:
        # Still read large libs if needed, but note that this is a bounded planner.
        pass
    raw = zf.read(entry)
    return [m.group(0).decode("latin-1", errors="ignore") for m in ASCII_RE.finditer(raw)]


def redacted_surface_scan(apk_path: Path, entry: str) -> dict[str, Any]:
    urls: list[str] = []
    secrets: list[str] = []
    uuids: list[str] = []
    tls_hits: list[str] = []
    try:
        with zipfile.ZipFile(apk_path) as zf:
            strings = strings_from_zip_entry(zf, entry)
    except Exception as exc:
        return {"error": str(exc)}

    for s in strings:
        if s.startswith("http") and URL_RE.match(s):
            if not any(noise in s for noise in NOISE_URL_PARTS):
                urls.append(clip(redact(s)))
        if SECRET_RE.search(s):
            secrets.append(clip(redact(s)))
        if UUID_RE.search(s):
            uuids.append(clip(redact(s)))
        if TLS_RE.search(s):
            tls_hits.append(clip(redact(s.strip())))

    return {
        "n_strings_min6": len(strings),
        "urls_sample": sorted(set(urls))[:10],
        "secret_like_sample": sorted(set(secrets))[:10],
        "uuid_like_sample": sorted(set(uuids))[:10],
        "tls_keyword_sample": sorted(set(tls_hits))[:20],
    }


def target_score(
    digest: str,
    occurrences: list[NativeOccurrence],
    already_analyzed: bool,
    boundary_by_apk: dict[str, dict[str, Any]],
) -> tuple[int, list[str]]:
    canonical = choose_canonical(occurrences)
    apk_names = {occ.apk for occ in occurrences}
    lib_names = {occ.lib_name for occ in occurrences}
    score = 0
    reasons: list[str] = []

    if any(occ.origin == "PleOS" for occ in occurrences):
        score += 100
        reasons.append("PleOS package")
    if not already_analyzed:
        score += 30
        reasons.append("not in prior n=4 static sample")
    if len(apk_names) > 1:
        score += 15 + min(20, len(apk_names) * 2)
        reasons.append(f"shared across {len(apk_names)} APKs")
    low_value = any(p in canonical.lib_name.lower() for p in LOW_VALUE_LIB_PATTERNS)
    if low_value:
        score -= 180
        reasons.append("known low-value common support library")
    if canonical.size_bytes < 128 * 1024 and not any(k in canonical.lib_name.lower() for k in SECURITY_LIB_KEYWORDS):
        score -= 90
        reasons.append("tiny library; low native vuln yield")
    if canonical.size_bytes >= 8 * 1024 * 1024:
        score += 40
        reasons.append("large native binary")
    for apk in apk_names:
        hits = [k for k in SECURITY_APK_KEYWORDS if k in apk.lower()]
        if hits:
            score += 8 * len(hits)
            reasons.append("high-value APK: " + ",".join(hits[:3]))
    for lib in lib_names:
        hits = [k for k in SECURITY_LIB_KEYWORDS if k in lib.lower()]
        if hits:
            score += 25 * len(hits)
            reasons.append("security-relevant lib name: " + ",".join(hits[:3]))

    load_names = {lib_to_load_name(lib) for lib in lib_names}
    for apk in apk_names:
        boundary = boundary_by_apk.get(apk, {})
        loaded = {row["library"] for row in boundary.get("load_libraries", [])}
        if load_names & loaded:
            score += 35
            reasons.append("matched System.loadLibrary")

    # Keep repeated reasons compact.
    compact_reasons = []
    for reason in reasons:
        if reason not in compact_reasons:
            compact_reasons.append(reason)
    return score, compact_reasons


def choose_canonical(occurrences: list[NativeOccurrence]) -> NativeOccurrence:
    return max(
        occurrences,
        key=lambda o: (
            o.abi == "arm64-v8a",
            ABI_PRIORITY.get(o.abi, 0),
            o.origin == "PleOS",
            o.size_bytes,
        ),
    )


def family_key(occurrences: list[NativeOccurrence]) -> tuple[str, tuple[str, ...]]:
    """Group ABI variants of the same logical library across the same APK set."""
    canonical = choose_canonical(occurrences)
    apks = tuple(sorted({occ.apk for occ in occurrences}))
    return (canonical.lib_name, apks)


def compact_occurrence(occ: NativeOccurrence) -> dict[str, Any]:
    row = asdict(occ)
    row["size_mb"] = round(occ.size_bytes / (1024 * 1024), 2)
    return row


def build_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    summary = payload["summary"]
    lines.append("# Native Deep-Dive Target Plan")
    lines.append("")
    lines.append(f"- Generated: {payload['generated_at']}")
    lines.append(f"- APKs scanned: {summary['apks_scanned']}")
    lines.append(f"- Native `.so` entries: {summary['native_entries']}")
    lines.append(f"- Unique native hashes: {summary['unique_hashes']}")
    lines.append(f"- Selected next targets: {summary['selected_targets']}")
    lines.append(f"- Already covered by prior static sample: {summary['already_analyzed_unique_hashes']}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The previous native result was a string/ELF-surface scan over n=4. "
        "This plan widens the target set and identifies Java-to-native boundary hints. "
        "A clean result here still does not prove the native layer is safe; it only defines "
        "where Ghidra xref analysis and Frida runtime probes should focus next."
    )
    lines.append("")
    lines.append("## APK Summary")
    lines.append("")
    lines.append("| APK | Origin | .so count | Native MB | JNI boundary hints |")
    lines.append("|---|---|---:|---:|---:|")
    for row in payload["apk_summary"]:
        boundary = payload["jni_boundary"].get(row["apk"], {})
        hints = (
            len(boundary.get("load_libraries", []))
            + len(boundary.get("system_load_calls", []))
            + len(boundary.get("native_methods", []))
        )
        lines.append(
            f"| `{row['apk']}` | {row['origin']} | {row['so_count']} | "
            f"{row['total_native_mb']:.1f} | {hints} |"
        )
    lines.append("")
    lines.append("## Ranked Native Targets")
    lines.append("")
    lines.append("| Rank | Canonical APK | Library | Size MB | Occurrences | Prior n=4? | Score | Why this target matters |")
    lines.append("|---:|---|---|---:|---:|---|---:|---|")
    for idx, row in enumerate(payload["selected_targets"], start=1):
        canonical = row["canonical_occurrence"]
        prior = "yes" if row["already_analyzed"] else "no"
        reasons = "; ".join(row["reasons"][:4])
        if row.get("extracted_path"):
            reasons = (reasons + f"; extracted `{row['extracted_path']}`").strip("; ")
        lines.append(
            f"| {idx} | `{canonical['apk']}` | `{canonical['lib_name']}` | "
            f"{canonical['size_mb']:.2f} | {row['occurrence_count']} | {prior} | "
            f"{row['score']} | {reasons} |"
        )
    lines.append("")
    lines.append("## Java-to-Native Boundary Hints")
    lines.append("")
    lines.append("| APK | Decompiled? | `loadLibrary` | `System.load` | native methods | Notable libraries |")
    lines.append("|---|---|---:|---:|---:|---|")
    for apk, boundary in sorted(payload["jni_boundary"].items()):
        libs = sorted({row["library"] for row in boundary.get("load_libraries", [])})
        lines.append(
            f"| `{apk}` | {boundary.get('decompiled_sources', False)} | "
            f"{len(boundary.get('load_libraries', []))} | "
            f"{len(boundary.get('system_load_calls', []))} | "
            f"{len(boundary.get('native_methods', []))} | "
            f"{', '.join('`' + lib + '`' for lib in libs[:6])} |"
        )
    lines.append("")
    lines.append("## Redacted Surface Samples For Top Targets")
    lines.append("")
    for row in payload["selected_targets"][:8]:
        canonical = row["canonical_occurrence"]
        surface = row.get("redacted_surface_scan", {})
        lines.append(f"### `{canonical['apk']}` / `{canonical['lib_name']}`")
        lines.append("")
        lines.append(f"- Entry: `{canonical['entry']}`")
        lines.append(f"- Strings >=6 chars: {surface.get('n_strings_min6', 'n/a')}")
        lines.append(f"- URLs sample: {surface.get('urls_sample', [])}")
        lines.append(f"- Secret-like sample: {surface.get('secret_like_sample', [])}")
        lines.append(f"- UUID-like sample: {surface.get('uuid_like_sample', [])[:3]}")
        lines.append(f"- TLS keywords sample: {surface.get('tls_keyword_sample', [])[:5]}")
        lines.append("")
    lines.append("## Next Concrete Work")
    lines.append("")
    lines.append("1. Extract the top non-prior targets into `data/_local/native_extracts/deep_dive/libs/` with SHA-based names.")
    lines.append("2. For Java boundary APKs, inspect `System.loadLibrary` call sites and native method wrappers.")
    lines.append("3. Run radare2/Ghidra xref on selected strings: URLs, UUIDs, TLS keywords, JNI export names.")
    lines.append("4. Add Frida probes for `System.loadLibrary`, `dlopen`, `connect`, `send`, `recv`, and matched JNI methods.")
    lines.append("5. Classify any hit under native finding rules: secret, endpoint, TLS bypass, Java secret transfer, telemetry plaintext, or unsafe file/socket behavior.")
    lines.append("")
    return "\n".join(lines) + "\n"


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def extract_selected_targets(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for idx, row in enumerate(selected, start=1):
        occ = row["canonical_occurrence"]
        apk_path = ROOT / occ["apk_path"]
        lib_path = Path(occ["lib_name"])
        suffix = lib_path.suffix or ".so"
        stem = safe_name(lib_path.name[: -len(suffix)] if lib_path.name.endswith(suffix) else lib_path.name)
        out_name = (
            f"{idx:02d}_{safe_name(occ['apk'])}_{safe_name(occ['abi'])}_"
            f"{stem}_{row['sha256_short']}{suffix}"
        )
        out_path = EXTRACT_DIR / out_name
        with zipfile.ZipFile(apk_path) as zf:
            out_path.write_bytes(zf.read(occ["entry"]))
        rel = str(out_path.relative_to(ROOT))
        row["extracted_path"] = rel
        manifest.append({
            "rank": idx,
            "sha256": row["sha256"],
            "sha256_short": row["sha256_short"],
            "apk": occ["apk"],
            "abi": occ["abi"],
            "entry": occ["entry"],
            "lib_name": occ["lib_name"],
            "size_bytes": occ["size_bytes"],
            "extracted_path": rel,
        })
    write_json(EXTRACT_MANIFEST, {
        "generated_at": now_kst(),
        "source_report": str(OUT_JSON.relative_to(ROOT)),
        "targets": manifest,
    })
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-apks", type=int, default=12, help="top native APKs from inventory to include")
    parser.add_argument("--scan-all-apks", action="store_true", help="scan every APK under data/_local/apks")
    parser.add_argument("--max-targets", type=int, default=15, help="ranked unique native libs to keep")
    parser.add_argument("--surface-scan-top", type=int, default=8, help="run redacted string scan for top N targets")
    parser.add_argument("--extract-selected", action="store_true", help="extract selected .so files to data/_local/native_extracts/deep_dive/libs")
    args = parser.parse_args()

    apk_paths = choose_apks(top_apks=args.top_apks, scan_all=args.scan_all_apks)
    by_hash, apk_summary = enumerate_native_libs(apk_paths)
    analyzed_hashes = analyzed_hashes_from_extracted()

    apks_with_native = sorted({occ.apk for occs in by_hash.values() for occ in occs})
    boundary_by_apk = {apk: scan_java_boundary(apk) for apk in apks_with_native}

    selected: list[dict[str, Any]] = []
    for digest, occurrences in by_hash.items():
        already = digest in analyzed_hashes
        score, reasons = target_score(digest, occurrences, already, boundary_by_apk)
        canonical = choose_canonical(occurrences)
        row = {
            "sha256": digest,
            "sha256_short": digest[:12],
            "score": score,
            "reasons": reasons,
            "already_analyzed": already,
            "prior_paths": analyzed_hashes.get(digest, []),
            "occurrence_count": len(occurrences),
            "canonical_occurrence": compact_occurrence(canonical),
            "occurrences": [compact_occurrence(occ) for occ in sorted(occurrences, key=lambda o: (o.apk, o.entry))[:20]],
        }
        selected.append(row)

    selected.sort(
        key=lambda r: (
            r["score"],
            ABI_PRIORITY.get(r["canonical_occurrence"]["abi"], 0),
            r["canonical_occurrence"]["size_bytes"],
        ),
        reverse=True,
    )
    family_to_best: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for row in selected:
        occurrences = [
            NativeOccurrence(
                apk=occ["apk"],
                origin=occ["origin"],
                abi=occ["abi"],
                entry=occ["entry"],
                lib_name=occ["lib_name"],
                size_bytes=occ["size_bytes"],
                apk_path=occ["apk_path"],
            )
            for occ in row["occurrences"]
        ]
        key = family_key(occurrences)
        if key not in family_to_best:
            family_to_best[key] = row
            continue
        current = family_to_best[key]
        row_rank = (
            row["score"],
            ABI_PRIORITY.get(row["canonical_occurrence"]["abi"], 0),
            row["canonical_occurrence"]["size_bytes"],
        )
        current_rank = (
            current["score"],
            ABI_PRIORITY.get(current["canonical_occurrence"]["abi"], 0),
            current["canonical_occurrence"]["size_bytes"],
        )
        if row_rank > current_rank:
            family_to_best[key] = row
    selected = list(family_to_best.values())[: args.max_targets]

    for row in selected[: args.surface_scan_top]:
        occ = row["canonical_occurrence"]
        apk_path = ROOT / occ["apk_path"]
        row["redacted_surface_scan"] = redacted_surface_scan(apk_path, occ["entry"])
    extracted_manifest = extract_selected_targets(selected) if args.extract_selected else []

    native_entries = sum(len(v) for v in by_hash.values())
    for row in apk_summary:
        row["total_native_mb"] = round(row["total_native_bytes"] / (1024 * 1024), 2)

    payload = {
        "generated_at": now_kst(),
        "method": {
            "scope": "planner only; APK zip native entry enumeration + SHA-256 dedup + JADX Java boundary hints",
            "no_llm_api": True,
            "redaction": "secret-like string samples are redacted in both JSON and Markdown outputs",
        },
        "summary": {
            "apks_scanned": len(apk_paths),
            "native_entries": native_entries,
            "unique_hashes": len(by_hash),
            "selected_targets": len(selected),
            "already_analyzed_unique_hashes": sum(1 for h in by_hash if h in analyzed_hashes),
            "extracted_targets": len(extracted_manifest),
        },
        "apk_summary": sorted(apk_summary, key=lambda r: (r["so_count"], r["total_native_bytes"]), reverse=True),
        "jni_boundary": boundary_by_apk,
        "selected_targets": selected,
    }

    write_json(OUT_JSON, payload)
    OUT_MD.write_text(build_report(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    if extracted_manifest:
        print(f"wrote {EXTRACT_MANIFEST.relative_to(ROOT)}")
        print(f"extracted {len(extracted_manifest)} targets to {EXTRACT_DIR.relative_to(ROOT)}")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
