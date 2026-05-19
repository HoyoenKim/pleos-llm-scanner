# LLM 기반 디컴파일러 분석 및 PleOS 적용 방안 검토

이 문서는 15주차 연구 진행이 모두 끝난 뒤 작성한 최종 보고서다. 보강 실험 A-E는 모두 수행 완료되어 최종 결과에 통합된 항목으로 다룬다.

## 1. 결론

PleOS / AAOS IVI APK 보안 분석에서 LLM을 단독 탐지기로 쓰는 것은 위험하다. 하지만 LLM을 deterministic triage와 Android-domain contextual verification 사이의 reasoning layer로 배치하면, 보안 가치가 높은 APK subset에서 후보 검증 비용을 줄이고 오탐을 크게 낮출 수 있다.

최종 combined GT `n=47`에서 Stage 1은 실제 취약점 38건을 모두 후보로 잡았다. Stage 3 `>=2/3` multi-perspective consensus는 오탐 9건을 모두 제거했고, 실제 low-severity hardening finding 1건만 보수적으로 누락했다. Stage 1 대비 Stage 3 개선은 McNemar exact test `p=0.0215`로 통계적으로 유의했다.

| Metric | Stage 1 | Stage 3 `>=2/3` |
|---|---:|---:|
| TP | 38 | 37 |
| FP | 9 | 0 |
| FN | 0 | 1 |
| Precision | 80.9% | 100.0% |
| Recall | 100.0% | 97.4% |
| F1 | 0.894 | 0.987 |

## 2. 연구 질문

| RQ | 질문 | 최종 답 |
|---|---|---|
| RQ1 | Stage 1 후보 탐지 후 Stage 2/3 검증이 오탐을 줄이는가? | 그렇다. Stage 3는 FP 9건을 모두 제거했고 McNemar `p=0.0215`로 개선이 유의했다. |
| RQ2 | multi-perspective consensus와 multi-model cross-read 중 무엇이 더 강한가? | 현재 artifact에서는 single-model multi-perspective Stage 3가 더 강했다. Codex 3-model cross-read는 precision 100%를 유지했지만 recall이 낮아졌다. |
| RQ3 | Java/Kotlin static pipeline의 blind spot은 무엇인가? | Native `.so`와 runtime/JNI flow가 구조적 blind spot이다. native static sample `n=4`에서는 추가 vuln 0건이었지만 dynamic flow는 아직 별도 한계다. |
| RQ4 | 난독화/real-world sample로 일반화되는가? | 부분적으로만 그렇다. hand-crafted sample은 upper bound이고, NewPipe real-world rename plausibility는 GOOD+ 67%로 낮아졌다. |
| RQ5 | 이 결과를 PleOS TARA/운영 산출물로 연결할 수 있는가? | 가능하다. AAOS/MASVS/TARA mapping과 risk matrix, public masked report, local-only evidence boundary를 구성했다. |

## 3. 15주차 연구 타임라인

| 주차 | 내용 | 산출 |
|---:|---|---|
| 1 | 문제 정의와 목표 설정 | LLM-assisted IVI APK 보안 분석 방향 |
| 2 | 도구 조사 | Java/Kotlin APK는 `jadx`, native는 별도 binary track |
| 3 | 환경 제약 확정 | 로컬 GPU 없음, 외부 유료 API 없음, Codex/Claude Code 분석 엔진 |
| 4 | APK 수집 환경 구성 | AAOS/PleOS emulator + ADB |
| 5 | 기본 파이프라인 scaffold | `scripts/apk/`, `configs/`, `src/` |
| 6 | Stage 0 난독화 측정 | entropy, jadx pattern, rename plausibility |
| 7 | Stage 1 설계 | six-category LLM candidate detection |
| 8 | 초기 PleOS APK 분석 | VehicleControl, SysLog, LLM Model Provider |
| 9 | Stage 2 검증 | manifest/caller/permission/route blocking control |
| 10 | Stage 3 합의 | attacker/defender/domain-expert perspective |
| 11 | 외부 GT 확장 | OWASP MASTG, InsecureBankv2, AOSP-derived |
| 12 | 정량 평가 | precision/recall/F1, bootstrap, ablation, McNemar |
| 13 | 산업 산출물 | AAOS/MASVS/TARA, case studies, architecture |
| 14 | 보강 실험 A-D | n=47, RAG, native scan, dynamic hooks |
| 15 | 보강 실험 E와 최종 통합 | Codex cross-read, README/docs/public artifacts |

