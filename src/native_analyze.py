#!/usr/bin/env python
"""Quick static analysis of native .so libraries — strings + interesting patterns.

Replaces `strings` + `grep` for Windows / Git Bash environment where `strings`
is not in PATH. Uses the same regex search patterns as the R3.c libgojni baseline.

Usage:
    python src/native_analyze.py path/to/lib.so [path2.so ...]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

# Force UTF-8 stdout on Windows.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

MIN_LEN = 6
ASCII_RE = re.compile(rb"[\x20-\x7e]{%d,}" % MIN_LEN)

PATTERNS = {
    "url": re.compile(r"^https?://[A-Za-z0-9.\-:/_?=&%#@~+]+$"),
    "secret_sk": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "akia": re.compile(r"AKIA[A-Z0-9]{16}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "uuid_secret": re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    "api_key_kv": re.compile(r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret|bearer)[\s:=]+[A-Za-z0-9_./+=-]{16,}"),
    "tls_keyword": re.compile(r"(?i)(TrustManager|HostnameVerifier|usePlaintext|CertificatePinner|x509|tls_no_verify|verify_peer|setHostnameVerifier|insecureChannel)"),
    "elf_arch_hint": re.compile(r"^(arm64|aarch64|armeabi|x86_64|x86)$"),
}

DOMAIN_HINTS = (
    ".pleos.ai", ".umos.ai", ".42dot.ai", "openai.com", "api.openai", "googleapis.com",
    "amazonaws.com", "huggingface", "anthropic.com", "azure", ".kakao", ".naver",
)


def scan_strings(blob: bytes) -> list[str]:
    return [m.group(0).decode("latin-1", errors="ignore") for m in ASCII_RE.finditer(blob)]


def analyze(path: Path) -> dict:
    raw = path.read_bytes()
    n_bytes = len(raw)
    # ELF magic
    is_elf = raw[:4] == b"\x7fELF"
    bits = ("64" if raw[4] == 2 else "32") if is_elf else "?"
    # NX / PIE / RELRO heuristic via DT_FLAGS would need full parsing; skip — defer
    # to file(1) classification done outside.

    strings = scan_strings(raw)
    n_strings = len(strings)

    urls: list[str] = []
    secrets: dict[str, list[str]] = {k: [] for k in PATTERNS if k != "elf_arch_hint"}
    domain_hits: dict[str, int] = Counter()
    tls_hits: list[str] = []

    for s in strings:
        # URL fast path
        if s.startswith("http"):
            if PATTERNS["url"].match(s):
                urls.append(s)
                for d in DOMAIN_HINTS:
                    if d in s:
                        domain_hits[d] += 1
        # Secret patterns
        for key, rx in PATTERNS.items():
            if key in ("url", "elf_arch_hint"):
                continue
            for m in rx.finditer(s):
                hit = m.group(0)
                if hit not in secrets[key]:
                    secrets[key].append(hit)
        # TLS keyword exact
        if PATTERNS["tls_keyword"].search(s):
            tls_hits.append(s.strip())

    # dedup urls and cap
    urls = sorted(set(urls))
    # filter obviously noise URLs
    DENY_NOISE = ("schemas.android.com", "schema.org", "w3.org", "json-schema.org",
                  "github.com", "go.dev", "golang.org", "example.com", "github.io")
    urls_filtered = [u for u in urls if not any(n in u for n in DENY_NOISE)]
    # dedup tls hits
    tls_hits = sorted(set(tls_hits))[:30]

    return {
        "path": str(path),
        "size_bytes": n_bytes,
        "is_elf": is_elf,
        "elf_bits": bits,
        "n_strings_min6": n_strings,
        "n_urls": len(urls),
        "n_urls_after_noise_filter": len(urls_filtered),
        "urls_sample": urls_filtered[:30],
        "domain_hits": dict(domain_hits),
        "secrets": {k: v[:10] for k, v in secrets.items() if v},
        "tls_keyword_hits_sample": tls_hits,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: native_analyze.py <so> [<so> ...]", file=sys.stderr)
        return 2
    out = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.is_file():
            print(f"skip (not file): {p}", file=sys.stderr)
            continue
        res = analyze(p)
        out.append(res)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
