#!/usr/bin/env bash
set -euo pipefail
APK="${1:?usage: decompile.sh <apk>}"
NAME="$(basename "$APK" .apk)"
OUT="data/decompiled/$NAME"
mkdir -p "$OUT"

jadx --deobf --show-bad-code -d "$OUT" "$APK"
echo "Decompiled -> $OUT"