## 4. 파이프라인

| Stage | 역할 | 구현/근거 |
|---|---|---|
| Stage 0 | 난독화 전처리 | `src/deobf/entropy.py`, `configs/prompts/stage0_deobfuscate.md` |
| Stage 1 | LLM 1차 후보 탐지 | `configs/keywords.yaml`, `configs/prompts/stage1_detect.md` |
| Stage 2 | 문맥 검증 | manifest, exported, permission, caller chain, route, protected broadcast |
| Stage 3 | 다중 시각 합의 | attacker / defender / domain expert / consensus prompts |
| Mapping | 보안 표준 연결 | `src/mapping/aaos_map.py`, `src/mapping/tara_generate.py` |

Stage 2가 중요한 이유는 Android 취약점 후보가 API 이름만으로 결정되지 않기 때문이다. `grantRuntimePermission`, exported receiver, WebView, provider query 같은 표면은 caller reachability, protected broadcast, signature permission, route binding, `setPackage`/`setComponent`와 함께 읽어야 한다.

## 5. 데이터셋과 라벨

| Origin | Findings | TP | FP | Precision | 의미 |
|---|---:|---:|---:|---:|---|
| PleOS-customized | 30 | 23 | 7 | 76.7% | 실제 연구 대상 중심 |
| External vulnerable corpus | 13 | 13 | 0 | 100.0% | OWASP MASTG + InsecureBankv2 |
| AOSP-derived / framework-like | 4 | 2 | 2 | 50.0% | framework-level blocking control 때문에 FP가 많음 |
| Total | 47 | 38 | 9 | 80.9% | 최종 combined GT |

카테고리 분포는 `intent` 18, `hardcoded` 11, `network` 9, `crypto` 5, `permission` 3, `reflection_dynamic` 1이다. FP는 주로 `intent`, `network`, `permission`에서 발생했다.

## 6. 핵심 결과

### 6.1 Stage 1 vs Stage 3

Stage 1은 recall-first 후보 생성기로 동작했다. 최종 보고 기준으로는 Stage 3 `>=2/3` consensus가 더 적절하다.

| Variant | Accepted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage 1 initial detection | 47 | 38 | 9 | 0 | 80.9% | 100.0% | 0.894 |
| Stage 3 `>=1/3` | 45 | 38 | 7 | 0 | 84.4% | 100.0% | 0.916 |
| Stage 3 `>=2/3` | 37 | 37 | 0 | 1 | 100.0% | 97.4% | 0.987 |
| Stage 3 `>=3/3` | 33 | 33 | 0 | 5 | 100.0% | 86.8% | 0.930 |

### 6.2 McNemar paired test

|  | Stage 3 correct | Stage 3 incorrect |
|---|---:|---:|
| Stage 1 correct | 37 | 1 |
| Stage 1 incorrect | 9 | 0 |

`b+c=10`, exact two-tailed `p=0.0215`. Stage 3의 개선은 단순 표본 우연으로 보기 어렵다.

### 6.3 Bootstrap CI

Stage 1 precision의 95% bootstrap CI는 `[70.2%, 91.5%]`이다. `n=19` 초기 feasibility에서 `n=47`로 확장하며 CI 폭이 줄었지만, 아직 일반화 성능 보장에는 부족하다.

### 6.4 Obfuscation

Hand-crafted MASTG sample에서는 rename exact match가 높았지만, NewPipe real-world sample에서는 GOOD+ plausibility 67%로 낮아졌다. 따라서 Stage 0는 “상한 가능성”과 “real-world plausibility”를 분리해 보고해야 한다.

### 6.5 Native boundary

PleOS Connect 207 APK 중 native library 보유 APK는 22개(10.6%)였다. PleOS 자체 패키지로 좁히면 14/28(50.0%)였다. Native static sample `n=4`에서는 추가 native-bound vulnerability가 나오지 않았지만, Go runtime/JNI/syscall flow는 정적 분석만으로 닫히지 않는다.

## 7. 대표 사례

