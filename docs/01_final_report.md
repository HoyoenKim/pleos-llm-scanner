# LLM 기반 디컴파일러 분석 및 PleOS 적용 방안 검토

## 2026-05-14 보충 — Codex multi-model cross-read

기존 보고서의 3차 검증은 **Claude Code 단일 모델 multi-perspective consensus**이다. 2026-05-14에 별도 보충 실험으로 **Codex 3-model cross-read**를 수행했다. 이 보충 실험은 기존 결과를 대체하지 않고, Claude Code baseline의 교차 검증 layer로만 해석한다.

실험 설정:

- 모델: `gpt-5.5`, `gpt-5.4`, `gpt-5.3-codex`
- 입력: `stage3_ensemble.json`의 기존 n=47 finding을 redacted model input으로 재구성
- 판정: 각 모델이 `report` 또는 `suppress`로 독립 재판정, Codex consensus는 2/3 이상 `report`
- 산출: `data/reports/aggregate/codex_multimodel_agreement.{md,json}`

핵심 결과:

| System | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Claude Code consensus | 37 | 0 | 9 | 1 | 1.000 | 0.974 | 0.987 |
| Codex `gpt-5.5` | 34 | 0 | 9 | 4 | 1.000 | 0.895 | 0.944 |
| Codex `gpt-5.4` | 28 | 0 | 9 | 10 | 1.000 | 0.737 | 0.849 |
| Codex `gpt-5.3-codex` | 25 | 0 | 9 | 13 | 1.000 | 0.658 | 0.794 |
| Codex 2/3 consensus | 29 | 0 | 9 | 9 | 1.000 | 0.763 | 0.866 |

Claude consensus와 Codex 2/3 consensus의 agreement는 83.0%, Cohen's kappa는 0.607이었다. `gpt-5.5` 단독은 agreement 93.6%, kappa 0.828로 가장 가까웠다.

결론: Codex multi-model은 FP를 추가하지 않았지만 recall이 낮아져 기존 Claude Code 3차 검증보다 강한 성능 근거가 되지는 않았다. 이 결과는 **multi-model 자체보다 evidence packaging과 prompt calibration이 더 중요하다**는 결론으로 반영한다. 최종 PPT에는 “multi-model 수행”이라고만 쓰지 않고, 반드시 **기존 Claude Code baseline + Codex 3-model cross-read**로 provenance를 분리해 표기한다.

## 자율주행연구프로젝트1 — 최종 보고서 v1.4 supplement

| 항목 | 내용 |
|---|---|
| 작성자 | 김호연 |
| 학기 | 2026-1 |
| 연계과제 | 현대자동차 계약학과 육성형 연구과제 — PleOS TARA 및 실차 보안 취약점 점검 |
| 작성일 | 2026-04-30 초안 → 2026-05-11 v1.0 (13주차) → 2026-05-11 v1.1 (14주차) → 2026-05-14 v1.2 (학기 외 A) → 2026-05-14 v1.3 (학기 외 B) → **2026-05-14 v1.4 보충본 (학기 외 A+B+C+D+E 완료)** |
| 버전 | **v1.4 supplement** (v1.3 통합본 + Codex `gpt-5.5` / `gpt-5.4` / `gpt-5.3-codex` cross-read n=47. Codex 2/3 consensus P 100.0% / R 76.3% / F1 86.6%, Claude Code baseline P 100.0% / R 97.4% / F1 98.7%. 결론: multi-model 자체보다 evidence packaging + prompt calibration 중요) |

---

## Notation & Glossary

본 보고서에서 자주 등장하는 약어 / finding ID / 단계 명명을 한 곳에 정리.

### Pipeline 단계 (Stage 0 / 1 / 2 / 3)

| Stage | 명명 | 역할 |
|---|---|---|
| **Stage 0** | Deobfuscation (preprocessing, optional) | 식별자 obfuscation score ≥ 0.7 클래스에 LLM 이름 복원 |
| **Stage 1** | Initial Detection | 키워드 grep 후 priority class 에 단일 LLM 1-pass 6 카테고리 탐지 |
| **Stage 2** | Contextual Verification | caller chain + manifest + regex rule + LLM 재독으로 후보 verdict (TP/FP/uncertain). AST rule 자동화는 Future Work |
| **Stage 3** | Single-model multi-perspective consensus | 동일 모델을 3개 시각 (공격자 / 방어자 / IVI 도메인 전문가) 으로 재질문하여 합의. ≥2/3 동의 = TP, ≥3/3 = strong TP |

> **PPT 계획서 표기 매핑**: PPT 의 "1차 / 2차 / 3차" 는 본 보고서의 **Stage 1 / Stage 2 / Stage 3** 와 동일. PPT 가설 수치 (1차 25% / 2차 12% / 3차 7%) 인용 시에만 PPT 표기 유지.

### 학기 작업 단계 (Phase A~E)

| Phase | 의미 |
|---|---|
| Phase A | 환경 구축 + 부트스트랩 (jadx, AVD 부팅, scaffold) |
| Phase B | Stage 1/2/3 LLM 검증 단계 적용 (자세히는 § 3) |
| Phase C | Ground truth 라벨링 + Precision / Recall / F1 측정 + Ablation |
| Phase D | AAOS / MASVS / TARA 매핑 + 사례 연구 + 통합 권고 + 일반화 평가 |
| Phase E | 발표 PPT + 라이브 데모 (본 보고서 범위 밖) |

### 한계 라벨 (§ 7 에서 사용)

| Label | 의미 |
|---|---|
| L1 | Native 코드 분석 불가 (Java-only 정적 분석 한계) — **학기 외 C 작업으로 부분 해소**: radare2 + `src/native/native_analyze.py` 로 R3.c.2 native sample n=4 정적 분석 (추가 vuln 0건). dynamic 행동 (Go runtime / JNI argument flow) 은 여전히 미관찰 — Frida hook (학기 외 D, script ready) 후속 |
| L2 | 표본 크기 (n=47 최종, R1.d.2~d.5 확장) — **McNemar exact p=0.0215 < α=0.05 통계적 유의 도달** (n=28 p=0.375 power 부족에서 진전, discordant b+c=10). v1.2 갱신 |
| L3 | 기존 본 실험은 Claude Code 단일 모델 multi-perspective consensus 로 수행. 2026-05-14 보충 실험으로 Codex 3-model cross-read를 n=47에 적용했으나, Codex consensus는 FP 0을 유지한 대신 recall이 낮아져 성능 우위 근거는 아님. |
| L4 | MASTG corpus의 hand-crafted 특성 (난독화 정확도는 upper-bound) |
| L5 | Stage 3 consensus의 MASTG 미평가 — 2026-04-30 해소됨 |
| L6 | ProGuard 활성 PleOS-customized APK 의 priority class 추출 yield 감소 (R1.d.5 maps 1 finding / callandmessage 비즈니스 패키지 2 클래스) — v1.2 신규. Stage 0 deobfuscation 통합 또는 manifest-only Stage 1 모드 권고. 학기 외 B(RAG) 가 finding_patterns_historical 로 부분 보조 |

### Finding ID 컨벤션

본 보고서의 모든 finding 은 `<APK 약어>-<번호>` 형식.

| Prefix | APK | 카테고리 |
|---|---|---|
| `vc-` | `ai.umos.vehiclecontrol` (PleOS) | 차량 제어 앱, system UID + 13 위험 권한 |
| `ssl-` | `ai.pleos.sync.syslog` (PleOS) | 시스템 로그 sync, INTERNET + 외부 송출 |
| `lmp-` | `ai.pleos.llm.model.provider` (PleOS) | 온디바이스 LLM 모델 게이트웨이 |
| `ucl1-` | UnCrackable-Level1 (OWASP MASTG) | hardcoded AES key 챌린지 |
| `ucl3-` | UnCrackable-Level3 (OWASP MASTG) | XOR-key 챌린지 |

핵심 finding 요약 (severity = stage1 기준, verdict = Stage 3 multi-perspective consensus 후):

| ID | Class | 카테고리 | Severity | Stage 3 합의 | 한 줄 |
|---|---|---|---|---|---|
| vc-1 / vc-2 | `HtmlWebViewKt` | network | HIGH/MEDIUM | FP | WebView setAllowFileAccess + loadUrl — OTA-trusted asset, 외부 진입 불가 |
| vc-3 / vc-4 | `AppPermissionManager` | permission | HIGH | FP | grant/revokeRuntimePermission — Compose Nav internal-only, 4중 차단 |
| **vc-5** | `GleoActionSender` | intent | HIGH (격상) | strong TP | implicit broadcast → IntentRouter chain. 차량 제어 명령 spoofing 가능 |
| **vc-6** | `VehicleBroadcastReceiver` | intent | HIGH | strong TP | exported + macAddress 미검증 → DB 주입 |
| vc-7 | `Broadcasts` | intent | LOW | TP | UnspecifiedRegisterReceiverFlag — API 34 hardening |
| **ssl-1 / ssl-5** | `SyncConfigsProvider` | hardcoded | HIGH | strong TP | `BuildConfig.IDENTIFIER` 를 KDF passphrase 로 사용 → 모든 device 동일 ECC 키 |
| ssl-2 | `AuthData` | hardcoded | HIGH | strong TP | Kotlin data class `toString()` 가 authenticatorToken 노출 → logcat 누출 |
| **ssl-3** | `CCGAuthenticator` | network | MEDIUM | strong TP | hardcoded prod endpoint + 패키지 내 pinning 부재 |
| **ssl-4** | `HMGAuthenticator$HmgUserInfo` | hardcoded | HIGH | TP (2/3) | PII (UUID/생년월일/이메일/이름) toString — emission 미확인이라 2/3 합의 |
| **ssl-6** | `SysLogService` | network | HIGH (격상) | strong TP | gRPC `.usePlaintext()` — 차량 syslog 평문 외부 송출 (MITM) |
| **lmp-1** | `PromptsContentProvider` | intent | HIGH | strong TP | exported ContentProvider 가 LLM system-prompt corpus 노출 |
| lmp-2 | `LLMModelProviderReceiver` | intent | MEDIUM | strong TP | exported receiver — 외부 앱이 GGUF 모델 파일 삭제 + process kill DoS |
| ucl1-1 | UnCrackable-Level1 | hardcoded | HIGH | strong TP | hardcoded AES key + ciphertext (canonical MASVS-CRYPTO-1) |
| ucl1-2 | UnCrackable-Level1 | (storage) | MEDIUM | strong TP | MASVS-STORAGE-2 |
| ucl1-3 | UnCrackable-Level1 | (logging) | LOW | TP (2/3) | logging hardening |
| ucl3-1 | UnCrackable-Level3 | hardcoded | HIGH | strong TP | XOR key hardcoded (2026-04-30 추가) |

전체 finding 별 정확한 (line, AAOS 매핑) 은 [`data/reports/aggregate/aaos_mapping_table.md`](../data/reports/aggregate/aaos_mapping_table.md) 참조.

---

## 0. 요약 (Executive Summary)

본 연구의 핵심 질문은 **자동차 IVI APK 보안 점검에서 LLM을 단독 탐지기가 아니라, deterministic triage와 도메인 검증 규칙 사이의 reasoning component로 사용할 때 실용적인 정적 분석 pipeline을 만들 수 있는가**이다.

이를 위해 PleOS 탑재 IVI APK에 대해 **다단계 LLM 검증 + 결정론적 룰 + 외부 GT 베이스라인**을 결합한 정적 분석 파이프라인을 설계·구현하였다. 실험은 PleOS Connect v2.0.5 에뮬레이터에서 추출한 207개 시스템 APK 중 보안 가치가 높은 3종 (`ai.umos.vehiclecontrol`, `ai.pleos.sync.syslog`, `ai.pleos.llm.model.provider`) 과 외부 OWASP MASTG corpus (UnCrackable-Level1/3)에 적용하였다.

단, 본 보고서의 정량값은 **combined corpus n=47 (PleOS-customized 30 + OWASP MASTG 4 + InsecureBankv2 9 + AOSP-derived 4) 에 대한 측정 결과**이다. 학기 외 R1.d.5 표본 확장으로 n=19 초기 feasibility → n=47 까지 도달했으나, 여전히 보안 가치 기반으로 선정된 corpus subset 한정 측정이다. 따라서 아래 수치는 일반화 성능이라기보다, 현재 corpus에서 관찰된 pipeline 동작과 한계를 보여주는 측정값으로 해석해야 한다.

### 핵심 측정값 (combined n=47 = PleOS-customized 30 + OWASP MASTG 4 + InsecureBankv2 9 + AOSP-derived 4)

| 지표 | PPT 가설 / 목표 | 측정값 (n=47) | 해석 |
|---|---|---|---|
| 1차 후보 기준 FP 비율 (Stage 1) | 25% | **19.1%** | 95% CI [8.5%, 29.8%]. 가설 25% 가 mean 위에 위치 — 충족. n=37→n=47 확장 시 R1.d.5 FP 3건 추가로 +2.9%p 후퇴 (정직 기록). |
| 3차 후보 기준 FP 비율 (Stage 3 ≥2/3) | 7% | **0%** (n=47 갱신) | Stage 3 ensemble 47/47 적용. Stage 3 reported 37건 중 FP 0건. 정확도 ceiling 유지. |
| Precision (Stage 1) | 0.93 (Full Pipeline 가설) | **0.809** | 95% CI [0.702, 0.915]. n=37 → n=47 확장에 따라 lower bound 73.0% → 70.2% (-2.8%p) — R1.d.5 FP 3건 (am-4, amb-4, amb-5) 영향. |
| Precision (Stage 3 ≥2/3, n=47) | — | **1.00** | 37 reported 중 FP 0건 — 학기 외 R1.d.2~d.5 신규 19건 ensemble 평가 후에도 ceiling 유지. |
| F1 (Stage 1) | — | **0.894** | 95% CI [0.825, 0.956]. n=37 0.911 대비 -0.017. |
| F1 (Stage 3 ≥2/3, n=47) | — | **0.987** | Stage 3 ≥2/3 Recall = 37/38 = 97.4% (FN 1건 vc-7), Precision = 100% |
| Recall (Stage 3 ≥2/3, n=47) | — | **97.4%** | FN 1건 (vc-7 LOW hardening 만 1/3 합의로 강등 — n=28과 동일). |
| **★ McNemar paired (Stage 1 vs Stage 3, n=47)** | — | **chi_sq=6.400 / p_chi=0.0114 / p_exact=0.0215** | **α=0.05 통계적 유의 첫 도달**. n=28 (p=0.375 power 부족)에서 진전. contingency a=37 / b=1 / c=9 / d=0 → discordant b+c=10. effect size 양수 (Stage 3 net +8건). RQ1의 핵심 정량 contribution. |
| 분석 대상 축소율 | 30~40% | **99.49%** + 추가 corpus 6종 (usb.handler 14→5 + statementservice 30→5 + account 5,377→5 + appmarket 3,589→5 + ambientai 16k→5 + maps ProGuard L6) | triage efficiency 지표. 제외 class의 full-audit recall 은 미검증. |
| 난독화 이름 복원 정확도 (hand-crafted) | 78% (8주차) | **100%** (UnCrackable n=17 exact) | hand-crafted MASTG corpus 에서의 upper-bound 성격. |
| 난독화 plausibility — real-world (R4 n=6) | — | NewPipe v0.27.6 ProGuard 활성 **GOOD+ 67%** (EXCELLENT 2 / GOOD 2 / PARTIAL 1 / POOR 1) | hand-crafted 100% upper-bound 대비 real-world 67%. EXCELLENT 2건 = DateTimeFormatterBuilder / ConcurrentHashMap.TreeBin (Java standard API 1:1 매칭). |
| Native binary 분석 (R3.c, libgojni.so 15 MB Go) | — | **0 추가 vuln (transport secure)** | Go crypto/tls + x509 verification 활성, hardcoded endpoint 0건. Java BuildConfig 가 single source of truth (ssl-3/5/6 와 정합). 한계: static-only, dynamic 행동 미관찰 |

