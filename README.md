# pleos-llm-scanner

LLM-driven static security analysis pipeline for in-vehicle Android (AAOS) APKs, applied to **PleOS Connect** as a case study.

본 저장소는 연세대학교 전기전자공학과 Computational Intelligence Lab의 *자율주행 연구 프로젝트 1* (2026-1학기) 산출물이다. 연계 과제: 현대자동차 계약학과 육성형 연구과제 — PleOS TARA 및 실차 보안 취약점 점검.

> **Note**: 이 저장소는 **재현 가능한 분석 파이프라인**을 공개한다. PleOS Connect APK 바이너리, 디컴파일 결과, 사례별 보고서는 계약과제 IP 보호 정책에 따라 별도 비공개 (`.gitignore`).

---

## Pipeline

```
APK ──► jadx --deobf ──► keyword filter (configs/keywords.yaml)
    ──► stage 1: single-pass LLM detection      (configs/prompts/stage1_detect.md)
    ──► stage 2: caller analysis                (manifest exported / Hilt graph / regex / AST)
    ──► stage 3: multi-prompt ensemble          (D3=B: attacker / defender / domain expert)
    ──► consensus rule                          (configs/prompts/stage3_ensemble_rule.md)
    ──► reports                                 (data/reports/, gitignored)
    ──► evaluation                              (src/eval.py against data/ground_truth/)
    ──► ablation                                (src/ablation.py)
    ──► AAOS guideline mapping + TARA           (configs/aaos_mapping.yaml)
```

## Key decisions (2026-04-29 현재)

| ID | Decision | Note |
|---|---|---|
| **D1** | Emulator image = PleOS Connect v2.0.5 x86_64 | manifest at `nexus-playground.pleos.ai/.../crp-sys-img.xml` |
| **D2** | First target APK = `ai.umos.vehiclecontrol` | system UID + 13 privileged permissions + 차량 제어 권한 |
| **D3** | Multi-prompt ensemble (single LLM × 3 perspectives) | original PPT plan was multi-LLM (Claude + GPT-4); replaced due to environment constraint (no external API budget, Claude Code single-model session) |
| **D4** | Ground truth = OWASP MASVS-MASTG + self labels | self labels first; MASTG corpus integration is future work |

## Representative results (n=15 first session)

| metric | stage 1 only | + stage 2 (caller) | + stage 3 (≥3/3 consensus) |
|---|---|---|---|
| Precision (lenient) | **71.4%** | 100.0%* | **100.0%** |
| FP rate | 28.6% | 0.0%* | 0.0% |
| Recall | 100.0% | 100.0%* | 70.0% |
| F1 | **0.833** | 1.000* | **0.824** |

\* `+ stage 2` is computed against self-GT `is_real==true`, so its 100% is a *P-ceiling* upper bound rather than a realistic measurement of the caller-trace step in isolation. See [`docs/ablation_results_20260429.md`](docs/ablation_results_20260429.md) for the full ablation including consensus-threshold sensitivity (≥1/3, ≥2/3, ≥3/3).

## Directory layout

```
pleos-llm-scanner/
├── README.md
├── LICENSE
├── .gitignore
├── CLAUDE.md                  # Claude Code 작업 가이드 + 의사결정 표
├── progress.md                # 주차별 진척 (단일 진실 출처)
├── next.md                    # 즉시 행동 항목 + 결정 필요 사항
├── configs/
│   ├── keywords.yaml          # 보안 민감 키워드 단일 출처
│   ├── aaos_mapping.yaml      # AAOS 가이드라인 매핑 v0
│   ├── result_schema.json     # 보고서 JSON 스키마
│   └── prompts/
│       ├── stage1_detect.md
│       ├── stage3_attacker.md
│       ├── stage3_defender.md
│       ├── stage3_domain_expert.md
│       └── stage3_ensemble_rule.md
├── scripts/
│   ├── pull_apks.sh           # `adb shell pm list packages -s` 일괄 추출
│   └── decompile.sh           # jadx --deobf 래퍼
├── src/
│   ├── eval.py                # Precision/Recall/F1 자동 측정
│   └── ablation.py            # stage / consensus threshold ablation
├── docs/
│   ├── ppt_revision_guide_20260429.md
│   └── ablation_results_20260429.md
└── data/
    └── ground_truth/          # 자체 라벨 (n=15)
    # data/apks, data/decompiled, data/reports — local-only (.gitignore)
```

## Quickstart (재현)

전제: PleOS Connect 또는 AAOS Automotive 에뮬레이터 부팅, ADB 연결, jadx 1.5.5+ 설치, Python 3.10+.

```bash
# 1) 시스템 APK 일괄 추출 (gitignored data/apks/)
bash scripts/pull_apks.sh data/apks

# 2) 단일 APK 디컴파일
bash scripts/decompile.sh data/apks/<package>.apk

# 3) Claude Code 세션에서 keyword grep + Stage 1 LLM 분석
#    -> data/reports/<apk>_<YYYYMMDD>.{json,md} 저장 (gitignored)

# 4) 자동 평가 (Precision/Recall/F1)
python src/eval.py \
    --labels data/ground_truth/self_labels_20260429.json \
    --reports 'data/reports/*.json'

# 5) Ablation: stage 효과 + 합의 임계 sensitivity
python src/ablation.py \
    --labels data/ground_truth/self_labels_20260429.json \
    --reports 'data/reports/*.json' \
    --stage3  data/reports/stage3_ensemble_20260429.json
```

## Privacy / IP boundary

- **Excluded from this repo** (계약과제 IP 보호): PleOS APK binaries, decompiled sources, per-APK case-study reports.
- **Included**: pipeline configuration, prompts (stage 1/3), scripts, evaluation/ablation code, ground-truth labels, AAOS-mapping skeleton, and reproducibility documentation.
- Finding evidence quotes (1–3 lines per finding) are kept inside the gitignored `data/reports/`. Their disclosure decision is deferred until the report-finalisation review.

## Environment

- Windows 11 + Git Bash + Miniconda Python (`/c/Users/cabin/Miniconda3/python.exe`)
- jadx 1.5.5 CLI
- Android Studio commandline-tools 20.0 + platform-tools 37 + emulator 36.5.11 + `platforms;android-34` + `system-images;android-34;pleos_car_emulator;x86_64`
- Hardware: Intel Core Ultra 7 155H + 16 GB RAM (discrete GPU 부재 → emulator는 `swiftshader_indirect`)
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
