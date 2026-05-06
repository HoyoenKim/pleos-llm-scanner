# LLM 기반 디컴파일러 분석 및 PleOS 적용 방안 검토

## 자율주행연구프로젝트1 — 중간 보고서 v0.9

| 항목 | 내용 |
|---|---|
| 작성자 | 김호연 |
| 학기 | 2026-1 |
| 연계과제 | 현대자동차 계약학과 육성형 연구과제 — PleOS TARA 및 실차 보안 취약점 점검 |
| 작성일 | 2026-04-30 (9주차) |
| 버전 | v0.9 (지도교수 1차 리뷰 대상) |

---

## Notation & Glossary

본 보고서에서 자주 등장하는 약어 / finding ID / 단계 명명을 한 곳에 정리.

### Pipeline 단계 (Stage 0 / 1 / 2 / 3)

| Stage | 명명 | 역할 |
|---|---|---|
| **Stage 0** | Deobfuscation (preprocessing, optional) | 식별자 obfuscation score ≥ 0.7 클래스에 LLM 이름 복원 |
| **Stage 1** | Initial Detection | 키워드 grep 후 priority class 에 단일 LLM 1-pass 6 카테고리 탐지 |
| **Stage 2** | Verification | caller chain + manifest + AST 룰 + LLM 재독으로 후보 verdict (TP/FP/uncertain) |
| **Stage 3** | Ensemble | 동일 모델 + 시각 3종 (공격자 / 방어자 / IVI 도메인 전문가) 합의. ≥2/3 동의 = TP, ≥3/3 = strong TP |

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
| L1 | Native 코드 분석 불가 (Java-only 정적 분석 한계) |
| L2 | 표본 크기 (n=19) — 통계적 유의성 caveat |
| L3 | Multi-LLM ensemble 미구현 (단일 모델 + 멀티 프롬프트로 대체) |
| L4 | MASTG corpus의 hand-crafted 특성 (난독화 정확도는 upper-bound) |
| L5 | Stage 3 ensemble의 MASTG 미평가 — 2026-04-30 해소됨 |

### Finding ID 컨벤션

본 보고서의 모든 finding 은 `<APK 약어>-<번호>` 형식.

| Prefix | APK | 카테고리 |
|---|---|---|
| `vc-` | `ai.umos.vehiclecontrol` (PleOS) | 차량 제어 앱, system UID + 13 위험 권한 |
| `ssl-` | `ai.pleos.sync.syslog` (PleOS) | 시스템 로그 sync, INTERNET + 외부 송출 |
| `lmp-` | `ai.pleos.llm.model.provider` (PleOS) | 온디바이스 LLM 모델 게이트웨이 |
| `ucl1-` | UnCrackable-Level1 (OWASP MASTG) | hardcoded AES key 챌린지 |
| `ucl3-` | UnCrackable-Level3 (OWASP MASTG) | XOR-key 챌린지 |

핵심 finding 요약 (severity = stage1 기준, verdict = Stage 3 합의 후):

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

전체 finding 별 정확한 (line, AAOS 매핑) 은 [`data/reports/aaos_mapping_table.md`](../data/reports/aaos_mapping_table.md) 참조.

---

## 0. 요약 (Executive Summary)

본 연구는 PleOS 탑재 IVI APK에 대해 **다단계 LLM 검증 + 결정론적 룰 + 외부 GT 베이스라인**을
결합한 정적 분석 파이프라인을 설계·구현하고, 실제 PleOS Connect v2.0.5 에뮬레이터에서
추출한 207개 시스템 APK 중 보안 가치가 높은 3종 (`ai.umos.vehiclecontrol`,
`ai.pleos.sync.syslog`, `ai.pleos.llm.model.provider`) 과 외부 OWASP MASTG corpus
(UnCrackable-Level1)에 적용하여 정량 측정값을 산출하였다.

### 핵심 측정값 (combined n=19 = PleOS 자체 라벨 15건 + OWASP MASTG 외부 corpus 4건)

| 지표 | PPT 가설 | 실측 | 충족 여부 |
|---|---|---|---|
| 1차 오탐률 (Stage 1) | 25% | **21.1%** | ✅ -3.9%p |
| 3차 오탐률 (Stage 3 ≥2/3) | 7% | **0%** | ✅ -7%p |
| Precision (Full Pipeline) | 0.93 | **1.00** (≥2/3 합의) | ✅ |
| F1 (Stage 1) | — | **0.882** | — |
| F1 (Stage 3 ≥2/3) | — | **0.966** | — |
| 분석 대상 축소율 | 30~40% | **99.49%** (1,765 → 9 priority class) | ✅ 초과 |
| 난독화 정확도 | 78% (8주차) | **100%** (UnCrackable n=17 exact) | ✅ 단, hand-crafted corpus caveat |

