# pleos-llm-scanner

LLM-driven static security analysis pipeline for in-vehicle Android (AAOS) APKs, applied to **PleOS Connect** as a case study.

> **Note**: 이 저장소는 **재현 가능한 분석 파이프라인**을 공개한다. PleOS Connect APK 바이너리, 디컴파일 결과, 사례별 보고서는 IP 보호 정책에 따라 비공개 (`.gitignore`).

---

## Pipeline

```
APK ──► jadx --deobf ──► keyword filter (configs/keywords.yaml)
    ──► stage 1: single-pass LLM detection      (configs/prompts/stage1_detect.md)
    ──► stage 2: caller analysis                (manifest exported / Hilt graph / regex / AST)
    ──► stage 3: multi-prompt ensemble          (attacker / defender / domain expert)
    ──► consensus rule                          (configs/prompts/stage3_ensemble_rule.md)
    ──► reports                                 (data/reports/, gitignored)
    ──► evaluation                              (src/eval.py against data/ground_truth/)
    ──► ablation                                (src/ablation.py)
    ──► AAOS guideline mapping + TARA           (configs/aaos_mapping.yaml)
```

## Documentation

측정값·분석·통합 문서는 [`docs/`](docs/)에 정리되어 있다. 통합 보고서: [`docs/report_v0.9.md`](docs/report_v0.9.md). 디렉토리 인덱스: [`docs/README.md`](docs/README.md).

## Directory layout

```
pleos-llm-scanner/
├── README.md
├── LICENSE
├── .gitignore
├── configs/
│   ├── keywords.yaml          # 보안 민감 키워드 단일 출처
│   ├── aaos_mapping.yaml      # AAOS 가이드라인 매핑
│   ├── result_schema.json     # 보고서 JSON 스키마
│   └── prompts/
│       ├── stage1_detect.md
│       ├── stage_b_deobfuscate.md
│       ├── stage3_attacker.md
│       ├── stage3_defender.md
│       ├── stage3_domain_expert.md
│       └── stage3_ensemble_rule.md
├── scripts/
│   ├── pull_apks.sh           # `adb shell pm list packages -s` 일괄 추출
│   └── decompile.sh           # jadx --deobf 래퍼
├── src/
│   ├── eval.py                # Precision / Recall / F1 자동 측정
│   ├── ablation.py            # stage / consensus threshold ablation
│   ├── aaos_map.py            # AAOS / MASVS / TARA 자동 매핑
│   ├── tara_generate.py       # ISO/SAE 21434 TARA artifact
│   ├── deobf/entropy.py       # Shannon entropy + jadx pattern obfuscation detector
│   └── viz/plot_metrics.py    # 측정값 시각화 (6 차트)
├── docs/                       # 측정 기록 + 통합 보고서 (docs/README.md 참조)
└── data/
    └── ground_truth/           # self labels + MASTG labels
    # data/apks, data/decompiled, data/reports — local-only (.gitignore)
```

## Quickstart (재현)

전제: PleOS Connect 또는 AAOS Automotive 에뮬레이터, ADB 연결, jadx 1.5.5+, Python 3.10+.

```bash
# 1) 시스템 APK 일괄 추출 (gitignored data/apks/)
bash scripts/pull_apks.sh data/apks

# 2) 단일 APK 디컴파일
bash scripts/decompile.sh data/apks/<package>.apk

# 3) Claude Code 세션에서 keyword grep + Stage 1 LLM 분석
#    → data/reports/<apk>_<YYYYMMDD>.{json,md} 저장 (gitignored)

# 4) 자동 평가 (Precision/Recall/F1)
python src/eval.py \
    --labels data/ground_truth/combined_labels_20260430.json \
    --reports 'data/reports/*.json'

# 5) Ablation: stage 효과 + 합의 임계 sensitivity
python src/ablation.py \
    --labels data/ground_truth/combined_labels_20260430.json \
    --reports 'data/reports/*.json' \
    --stage3  data/reports/stage3_ensemble_20260429.json
```

## Privacy / IP boundary

- **Excluded from this repo**: PleOS APK binaries, decompiled sources, per-APK case-study reports, internal working notes.
- **Included**: pipeline configuration, prompts, scripts, evaluation / ablation / mapping code, ground-truth labels, AAOS-mapping skeleton, integration / generalization docs, reproducibility documentation.
- Finding evidence quotes (1–3 lines per finding) live inside the gitignored `data/reports/`. Disclosure decision is deferred until the report-finalisation review.

## Environment

- Python 3.10+
- jadx 1.5.5+ (CLI)
- Android Studio commandline-tools + platform-tools + emulator + `platforms;android-34` + `system-images;android-34;pleos_car_emulator;x86_64`
- Claude Opus 4.7 (1M context) — analysis engine

## License

[MIT](LICENSE).

## References

- jadx — https://github.com/skylot/jadx
- jadx-ai-mcp (related work) — https://github.com/zinja-coder/jadx-ai-mcp
- android-scanner-ai (baseline candidate) — https://github.com/X-Vector/android-scanner-ai
- Androidmeda (baseline candidate) — https://github.com/In3tinct/Androidmeda
- Android Automotive Security — https://source.android.com/docs/automotive/start/secure_aaos
- OWASP MASVS-MASTG — https://github.com/OWASP/owasp-mastg
- PleOS Connect SDK — https://document.pleos.ai/
