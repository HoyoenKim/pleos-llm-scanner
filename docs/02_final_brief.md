# 프로젝트 이해용 최종 요약

이 문서는 15주차 종료 기준 최종 요약이다. 완료된 보강 실험 A-E를 최종 결과의 일부로 설명한다.

## 한 문장 결론

PleOS IVI APK 보안 분석에서 LLM은 단독 탐지기가 아니라, deterministic keyword triage와 Android-domain contextual verification 사이에 놓인 reasoning component로 쓸 때 가장 효과적이었다.

## 최종 수치

| Metric | Value |
|---|---:|
| Combined GT | 47 |
| Stage 1 TP / FP / FN | 38 / 9 / 0 |
| Stage 1 Precision / Recall / F1 | 80.9% / 100.0% / 0.894 |
| Stage 3 `>=2/3` TP / FP / FN | 37 / 0 / 1 |
| Stage 3 `>=2/3` Precision / Recall / F1 | 100.0% / 97.4% / 0.987 |
| McNemar exact p-value | 0.0215 |

## 연구 흐름

```text
APK
  -> jadx --deobf
  -> keyword triage
  -> Stage 0 obfuscation check
  -> Stage 1 LLM candidate detection
  -> Stage 2 contextual verification
  -> Stage 3 multi-perspective consensus
  -> AAOS / MASVS / TARA mapping
```

## 데이터셋

| Origin | Findings | TP | FP | Precision |
|---|---:|---:|---:|---:|
| PleOS-customized | 30 | 23 | 7 | 76.7% |
| External vulnerable corpus | 13 | 13 | 0 | 100.0% |
| AOSP-derived | 4 | 2 | 2 | 50.0% |
| Total | 47 | 38 | 9 | 80.9% |

## 핵심 사례

| Finding | Summary | Final Meaning |
|---|---|---|
| `amb-1` | AmbientAI production LLM API key hardcoding | credential leakage and privacy/billing risk |
| `am-3` | AppMarket HMG OAuth client secret | cross-APK credential pattern with account flow |
| `acc-4` | Exported SSO Activity receives `user-client-secret` | sensitive value crossing Activity boundary |
| `ssl-6` | SysLog gRPC `.usePlaintext()` | diagnostic/system log transport risk |
| `lmp-1` | Exported prompt provider | IVI LLM prompt/corpus disclosure |
| `vc-6` | VehicleBroadcastReceiver accepts untrusted MAC-like payload | vehicle-control spoofing/tampering risk |

## What Changed From Initial Plan

| Initial Plan / Concern | Final State |
|---|---|
| 1-pass LLM could over-report | Stage 2/3 reduced FP to 0 on final reported corpus |
| Multi-LLM ensemble unavailable | Single-model multi-perspective consensus worked better than Codex 3-model cross-read |
| Small sample size | Expanded to `n=47`, McNemar significance reached |
| Java-only blind spot | Native static track added; dynamic/native runtime flow still remains open |
| Static-only method | Dynamic state machine and Frida hooks prepared for selected findings |
| Domain knowledge hardcoded in prompt | Local RAG retrieval path implemented and measured intrinsically |

## Final Interpretation

The strongest result is the paired improvement from Stage 1 to Stage 3. Stage 1 should be viewed as a high-recall candidate generator. Stage 3 `>=2/3` is the final reporting threshold for this artifact.

The strongest caution is corpus bias. The dataset is intentionally security-value selected, not a random population of Android apps. Therefore the measured numbers are valid for this project corpus, not a universal scanner benchmark.

## Where To Read Next

- Full report: `01_final_report.md`
- Evidence cases: `03_case_studies.md`
- Stage 2 method: `04_methodology_stage2.md`
- Limits and cost: `06_limitations_and_costs.md`
- Completed reinforcement experiments: `08_completed_reinforcements.md`