> **Update history**: 2026-04-30 초안은 n=18 (Stage 1 F1 0.875 / Stage 3 ≥2/3 F1 0.952). 같은 날 두 가지 보강으로 n=19 / F1 0.882 / 0.966 으로 갱신: (1) 외부 corpus(UnCrackable-Level1) finding 3건에 Stage 3 멀티 시각 평가를 새로 적용, (2) UnCrackable-Level3 sample (XOR-key 챌린지) 디컴파일 + Stage 1 적용해 finding 1건 (ucl3-1, hardcoded XOR key, HIGH) 추가.

### 핵심 산출물

1. **GitHub public repo**: [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT)
2. **GT corpus**: `data/ground_truth/combined_labels.json` (n=19, self 15 + MASTG 4)
3. **AAOS / MASVS / TARA 매핑 표**: `data/reports/aaos_mapping_table.{md,json}`
4. **TARA 시나리오 + Risk Matrix**: `data/reports/tara_artifact.{md,json}`
5. **사례 연구 5건**: `docs/case_studies.md`
6. **6개 시각화 차트**: `data/viz/01~06_*.png`

---

## 1. 연구 배경 및 목표

### 1.1 배경

PleOS는 현대자동차 그룹의 IVI 플랫폼이며, PleOS Connect v2.0.5는 Android 14 기반의
자체 변형 (AAOS-like)이다. IVI는 차량 안전과 사용자 자격증명, 위치/PII 데이터를
다루며 OTA 업데이트로 빈번히 갱신되므로 정적 분석 기반 보안 점검의 실용적
가치가 크다.

본 연구는 LLM (Claude Code, Opus 4.7)을 분석 엔진으로 하여 **APK → 디컴파일 →
키워드 → LLM 다단계 → AAOS / TARA 매핑** 파이프라인을 만들고, 그 정확도를
self-labeled GT + OWASP MASTG 외부 GT로 정량 평가한다.

### 1.2 목표 (PPT 계획서 기준)

| # | 목표 |
|---|---|
| G1 | 디컴파일러 도구 비교 + 환경 구축 (jadx 1순위) |
| G2 | 키워드 기반 우선순위 큐 + 분석 대상 축소 30-40% |
| G3 | LLM 다단계 검증 (1차 → 2차 → 3차) — 오탐률 25% → 12% → 7% |
| G4 | 난독화 코드 처리 (40% → 78% 정확도) |
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
| 단일 모델 세션 | "다중 LLM 앙상블"은 (B) **단일 모델 다중 프롬프트 앙상블**로 대체 |

---

## 2. 방법론

### 2.1 파이프라인 구조

```
APK
 └─ scripts/decompile.sh (jadx 1.5.5 --deobf)
     └─ data/decompiled/<apk>/sources/...
         └─ src/deobf/entropy.py (Shannon entropy)
             └─ HIGH 난독화? → configs/prompts/stage0_deobfuscate.md (LLM 이름 복원)
         └─ configs/keywords.yaml grep (priority queue)
             └─ Stage 1 LLM (configs/prompts/stage1_detect.md)
                 → finding 후보 (JSON schema 강제, configs/result_schema.json)
                 └─ Stage 2 caller 분석 + (선택) AST 룰
                     └─ Stage 3 멀티 프롬프트 합의
                         (configs/prompts/stage3_attacker.md
                        + stage3_defender.md
                        + stage3_domain_expert.md
                        + stage3_consensus.md)
                         └─ src/aaos_map.py + src/tara_generate.py
                             → data/reports/<apk>_<DATE>.{md,json}
                             → data/reports/aaos_mapping_table_<DATE>.md
                             → data/reports/tara_artifact_<DATE>.md
```

### 2.2 키워드 카테고리 (`configs/keywords.yaml`)

6 카테고리 — crypto / network / permission / intent / hardcoded / reflection_dynamic.
각 카테고리는 regex 패턴 + 기본 severity를 가진다.

### 2.3 다단계 LLM 검증