### **PleOS-customized vs AOSP-derived 정밀도 분리 (n=47 origin breakdown)**

| Origin | n | TP | FP | Precision | RQ implication |
|---|---:|---:|---:|---:|---|
| PleOS-customized (`ai.umos.*`, `ai.pleos.*`) | **30** | 23 | 7 | **76.7%** | R1.d.5 추가 (+10 finding: TP 7 / FP 3). n=20 80.0% → n=30 76.7% (-3.3%p). FP 3건 = am-4 (gleo navigation), amb-4 (explicit broadcast), amb-5 (signature gate). **단 systematic hardcoded credential 패턴 4 APK 공통 발견** (acc-4 + am-3 + amb-1/2). |
| AOSP-derived (`android.car.usb.handler`, `com.android.statementservice`) | 4 | 2 | 2 | **50.0%** | AOSP/AAOS 표준 system component — OS/framework-level mitigation 으로 Stage 2 FP 다수. 변경 없음. |
| External vuln corpus (MASTG + InsecureBankv2) | 13 | 13 | 0 | **100.0%** | 의도된 vuln corpus — Stage 1 detect rule 의 ceiling. 변경 없음. |

핵심 finding: PleOS 적용 시 Stage 1 만으로는 부족. **AOSP-derived 컴포넌트는 Stage 2 caller-chain + manifest 분석이 essential** (FP 절반이 OS/framework-level mitigation 으로 차단되는 case). PleOS-customized 자체 코드에 분석 자원 집중 권고. **R1.d.5 추가 발견**: hardcoded credential systematic pattern — `ai.pleos.playground.account` (acc-4) + `ai.umos.appmarket` (am-3) 가 동일 HMG OAuth client_secret 사용, `ai.umos.ambientai` (amb-1/2) 가 OpenAI API key 하드코딩. 4 APK 공통 — single APK leak 이 다른 PleOS APK 의 credential domain 도 함께 노출.

> **Metric note**: 본 보고서의 ‘오탐률’은 전체 non-vulnerable code element 대비 false positive rate가 아니라, LLM이 report한 finding 후보 중 FP의 비율인 `FP / (TP + FP)`로 정의한다. 엄밀히는 false discovery rate에 가깝다.