| ID | APK | 판단 | 핵심 의미 |
|---|---|---|---|
| `amb-1` | `ai.umos.ambientai` | TP | production LLM API key hardcoding |
| `am-3` | `ai.umos.appmarket` | TP | HMG OAuth `client_id` + `client_secret` cross-APK exposure |
| `acc-4` | `ai.pleos.playground.account` | TP | exported SSO Activity receives `user-client-secret` |
| `ssl-6` | `ai.pleos.sync.syslog` | TP | gRPC `.usePlaintext()` transport |
| `lmp-1` | `ai.pleos.llm.model.provider` | TP | exported prompt provider leaks IVI LLM corpus |
| `vc-6` | `ai.umos.vehiclecontrol` | TP | exported VehicleBroadcastReceiver accepts untrusted MAC-like payload |
| `vc-3/4` | `ai.umos.vehiclecontrol` | FP | caller route blocked by manifest/Nav/internal binding |
| `usb-2` | `android.car.usb.handler` | FP | framework permission path blocks caller control |
| `ss-1` | `com.android.statementservice` | FP | `BOOT_COMPLETED` protected broadcast |
| `amb-4` | `ai.umos.ambientai` | FP | explicit component binding blocks external broadcast |

Detailed evidence is in `03_case_studies.md`. Public PleOS reports keep code excerpts redacted.

## 8. Completed Reinforcement Experiments A-E

| Code | Final Name | Result |
|---|---|---|
| A | Corpus/statistics reinforcement | GT expanded to `n=47`; McNemar significance reached |
| B | RAG knowledge reinforcement | Chroma 4 collections, 158 chunks, NN/AAOS 85.1% |
| C | Native boundary reinforcement | radare2 + native scanner, sample `n=4`, additional vuln 0 |
| D | Dynamic verification reinforcement | deterministic state machine + 5 Frida hooks |
| E | Codex multi-model cross-read | did not beat Stage 3; evidence packaging matters more |

These are final integrated results in the 15-week archive.

## 9. AAOS / MASVS / TARA

The mapping layer translates findings into automotive-security language:

| Category | Main AAOS / MASVS Area |
|---|---|
| `intent`, `permission` | AAOS permission/component exposure, MASVS-PLATFORM |
| `network` | AAOS communication security, MASVS-NETWORK |
| `hardcoded`, `crypto` | credential protection, MASVS-STORAGE / MASVS-CRYPTO |
| `reflection_dynamic` | code integrity and dynamic execution |

TARA scenarios focus on impact, feasibility, and treatment. The most severe cases involve vehicle control spoofing/tampering and credential leakage across PleOS-customized components.

## 10. Limitations

| Limit | Final State |
|---|---|
| Self-label bias | External corpora were added, but PleOS-customized labels still need independent reviewer validation |
| Corpus selection bias | The dataset is security-value selected, not random app-store scale |
| Native/runtime flow | Native static track exists, but dynamic JNI/Go/runtime behavior remains partially unobserved |
| RAG effect | Intrinsic retrieval quality measured; prompted with/without RAG LLM ablation remains open |
| ProGuard-heavy APKs | Priority-class yield can fall sharply; manifest-only and stronger Stage 0 are needed |
| Stage 2 automation | Current Stage 2 includes deterministic rules but is not a fully general Android static analyzer |

## 11. Contributions

1. A 4-stage LLM-assisted APK security analysis pipeline for PleOS/AAOS IVI.
2. A final combined GT corpus of 47 labelled findings with origin breakdown.
3. Evidence that multi-perspective verification can significantly reduce FP on the measured corpus.
4. AAOS/MASVS/TARA mapping artifacts that connect code findings to automotive risk language.
5. A clear disclosure boundary between public-safe summaries and local-only proprietary evidence.
6. Reinforcement experiments covering statistics, RAG, native static analysis, dynamic hooks, and Codex cross-read.

## 12. Artifact Index

| Artifact | Path |
|---|---|
| Final brief | `docs/02_final_brief.md` |
| Case studies | `docs/03_case_studies.md` |
| Stage 2 methodology | `docs/04_methodology_stage2.md` |
| Limitations/cost | `docs/06_limitations_and_costs.md` |
| Completed reinforcements | `docs/08_completed_reinforcements.md` |
| Remaining work | `docs/07_remaining_work.md` |
| GT labels | `data/ground_truth/combined_labels.json` |
| Aggregate reports | `data/reports/aggregate/` |
| Public masked reports | `data/reports/public/` |
| Local-only evidence | `data/_local/`, `data/reports/*_local/` |