- **Stage 1**: 1-pass 키워드 + LLM 분석. 출력 = JSON-schema 강제 finding 객체.
- **Stage 2**: caller 추적 + AST/regex 룰 (regex는 자동, AST는 Future Work).
- **Stage 2.b**: deep-link audit (Compose Nav route + manifest URI + IntentRouter
  binding의 3-축 정합성).
- **Stage 3**: 동일 모델 (Opus 4.7), 다른 시각 3종 (attacker / defender /
  domain_expert) 의 합의. ≥2/3 동의 = TP, ≥3/3 = strong TP.

### 2.4 평가 프레임워크

- **GT 라벨**: `data/ground_truth/self_labels.json` (n=15 PleOS) +
  `data/ground_truth/mastg/uncrackable_level1.labels.json` (n=3 MASTG).
- **측정 코드**: `src/eval.py` (Precision / Recall / F1) + `src/ablation.py`
  (A 변형 — stage 1/2/3, B 변형 — 합의 임계 1/3-2/3-3/3).
- **시각화**: `src/viz/plot_metrics.py` — 6 차트 (PNG).

---

## 3. 실험 결과

### 3.1 분석 대상 축소율 (G2)

VehicleControl APK 기준:
- 디컴파일 결과: **1,765 Java files** (`ai/umos` + `ai/pleos`)
- 키워드 매치 후 priority class: **9개**
- 축소율: **99.49%** (PPT 가설 30-40% 대비 큰 폭 초과)

캐비어트: priority 9개 외에도 stage 2 caller 추적 시 후보가 늘어날 수 있음.

### 3.2 Stage 1 / Stage 3 오탐률 (G3) — combined n=19

| 단계 | n | TP | FP | Precision | F1 |
|---|---|---|---|---|---|
| Stage 1 (PleOS-only n=15) | 15 | 11 | 4 | 73.3% | 0.846 |
| Stage 1 (combined n=19) | 19 | 15 | 4 | **78.9%** | **0.882** |
| Stage 1 (MASTG-only n=4) | 4 | 4 | 0 | **100%** | — |
| Stage 3 ≥2/3 (combined n=19) | 19 | 14 | 0 | **100%** | **0.966** |
| Stage 3 ≥3/3 (combined n=19) | 19 | 12 strong | 0 | **100%** | 0.889 |

**핵심 결과**:
- Stage 1 P 78.9% (FP 21.1%) — 초기 계획서의 가설 25%에 -3.9%p 충족.
- Stage 3 ≥2/3 합의로 P 100% 달성 — 초기 계획서 가설 Precision 0.93 도달 + 초과.
- 합의 임계 ≥2/3 와 ≥3/3 의 차이는 두 finding 에서 발생: `ssl-4` (sync.syslog 의 PII toString) 과 `ucl1-3` (UnCrackable-Level1 의 logging hardening) 가 시각 3종 중 2종에서만 합의 — emission 경로가 코드만으로 확정되지 않아 1 시각이 uncertain. 두 finding 을 잡으려면 ≥2/3 가 default 적합.

### 3.3 Ablation (combined n=19)

#### Variant A — 단계 추가 효과

| 변형 | 표본 | F1 | 비고 |
|---|---|---|---|
| A.1 Stage 1 only | n=15 → 18 → 19 | 0.846 → 0.875 → **0.882** | 표본이 늘면서 Precision 안정 |
| A.2 + Stage 2 (caller) | 모든 n | **1.000** | GT 기반 P-ceiling 시뮬 (caller 분석 단계의 상한) |
| A.3 + Stage 3 (≥3/3) | n=19 | **0.889** | 초기 측정값 (n=18 시점 0.783) 은 외부 corpus(MASTG) 의 Stage 3 평가 누락이 만든 artifact 였다. Stage 3 평가를 외부 corpus에 확장 + UnCrackable-Level3 추가 후 일관성 회복 |

#### Variant B — Stage 3 합의 임계 sensitivity (combined n=19)

| 임계 | Precision | Recall | F1 |
|---|---|---|---|
| ≥1/3 (시각 1 종 이상이 flag) | 78.9% | 100% | 0.882 |
| **≥2/3 (default — 다수결)** | **100%** | **93.3%** | **0.966** ← 초기 계획서 가설 0.93 초과 |
| ≥3/3 (만장일치) | 100% | 80.0% | 0.889 |

### 3.4 난독화 정확도 (G4)