> **Update history**:
>
> - 2026-04-30 초안 n=18 (Stage 1 F1 0.875 / Stage 3 ≥2/3 F1 0.952).
> - 2026-04-30 같은 날 n=19 갱신: 외부 corpus (UnCrackable-Level1) 의 Stage 3 multi-perspective consensus 평가 적용 + UnCrackable-Level3 sample 추가 (ucl3-1, hardcoded XOR key, HIGH). Stage 1 F1 0.882 / Stage 3 ≥2/3 F1 0.966.
> - 2026-05-06 R1.b bootstrap CI 도입. n=19 corpus 의 95% CI 측정으로 표본 작음 약점 정량화.
> - **2026-05-07 R1.d 표본 확장 — n=28**. 외부 의도적 취약 corpus InsecureBankv2 도입 (9 finding 모두 TP). Stage 1 Precision 78.9% → 85.7%, F1 0.882 → 0.923. CI 폭 약 1/3 감소.
> - **2026-05-08 Stage 3 ensemble 을 InsecureBankv2 까지 확장 + NewPipe entropy 측정**. 합의 ≥2/3 의 corpus 가 n=19 → n=28 으로 동일하게 확장 — Stage 3 ≥2/3 F1 0.966 → **0.979**. 동시에 R4 첫 측정 — NewPipe (real-world ProGuard 활성 OSS) HIGH 난독화 1.7% (hand-crafted MASTG 40~50% 와 PleOS 0.2~0.4% 의 사이).
> - **2026-05-11 12주차 작업 — R4 NewPipe sample 확장 n=3 → n=6**. 추가 sample 3종 (nio attr builder / time formatter / CHM tree bin) Stage 0 LLM rename. C1188w → DateTimeFormatterBuilder (19/27 method match), C1290q → ConcurrentHashMap.TreeBin (9/9 match) — 첫 EXCELLENT plausibility 측정. Plausibility 분포 EXCELLENT 2 / GOOD 2 / PARTIAL 1 / POOR 1 = **GOOD+ 67% (n=3 33% 대비 +33%p)**.
> - **2026-05-11 12주차 작업 — R1.d.2 표본 확장 n=28 → n=31**. PleOS Connect 시스템 APK 중 AAOS-derived `android.car.usb.handler` (system UID + MANAGE_USB + 14 클래스) 분석. 3 finding (2 TP / 1 FP): usb-1 MD5 weak hash (TP), usb-2 grantPermission flow (FP), usb-3 Build.getSerial PII (TP). Manifest 확인 — 모든 components exported=false.
> - **2026-05-11 13주차 작업 — R1.d.3 표본 확장 n=31 → n=32**. PleOS Connect 시스템 APK 중 AOSP-derived `com.android.statementservice` (Digital Asset Links / app verification, 30+ 클래스). UrlFetcher / StatementRetriever / DomainVerifier — 모두 매우 견고한 security design (HTTPS only, default trust store, recursion guard, cert fingerprint 비교). 1 finding (ss-1, BootCompletedReceiver exported=true, BOOT_COMPLETED protected broadcast 라 FP). **n=32 결과**: Stage 1 P 81.2% / F1 0.896 / FP rate 18.8%. 95% CI Precision [68.8%, 93.8%].
> - **2026-05-11 13주차 신규 finding — PleOS-customized vs AOSP-derived 정밀도 분리** (§ 0 표 참조). PleOS-customized 15 finding P 73.3% / AOSP-derived 4 finding P 50.0% / External vuln corpus 13 finding P 100%. RQ1 새 implication: AOSP-derived 컴포넌트의 FP 절반이 OS/framework-level mitigation 으로 차단되는 case — Stage 2 caller-chain + manifest 분석이 essential.
> - **2026-05-11 14주차 v1.1 — Future Work 5종 partial-implementation 통합** ([`docs/08_future_work_implementations.md`](08_future_work_implementations.md) 참조):
>   - **R1.d.4 표본 확장 n=32 → n=37** (PleOS-customized `ai.pleos.playground.account` auth/SSO APK 5,377 클래스 — priority 5 클래스 stage1 분석 5 finding 모두 TP: acc-1 cleartext HTTP / acc-2 reflection non-SDK / acc-3 LoginActivity WebView JS / acc-4 SsoActivity client_secret intent extra / acc-5 SsoActivity WebView). PleOS-customized origin precision 73.3% → **80.0%** (+6.7%p).
>   - **R3.c (radare2 native binary 분석)** — `data/_local/tools/r2/radare2-6.1.4-w64/bin/radare2.exe` 통합 후 `libgojni.so` (15 MB Go binary, ai.pleos.sync.syslog) 정적 분석. Result: **transport secure (Go crypto/tls + x509 verification 활성), hardcoded endpoint 0건, 추가 vuln 0건**. R3.a corpus-level + R3.c sample-level 두 axis 완성. Static-only 한계 정직 명시.
>   - **Multi-model ensemble 보충 실행** — Codex `gpt-5.5` / `gpt-5.4` / `gpt-5.3-codex` cross-read n=47 완료. Claude vs Codex consensus agreement 83.0%, κ=0.607. Codex 2/3 consensus F1 86.6%로 기존 Claude Code 3차 검증보다 낮아, prompt/evidence calibration 중요성으로 결론 정정.
>   - **동적 분석 (LangGraph agent loop) design** — Frida hook + Static→Dynamic feedback loop 설계 + vc-5 GleoActionSender Frida script 예시. 본 학기 진행률 15%.
>   - **RAG 도메인 지식 주입 design** — AAOS / MASVS / TARA template vector DB schema 설계 + RAG-enhanced Stage 1 prompt 흐름. 본 학기 진행률 10%.
>   - **n=37 통계 갱신** (bootstrap 1000 iter, seed=42): Stage 1 P **83.8%** / F1 **0.911** / FP rate **16.2%**. 95% CI Precision **[73.0%, 94.6%]** (n=19 [57.9%, 94.7%] 에서 lower bound +15.1%p). CI 폭 -15.2%p (본 학기 최대 좁힘).
> - **★ 2026-05-14 v1.2 — 학기 외 A 작업 100% 완료 (R1.d.5 + Stage 3 ensemble 19건 + McNemar 통계적 유의 첫 도달)**:
>   - **R1.d.5 표본 확장 n=37 → n=47** — PleOS-customized 3 APK 추가 분석. **ai.umos.appmarket** 4 finding (am-1 Suggestions ContentProvider permission="" intent injection HIGH / am-2 DownloadService implicit broadcast MEDIUM / **am-3 hardcoded HMG OAuth client_secret HIGH** — acc-4와 동일 secret cross-APK / am-4 MainActivity gleo navigation FP). **ai.umos.ambientai** 5 finding incl. **CRITICAL amb-1 LlmHandler.java:218 hardcoded OpenAI API key `sk-pxxa…`** + amb-2 same key in LlmHandlerForTest (release-shipped test code) 둘 다 HIGH / amb-3 SettingsActivity assistant:// deep-link MEDIUM / amb-4 explicit broadcast FP / amb-5 BIND_VOICE_INTERACTION signature gate FP. **ai.umos.maps** 1 finding (map-1 NaviContentProvider exported PII MEDIUM) — **ProGuard 활성 priority class 축소 (L6 신규 한계)**. n=47 = TP 38 / FP 9.
>   - **Systematic hardcoded credential 4 APK 공통 패턴 발견** (학기 외 가장 큰 정성 finding): acc-4 (account SsoActivity user-client-secret via Intent extra) + am-3 (appmarket HMG client_secret 동일 값) + amb-1 (ambientai OpenAI API key production) + amb-2 (test handler same OpenAI key). single APK leak 이 PleOS-customized credential domain 의 cross-APK 단일 leak point 로 작동.
>   - **amb-narr-1 외부 LLM API 정책 위반 발견** — ai.umos.ambientai 의 LlmHandler.callOpenaiChatgptApi + com.aallam.openai.client.* SDK 가 api.openai.com 호출. 본 프로젝트 환경 정책 ('외부 LLM API 미사용', CLAUDE.md ## 환경 제약) 과 충돌. AiAssistantService 의 mic + READ_SMS + READ_CONTACTS PII 가 외부 LLM 으로 전송 가능 (independent of amb-1/2 credential issue).
>   - **eval.py n=47 bootstrap CI 재측정** (1000 iter, seed=42): Stage 1 P **80.9%** / F1 **0.894** / FP rate **19.1%**. 95% CI Precision **[70.2%, 91.5%]** / F1 **[82.5%, 95.6%]** / FP rate **[8.5%, 29.8%]**.
>   - **Stage 3 ensemble 19건 적용 (R1.d.2/d.3/d.4/d.5 신규 모두)** — attacker / defender / domain_expert 3 perspective. 결과: Strong TP (3/3) 14건 (usb-1/3, acc-1~5, am-1/2/3, amb-1/2/3, map-1) / Uncertain (1/3) 3건 (usb-2, am-4, amb-5) / Clean (0/3) 2건 (ss-1, amb-4). 결합 n=47 distribution: strong_TP 33 / TP 4 / uncertain 8 / clean 2. **Stage 3 ≥2/3: P 100% / Recall 37/38 = 97.4% / F1 98.7%**.
>   - **★ McNemar paired test (n=47) — 통계적 유의 첫 도달**: contingency a=37 / b=1 (vc-7 GT TP but Stage 3 unreported, defender-only 1/3) / c=9 (all 9 FPs cleared by Stage 3) / d=0. chi_sq=6.400 / p_chi=0.0114 / **p_exact=0.0215 < α=0.05**. n=28 (p=0.375 power 부족) 에서 진전 — discordant b+c=10 으로 power 확보, effect size 양수 (Stage 3 net +8건). 본 학기 외 작업의 **가장 큰 RQ1 정량 contribution**.
>   - **L6 한계 신규 추가** — ProGuard 활성 PleOS-customized APK 의 priority class 추출 yield 감소 (maps 1 finding / callandmessage R1.d.3 비즈니스 패키지 2 클래스). Stage 0 deobfuscation 통합 또는 manifest-only Stage 1 모드 권고. 학기 외 B(RAG)/C(L1 native) 후속.
> - **★ 2026-05-14 v1.3 — 학기 외 B 작업 100% 완료 (RAG 도메인 지식 주입 + Chroma local + intrinsic ablation)**:
>   - **환경 정책 호환 설계** — 외부 LLM/embedding API 호출 0건. `chromadb 1.5.9` + `sentence-transformers 5.5.0` + `torch 2.12.0` (CPU). Embedding model `sentence-transformers/all-MiniLM-L6-v2` (22M params, CPU 추론). HuggingFace 모델은 1회 cache 후 offline 추론.
>   - **Chroma 4 collection 빌드** (`data/_local/rag_db/chroma/`, 총 158 chunks): `aaos_guidelines` 6 (configs/aaos_mapping.yaml 의 6 category × AAOS § + MASVS + TARA), `masvs_controls` **99** (OWASP MASTG 41 docs H2-sectioned chunks, 영어 ~2000 char/chunk), `tara_templates` 6 (yaml + tara_artifact markdown), `finding_patterns_historical` 47 (combined GT 의 모든 finding × code excerpt + rationale).
>   - **`src/rag/{build_index,retrieve,ablation}.py` + `configs/prompts/stage1_detect_rag.md`** — RAG-enhanced Stage 1 prompt 는 retrieve.py 가 4 collection 각각 top-k (default 3) 를 가져와 prompt 에 inject + AAOS § / MASVS controls 인용 강제 + historical TP/FP pattern 으로 confidence calibration (TP nearest → +0.1, FP nearest → -0.2). [`src/rag/`](../src/rag/) 모듈 + [`configs/prompts/stage1_detect_rag.md`](../configs/prompts/stage1_detect_rag.md).
>   - **★ Intrinsic ablation 측정 (n=47, `data/reports/rag_local/rag_ablation.{md,json}`)**: (1) **NN verdict propagation 40/47 = 85.1%** — historical 가장 가까운 finding (self 제외) 의 GT verdict 가 query GT verdict 와 일치. TP queries 38건 중 **36 match / 2 mismatch**, FP queries 9건 중 **4 match / 5 mismatch**. 임베딩 모델이 TP 계열 anti-pattern은 강하게 묶지만 FP 억제에는 아직 보완이 필요하다는 신호다. (2) **AAOS category alignment 40/47 = 85.1%** — RAG top-1 의 6-category 라벨 (crypto/network/permission/intent/hardcoded/reflection_dynamic) 이 GT stage1_category 와 일치. 카테고리별 정확도: `hardcoded` 9/11, `intent` 15/18, `network` 8/9, `crypto` 5/5, `permission` 2/3, `reflection_dynamic` 1/1. (3) **MASVS area match 11/47 = 23.4%** — MASTG Document chunking 이 너무 거칠어서 (H2 단위 ~2000 char) MASVS_CATEGORY meta 와 query 의 semantic alignment 가 약함. **Sub-task**: chunking 을 H3 + sliding-window 로 fine-grained 화하면 개선 예상.
>   - **End-to-end prompted-LLM ablation 은 v1.4 supplement 이후 후속** — 본 측정은 intrinsic retrieval quality (embedding 모델이 anti-pattern 별로 정렬하는가). with-RAG vs without-RAG Stage 1 prompted-LLM 응답 비교 (FP rate 변화 측정) 는 별도 work-load 로 분리. NN 85.1% 가 calibration 의 ceiling 을 시사하므로 prompted ablation 의 기대 효과는 +5~10%p Precision (현 80.9% → 85~90% range) 으로 보수적 추정.
>   - **본 학기 외 B 작업의 RQ1/RQ2/RQ3/RQ4 implication**: RQ1 — RAG calibration 으로 추가 Precision 향상 여지. RQ2 — multi-perspective consensus 의 calibration 보조 가능 (defender / domain_expert prompt 에 retrieved AAOS / MASVS 첨부). RQ3 — `masvs_controls` 의 native binary 관련 chunks (RASP / anti-tamper) 가 native-bound 분석의 도메인 지식 inject 가능. RQ4 — 난독화 corpus 의 `finding_patterns_historical` 이 deobfuscation accuracy 의 calibration 보조.
> - **★ 2026-05-14 v1.3 — 학기 외 C 작업 100% 완료 (R3.c.2 native sample-level n=4)**:
>   - **`src/native/native_analyze.py`** — Python regex strings 분석 (Windows / Git Bash binutils 부재 우회). URL noise filter + sk-prefix + AKIA + PEM + UUID + api_key/bearer + TLS keyword 검색.
>   - **3 .so 추가 추출 + 분석**: `caas/libgojni.so` (15MB, Go) + `caas/libairspeech_stt.so` (4.4MB, NDK r25b 음성 인식) + `navigation/libmapbox-maps.so` (9.3MB, Mapbox SDK).
>   - **R3.c.2 sample-level 결과**: **n=4 모두 추가 vuln 0건**. sync.syslog/libgojni 와 caas/libgojni 는 size + ELF header 동일 (공유 Go binary). caas/libgojni 의 UUID `258EAFA5-…` standalone string (Go embedded constant 추정). libairspeech_stt / libmapbox-maps 모두 hardcoded URL / secret 0건 — endpoint 가 Java BuildConfig 또는 SDK config 에서 inject 되는 패턴.
>   - **Ghidra Go plugin 도입 deferred** — function-naming recovery 는 별도 workload, frida-server 환경과 합쳐 학기 외 후속.
>   - **R3 두 axis 종합**: corpus-level R3.a 10.6% + sample-level R3.c.2 **n=4 / 0 additional vulns** — Java/native transport security 일관성의 정량 증거.
>   - 산출: `data/reports/native_local/native_r3c2_20260514.md` + `data/reports/native_local/native_r3c2_raw.json`.
> - **★ 2026-05-14 v1.3 — 학기 외 D 작업 100% 완료 (Dynamic state machine + 5 Frida hook scripts)**:
>   - **환경 정책 호환 설계** — `langgraph 1.2.0` + `frida 17.9.8` + `frida-tools 14.8.2` 설치 (외부 LLM/embedding API 호출 0건 정책 유지). **LangGraph state graph 는 deterministic transition 만, LLM node 미등록** — LLM 분석은 Claude Code 세션이 외부 driver 로 유지.
>   - **`src/dynamic/state_machine.py`** — receive_finding → stage1_classify → stage2_static_verify (Stage 2 rule dict for vc-5/6, ssl-2/5, lmp-1) → conditional[frida_hook / stage3_correlate] → END. 5 deterministic node. 검증: vc-5 입력 → TP_static_only (runtime observation 부재 시), runtime_observation provided → strong_TP_dynamic.
>   - **`src/dynamic/hooks/` 5 Frida hook scripts** — (1) vc-5 GleoActionSender (ContextWrapper.sendBroadcast wrap + stack trace 검사) / (2) vc-6 VehicleBroadcastReceiver (onReceive + Binder.getCallingUid 로 외부 caller 검증) / (3) ssl-2 AuthData toString + Log.* 호출에서 token emission 확인 / (4) ssl-5 BuildConfig.IDENTIFIER 캡처 + ECCCrypto.deriveKey passphrase 일치 검증 / (5) lmp-1 PromptsContentProvider.query + calling UID/row_count.
>   - **`docs/03_case_studies.md` Case 6~10 dynamic 추가** — 각 case 에 hook script + verdict transition table. Static-only vs Static+Dynamic 비교 표.
>   - **AVD 실제 실행은 환경 의존 후속** — PleOS Connect AVD userdebug build + frida-server-arm64 (API 34) 또는 frida-gadget injection (user build 우회). Script + state machine ready, runtime capture 만 environment-dependent step.
> - **★ 2026-05-14 v1.4 supplement — Codex multi-model cross-read 추가 완료**: 기존 A R1.d.5 / B RAG / C L1 native / D Dynamic 완료본에 더해 Multi-model ensemble도 Codex 3-model 방식으로 실제 실행. 결과는 성능 우위가 아니라 recall 하락을 보였으므로, 최종 메시지는 “모델 수 증가”보다 “evidence packaging + prompt calibration”의 중요성으로 정정.

### 핵심 산출물

1. **GitHub public repo**: [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT)
2. **GT corpus**: `data/ground_truth/combined_labels.json` (n=47 = PleOS-customized 30 + MASTG 4 + InsecureBankv2 9 + AOSP-derived 4)
3. **AAOS / MASVS / TARA 매핑 표**: `data/reports/aggregate/aaos_mapping_table.{md,json}`
4. **TARA 시나리오 + Risk Matrix**: `data/reports/aggregate/tara_artifact.{md,json}`
5. **사례 연구 10건**: `docs/03_case_studies.md` (정적 5건 + 학기 외 D Dynamic 5건)
6. **6개 시각화 차트**: `data/viz/01~06_*.png`
7. **학기 외 산출물**: `src/native/native_analyze.py` (C) + `src/rag/` 4 모듈 + `configs/prompts/stage1_detect_rag.md` (B) + `src/dynamic/state_machine.py` + `src/dynamic/hooks/` 5 Frida scripts (D) + `docs/08_future_work_implementations.md`

## 1. 연구 배경 및 목표

### 1.1 배경

PleOS는 현대자동차 그룹의 IVI 플랫폼이며, PleOS Connect v2.0.5는 Android 14 기반의
자체 변형 (AAOS-like)이다. IVI는 차량 안전과 사용자 자격증명, 위치/PII 데이터를
다루며 OTA 업데이트로 빈번히 갱신되므로 정적 분석 기반 보안 점검의 실용적
가치가 크다.

본 연구는 LLM (Claude Code, Opus 4.7)을 분석 엔진으로 하여 **APK → 디컴파일 →
키워드 → LLM 다단계 → AAOS / TARA 매핑** 파이프라인을 만들고, 그 정확도를
self-labeled GT + OWASP MASTG 외부 GT로 초기 정량 평가한다. 여기서 LLM은
취약점을 단독 판정하는 black-box detector가 아니라, 키워드 기반 triage와 caller/manifest 기반
검증 사이에서 reasoning을 수행하는 component로 사용한다.

### 1.2 목표 (PPT 계획서 기준)

| # | 목표 |
|---|---|
| G1 | 디컴파일러 도구 비교 + 환경 구축 (jadx 1순위) |
| G2 | 키워드 기반 우선순위 큐 + 분석 대상 축소 30-40% |
| G3 | LLM 다단계 검증 (1차 → 2차 → 3차 = Stage 1 → 2 → 3) — reported finding 기준 FP 비율 25% → 12% → 7% |
| G4 | 난독화 코드 처리 (40% → 78% 정확도). 단, hand-crafted corpus와 real-world corpus를 구분 |
| G5 | AAOS 보안 가이드라인 매핑 표 |
| G6 | TARA 산출물 자동 생성 |
| G7 | 사례 연구 5건 |
| G8 | OWASP MASVS-MASTG 베이스라인 비교 |
| G9 | 일반화 평가 (QNX / Linux IVI) |

### 1.3 환경 제약

| 제약 | 영향 / 대응 |
|---|---|
| 로컬 GPU 없음 | 로컬 LLM 사용 불가 → Claude Code만 사용 |
| 외부 유료 API 없음 | OpenAI 직접 호출 코드 X → Claude Code 인터랙티브 세션 |
| 실차 접근 불가 | PleOS Connect 에뮬레이터 + ADB |
| 계약과제 IP 보호 | APK / 디컴파일 결과 / 보고서 비공개, 파이프라인 코드만 MIT |
| 단일 모델 세션 | Multi-LLM ensemble은 주장하지 않고, **단일 모델 multi-perspective consensus**로 범위를 한정 |

---

## 2. 방법론

### 2.1 파이프라인 구조

```
APK
 └─ scripts/apk/decompile.sh (jadx 1.5.5 --deobf)
     └─ data/_local/decompiled/<apk>/sources/...
         └─ src/deobf/entropy.py (Shannon entropy)
             └─ HIGH 난독화? → configs/prompts/stage0_deobfuscate.md (LLM 이름 복원)
         └─ configs/keywords.yaml grep (priority queue)
             └─ Stage 1 LLM (configs/prompts/stage1_detect.md)
                 → finding 후보 (JSON schema 강제, configs/result_schema.json)
                 └─ Stage 2 caller/manifest/regex 검증 (AST 자동화는 Future Work)
                     └─ Stage 3 single-model multi-perspective consensus
                         (configs/prompts/stage3_attacker.md
                        + stage3_defender.md
                        + stage3_domain_expert.md
                        + stage3_consensus.md)
                         └─ src/mapping/aaos_map.py + src/mapping/tara_generate.py
                             → data/reports/per_apk_local/<apk>_<DATE>.{md,json}
                             → data/reports/aggregate/aaos_mapping_table_<DATE>.md
                             → data/reports/aggregate/tara_artifact_<DATE>.md
```

### 2.2 키워드 카테고리 (`configs/keywords.yaml`)

6 카테고리 — crypto / network / permission / intent / hardcoded / reflection_dynamic.
각 카테고리는 regex 패턴 + 기본 severity를 가진다.

### 2.3 다단계 LLM 검증

- **Stage 1**: 1-pass 키워드 + LLM 분석. 출력 = JSON-schema 강제 finding 객체.
- **Stage 2**: caller chain + manifest + regex rule 기반 검증. AST rule은 설계에는 포함되어 있으나 본 보고서 범위에서는 자동화 범위 밖이며, 일부 확인은 수동/LLM 재독으로 보완한다.
- **Stage 2.b**: deep-link audit (Compose Nav route + manifest URI + IntentRouter binding의 3-축 정합성).
- **Stage 3**: 동일 모델 (Opus 4.7)을 다른 시각 3종 (attacker / defender / domain_expert) 으로 재질문하는 **single-model multi-perspective consensus**. ≥2/3 동의 = TP, ≥3/3 = strong TP.

> 본 보고서에서는 Stage 3를 multi-LLM ensemble로 주장하지 않는다. 외부 유료 API와 복수 모델 세션이 없는 환경 제약 때문에, 단일 모델을 여러 보안 관점으로 재질문하는 self-consistency 방식으로 범위를 한정한다.

### 2.4 평가 프레임워크

- **GT 라벨**: `data/ground_truth/combined_labels.json` (**combined n=47** = PleOS self 15 + MASTG 4 + InsecureBankv2 9 + R1.d.2~d.5 AOSP-derived 4 + PleOS-customized 15). 초기 baseline 은 `self_labels.json` (n=15 PleOS) + `mastg/*.labels.json` (n=4 MASTG).
- **측정 코드**: `src/evaluation/eval.py` (Precision / Recall / F1 + bootstrap CI) + `src/evaluation/ablation.py` (A 변형 — stage 1/2/3, B 변형 — 합의 임계 1/3-2/3-3/3) + `scripts/research/research_r1c_mcnemar.py` (paired McNemar).
- **시각화**: `src/viz/plot_metrics.py` — 6 차트 (PNG). 차트 01~05 는 combined n=47 재생성 (2026-05-14), 06 은 obfuscation corpus live.

#### Metric 정의

| 용어 | 본 보고서에서의 정의 |
|---|---|
| TP | Stage output finding이 GT vulnerable finding과 동일한 source location 또는 동일한 weakness class / data-flow evidence로 매칭되는 경우 |
| FP | Stage output finding이 GT에서 non-issue, unreachable, externally inaccessible, 또는 보안 영향이 불충분한 것으로 판정된 경우 |
| FN | GT vulnerable finding이 해당 stage output에서 누락된 경우 |
| Precision | `TP / (TP + FP)` |
| Recall | `TP / (TP + FN)` |
| F1 | `2 * Precision * Recall / (Precision + Recall)` |
| 후보 기준 FP 비율 | `FP / (TP + FP)`. 일반적인 전체 negative 대비 FPR이 아니라 reported finding 기준 false discovery rate 성격 |

#### GT 독립성 caveat

PleOS self-label은 실제 도메인 특화 finding을 포함한다는 장점이 있지만, 연구자가 직접 라벨링했기 때문에 evaluator bias 가능성이 있다. 이를 완화하기 위해 OWASP MASTG (n=4) + InsecureBankv2 (n=9, 의도된 vuln corpus) + AOSP-derived 시스템 component (n=4) 를 추가해 **combined n=47, 7 corpus origin** 으로 확장했고, External vuln corpus 의 Precision 100% 가 Stage 1 detect rule 의 ceiling 을 외부 정답으로 검증한다. 그럼에도 PleOS-customized self-label 의존이 남아 있으므로, 외부 라벨러 검증은 Future Work 로 남긴다.

---

## 3. 실험 결과

### 3.1 분석 대상 축소율 / triage reduction (G2)

VehicleControl APK 기준:
- 디컴파일 결과: **1,765 Java files** (`ai/umos` + `ai/pleos`)
- 키워드 매치 후 priority class: **9개**
- triage reduction: **99.49%** (1,765 → 9 priority class)

이 값은 **분석 효율성 지표**이다. 즉, 사람이 우선적으로 검토해야 할 class 수를 크게 줄였다는 의미이며, 제외된 1,756개 class에 취약점이 없음을 보장하는 full-audit recall 지표는 아니다. Stage 2 caller 추적 시 priority 9개 외부의 caller/callee가 추가로 분석될 수 있으며, 최종 v1.0에서는 일부 APK에 대해 broader static scanner 또는 manual audit과 비교해 missed finding 여부를 별도 확인할 필요가 있다.

### 3.2 Stage 1 / Stage 3 후보 기준 FP 비율 (G3) — combined n=47

| 단계 | n | TP | FP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Stage 1 (PleOS-only) | 15 | 11 | 4 | 73.3% | 100% | 0.846 |
| Stage 1 (combined, 2026-05-06) | 19 | 15 | 4 | 78.9% | 100% | 0.882 |
| Stage 1 (combined, 2026-05-07) | 28 | 24 | 4 | 85.7% | 100% | 0.923 |
| Stage 1 (combined, 2026-05-11 R1.d.4) | 37 | 31 | 6 | 83.8% | 100% | 0.911 |
| **Stage 1 (combined, 2026-05-14 R1.d.5)** | **47** | **38** | **9** | **80.9%** | **100%** | **0.894** |
| Stage 1 (MASTG-only) | 4 | 4 | 0 | 100% | 100% | — |
| Stage 1 (InsecureBankv2-only) | 9 | 9 | 0 | 100% | 100% | — |
| Stage 3 ≥2/3 (combined, 2026-04-30) | 19 | 14 | 0 | 100% | 90.9% | 0.952 |
| Stage 3 ≥2/3 (combined, 2026-05-08) | 28 | 23 | 0 | 100% | 95.8% | 0.979 |
| **Stage 3 ≥2/3 (combined, 2026-05-14)** | **47** | **37** | **0** | **100%** | **97.4%** | **0.987** |
| Stage 3 ≥3/3 (combined, 2026-05-14) | 47 | 33 | 0 | 100% | 86.8% | 0.930 |

**핵심 해석** (n=47, 학기 외 A 작업):
- Stage 1 의 Precision/F1 은 표본이 19 → 28 → 37 → 47 로 늘면서 78.9% → 85.7% → 83.8% → **80.9%** 로 변동. n=37 → n=47 에서 R1.d.5 의 신규 FP 3건 (am-4 gleo navigation / amb-4 explicit broadcast / amb-5 signature gate) 이 추가되어 -2.9%p 후퇴 — 정직 기록. F1 0.894 (95% CI [0.825, 0.956]).
- Stage 3 ≥2/3 consensus 에서는 corpus 기준 reported FP **0 건 유지** (n=19 → n=47 모든 확장에서 불변). 학기 외 Stage 3 ensemble 을 R1.d.2~d.5 신규 19건에 적용 — 9 FP 모두 uncertain/clean 으로 강등, strong TP 33 / TP 4. Recall 37/38 = **97.4%**, 유일한 FN 은 vc-7 (LOW hardening, 1/3 합의로 강등).
- **합의 ≥2/3 가 default threshold 로 가장 안정적** (F1 0.987 > ≥3/3 의 0.930). ≥3/3 은 strong TP 33건만 채택해 Recall 손실 (86.8%).
- **★ McNemar paired test (n=47)**: Stage 1 → Stage 3 향상이 **α=0.05 기준 통계적으로 유의** (p_exact=0.0215, χ²=6.400) — 본 학기 외 작업의 핵심 정량 contribution, 상세는 § 3.6.5.

### 3.3 Ablation (combined n=19 시점)

> 본 절의 ablation 표는 n=19 시점의 측정이다. 학기 외 A 작업으로 corpus 가 n=47 로 확장된 후의 Stage 1 / Stage 3 종합 수치는 § 3.2 표 + § 3.6.5 McNemar 참조. 단계별 효과의 상대 패턴 (Stage 1 → 2 → 3 의 F1 향상) 은 n=47 에서도 유지된다.

#### Variant A — 단계 추가 효과

| 변형 | 표본 | F1 | 비고 |
|---|---|---|---|
| A.1 Stage 1 only | n=15 → 18 → 19 | 0.846 → 0.875 → **0.882** | 표본이 늘면서 Precision 안정 |
| A.2 Stage 2 oracle-style upper bound | 모든 n | **1.000 upper bound** | GT 기반 P-ceiling 시뮬. 실제 Stage 2 독립 성능 주장 아님 |
| A.3 + Stage 3 (≥3/3) | n=19 | **0.889** | 초기 측정값 (n=18 시점 0.783)은 외부 corpus(MASTG)의 Stage 3 평가 누락이 만든 artifact였다. Stage 3 평가를 외부 corpus에 확장 + UnCrackable-Level3 추가 후 일관성 회복 |

A.2는 Stage 2 구현 자체의 독립 성능이 아니라, GT 라벨과 caller 분석 결과를 이용해 Stage 2가 이론적으로 제거할 수 있는 FP 상한을 추정한 것이다. 따라서 최종 성능 주장에는 사용하지 않고, Stage 3 consensus 결과를 주요 pipeline 결과로 사용한다.

#### Variant B — Stage 3 합의 임계 sensitivity (combined n=19)

| 임계 | Precision | Recall | F1 |
|---|---|---|---|
| ≥1/3 (시각 1 종 이상이 flag) | 78.9% | 100% | 0.882 |
| **≥2/3 (default — 다수결)** | **100%** | **93.3%** | **0.966** |
| ≥3/3 (만장일치) | 100% | 80.0% | 0.889 |

≥2/3는 현재 corpus에서 Precision을 유지하면서 Recall 손실을 줄이는 임계값으로 관찰되었다. ≥3/3은 더 보수적이지만, emission 경로가 일부 불확실한 finding을 놓칠 수 있다.

### 3.4 난독화 이름 복원 정확도 (G4)

OWASP MASTG의 UnCrackable-Level1/2 의 `sg.vantagepoint` 패키지 (anti-tamper helper) 에 Stage 0 (deobfuscation) 프롬프트 적용:
- n=17 (6 class + 11 method) — **exact match 100%**
- 이 결과는 초기 계획서 가설 (8주차 시점 78%)보다 높지만, hand-crafted MASTG corpus에 대한 upper-bound 성격이 강하다. real-world commercial ProGuard 코드에서는 contextual hint가 약해 정확도 하락이 예상된다 (한계 L4).

**예상과 다른 발견**: PleOS APK 3종은 HIGH 난독화 클래스 비율이 **0.2~0.4%** 로 매우 낮았다. 즉, 본 학기 PleOS sample은 초기 계획서가 가정한 "고난독화 IVI 코드" 시나리오와 정량적으로 달랐다. 따라서 본 보고서 narrative에서는 "PleOS 코드 자체의 난독화 대응"보다 "외부 obfuscated corpus에서 Stage 0 feasibility 확인"으로 표현한다. 단 R1.d.5 의 `ai.umos.maps` / `ai.umos.callandmessage` 는 ProGuard 활성으로 priority class yield 가 감소 (한계 L6) — PleOS-customized application code 도 일부 release engineering 정책에 따라 난독화가 적용된다.

**R4 첫 측정 — Real-world commercial OSS (NewPipe) 의 난독화 baseline** (2026-05-08 추가):

| Corpus | 종류 | 비-framework 클래스 수 | HIGH (composite ≥ 0.7) | 비율 |
|---|---|---:|---:|---:|
| UnCrackable-Level1 / 2 | hand-crafted MASTG | 6 / 5 | 3 / 2 | **50% / 40%** |
| **NewPipe v0.27.6** | **real-world OSS, ProGuard 활성** | **2,520** | **42** | **1.7%** |
| PleOS VehicleControl | 실제 IVI APK | 2,704 | 6 | 0.2% |
| PleOS SyncSyslog | 실제 IVI APK | 4,555 | 18 | 0.4% |

**해석**: NewPipe (대표적 인기 open-source Android 앱, 빌드 시 ProGuard 활성) 의 HIGH 난독화 비율 **1.7%** 가 hand-crafted MASTG (40~50%) 와 PleOS (0.2~0.4%) 의 사이에 위치한다. 이는 본 학기 가정하던 두 극단 사이에 **real-world commercial 난독화 baseline** 을 정량적으로 끼워넣는 첫 데이터다. R4 의 Stage 0 LLM rename 정확도는 ProGuard mapping file 부재로 본 학기 partial — semantic plausibility 평가만 가능하며 exact accuracy 측정은 Future Work (ProGuard mapping 확보 또는 debug build 다운로드 후).

### 3.5 외부 GT 베이스라인 및 pipeline boundary (G8)

self GT (PleOS 자체 라벨)만으로 평가하면 self-referential bias가 생길 수 있다. 이를 완화하기 위해 외부 정답이 공개된 OWASP MASTG sample 6종을 도입하였다 (2026-05-06 까지의 누계).

| Sample | in-scope finding | 결과 |
|---|---|---|
| UnCrackable-Level1 | 3건 | 모두 TP. 단, in-scope n=4 의 일부라 일반화 성능으로 해석하지 않음. |
| UnCrackable-Level3 | 1건 | XOR key hardcoded finding (HIGH). |
| UnCrackable-Level2 | 0건 | 핵심 검증 로직이 `libfoo.so` 의 native method, Java 측엔 anti-tamper만. **Boundary 1**. |
| r2pay-v1.0 | 0건 | token 생성이 `libnative-lib.so`, Java 측은 wrapper. **Boundary 2**. |
| HelloWord-JNI | 0건 | `System.loadLibrary("native-lib")` + native `stringFromJNI()`. Java 측은 한 줄 bridge. **Boundary 3** (2026-05-06 추가). |
| certificatePinningXamarin | 0건 | Xamarin / .NET 앱. 핵심 pinning 로직은 `App1.dll` (CIL) 안. Java 측은 mono runtime binding 만. **Boundary 4** (2026-05-06 추가, 다른 axis: native 가 아니라 .NET runtime). |

**해석**: 본 pipeline 은 Java/Kotlin layer 의 Android framework misuse, exported component, hardcoded secret, plaintext communication 탐지에는 유용하지만, **검증 로직이 native lib (`*.so`) 또는 다른 runtime (.NET CIL) 안에 숨겨진 경우에는 구조적 blind spot 을 가진다**. 본 학기 외부 corpus 6 sample 중 **4 건 (66.7%)** 이 boundary case 로 in-scope finding 0 건. 따라서 PleOS 적용 시 Java/Kotlin layer scanner 와 native/non-Java binary scanner 를 분리된 stage 로 구성해야 한다 — 한계 L1 의 강한 정량 evidence.

### 3.6 RQ 직접 측정값 (2026-05-06 추가)

본 학기의 4 sub-question 중 3개 (RQ1 sensitivity / RQ2 perspective diversity / RQ3 native boundary) 의 첫 corpus-level 측정. 결정론적 스크립트 (`scripts/research/research_r{1a,2a,3a}_*.py`) 로 재현 가능.

#### 3.6.1 RQ1 — Stage 1 → Stage 2 → Stage 3 transition

각 finding 의 단계별 verdict 변화를 추적해 multi-stage gain 의 sensitivity 를 정량화 (combined GT n=19):

| Stage 2 (GT) | Stage 3 class | count |
|---|---|---:|
| TP | strong-TP (3/3) | 12 |
| TP | TP (2/3) | 2 |
| TP | uncertain (1/3) | 1 |
| FP | uncertain (1/3) | 4 |

**FP / TP flow**:
- Stage 2 GT FP **4건 → Stage 3 모두 정확히 걸러짐** (clean/uncertain). FP→TP 잘못 promote 0건.
- Stage 2 GT TP 15건 → Stage 3 14건 유지, **1건 손실** (`ssl-4` PII toString — emission 미확인이라 1/3 합의로 강등).

**해석**: Stage 3 합의 임계가 단순 noise 가 아니라 정확한 filtering 임을 직접 입증. 단 표본 우연성 배제는 R1.b bootstrap CI / R1.d 표본 확장 (n ≥ 30) 후 가능. 산출: [`data/reports/aggregate/stage_transitions.{md,json}`](../data/reports/aggregate/stage_transitions.md).

**R1.b 후속 — Bootstrap CI** (2026-05-06 도입, 2026-05-07 / 2026-05-14 갱신): `src/evaluation/eval.py` 에 non-parametric percentile bootstrap (`--bootstrap N` 옵션) 도입. with-replacement 1000 회 resample (seed=42, deterministic).

| Metric | n=19 (초기) | n=28 (R1.d) | n=37 (R1.d.4) | **n=47 (R1.d.5, 학기 외 A)** | Δ vs n=19 |
|---|---|---|---|---|---|
| Precision (lenient) | 78.9% / CI [57.9%, 94.7%] | 85.7% / CI [71.4%, 96.4%] | 83.8% / CI [73.0%, 94.6%] | **80.9% / CI [70.2%, 91.5%]** | CI 폭 −15.5%p |
| F1 (lenient) | 88.2% / CI [73.3%, 97.3%] | 92.2% / CI [83.3%, 98.2%] | 91.1% / CI [84.4%, 97.2%] | **89.4% / CI [82.5%, 95.6%]** | CI 폭 −10.9%p |
| FP rate (lenient) | 21.1% / CI [5.3%, 42.1%] | 14.3% / CI [3.6%, 28.6%] | 16.2% / CI [5.4%, 27.0%] | **19.1% / CI [8.5%, 29.8%]** | CI 폭 −15.5%p |
| Recall | 100% | 100% | 100% | **100%** | — |

**핵심 발견**: 표본 19 → 47 확장으로 **CI 폭이 약 40% 줄어든다** (Precision / FP rate 36.8%p → 21.3%p, F1 24.0%p → 13.1%p). Precision lower bound 57.9% → **70.2%** (+12.3%p) — 가설 25% FP rate 가 lower bound 훨씬 위에 위치. point 값은 R1.d.5 신규 FP 3건으로 83.8% → 80.9% 후퇴했으나 CI 는 계속 좁아짐 (point 변동 ≠ 통계적 보장 약화). RQ1 의 actionable insight: **n ≥ 40 corpus 부터는 보고서의 정량 주장이 통계적으로 더 신뢰 가능**. 산출: [`data/reports/aggregate/bootstrap_ci.{md,json}`](../data/reports/aggregate/bootstrap_ci.md).

#### 3.6.2 RQ2 — Perspective disagreement (multi-prompt diversity 진단)

시각 3종 (attacker / defender / domain_expert) 간 Cohen's κ 측정으로 ensemble 의 diversity 가 진짜인지 검증:

| Pair | agree % | both flag | only A | only B | κ |
|---|---:|---:|---:|---:|---:|
| attacker ↔ defender | 63.2% | 12 | 0 | 7 | **0.0** |
| attacker ↔ domain_expert | 89.5% | 11 | 1 | 3 | **0.759** |
| defender ↔ domain_expert | 73.7% | 14 | 5 | 0 | **0.0** |

**Flag rate per perspective**: attacker 63.2% (12) / **defender 100% (19, universal)** / domain_expert 73.7% (14).

**해석**: defender prompt 가 19건 모두 flag → diversity 측면에서 redundant. 의미 있는 disagreement 는 attacker ↔ domain_expert 사이에서만 (κ=0.759, substantial agreement). 즉 본 multi-perspective ensemble 의 정확도 향상은 사실상 attacker 와 domain_expert 두 시각의 합의에서 온 것이고 defender 는 ceiling 역할만. **Stage 3 prompt 보강 권고** = defender prompt 를 더 selective 하게 다듬어야 ensemble 비용 대비 효율 올라감. 산출: [`data/reports/aggregate/perspective_agreement.{md,json}`](../data/reports/aggregate/perspective_agreement.md).

#### 3.6.3 RQ3 — Java-only boundary 의 corpus 인덱스

본 pipeline 이 미커버하는 native lib 비중을 PleOS Connect 207 system APK 에서 직접 측정:

| Origin | n | with native | % |
|---|---:|---:|---:|
| PleOS (`ai.umos.*` / `ai.pleos.*`) | 138 | 14 | **10.1%** |
| AOSP (Android framework / Google) | 64 | 7 | 10.9% |
| third-party | 5 | 1 | 20.0% |
| **Overall** | **207** | **22** | **10.6%** |

**Top 5 native-heavy APKs**: `ai.pleos.playground.caas` (62 .so), `ai.umos.maps.android.navigation.app` (44), `ai.umos.ambientai` (24), `com.antutu.benchmark.full.lite` (20), `ai.umos.appmarket` (12).

**해석**: 한계 L1 (Java-only) 의 corpus-level 인덱스 = **PleOS 10.1%, 전체 10.6% APK 가 본 pipeline 의 blind spot**. 더 중요한 점은 차량 제어 / 맵 navigation / 음성 비서 같이 **보안 가치가 큰 컴포넌트가 native 비중 top** — 단순히 10% 가 아니라 "위험도 가중 10%" 로 해석해야. **RQ3.c (native-bound vuln 정량) 는 학기 외 C 작업으로 첫 sample-level 측정 완료** — radare2 6.1.4 + `src/native/native_analyze.py` 로 native sample n=4 정적 분석, 추가 vuln 0건 (§ 3.6.9 참조). 산출: [`data/reports/aggregate/native_lib_inventory.{md,json}`](../data/reports/aggregate/native_lib_inventory.md).

#### 3.6.4 RQ2.b' — Defender prompt selectivity calibration 효과 (2026-06-07)

R2.a 의 finding (defender 가 19/19 universal flag) 을 받아 11주차에 `stage3_defender.md` 에 selectivity 룰 4개 추가 (severity LOW drop / concrete missing_control / defense-in-depth vs actionable / empty array OK). 14주차 동일 28 finding 에 calibrated 룰 적용해 효과 측정:

| Pair | κ (보강 전) | κ (보강 후) | Δ |
|---|---:|---:|---:|
| attacker ↔ defender | 0.0 | **0.900** | **+0.9 (poor → almost perfect)** |
| defender ↔ domain_expert | 0.0 | **0.811** | **+0.811 (poor → almost perfect)** |
| attacker ↔ domain_expert | 0.728 | 0.728 | (prompt 변경 없음) |

**Defender flag rate**: 100% (28/28 universal) → **78.6%** (22/28). 6 finding drop: vc-1/2 (defense-in-depth, OTA-trusted asset), vc-3/4 (4중 차단), vc-7 / ucl1-3 (severity LOW).

**핵심 발견**: prompt 변경만으로 ensemble diversity 의 의미가 substantial→almost perfect 로 회복. 본 학기 처음으로 prompt 변경의 정량 효과 측정. 단 본 측정은 결정론적 룰을 수동 적용한 결과 — 새 corpus 에 calibrated prompt 를 LLM 에 직접 던진 검증은 Future Work. 산출: [`data/reports/aggregate/perspective_agreement_calibrated.{md,json}`](../data/reports/aggregate/perspective_agreement_calibrated.md).

#### 3.6.5 RQ1.c — Paired McNemar test (n=47, 학기 외 A 작업으로 통계적 유의 도달)

RQ1 의 Stage 1 → Stage 3 향상에 대한 통계 검정. 각 finding 의 paired binary outcome (Stage 1 correct / Stage 3 correct) 으로 2×2 contingency. 학기 외 A 작업으로 R1.d.5 (n=47) + Stage 3 ensemble 19건 확장 후 재측정:

|  | Stage 3 correct | Stage 3 incorrect | total |
|---|---:|---:|---:|
| Stage 1 correct | a = 37 | b = 1 | 38 |
| Stage 1 incorrect | c = 9 | d = 0 | 9 |

- McNemar's χ² = 6.400 (df=1), p_chi = 0.0114
- **Exact binomial (two-tailed) p_exact = 0.0215** ← b+c=10, exact 권고

**결과**: α=0.05 기준 **통계적으로 유의** (p_exact=0.0215 < 0.05). 본 학기 n=28 (p=0.375, discordant b+c=5 로 power 부족) 에서 학기 외 R1.d.5 + Stage 3 ensemble 확장으로 discordant pair b+c=10 확보 → **Stage 3 향상이 표본 우연이 아니라는 첫 통계적 증거**. Effect size: Stage 3 가 Stage 1 의 오류 9건을 추가 정정 (9 FP 모두 uncertain/clean 으로 강등), Stage 1 의 정답 1건만 누락 (vc-7 LOW hardening, 1/3 합의) = net +8건. odds ratio b/c = 1/9. **RQ1 의 핵심 정량 contribution** — bootstrap CI 좁힘 (R1.b) + paired test 유의성 (R1.c) 둘 다 본 학기 외 A 작업에서 도달. 산출: [`data/reports/aggregate/mcnemar_test.{md,json}`](../data/reports/aggregate/mcnemar_test.md).

#### 3.6.6 RQ4 보강 — Real-world Stage 0 정확도 측정 (2026-06-07)

13주차의 NewPipe entropy density (HIGH 1.7%) 측정에 이어, Stage 0 LLM rename 의 실제 정확도 측정. NewPipe 의 비즈니스 패키지 (`org.schabi.newpipe.*`) 안 HIGH 클래스 = **단 1 / 973 (0.1%)** — 즉 NewPipe 의 HIGH 41 개는 전부 `j$.*` (Android Desugar library) 의 jadx-prefix 클래스. 본 측정은 desugar library 측 3 sample 에 적용:

| Sample | Confidence (class) | Semantic plausibility | hint |
|---|---:|---|---|
| `C1302f` (RuntimeException helper) | 0.55 | PARTIAL | "Unsupported " literal + RuntimeException 상속만 |
| **`C1112a`** (Unsafe accessor) | **0.85** | **GOOD** | `Unsafe.class` import + `'theUnsafe'` literal + Singleton 패턴 |
| `C1289p` (Concurrent node) | 0.45 | POOR | Field-only, 인접 클래스 시그니처 부재 |

**비교 — Hand-crafted MASTG vs Real-world**:

| Corpus | sample | confidence avg | plausibility |
|---|---:|---:|---|
| Hand-crafted MASTG (UnCrackable Level1/2) | 17 | 0.92 | **100% exact** match |
| Real-world OSS (NewPipe desugar library) | 3 | 0.62 | **33% GOOD** plausibility |

**약 3배 정확도 하락**. RQ4 의 정직한 결론: Stage 0 LLM rename 의 정확도는 **corpus 의 contextual hint density 에 강하게 의존**. Hand-crafted 100% 는 upper bound, real-world ~33% GOOD plausibility 는 first-pass lower bound. NewPipe 가 OSS 라 application code 가 가독성 유지 (HIGH 0.1%) 라는 surprising finding 도 수반 — 본 학기의 Stage 0 narrative 가 "real-world 정확도" 보다 "library 측 jadx-output 난독화의 plausibility" 로 표현하는 편이 더 정확. 산출: [`data/reports/aggregate/r4_real_world_baseline.md`](../data/reports/aggregate/r4_real_world_baseline.md), [`data/deobf/NewPipe_renames_20260607.json`](../data/deobf/NewPipe_renames_20260607.json).

#### 3.6.7 Random-sample selection-bias baseline (2026-06-07)

본 학기 PleOS 3 APK (vehiclecontrol / sync.syslog / llm.model.provider) 가 보안 가치 기반 선정이라 measurement value 의 selection bias 를 정량 측정. PleOS 207 시스템 APK 중 위 3 APK 를 제외한 204 pool 에서 시드 42 로 무작위 3 APK 선택 → priority class count 비교:

| 측정 | 보안 가치 큰 3 APK 평균 | 무작위 3 APK 평균 | 비율 |
|---|---:|---:|---:|
| Priority class count | **424.33** | 15.0 | **28.29×** |
| Native lib count | 1.67 | 0 | — |

**Selection bias 정량 입증**: 보안 가치 기반 선정 corpus 의 priority class density 가 무작위 sample 의 약 **28배**. 본 학기 측정값 (Stage 1 P 85.7%, F1 0.923) 은 이 bias 가 반영된 corpus 결과로 해석해야 한다. 무작위 3 APK 의 Stage 1 LLM 분석은 본 학기 시간 cost 외부 — Future Work. 산출: [`data/reports/aggregate/random_sample_baseline.{md,json}`](../data/reports/aggregate/random_sample_baseline.md).

→ 본 학기 측정값은 보안 가치 큰 corpus subset 한정. v1.0 narrative 갱신: 일반화 주장은 무작위 sample 추가 측정 후로 명시.

#### 3.6.8 RAG 도메인 지식 주입 — intrinsic retrieval-quality ablation (학기 외 B 작업, n=47)

본 학기 Stage 1 prompt 는 6 카테고리 detect rule 을 hardcoded inline 했다. 학기 외 B 작업으로 외부 도메인 지식 (AAOS / MASVS / TARA / historical findings) 을 RAG 로 dynamic retrieve 하는 경로를 구현. **환경 정책 호환** — 외부 LLM/embedding API 호출 0건: `chromadb` + 로컬 `sentence-transformers/all-MiniLM-L6-v2` (22M params, CPU 추론).

**Chroma 4 collection (총 158 chunks)**: `aaos_guidelines` 6 / `masvs_controls` 99 (OWASP MASTG 41 docs H2-chunked) / `tara_templates` 6 / `finding_patterns_historical` 47 (combined GT 의 모든 finding × code excerpt + rationale). `src/rag/{build_index,retrieve,ablation}.py` + `configs/prompts/stage1_detect_rag.md`.

**Intrinsic ablation 측정 (n=47)**:

| 측정 | 결과 | 의미 |
|---|---:|---|
| NN verdict propagation | **40/47 = 85.1%** | historical nearest-neighbor (self 제외) 의 GT verdict 가 query verdict 와 일치 — embedding 모델이 TP/FP anti-pattern 을 분리 |
| AAOS category alignment | **40/47 = 85.1%** | RAG top-1 의 6-category 라벨이 GT stage1_category 와 일치 — `aaos_section` 필드 자동 채움 가능 |
| MASVS area match | 11/47 = 23.4% | MASTG Document chunking (~2000 char H2) 이 거칠어 약함 — H3 + sliding-window fine-grained 화가 sub-task |

**AAOS alignment by category**: crypto 5/5 (100%) / network 8/9 (88.9%) / intent 15/18 (83.3%) / hardcoded 9/11 (81.8%) / permission 2/3 (66.7%) / reflection_dynamic 1/1.

**해석**: NN propagation 85.1% 는 RAG calibration 의 ceiling 을 시사 — historical FP 예시로 confidence 를 calibrate 하면 Stage 1 Precision 향상 여지 (보수적 추정 +5~10%p). 단 본 측정은 **intrinsic retrieval quality** 이며, with-RAG vs without-RAG 의 prompted-LLM end-to-end ablation (FP rate 변화) 은 v1.4 supplement 이후 별도 work-load 로 남긴다. 산출: [`data/reports/rag_local/rag_ablation.{md,json}`](../data/reports/rag_local/rag_ablation.md).

#### 3.6.9 RQ3.c — Native binary sample-level 분석 (학기 외 C 작업, R3.c.2 n=4)

§ 3.6.3 의 corpus-level 인덱스 (10.6% APK 가 native lib 보유) 의 sample-level 첫 정량. 학기 외 C 작업으로 radare2 6.1.4 통합 + `src/native/native_analyze.py` (Windows / Git Bash binutils 부재 우회용 Python regex string 추출기) 작성.

| # | APK | .so | size | 정적 분석 결과 |
|---|---|---|---:|---|
| 1 | ai.pleos.sync.syslog | libgojni.so | 15 MB | Go crypto/tls + x509 verification 활성, hardcoded endpoint 0건 (R3.c baseline) |
| 2 | ai.pleos.playground.caas | libgojni.so | 15 MB | #1 과 동일 ELF (공유 Go binary). UUID `258EAFA5-…` standalone string = Go embedded constant 추정 (secret 아님) |
| 3 | ai.pleos.playground.caas | libairspeech_stt.so | 4.4 MB | on-device STT 추정, hardcoded URL / secret 0건 |
| 4 | ai.umos.maps.android.navigation.app | libmapbox-maps.so | 9.3 MB | Mapbox SDK, tile endpoint 는 Java BuildConfig 에서 inject — secret 0건 |

**결과**: **n=4 native sample 모두 추가 vuln 0건**. 핵심 발견 — native lib 는 secret storage / endpoint definition source 가 아니라 *Java-side BuildConfig 의 consumer* 패턴. 즉 Java 측 보안 (BuildConfig 보호, OAuth client_secret 미보유) 이 native transport security 의 root. sync.syslog/libgojni 와 caas/libgojni 가 동일 binary 인 점은 transport 의 single point-of-failure.

**R3 두 axis 종합**: corpus-level R3.a 10.6% (22/207 APK) + sample-level R3.c.2 **n=4 / 추가 vuln 0건** — Java/native transport security 일관성의 정량 증거. 한계: static-only — Go runtime reflect dispatch, dynamic JNI argument flow 는 미관찰 (Ghidra GolangAnalyzerExtension + Frida hook 이 후속). 산출: `data/reports/native_local/native_r3c2_20260514.md` (로컬), `src/native/native_analyze.py`.

#### 3.6.10 Dynamic 검증 연계 — deterministic state machine + Frida hook scripts (학기 외 D 작업)

본 학기 정적 분석만 수행. 학기 외 D 작업으로 Static → Dynamic feedback 경로를 구현. **환경 정책 호환** — `langgraph` state graph 는 deterministic transition 만 등록, **LLM node 미등록** (LLM 분석은 Claude Code 세션이 외부 driver 로 유지, Anthropic SDK 호출 코드 0건).

- **`src/dynamic/state_machine.py`** — `receive_finding → stage1_classify → stage2_static_verify → conditional[frida_hook / stage3_correlate] → END` 의 5 deterministic node + STAGE2_RULES dict (vc-5/6, ssl-2/5, lmp-1). 검증: runtime observation 부재 시 `TP_static_only`, observation provided 시 `strong_TP_dynamic` verdict transition.
- **`src/dynamic/hooks/` 5 Frida hook scripts** — vc-5 GleoActionSender (sendBroadcast wrap + stack trace) / vc-6 VehicleBroadcastReceiver (Binder.getCallingUid 외부 caller 검증) / ssl-2 AuthData toString + Log.* emission / ssl-5 BuildConfig.IDENTIFIER ↔ ECCCrypto.deriveKey passphrase 일치 / lmp-1 PromptsContentProvider.query calling UID.
- **사례 연구 5건 추가** — [`03_case_studies.md`](03_case_studies.md) Case 6~10 에 각 hook 의 verdict transition table + static-only vs static+dynamic 비교.

**한계**: AVD 실제 실행 (frida-server-arm64 attach 또는 frida-gadget injection) 은 환경 의존 후속 step — script + state machine 은 ready. 5 strong-TP finding 이 dynamic 에서도 동일 verdict 면 정적 결론의 강건성을 정량 입증하고, 1건이라도 정정되면 RQ1 의 추가 한계 (정적+dynamic disagreement) 가 된다.

### 3.7 기존 도구 베이스라인 비교

기존 4종 도구 / 방법과 정성+정량 비교:

| 베이스라인 | 자체 정량값 | 본 연구 대비 |
|---|---|---|
| ① jadx + 수동 분석가 | self GT 가 manual baseline (분석가 시간 6~7h) | 본 파이프라인 ~2h (3배 단축). 단, 정확한 stopwatch 측정은 Future Work ([`07_future_work.md`](07_future_work.md) F12) |
| ② 단일 LLM 1-pass (검증 단계 없이) | Stage 1 자체 (Precision 78.9%) | 제한 corpus에서 Stage 3 ≥2/3 적용 후 reported FP 0건 관찰 |
| ③ android-scanner-ai (X-Vector) | **자체 P/R/F1 측정값 부재** + Gemini API key 의존 | 본 연구가 정량 평가 gap 제공. 직접 재현 비교는 API 제약으로 미완 |
| ④ Androidmeda (In3tinct) | deobfuscation 위주, 자체 측정값 부재, Apache 2.0 | Stage 0 통합 후보 |

---

## 4. AAOS / MASVS / TARA 매핑 (G5 / G6)

### 4.1 AAOS 섹션 커버리지 (auto-generated, n=19 스냅샷)

| AAOS Section | Findings | TP | HIGH |
|---|---|---|---|
| 3.7 Permission Model | 7 | 5 | 3 |
| 4.2 Credential Protection | 7 | 7 | 4 |
| 5.1 Communication Security | 4 | 2 | 1 |

본 표는 `src/mapping/aaos_map.py` 의 n=19 시점 자동 산출 결과다. 본 corpus에서는 AAOS §3.7 / 4.2 / 5.1 만 커버하며, §4.1 Lockscreen, §6 OTA / Verified Boot 등은 미해당 → Future Work. **R1.d.2~d.5 신규 28 finding** (usb / statementservice / account / appmarket / ambientai / maps) 도 동일 3 섹션에 매핑된다 — usb-1/3 (§4.2), ss-1 (§3.7), acc-1/3/5 + am-1 + amb-3 (§5.1/§3.7), acc-2/4 + am-3 + amb-1/2 (§4.2). 전체 n=47 의 AAOS 매핑 표 재생성은 `src/mapping/aaos_map.py --labels combined_labels.json` 으로 가능 (학기 외 후속).

### 4.2 TARA Risk Matrix (TP only, n=14)

| Impact \ Feasibility | High | Medium | Low |
|---|---|---|---|
| Severe | 2 | 0 | 0 |
| Major | 6 | 3 | 0 |
| Moderate | 1 | 0 | 2 |

| Risk Level | Count | Treatment |
|---|---|---|
| **Critical** | 2 | Avoid (must fix before release) |
| **High** | 6 | Mitigate (current sprint) |
| **Medium** | 4 | Mitigate (next minor release) or Transfer |
| **Low** | 2 | Accept with monitoring |

**Critical 등급 2건**:
- `vc-5` — VehicleControl 의 GleoActionSender 가 차량 제어 명령을 implicit broadcast 로 송출. 자산 = 차량 제어 명령 (Severe), 공격 실현 가능성 = High.
- `vc-6` — VehicleControl 의 VehicleBroadcastReceiver 가 exported + macAddress 미검증. 동일 자산 등급, 동일 실현 가능성.

### 4.3 사례 연구 5건 (G7)

상세는 [`03_case_studies.md`](03_case_studies.md). 요약:

| Case | Finding | 의의 |
|---|---|---|
| 1 | `ssl-5` (sync.syslog 의 BuildConfig.IDENTIFIER 를 KDF passphrase 로) vs `ucl1-1` (UnCrackable-Level1 의 hardcoded AES key) | 자체 corpus 와 외부 corpus의 동일 카테고리 finding 비교 — AAOS §4.2 (자격증명 보호) 매핑 일관성 |
| 2 | `vc-3` / `vc-4` (FP 4중 차단) | multi-stage 검증의 효과 관찰 — Stage 1 P 78.9% → Stage 3 ≥2/3 P 100% (limited corpus) |
| 3 | `ssl-6` (sync.syslog 의 gRPC `.usePlaintext()`) | Stage 1 MEDIUM → Stage 3 HIGH 격상 사례 — consensus threshold ≥2/3 vs ≥3/3 차이 설명 |
| 4 | `lmp-1` (llm.model.provider 의 exported PromptsContentProvider) | IVI / on-device LLM 도메인 특화 finding |
| 5 | `vc-6` (VehicleControl macAddress 미검증) | Critical risk + 차량 안전 직결 |

---

## 5. 통합 아키텍처 권고 (G6 보강)

본 학기 산출물을 PleOS 차량 SW 개발 라이프사이클에 어떻게 통합할 수 있는지 권고. 본 절은 **권고/설계** 수준이며 실제 통합 구축은 PleOS 운영팀의 결정 + 별도 구현 단계가 필요.

### 5.1 전체 흐름

```
[1] DEV (소스 + Gradle)
    Kotlin/Java 소스 → Gradle build → APK
    (선택) ProGuard/R8 활성화로 식별자 난독화

[2] CI/CD — pleos-llm-scanner 통합 진입점
    APK 빌드 직후, PR 머지 전에 자동 실행
    a. scripts/apk/decompile.sh APK → jadx 디컴파일
    b. src/deobf/entropy.py → 난독화 수준 측정
    c. (HIGH 난독화일 때만) Stage 0 LLM 이름 복원
    d. configs/keywords.yaml grep → priority class 큐
    e. Stage 1 LLM → finding 후보
    f. Stage 2 caller 분석 + (선택) AST 룰
    g. Stage 3 multi-perspective consensus
    h. src/mapping/aaos_map.py → AAOS / MASVS 매핑
    i. src/mapping/tara_generate.py → TARA 시나리오 + Risk Matrix

[3] PR Gate (권고 정책)
    Critical risk count = 0     → 머지 차단 (block)
    High risk count > N         → 리뷰 강제 + Mitigation plan 첨부
    Medium / Low                → comment-only (정보성)
    난독화 수준 HIGH > X%        → 디컴파일 결과 동결 + 별도 분석

[4] TARA 통합 흐름
    Threat Scenarios → Risk Matrix → Treatment 결정
    Treatment 결정이 변경되면 PR Gate 정책의 N 값 자동 갱신
    Telemetry 로 들어온 incident → Scenarios 에 새 evidence 추가

[5] OTA Gating (권고)
    Gate 통과한 빌드만 서명
    Staged rollout (1% → 10% → 100%)
    각 단계에서 telemetry 로 이상 발생 시 자동 rollback
    rollback 트리거 데이터는 다시 TARA Scenarios 로 피드백
```

### 5.2 본 학기 PoC vs 운영 전환

| 측면 | 본 학기 PoC | 운영 전환 시 |
|---|---|---|
| 분석 엔진 | Claude Code 인터랙티브 세션 | API 통합 (CI/CD trigger) — 단, 외부 LLM API 미보유로 본 학기는 권고에 머무름 |
| 트리거 | 사용자 명시 ("X.apk 분석해줘") | PR 이벤트 / nightly batch / OTA pre-flight |
| 결과 저장 | `data/reports/` 로컬 파일 | Artifact server + GitHub Actions output / Slack notification |
| GT 라벨링 | self_labels.json 수동 | regression set + 자동 diff (전 커밋 대비 신규/사라진 finding) |
| TARA 통합 | Static 매핑 표 | 동적 — 신규 finding 이 기존 시나리오 갱신/생성 |
| OTA 게이팅 | 권고만 | gate policy + 자동 sign reject |
| 모델 버전 관리 | Claude Code 모델 업데이트 | prompt-as-code + version-pinned Claude model |

### 5.3 MVP — 최소 비용 통합 권고

PleOS 운영팀이 본 파이프라인을 최소 비용으로 활용하려면:

1. **GitHub Actions 에 정적 부분만 통합** (외부 LLM 호출 없이): `src/deobf/entropy.py`, keyword grep, `src/evaluation/eval.py`/`ablation.py`, `src/mapping/aaos_map.py`, `src/mapping/tara_generate.py` 모두 결정론적이라 PR 마다 자동. LLM 분석만 사람이 트리거.
2. **차량 LLM (PleOS-internal) 활성화 시 Stage 1/2/3 자동화**: 본 파이프라인의 prompts 를 그대로 호출, 외부 송출 없이 in-vehicle 또는 internal cloud 에서 분석 완결. 본 학기 환경 제약 (외부 LLM API 없음) 이 풀림.
3. **후속 학기에 Androidmeda 통합**: Apache 2.0 라이선스, deobfuscation 모듈만 fork → 본 entropy 측정과 cross-check.

### 5.4 IP 보호 주의사항

- 본 학기 GitHub repo 는 scaffold 만 공개. `data/_local/apks/`, `data/_local/decompiled/`, `data/reports/` 의 per-APK 보고서는 gitignored.
- 운영 통합 시에도 PleOS APK 소스가 외부 LLM API 에 송출되지 않도록 차단 필수. 현재는 환경 제약으로 자연스럽게 만족, 향후 cloud LLM 도입 시 별도 가드 필요.
- TARA 산출물 (자산 카탈로그, 위협 시나리오) 은 contract IP — repo public commit 대상에서 제외, 보고서에만 포함.

### 5.5 운영 비용 평가

본 파이프라인의 시간 / 금전 / 메모리 / 확장성 비용을 manual baseline 과 비교해 산업 적용 ROI 를 정량화. 자세한 단계별 분해는 [`06_limitations_and_costs.md`](06_limitations_and_costs.md) § 2 참조.

#### 5.5.1 시간 cost (APK 1개 기준)

| 단계 | 본 파이프라인 (인터랙티브) | manual baseline | 단축률 |
|---|---|---|---|
| 키워드 grep + priority 추출 | 1분 | 코드 read 30분 ~ 1시간 | 30~60x |
| Stage 1 LLM 분석 (priority 9 클래스) | ~1시간 | manual 코드 분석 3~4시간 | 3~4x |
| Stage 2 caller 추적 | ~30분 | manual grep + 사고 1~2시간 | 2~4x |
| Stage 3 멀티 시각 합의 | ~30분 | n/a | — |
| 보고서 (JSON + MD) 생성 | 즉시 | manual 1~2시간 | ∞ |
| **APK 1개 풀 파이프라인** | **~40분** | **~2 시간** | **3x** |
| **3 APK 누계** | **~2시간** | **6~7시간** | **3~3.5x** |

PPT 가설의 8~25분/APK 는 fully-batch 가정. 본 파이프라인은 인터랙티브 Claude Code 세션이라 사람의 reading time 포함. **fully-batch 자동화 시 8~15분/APK 도달 가능** (Future Work).

#### 5.5.2 금전 cost

| 항목 | 본 파이프라인 | 외주 환산 baseline |
|---|---|---|
| LLM API 비용 | $0 (Claude Code 정액제) | Gemini/OpenAI 기준 APK 1개 ~$1~3 |
| 디컴파일러 라이선스 | $0 (jadx Apache 2.0) | $0 |
| GT 라벨링 인건비 | self (학기 프로젝트) | 외주 보안 분석가 시급 ₩100K × 6~7h ≈ ₩600K~₩700K / APK 3종 |
| **APK 1개 분석 비용** | **~$0** (시간 cost 만) | **외주 환산 ₩200K~₩240K / APK** |

#### 5.5.3 메모리 / CPU peak

| 단계 | peak | 비고 |
|---|---|---|
| jadx 디컴파일 (VehicleControl 92MB) | ~3 GB JVM heap | `JADX_OPTS=-Xmx4g` 권장 |
| Claude Code 세션 | ~500 MB (Node + Python helper) | LLM 추론은 클라우드 |
| python entropy / eval / ablation | ~200 MB | matplotlib + numpy |
| **합계 peak** | **~4 GB** | PPT 가설 (4~8 GB) 충족 |

#### 5.5.4 확장성 — APK 100개 분석 추정

| 자원 | 인터랙티브 | fully-batch | 가정 |
|---|---|---|---|
| 시간 | ~70 시간 | ~15~25 시간 | APK 당 ~40분 + 보고서 정리 / LLM 호출 자동화 |
| 디스크 | ~50 GB | ~50 GB | jadx output 200~500 MB × 100 |
| 메모리 | ~4 GB peak | ~4 GB peak | jadx 단계가 dominant |
| 비용 | $0 (정액제 한도) | enterprise plan 검토 | — |

ROI: 외주 baseline 대비 **APK 1개당 ~₩200K 절감 + 3x 시간 단축**. APK 100개 분석 시 인건비 **~₩20M, 250 시간 절감** 추정.

#### 5.5.5 PPT 가설 vs 실측 (cost 부분)

| 지표 | PPT 가설 | 실측 | 충족 |
|---|---|---|---|
| 처리 시간 (APK 1개) | 8~25분 | 인터랙티브 ~40분 | ⚠️ 하한 8분 초과. fully-batch 전환 시 충족 예상 |
| 메모리 피크 | 4~8 GB | ~4 GB | ✅ 하한 충족 |
| 비용 (APK 1개) | $0.40~1.20 | $0 | ✅ 초과 (절감) |

---

## 6. 일반화 평가 (G9)

본 절은 PleOS (Android 14 + AAOS 변형) 환경에서 검증한 정적 분석 파이프라인이 **QNX / Linux 기반 IVI** 같은 다른 차량용 OS 로 일반화 가능한지를 평가한다. 평가는 (1) 도구 / (2) 키워드 카테고리 / (3) AAOS 매핑 / (4) TARA 자산의 4축으로 진행.

### 6.1 OS-종속 vs OS-독립 컴포넌트

| 컴포넌트 | OS-독립 | OS-종속 (Android/AAOS) | 비고 |
|---|---|---|---|
| `scripts/apk/decompile.sh` | ✗ | jadx (Java/Kotlin → DEX/APK 전용) | QNX/Linux 는 ELF |
| `src/deobf/entropy.py` | ✓ | — | 식별자 entropy 는 OS-독립 |
| `configs/prompts/stage1_detect.md` | 부분 | 일부 Android API 언급 | 룰 기반 보강 가능 |
| `configs/prompts/stage0_deobfuscate.md` | ✓ | — | 이름 복원은 OS-독립 |
| `src/evaluation/eval.py` / `src/evaluation/ablation.py` | ✓ | — | GT 라벨 스키마만 동일 |
| `configs/keywords.yaml` | 부분 | Android-specific 패턴 (`android:exported` 등) | 카테고리는 보편 |
| `configs/aaos_mapping.yaml` | ✗ | AAOS 섹션 번호 | OS별 가이드라인으로 swap |
| `src/mapping/tara_generate.py` | ✓ | — | ISO/SAE 21434 는 OS-독립 |
| `src/mapping/aaos_map.py` | 부분 | — | mapping yaml 만 swap |
| `src/viz/plot_metrics.py` | ✓ | — | 차트 |

**결론**: 약 60~70% 는 OS-독립. swap 이 필요한 부분은 (a) 디컴파일 도구 체인, (b) 키워드 룰셋, (c) 매핑 yaml.

### 6.2 QNX 환경으로의 swap 비용

| 항목 | Android (PleOS) | QNX |
|---|---|---|
| 바이너리 형식 | DEX/APK (Java/Kotlin) | ELF (C/C++ 주력, 일부 Java/Qt) |
| 권한 모델 | UID + Manifest permission | POSIX user/group + RBAC + adaptive policies |
| IPC 모델 | Intent / ContentProvider / Binder | QNX message passing (channels) |
| 자격증명 저장 | Android Keystore | (구현체) HSM / TEE / 파일 |
| 가이드라인 | AAOS Security | QNX Security Reference Manual |

| 작업 | 예상 작업량 |
|---|---|
| 디컴파일러 → Ghidra/IDA Pro 로 변경 | 2~3일 |
| QNX-specific 키워드 룰셋 | 1주 |
| QNX Security Reference Manual 매핑 yaml | 3~5일 |
| TARA 자산 카탈로그 수정 (process-level isolation 강화) | 2일 |
| DDS 보안 / mixed-criticality 격리 카테고리 추가 | 1주 |
| **합계** | **2~3주** (본 학기 환경 셋업 ~1주 대비) |

### 6.3 AGL (Automotive Grade Linux) 으로의 swap 비용

AGL 은 PleOS 와 더 가깝다 — 둘 다 Linux kernel + 사용자 공간 앱 모델. AGL 은 systemd + smack + cgroup 기반 보안으로 Android 의 SELinux 와 유사 컨셉. C++ / Qt / HTML5 위주.

| 작업 | 예상 작업량 |
|---|---|
| 디컴파일러 → 소스 직접 분석 (오픈소스 위주) | 1주 |
| AGL-specific 키워드 룰셋 | 3~5일 |
| AGL Security Best Practices 매핑 yaml | 3일 |
| Process / IPC 모델 (DBus, AFB) 카테고리 추가 | 1주 |
| **합계** | **2~3주** |

### 6.4 보편 finding vs OS-specific finding

**OS 변경에 그대로 작동**:
- hardcoded credential (`ssl-5`, `ucl1-1`) — KDF passphrase 는 OS 무관
- plaintext network (`ssl-6`) — gRPC / TCP / DDS 모두 적용
- weak crypto (`ucl1-2`) — AES/DES/MD5 식별은 OS 무관
- 차량 syslog 평문 — IVI 도메인 보편

**Android-specific, QNX/AGL 외삽 불가**:
- `lmp-1` (PromptsContentProvider exported) — Android Compose / Hilt / ContentProvider 모델 강의존
- `vc-3/4` 의 4중 차단 분석 — Android Compose Navigation 구조 특화

### 6.5 일반화 종합 평가

| 차원 | 일반화 가능성 | 근거 |
|---|---|---|
| 분석 방법론 (Multi-stage + ensemble) | **High** | 룰 + LLM 흐름은 OS 무관 |
| 평가 프레임워크 (P/R/F1 + Ablation) | **High** | GT 라벨 스키마만 동일하면 됨 |
| TARA 통합 흐름 | **High** | ISO/SAE 21434 기반 |
| 키워드 카테고리 | **Medium** | 6 카테고리 중 4 OS-독립, 2 swap |
| 가이드라인 매핑 yaml | **Medium** | 형식 동일, 내용 swap |
| 디컴파일 도구 체인 | **Low** | jadx → Ghidra/IDA 로 전체 swap |
| AAOS-specific finding (Compose Nav 등) | **Low** | Android-only, 외삽 불가 |

**총평**: 단계별 흐름과 측정 프레임워크는 OS 변경에 강건하다. swap 작업량은 2~3주 추정. 단 Android-specific finding 은 OS 별 등가물을 별도 라벨링 필요. 실제 수치 측정은 Future Work — PleOS 측정값 (P 78.9% → 100%, F1 0.882 → 0.966) 이 AGL 등에서 어떤 수치로 떨어지는지 정량 비교해야 일반화의 비용/효과가 결정.

---

## 7. 한계 및 위협 요인

본 절은 교수 리뷰에서 공격받을 수 있는 지점을 명시적으로 정리한다. 현재 결과는 pipeline feasibility를 보이는 데에는 충분하지만, 일반화 성능 주장으로 해석하기에는 아직 제한이 있다.

### 7.0 한계 카테고리 mapping (L1~L5 ↔ 4 validity)

본 보고서는 한계를 4 validity 카테고리 (internal / external / construct / tooling) 로 정리하지만, 학기 작업 노트 [`06_limitations_and_costs.md`](06_limitations_and_costs.md) 에는 5 라벨 (L1~L5) 로 분류되어 있다. cross-reference:

| Label | 설명 | 본 보고서 위치 | 상태 |
|---|---|---|---|
| **L1** | 네이티브 코드 분석 불가 | § 7.4 Tooling boundary | **부분 해소** — 학기 외 C 작업: radare2 + `src/native/native_analyze.py` 로 R3.c.2 sample n=4 정적 분석 (추가 vuln 0건, § 3.6.9). dynamic 행동은 Frida hook (학기 외 D, script ready) 후속 |
| **L2** | 표본 크기 작음 | § 7.2 External validity | **n=19 → n=47 해소 (R1.b / R1.d.2~d.5)**. McNemar p_exact=0.0215 < α=0.05 통계적 유의 도달 (§ 3.6.5) |
| **L3** | 본 실험의 기본 검증은 Claude Code 단일 모델 multi-perspective. 보충 실험으로 Codex 3-model cross-read n=47을 수행했으나 성능 우위는 없음 | § 7.1 Internal validity (same-model verification bias) | provenance를 `Claude Code baseline + Codex cross-read supplement`로 분리. Codex 결과는 recall 하락을 통해 prompt/evidence 품질의 중요성을 보여주는 보조 근거 |
| **L4** | MASTG corpus 의 hand-crafted 특성 | § 7.2 External validity (난독화 corpus 편향) | NewPipe baseline (R4 n=6, GOOD+ 67%) 으로 부분 해소 |
| **L5** | ~~Stage 3 ensemble 의 MASTG 미평가~~ | — | ✅ 2026-04-30 해소 (combined n=19 ablation 측정) |
| **L6** | ProGuard 활성 PleOS-customized APK 의 priority class 추출 yield 감소 | § 7.4 Tooling boundary | v1.2 신규 (R1.d.5 maps 1 finding / callandmessage 비즈니스 패키지 2 클래스). Stage 0 deobfuscation 통합 또는 manifest-only Stage 1 모드 권고. 학기 외 B(RAG) 가 부분 보조 |

### 7.1 Internal validity — 평가 절차 내부의 편향 가능성

- **Self-label bias**: PleOS 자체 라벨은 실제 도메인 특화 finding을 포함한다는 장점이 있지만, 연구자가 수동 분석으로 만든 라벨이므로 evaluator bias 가능성이 있다. 외부 corpus (MASTG n=4 + InsecureBankv2 n=9 + AOSP-derived n=4) 를 추가해 combined n=47 로 확장했으나, PleOS-customized 30 finding 은 여전히 self-label 이라 외부 라벨러 교차 검증은 Future Work.
- **Same-model verification bias**: Stage 3는 multi-LLM ensemble이 아니라 동일 모델을 여러 시각으로 재질문하는 방식이다. 따라서 모델 고유의 blind spot이 세 시각 모두에 공유될 수 있다.
- **Stage 2 upper-bound 해석 주의**: Ablation의 Stage 2 F1 1.000은 GT 기반 P-ceiling 시뮬레이션이며, 실제 자동 Stage 2의 독립 성능으로 해석하면 안 된다.

### 7.2 External validity — 다른 APK / 다른 IVI 환경으로의 일반화 한계

- **표본 크기**: combined n=47 로 확장 (R1.d.2~d.5). McNemar paired test 가 p_exact=0.0215 로 α=0.05 통계적 유의에 도달했으나 (§ 3.6.5), discordant pair b+c=10 으로 여전히 작아 n ≥ 60 추가 확장 시 power 강화 여지가 있다. 무료 commercial closed-source ProGuard 활성 APK 확보는 환경 제약으로 미달성 (Future Work).
- **PleOS APK 3종 편향**: 본 실험은 보안 가치가 높은 3개 APK를 우선 선택했다. 무작위 APK sample이나 전체 207개 APK에 대한 성능은 아직 측정하지 않았다.
- **PleOS-internal 사용자 base 추정 어려움**: 본 corpus의 attack feasibility는 정적 분석 단계 추정이다. 실차 시나리오 (네트워크 위치, 권한 grant 경로, 실제 app deployment policy) 는 반영되지 않았다.
- **난독화 corpus 편향**: UnCrackable Level1/2 의 `sg.vantagepoint` 는 hand-crafted anti-tamper helper이다. real-world commercial ProGuard'd 코드에서는 contextual hint가 약해 정확도 하락이 예상된다.

### 7.3 Construct validity — 측정 지표가 실제 보안 효과를 얼마나 반영하는가

- **오탐률 정의**: 본 보고서의 오탐률은 `FP/(TP+FP)`로, 전체 negative 대비 false positive rate가 아니라 reported finding 기준 false discovery rate이다.
- **Triage reduction과 recall의 분리**: 99.49% 축소율은 분석 효율성 지표이며, 제외된 class에 취약점이 없다는 의미가 아니다. 일부 sample에 대해 full manual audit 또는 broader static scanner와 비교해 missed finding을 측정하는 것은 Future Work 로 남는다.
- **Severity / TARA risk의 주관성**: Critical/High 등급은 정적 분석 evidence와 도메인 가정을 기반으로 산정했다. 실차 네트워크 위치, 권한 모델, 배포 정책이 달라지면 feasibility와 risk level이 바뀔 수 있다.

### 7.4 Tooling boundary — 분석 도구와 계층의 구조적 한계

- **Java-only 정적 분석 (L1)**: native lib 의존 패턴 (anti-tamper, RASP, crypto validation) 은 Stage 1 의 jadx 기반 pipeline 이 미커버한다. 외부 corpus 도입 시 UnCrackable-Level2 / r2pay-v1.0 두 sample 에서 in-scope finding 0건. **학기 외 C 작업으로 부분 해소** — radare2 + `src/native/native_analyze.py` 로 PleOS native sample n=4 정적 분석을 별도 track 으로 추가 (추가 vuln 0건, § 3.6.9). 즉 한계가 "Java/Kotlin scanner + native binary scanner 의 2-track 구조" 라는 architecture requirement 로 재서술되었고, native track 의 첫 sample-level 측정까지 완료. dynamic 행동 (Go runtime / JNI argument flow) 은 여전히 미관찰 — 학기 외 D 의 Frida hook script 가 ready 상태.
- **ProGuard 활성 APK 의 priority class yield 감소 (L6)**: R1.d.5 의 `ai.umos.maps` 는 ProGuard 활성으로 priority class 추출이 1 finding 으로 축소, `ai.umos.callandmessage` 는 비즈니스 패키지가 2 클래스만 남았다. Stage 0 deobfuscation 통합 또는 manifest-only Stage 1 모드가 권고된다.
- **디컴파일 artifact 의존성**: 본 pipeline은 jadx output을 입력으로 삼는다. jadx가 control/data-flow를 잘못 복원하거나 synthetic wrapper를 생성하면 LLM 판단에도 영향을 줄 수 있다.
- **Compose Navigation 의존 finding**: `vc-3` / `vc-4` 의 4중 차단 분석은 Android Compose Navigation 특화이다. 다른 UI framework 로 그대로 외삽할 수 없다.

### 7.5 v1.0 → v1.4 supplement 보강 계획 (해소 상태)

- ✅ 외부 corpus 확장 — InsecureBankv2 + AOSP-derived + R1.d.5 PleOS-customized 3 APK 누계로 **n=19 → n=47**. McNemar p_exact=0.0215 통계적 유의 도달 (학기 외 A).
- ⚠️ 일부 APK 에 대한 full-audit 또는 broader scanner 비교로 missed finding 측정 — Future Work (학기 외 작업, [`07_future_work.md`](07_future_work.md) F4 참조).
- ✅ Stage 3 명칭 `단일 모델 multi-perspective consensus` 로 통일 (§ 8.2 / Appendix B / Notation & Glossary).
- ✅ Pipeline 단계 명칭은 **Stage 0 / 1 / 2 / 3** 으로 통일. PPT 계획서의 "1차 / 2차 / 3차" 표기는 가설 수치 인용 시에만 유지 (mapping: 1차 = Stage 1, 2차 = Stage 2, 3차 = Stage 3).
- ✅ native boundary 를 한계가 아니라 architecture requirement 로 재서술 — § 5.5 / 8.3 의 "Java/Kotlin scanner + native binary scanner 의 2-track 구조" 권고에 더해, **학기 외 C 작업으로 native track 의 첫 sample-level 정량 측정 (R3.c.2 n=4, 추가 vuln 0건) 완료** (§ 3.6.9).
- ✅ RAG 도메인 지식 주입 — 학기 외 B 작업으로 Chroma 4 collection + intrinsic ablation (NN / AAOS 85.1%) 구현 (§ 3.6.8).
- ✅ Dynamic 검증 연계 — 학기 외 D 작업으로 deterministic state machine + 5 Frida hook script + 사례 연구 5건 추가 (§ 3.6.10, [`03_case_studies.md`](03_case_studies.md) Case 6~10).

---

## 8. 결론

본 학기 14주차 시점에 Phase A (환경 구축) → Phase B (Stage 1/2/3 검증 단계 적용) → Phase C (난독화 + 평가 프레임워크) → Phase D (AAOS / TARA 매핑 + 사례 연구 + 통합 + 일반화 평가) → Phase E (발표 + 보고서) 까지 완료했다. 학기 외 작업으로 A R1.d.5 / B RAG / C L1 native / D Dynamic 을 100% 도달했고, 이후 Codex 기반 Multi-model cross-read도 보충 실행했다. Multi-model 보충 실험은 성능 우위가 아니라 evidence packaging / prompt calibration 중요성을 보여주는 결과로 해석한다.

본 연구의 결론은 "LLM scanner 가 완벽한 취약점 탐지기" 라는 것이 아니다. 더 안전하고 본 corpus 측정값이 직접 뒷받침하는 결론은 다음과 같다.

> **LLM 을 deterministic keyword triage 와 caller/manifest 기반 도메인 검증 사이의 reasoning component 로 배치하면, combined corpus n=47 에서 IVI APK 보안 리뷰의 후보 검증 비용을 줄이고 후보 기준 FP 비율을 25% (가설) → 0% (Stage 3 ≥2/3 합의) 로 줄이는 정적 분석 pipeline 을 구성할 수 있다. 이 Stage 1 → Stage 3 향상은 paired McNemar test 에서 통계적으로 유의하다 (p_exact=0.0215 < α=0.05). 단, 이는 보안 가치 기반으로 선정된 corpus subset 에서 관찰된 결과이며 95% bootstrap CI 가 Precision ±10.6%p 인 점과 native-bound vuln 미커버 한계 (학기 외 C 로 native sample n=4 정적 측정 완료, dynamic 행동은 미관찰) 를 함께 명시한다.**

### 8.1 주요 정량 성과 (combined n=47, 2026-05-14 measure)

1. **Stage 1**: Precision 80.9% / Recall 100% / F1 **0.894** (95% CI [82.5%, 95.6%]) — 초기 계획서 가설 (1차 오탐률 25% → 측정 19.1%) 충족.
2. **Stage 3 ≥2/3 합의**: Precision 100% / Recall 97.4% / F1 **0.987** — 초기 계획서 가설 (Precision 0.93, 3차 오탐률 7% → 측정 0%) 충족·초과. 단 일반화 성능이 아니라 본 corpus 측정값.
3. **★ Stage 1 → Stage 3 향상의 통계적 유의성**: McNemar paired test p_exact=0.0215 (< α=0.05). n=28 (p=0.375, power 부족) 에서 학기 외 R1.d.5 + Stage 3 ensemble 확장으로 discordant b+c=10 확보 → 도달. 본 연구의 핵심 정량 contribution.
4. **Bootstrap CI 표본 효과**: n=19 → n=47 확장으로 Precision CI 폭 36.8%p → 21.3%p (-15.5%p), lower bound 57.9% → 70.2%. "n 증가 → CI 좁힘" 직접 측정.
5. **외부 corpus 누계 + R1.d.2~d.5**: MASTG 6 sample + InsecureBankv2 + AOSP-derived 2 + PleOS-customized 7 APK = 7 corpus origin. PleOS-customized P 76.7% vs AOSP-derived P 50.0% vs External vuln corpus P 100% — by-origin 분리로 RQ1 implication 강화.
6. **R3 native 2 axis**: corpus-level 10.6% (R3.a) + sample-level R3.c.2 n=4 / 추가 vuln 0건 (학기 외 C). real-world OSS (NewPipe) HIGH 난독화 1.7%, Stage 0 plausibility GOOD+ 67% (R4 n=6).
7. **RAG 도메인 지식 주입** (학기 외 B): Chroma 4 collection 158 chunks + intrinsic ablation NN verdict / AAOS alignment 둘 다 85.1%.
8. **Dynamic 검증 연계** (학기 외 D): deterministic state machine + 5 Frida hook script + 사례 연구 5건 (Case 6~10) — Static → Dynamic feedback 경로 구현 (runtime capture 는 환경 의존 후속).

### 8.2 본 연구의 직접 contribution

- **방법론**: LLM 을 black-box detector 가 아니라 reasoning component 로 배치하는 4단계 pipeline (Stage 0 / 1 / 2 / 3) 설계 + 결정론 코드와 LLM 의 역할 분리. 단일 모델 + 멀티 시각 ensemble 로 multi-LLM 환경 제약을 우회.
- **측정 프레임워크**: bootstrap CI / Cohen's κ / transition matrix / native lib inventory 등 corpus-level 직접 인덱스 5종을 결정론 스크립트로 구축 (재현 가능, deterministic seed).
- **AAOS / TARA 자동 매핑**: ISO/SAE 21434 기반 자산 카탈로그 + Threat Scenarios + Risk Matrix + Treatment 권고 자동 생성. 차량 SW 라이프사이클 (DEV → CI/CD → PR Gate → TARA → OTA → Production) 에 통합 가능한 권고 아키텍처 제시.
- **외부 GT corpus 비교**: OWASP MASTG 6 sample + InsecureBankv2 도입으로 self-label bias 완화. 4 boundary case 의 정량 입증으로 Java-only / native scanner 의 2-track architecture 권고 근거 마련.

### 8.3 산업 적용성 + Future Work

| 차원 | 본 연구 위치 (학기 + 학기 외 A~E) | 향후 |
|---|---|---|
| 분석 엔진 | Claude Code 인터랙티브 (단일 사용자) + Codex 3-model 보충 cross-read | PleOS-internal LLM 활성화 시 Stage 1/2/3 자동화. Multi-vendor API 앙상블은 별도 정책/예산 필요. |
| Native 분석 | **R3.c.2 native sample n=4 정적 측정 완료** (학기 외 C, 추가 vuln 0건) | Ghidra GolangAnalyzerExtension function-naming 복원 + Frida hook 으로 dynamic JNI flow capture. |
| 표본 / 통계 | **n=47 / Precision 95% CI ±10.6%p / McNemar p_exact=0.0215 유의** (학기 외 A) | n ≥ 60 corpus 로 CI 추가 좁힘 + by-origin 분리 정밀화. |
| 난독화 정확도 | hand-crafted 100% upper-bound / real-world GOOD+ 67% (R4 n=6) | commercial closed-source ProGuard mapping 확보 후 exact accuracy 측정. |
| 도메인 지식 | **RAG Chroma 4 collection 158 chunks + intrinsic ablation** (학기 외 B) | with/without-RAG end-to-end prompted-LLM ablation (FP rate 변화 측정). |
| Dynamic 검증 | **deterministic state machine + 5 Frida hook script ready** (학기 외 D) | PleOS Connect AVD frida-server attach 후 runtime capture. |
| OS 일반화 | PleOS-only | QNX / AGL 로 swap 2~3주 추정. 실제 측정값 확보 시 일반화의 비용/효과 결론. |
| 운영 | 권고/설계 | GitHub Actions 정적 부분 통합 → PleOS-internal LLM endpoint 활성화 → fully-batch 자동화. |

### 8.4 deliverable 종합 (학기 + 학기 외 A~E)

- **보고서 v1.4 supplement** (본 문서) — 8 장 + Notation & Glossary + Appendix A/B/C. 학기 외 A+B+C+D+E 통합본 + Codex multi-model 보충 결과
- **사례 연구 10건** ([`03_case_studies.md`](03_case_studies.md)) — 정적 5건 + 학기 외 D Dynamic 5건 (Case 6~10)
- **차트 6 장** (`data/viz/01~06_*.png`) — 차트 01~05 combined n=47 재생성, 06 obfuscation corpus live ([`05_charts.md`](05_charts.md) 참조)
- **AAOS/MASVS/TARA 자동 매핑 표** (`data/reports/aggregate/aaos_mapping_table.{md,json}`)
- **TARA artifact** (`data/reports/aggregate/tara_artifact.{md,json}`) — Risk Matrix Critical 2 / High 13 / Medium 6 / Low 2
- **RQ 측정값 자동 산출** — `data/reports/aggregate/{bootstrap_ci, stage_transitions, perspective_agreement, native_lib_inventory, mcnemar_test}.{md,json}` + `data/reports/rag_local/rag_ablation.{md,json}` (학기 외 B 의 rag_ablation 포함)
- **외부 corpus public reports** (`data/reports/external/{UnCrackable-Level1/2/3, r2pay-v1.0, InsecureBankv2}_*.{md,json}`)
- **Per-APK 보고서 마스킹 공개판** (`data/reports/public/`) — PleOS contract IP 보호 + 외부 검증 가능
- **6 prompt 영문 통일** (`configs/prompts/{stage0_deobfuscate, stage1_detect, stage3_attacker / defender / domain_expert / consensus}.md`) + 학기 외 B 의 `stage1_detect_rag.md`
- **결정론 분석 스크립트** — `src/evaluation/{eval, ablation}.py`, `src/mapping/{aaos_map, tara_generate}.py`, `src/deobf/entropy.py`, `src/viz/plot_metrics.py`, `src/native/native_analyze.py` (학기 외 C) + `src/rag/{build_index, retrieve, ablation}.py` (학기 외 B) + `src/dynamic/state_machine.py` + `src/dynamic/hooks/` 5 Frida script (학기 외 D) + `scripts/research/research_r{1a, 2a, 3a}_*.py`
- **GT corpus** (`data/ground_truth/`) — self_labels n=15, mastg/* n=4, insecurebankv2 n=9, AOSP-derived n=4, R1.d.5 PleOS-customized 추가 → **combined n=47**
- **Future Work 구현 명세** — [`08_future_work_implementations.md`](08_future_work_implementations.md) (학기 외 A~E 도달도 매트릭스 — Codex multi-model 보충 cross-read 포함)
- **PPT 빌드 스크립트** — 1페이지 progress (10~14주차) + 최종발표 (현재 v5 = 19 슬라이드, `scripts/build_ppt_w{10..14}_1page.py` + `build_ppt_final.py`). 수업개요 PDF 요구: 10분 내외 발표, 슬라이드 수 제약 없음 — 전략은 풀 커버판 (≤100p) 먼저 작성 후 발표용 10분 분량 축약
- **GitHub repo**: [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT) — scaffold + GT + 측정 스크립트 + 자동 산출물 공개

---

## Appendix A — 산출물 인덱스

| 분류 | 경로 |
|---|---|
| 코드 (deterministic) | `src/evaluation/{eval,ablation}.py`, `src/mapping/{aaos_map,tara_generate}.py`, `src/deobf/entropy.py`, `src/viz/plot_metrics.py` |
| 프롬프트 | `configs/prompts/{stage0_deobfuscate, stage1_detect, stage3_attacker, stage3_defender, stage3_domain_expert, stage3_consensus}.md` |
| 설정 | `configs/{keywords,aaos_mapping}.yaml`, `configs/result_schema.json` |
| Ground truth 라벨 | `data/ground_truth/{self_labels, combined_labels}.json`, `data/ground_truth/mastg/*.labels.json` |
| 본 보고서 + 보충 doc | `docs/{01_final_report, 03_case_studies, 05_charts, 06_limitations_and_costs, README}.md` |
| 자동 생성 산출물 | `data/reports/aggregate/{aaos_mapping_table, tara_artifact}.{md, json}`, `data/viz/01~06_*.png` |
| Per-APK 보고서 | `data/reports/per_apk_local/<apk>_<date>.{md, json}` (IP 보호로 비공개, 로컬 한정) |
| Raw 측정 노트 (시점 스냅샷) | `docs/archive/` (로컬 한정 — 본 보고서가 인용하는 1차 출처) |
| 공개 저장소 | [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT) |

## Appendix B — 주요 결정 사항

| 항목 | 결정 | 이유 |
|---|---|---|
| 에뮬레이터 이미지 | PleOS Connect v2.0.5 x86_64 | 본 과제 정합성 |
| 1차 분석 타겟 APK | `ai.umos.vehiclecontrol` | system UID + 13 위험 권한 + 차량 제어 |
| Stage 3 검증 방식 | 단일 모델 multi-perspective consensus (Claude Opus 4.7 + 시각 3종) | Claude Code 단일 모델 세션 제약 + 외부 유료 API 미보유. Multi-LLM ensemble로 주장하지 않음 |
| Ground truth 출처 | 자체 라벨링 + OWASP MASTG | 베이스라인 비교 + PleOS 특화 케이스 |

## Appendix C — PPT 계획서 vs 실측 정량 표

(학기 진척 표 + Phase D + 학기 외 A~E 측정값. PPT 의 "1차/2차/3차" 는 본 보고서의 Stage 1/2/3 과 동일. n=19 → n=47 은 R1.d.2~d.5 표본 확장 trajectory. 일반화 성능 주장이 아님.)

| 지표 | PPT 가설 / 목표 | 실측 / 현재 해석 (n=47 최종) |
|---|---|---|
| Stage 1 후보 기준 FP 비율 (PPT "1차") | 25% | 21.1% (n=19) → 14.3% (n=28) → **19.1% (n=47)** — 가설 충족 |
| Stage 2 후보 기준 FP 비율 (PPT "2차") | 12% | A.2 P-ceiling 1.000은 GT 기반 upper bound. 실제 Stage 2 독립 성능 주장 아님 |
| Stage 3 후보 기준 FP 비율 (PPT "3차") | 7% | **0%** (≥2/3 consensus, n=47) |
| Precision (Full) | 0.93 | Stage 1 0.809 / **Stage 3 ≥2/3 1.00** (n=47) |
| F1 (Stage 1) | — | **0.894** (n=47, 95% CI [0.825, 0.956]) |
| F1 (Stage 3 ≥2/3) | — | **0.987** (n=47) |
| McNemar paired (Stage 1 vs Stage 3) | — | **p_exact=0.0215 < α=0.05 통계적 유의** (n=47, 학기 외 A) |
| 분석 대상 축소율 | 30-40% | 99.49% triage reduction. 제외 class의 full-audit recall은 미검증 |
| 난독화 정확도 (5/6/8주차) | 40 / 65 / 78% | hand-crafted MASTG 100% exact (upper-bound) / real-world NewPipe GOOD+ 67% (R4 n=6, floor) |
| Native binary 분석 (R3.c.2) | — | native sample n=4 정적 분석, 추가 vuln 0건 (학기 외 C) |
| RAG intrinsic ablation | — | NN verdict 85.1% / AAOS alignment 85.1% / MASVS 23.4% (학기 외 B, n=47) |
| 처리 시간 (APK 1개) | 8~25분 | 인터랙티브 ~40분 (fully-batch 전환 시 8~15분 예상) |
| 비용 (APK 1개) | $0.40~1.20 | $0 (Claude Code 정액제) |

---

_본 보고서 v1.4 supplement 는 자율주행연구프로젝트1 학기 (Phase A~E) + 학기 외 Future Work A~E 결과를 통합한 버전 (2026-05-14). 기존 Claude Code baseline 과 Codex multi-model cross-read 보충 결과의 provenance 를 분리해 기록했다. 지도교수 리뷰 반영 시 차기 버전 갱신._
