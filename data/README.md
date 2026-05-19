# data/

Data is split by disclosure boundary.

| Path | Tracked? | Role |
|---|---|---|
| `ground_truth/` | yes | Self, MASTG, InsecureBankv2, and combined labels |
| `reports/aggregate/` | yes | GT-derived public-safe summary reports |
| `reports/external/` | yes | Public vulnerable-corpus per-APK reports |
| `reports/public/` | yes | Masked public PleOS reports |
| `deobf/` | yes | Obfuscation entropy JSON and rename outputs |
| `viz/` | yes | Chart PNGs used by docs and presentations |
| `_local/` | no | APKs, JADX output, raw evidence, vector DBs, native extracts, tools |
| `reports/*_local/` | no | Private or generated report tracks |

## Local-Only Buckets

```text
_local/apks/                 APK inputs
_local/decompiled/           JADX output
_local/poc_evidence/         screenshots, logcat, UI dumps
_local/runtime_videos/       demo recordings
_local/runtime_poc_harness/  generated Android harness build output
_local/rag_db/               Chroma vector DB
_local/native_extracts/      extracted .so files and native scan workspace
_local/tools/                portable radare2 and similar binaries
```

`data/_local/` is intentionally ignored. Do not force-add it.

## Report Buckets

See `reports/README.md`.