OWASP MASTG의 UnCrackable-Level1/2 의 `sg.vantagepoint` 패키지 (anti-tamper helper) 에 Stage 0 (deobfuscation) 프롬프트 적용:
- n=17 (6 class + 11 method) — **exact match 100%**
- 초기 계획서 가설 (8주차 시점 78%) 도달. 단 hand-crafted MASTG corpus 한정 — real-world commercial ProGuard 코드에서는 contextual hint 약화로 정확도 하락 예상 (한계 L4).

**예상과 다른 발견**: PleOS APK 3종은 HIGH 난독화 클래스 비율이 **0.2~0.4%** 로 매우 낮음. PleOS 빌드는 의미적 클래스명을 그대로 유지. 초기 계획서가 가정한 "고난독화 IVI 코드" 시나리오와 정량적으로 다르다 — narrative 정정 권고.

### 3.5 외부 GT 베이스라인 (G8)

self GT (PleOS 자체 라벨) 만으로 평가하면 self-referential. 외부 정답이 공개된 corpus 가 필요해 OWASP MASTG (Mobile Application Security Testing Guide) 의 Crackmes 3종 도입.

| Sample | in-scope finding | 결과 |
|---|---|---|
| UnCrackable-Level1 | 3건 | 모두 TP, MASTG-only **Precision 100%** |
| UnCrackable-Level2 | 0건 | 핵심 검증 로직이 `libfoo.so` 의 native method, Java 측엔 anti-tamper만 |
| r2pay-v1.0 | 0건 | token 생성이 `libnative-lib.so`, Java 측은 wrapper |

**Pipeline boundary 정량 입증**: Java-only 정적 분석은 native lib 의존 패턴 (MASVS-CODE / MASVS-RESILIENCE 일부) 을 못 잡음. 본 학기 한계로 명시 (한계 L1).

### 3.6 기존 도구 베이스라인 비교

기존 4종 도구 / 방법과 정성+정량 비교:

| 베이스라인 | 자체 정량값 | 본 연구 대비 |
|---|---|---|
| ① jadx + 수동 분석가 | self GT 가 manual baseline (분석가 시간 6~7h) | 본 파이프라인 ~2h (3배 단축) |
| ② 단일 LLM 1-pass (검증 단계 없이) | Stage 1 자체 (Precision 77.8%) | Stage 2 / Stage 3 거치며 Precision 100% (+22.2%p) |
| ③ android-scanner-ai (X-Vector) | **자체 P/R/F1 측정값 부재** + Gemini API key 의존 | 본 연구가 정량 평가 gap 제공 |
| ④ Androidmeda (In3tinct) | deobfuscation 위주, 자체 측정값 부재, Apache 2.0 | Stage 0 통합 후보 |

---

## 4. AAOS / MASVS / TARA 매핑 (G5 / G6)

### 4.1 AAOS 섹션 커버리지 (auto-generated, n=19)

| AAOS Section | Findings | TP | HIGH |
|---|---|---|---|
| 3.7 Permission Model | 7 | 5 | 3 |
| 4.2 Credential Protection | 7 | 7 | 4 |
| 5.1 Communication Security | 4 | 2 | 1 |

본 corpus에서는 AAOS §3.7 / 4.2 / 5.1 만 커버. §4.1 Lockscreen, §6 OTA / Verified
Boot 등은 본 corpus 미해당 → Future Work.

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

상세는 [`docs/case_studies.md`](case_studies.md). 요약:

| Case | Finding | 의의 |
|---|---|---|
| 1 | `ssl-5` (sync.syslog 의 BuildConfig.IDENTIFIER 를 KDF passphrase 로) vs `ucl1-1` (UnCrackable-Level1 의 hardcoded AES key) | 자체 corpus 와 외부 corpus의 동일 카테고리 finding 비교 — AAOS §4.2 (자격증명 보호) 매핑 일관성 |
| 2 | `vc-3` / `vc-4` (FP 4중 차단) | multi-stage 검증의 효과 정량 입증 — Stage 1 P 77.8% → Stage 3 합의 P 100% |
| 3 | `ssl-6` (sync.syslog 의 gRPC `.usePlaintext()`) | Stage 1 MEDIUM → Stage 3 HIGH 격상 사례 — 합의 임계 ≥2/3 vs ≥3/3 차이 설명 |
| 4 | `lmp-1` (llm.model.provider 의 exported PromptsContentProvider) | IVI / on-device LLM 도메인 특화 finding |
| 5 | `vc-6` (VehicleControl macAddress 미검증) | Critical risk + 차량 안전 직결 |

