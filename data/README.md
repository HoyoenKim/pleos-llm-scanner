# data/ — Inventory

이 디렉토리는 파이프라인의 입력 (APK / decompiled / ground truth) 과 출력 (per-APK reports / aggregated mapping / charts / obfuscation entropy / runtime PoC evidence) 을 모아둔다. **APK 바이너리 / 디컴파일 결과 / per-APK 보고서 / raw runtime evidence / videos**는 contractor IP 보호와 claim-boundary 보존을 위해 gitignored이고, 집계 산출물 / GT 라벨 / 차트 / redacted public reports만 commit된다.

## Subdirectories

| Path | Tracked? | Content |
|---|---|---|
| `apks/` | ✗ gitignored | 에뮬레이터에서 추출한 시스템 APK 바이너리 (`scripts/pull_apks.sh` 출력). `.apk` 파일 다수. |
| `decompiled/` | ✗ gitignored | jadx 디컴파일 결과 (`scripts/decompile.sh` 출력). APK당 sources/ 폴더. |
| `reports/` | **partial** | per-APK Stage 1/2/3 보고서는 gitignored. **집계 결과 2종 (AAOS/MASVS 매핑 + TARA artifact) 만 commit** — `.gitignore` 의 negation 규칙으로 명시. |
| `deobf/` | ✓ all | 6 APK 의 obfuscation entropy 측정값 (`<APK>.json`) + UnCrackable rename 결과. 자동 생성 `<APK>.md`는 gitignored (JSON이 source of truth). 자세히는 [`deobf/README.md`](deobf/README.md). |
| `viz/` | ✓ all | 측정값 시각화 차트 6장 (`01~06_*.png`). `src/viz/plot_metrics.py` 출력. |
| `ground_truth/` | ✓ all | 자체 라벨 + OWASP MASTG 라벨 + combined GT. eval/ablation/aaos_map/tara_generate 가 입력으로 사용. |
| `poc_evidence/` | ✗ gitignored | 2026-05-18 runtime PoC raw evidence. screenshots, logcat, UIAutomator dump, replay videos. 공개 전 redaction review 필수. |
| `runtime_poc_*` | ✗ gitignored | PoC recording/final/improved/LLM-boundary demo videos and bundles. 발표용 local artifacts. |
| `native*`, `rag/`, `tools/` | ✗ gitignored | extracted native libs, Chroma vector DB, portable radare2 등 generated/binary dependency. summary만 docs/reports에 기록. |

## File-name convention

- **시점 스냅샷이 아닌 산출물** (`combined_labels.json`, `self_labels.json`, `aaos_mapping_table.{md,json}`, `tara_artifact.{md,json}`, `<APK>_renames.json`): 파일명에 날짜 없음. 측정일은 본문 metadata (`labeled_at` / `last_updated` / `generated_at` / `analyzed_at`) 에 명시. 갱신 시 같은 파일을 overwrite — git history가 시점 추적.
- **번호 prefix가 의미 있는 파일** (`viz/01_*.png` 등): 순서 유지를 위해 prefix 보존.
- **차트 PNG**: 날짜 없음. 측정일은 차트 caption에 명시.

## tracked vs gitignored 상세

```
data/
├── apks/                       # gitignored (APK 바이너리, IP)
├── decompiled/                 # gitignored (jadx 출력, IP)
├── reports/
│   ├── aaos_mapping_table.md   # tracked (집계, GT-derived)
│   ├── aaos_mapping_table.json # tracked
│   ├── tara_artifact.md        # tracked
│   ├── tara_artifact.json      # tracked
│   ├── <allowed RQ aggregate>.{md,json} # tracked by .gitignore negation
│   ├── _raw/                   # gitignored (dumpsys/log/source-like raw evidence)
│   ├── prompt_leak_attack_poc/ # gitignored (video/preview/demo bundle)
│   └── <other>.{json,md}       # gitignored (per-APK reports / local-only runtime summaries)
├── deobf/
│   ├── README.md               # tracked (요약 인덱스)
│   ├── <APK>.json × 7          # tracked (entropy 측정 결과)
│   ├── <APK>.md × 7            # gitignored (auto-generated summary)
│   └── UnCrackable-*_renames*.json # tracked (Stage 0 결과 + GT)
├── viz/
│   └── 01~06_*.png             # tracked (차트 6장)
└── ground_truth/
    ├── self_labels.json        # tracked (PleOS 자체 라벨)
    ├── combined_labels.json    # tracked (최종 n=47 combined GT)
    └── mastg/
        ├── uncrackable_level1.labels.json
        ├── uncrackable_level2_r2pay.labels.json
        └── uncrackable_level3.labels.json
```

## 빈 clone 시

`data/apks/` 와 `data/decompiled/` 는 gitignored 이므로 새 clone 직후 디렉토리 자체가 없다. `scripts/pull_apks.sh` / `scripts/decompile.sh` 가 처음 실행될 때 자동 생성한다.
