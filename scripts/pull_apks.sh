#!/usr/bin/env bash
set -euo pipefail
# Git Bash on Windows rewrites POSIX-looking absolute paths (e.g. /system/...) to Windows form,
# breaking `adb pull`. Disable that translation for the whole script.
export MSYS_NO_PATHCONV=1
OUT="${1:-data/apks}"
mkdir -p "$OUT"

adb shell 'pm list packages -f -s' \
  | sed -e 's/^package://' -e 's/\r$//' \
  | while IFS='=' read -r path pkg; do
      [ -n "$pkg" ] || continue
      target="$OUT/${pkg}.apk"
      if [ -f "$target" ]; then
        echo "[skip] $pkg (already pulled)"
        continue
      fi
      echo "[pull] $pkg"
      if ! adb pull "$path" "$target" >/dev/null 2>&1; then
        echo "  fail: $pkg ($path)"
      fi
    done

count=$(ls -1 "$OUT" 2>/dev/null | wc -l)
echo "Done. $count APKs in $OUT"