---

## 5. 통합 아키텍처 권고 (G6 보강)

상세는 `docs/integration_architecture.md`. 본 학기 산출물을 PleOS 운영
라이프사이클에 어떻게 통합할 수 있는지 권고:

```
DEV (소스 + Gradle)
  → CI/CD (pleos-llm-scanner: jadx + LLM stage 1/2/3 + AAOS/TARA mapping)
    → PR Gate (Critical=0, High≤N)
      → TARA Workflow (자산 카탈로그 → Threat Scenarios → Risk Matrix → Treatment)
        → OTA Gating (서명 + Staged rollout)
          → Production Vehicle (telemetry → 다시 TARA로 피드백)
```

본 학기 PoC는 정적 분석 + AAOS/TARA 매핑까지. 운영 통합은 PleOS-internal LLM
endpoint 정의 후 (Future Work).

---

## 6. 일반화 평가 (G9)

상세는 `docs/generalization_assessment.md`. 요약:

| 차원 | QNX | AGL (Linux IVI) | 평가 |
|---|---|---|---|
| 분석 방법론 | High | High | OS 무관, 그대로 |
| 평가 프레임워크 | High | High | GT 라벨 스키마만 동일 |
| TARA 통합 | High | High | ISO/SAE 21434 기반 |
| 키워드 카테고리 | Medium | Medium | 6 중 4 OS-독립 |
| 매핑 yaml | Medium | Medium | 형식 동일, 내용 swap |
| 디컴파일 도구 | Low | Low | jadx → Ghidra/IDA, ELF parser |

총 swap 작업량 추정: **2-3주**. 본 학기 환경 셋업 (~1주)에 비해 대형 작업이지만
방법론은 그대로 활용 가능.

---

## 7. 한계 및 위협 요인

### 7.1 측정 caveat

- **표본 작음**: n=19로 확장됐지만 통계적 일반화에는 여전히 부족. 추가 MASTG sample (certificatePinningXamarin,
  certificatePinning 등) + 의도적 취약 corpus (DIVA, InsecureBankv2) 도입 필요.
- **PleOS-internal 사용자 base 추정 어려움**: 본 corpus의 attack feasibility는
  정적 분석 단계 추정. 실차 시나리오 (네트워크 위치, 권한 grant 경로) 미반영.
- **난독화 측정의 hand-crafted corpus caveat**: UnCrackable Level1/2 의 sg.vantagepoint
  는 의도적 anti-tamper helper. real-world commercial ProGuard'd 코드에서는
  contextual hint 약해 정확도 하락 예상.

### 7.2 환경 제약 영향

- **단일 모델 세션** → Multi-LLM ensemble을 (B) 단일 모델 다중 프롬프트로 대체.
  PPT narrative 변경 ("다중 LLM 앙상블" → "단일 LLM 다중 프롬프트 앙상블").
- **외부 LLM API 미보유** → ③ android-scanner-ai 직접 비교 측정 불가, 정성 비교만.
- **실차 접근 불가** → 정적 분석에 머무름, 동적 검증 (instrument, fuzz, 실차 통신
  관찰)은 Future Work.

### 7.3 Pipeline boundary

- **Java-only 정적 분석** → native lib 의존 패턴 (anti-tamper, RASP) 미커버. 외부 corpus 도입 시 UnCrackable-Level2 / r2pay-v1.0 두 sample 에서 in-scope finding 0건 — 정량 입증된 한계 (한계 L1).
- **Compose Navigation 의존 finding** → `vc-3` / `vc-4` 의 4중 차단 분석은 Android Compose Navigation 특화. 다른 UI framework 로 외삽 불가.

---

## 8. 결론

본 학기 9주차 시점에 학기 계획서의 5~8주차 분량을 모두 따라잡고, Phase A (환경) → Phase B (Stage 1/2/3 다단계 검증) → Phase C 진입 측정 (난독화) → Phase D (AAOS / TARA 매핑 + 사례 연구 + 통합 + 일반화) 까지 완료하였다.

**주요 성과**:
1. 초기 계획서의 정량 가설 (1차 오탐 25%, Full pipeline Precision 0.93, 분석 대상 축소 30-40%) 모두 충족 또는 초과.
2. Stage 3 합의 임계 ≥2/3 에서 **Precision 100% / Recall 93.3% / F1 0.966** (combined n=19) — 가설 Precision 0.93 도달·초과.
3. 자체 GT (n=15) + OWASP MASTG (n=4) combined corpus 로 외부 베이스라인 비교 체계 구축.
4. Pipeline boundary 정량 입증 — UnCrackable-Level2 / r2pay-v1.0 두 sample 에서 Java-only 정적 분석의 in-scope finding 0건 도출. 본 학기 한계 (L1) 의 객관적 근거.
5. AAOS / TARA 자동 매핑 + 5건 사례 연구 + 통합 아키텍처 권고 + 일반화 평가 등 학기 deliverable 완료.

**남은 작업 (10~14주차)**:
- 표본 확장 (MASTG 추가 sample, 의도적 취약 corpus 도입)
- 운영 비용 평가 (Claude Code 정액제 사용 시 정확한 시간 측정)
- 발표 PPT v1.0 + 라이브 데모 시나리오
- 지도교수 1차 리뷰 → 보고서 v1.0

---

## Appendix A — 산출물 인덱스

| 분류 | 경로 |
|---|---|
| 코드 (deterministic) | `src/{eval,ablation,aaos_map,tara_generate}.py`, `src/deobf/entropy.py`, `src/viz/plot_metrics.py` |
| 프롬프트 | `configs/prompts/{stage0_deobfuscate, stage1_detect, stage3_attacker, stage3_defender, stage3_domain_expert, stage3_consensus}.md` |
| 설정 | `configs/{keywords,aaos_mapping}.yaml`, `configs/result_schema.json` |
| Ground truth 라벨 | `data/ground_truth/{self_labels, combined_labels}.json`, `data/ground_truth/mastg/*.labels.json` |
| 본 보고서 + 통합 doc | `docs/{report_v0.9, case_studies, integration_architecture, generalization_assessment, viz, week11_limitations_costs, README}.md` |
| 자동 생성 산출물 | `data/reports/{aaos_mapping_table, tara_artifact}.{md, json}`, `data/viz/01~06_*.png` |
| Per-APK 보고서 | `data/reports/<apk>_<date>.{md, json}` (IP 보호로 비공개, 로컬 한정) |
| Raw 측정 노트 (시점 스냅샷) | `docs/archive/` (로컬 한정 — 본 보고서가 인용하는 1차 출처) |
| 공개 저장소 | [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT) |

## Appendix B — 주요 결정 사항

| 항목 | 결정 | 이유 |
|---|---|---|
| 에뮬레이터 이미지 | PleOS Connect v2.0.5 x86_64 | 본 과제 정합성 |
| 1차 분석 타겟 APK | `ai.umos.vehiclecontrol` | system UID + 13 위험 권한 + 차량 제어 |
| 3차 검증 방식 | 단일 LLM 다중 프롬프트 앙상블 (Claude Opus 4.7 + 시각 3종) | Claude Code 단일 모델 세션 제약 + 외부 유료 API 미보유 |
| Ground truth 출처 | 자체 라벨링 + OWASP MASTG | 베이스라인 비교 + PleOS 특화 케이스 |

## Appendix C — PPT 계획서 vs 실측 정량 표

(학기 진척 표 + Phase D 측정값)

| 지표 | PPT 가설 | 실측 |
|---|---|---|
| 1차 오탐률 | 25% | 21.1% (n=19) |
| 2차 오탐률 | 12% | A.2 P-ceiling 1.000 (GT 기반 caveat) |
| 3차 오탐률 | 7% | 0% (≥2/3 합의) |
| Precision (Full) | 0.93 | 1.00 (≥2/3) |
| F1 (Stage 1) | — | 0.882 |
| F1 (Stage 3 ≥2/3) | — | 0.966 |
| 분석 대상 축소율 | 30-40% | 99.49% |
| 난독화 정확도 (5주차) | 40% | 100% (caveat) |
| 난독화 정확도 (6주차) | 65% | 100% (동일 caveat) |
| 난독화 정확도 (8주차) | 78% | 100% (동일 caveat) |
| 처리 시간 (APK 1개) | 8~25분 | 측정 미완 |
| 비용 (APK 1개) | $0.40~1.20 | N/A (Claude Code 정액제) |

---

_본 보고서는 자율주행연구프로젝트1 9주차 시점의 v0.9. 지도교수 1차 리뷰 후 v1.0
업데이트 예정 (10주차 이후)._
