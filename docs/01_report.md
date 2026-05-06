# LLM 기반 디컴파일러 분석 및 PleOS 적용 방안 검토

## 자율주행연구프로젝트1 — 중간 보고서 v0.9-r1

| 항목 | 내용 |
|---|---|
| 작성자 | 김호연 |
| 학기 | 2026-1 |
| 연계과제 | 현대자동차 계약학과 육성형 연구과제 — PleOS TARA 및 실차 보안 취약점 점검 |
| 작성일 | 2026-04-30 (9주차) |
| 버전 | v0.9-r1 (리뷰 반영본: 정량 주장 완화 + metric 정의 보강) |

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
| L3 | Multi-LLM ensemble 미구현. 본 보고서는 단일 모델 multi-perspective consensus 로 범위를 한정 |
| L4 | MASTG corpus의 hand-crafted 특성 (난독화 정확도는 upper-bound) |
| L5 | Stage 3 consensus의 MASTG 미평가 — 2026-04-30 해소됨 |

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

전체 finding 별 정확한 (line, AAOS 매핑) 은 [`data/reports/aaos_mapping_table.md`](../data/reports/aaos_mapping_table.md) 참조.

---

## 0. 요약 (Executive Summary)

본 연구의 핵심 질문은 **자동차 IVI APK 보안 점검에서 LLM을 단독 탐지기가 아니라, deterministic triage와 도메인 검증 규칙 사이의 reasoning component로 사용할 때 실용적인 정적 분석 pipeline을 만들 수 있는가**이다.

이를 위해 PleOS 탑재 IVI APK에 대해 **다단계 LLM 검증 + 결정론적 룰 + 외부 GT 베이스라인**을 결합한 정적 분석 파이프라인을 설계·구현하였다. 실험은 PleOS Connect v2.0.5 에뮬레이터에서 추출한 207개 시스템 APK 중 보안 가치가 높은 3종 (`ai.umos.vehiclecontrol`, `ai.pleos.sync.syslog`, `ai.pleos.llm.model.provider`) 과 외부 OWASP MASTG corpus (UnCrackable-Level1/3)에 적용하였다.

단, 본 보고서의 정량값은 **combined corpus n=19에 대한 초기 feasibility 결과**이다. 따라서 아래 수치는 일반화 성능이라기보다, 현재 corpus에서 관찰된 pipeline 동작과 한계를 보여주는 측정값으로 해석해야 한다.

### 핵심 측정값 (combined n=19 = PleOS 자체 라벨 15건 + OWASP MASTG 외부 corpus 4건)

| 지표 | PPT 가설 / 목표 | 제한된 corpus 실측 | 해석 |
|---|---|---|---|
| 1차 후보 기준 FP 비율 (Stage 1) | 25% | **21.1%** | 초기 목표 대비 낮게 관찰. 단, `FP/(TP+FP)` 기준 |
| 3차 후보 기준 FP 비율 (Stage 3 ≥2/3) | 7% | **0%** | reported finding 기준 FP 0건. 단, n=19라 일반화 주장 불가 |
| Precision (Full Pipeline) | 0.93 | **1.00** (≥2/3 합의) | 제한 corpus에서 관찰된 값 |
| F1 (Stage 1) | — | **0.882** | 초기 탐지 단계의 baseline |
| F1 (Stage 3 ≥2/3) | — | **0.966** | 다수결 consensus 적용 후 관찰값 |
| 분석 대상 축소율 | 30~40% | **99.49%** (1,765 → 9 priority class) | triage efficiency 지표. 제외 class의 full-audit recall은 미검증 |
| 난독화 이름 복원 정확도 | 78% (8주차) | **100%** (UnCrackable n=17 exact) | hand-crafted MASTG corpus에서의 upper-bound 성격 |

> **Metric note**: 본 보고서의 ‘오탐률’은 전체 non-vulnerable code element 대비 false positive rate가 아니라, LLM이 report한 finding 후보 중 FP의 비율인 `FP / (TP + FP)`로 정의한다. 엄밀히는 false discovery rate에 가깝다.

> **Update history**: 2026-04-30 초안은 n=18 (Stage 1 F1 0.875 / Stage 3 ≥2/3 F1 0.952). 같은 날 두 가지 보강으로 n=19 / F1 0.882 / 0.966 으로 갱신하였다: (1) 외부 corpus(UnCrackable-Level1) finding 3건에 Stage 3 multi-perspective consensus 평가를 적용, (2) UnCrackable-Level3 sample (XOR-key 챌린지) 디컴파일 + Stage 1 적용으로 finding 1건 (ucl3-1, hardcoded XOR key, HIGH) 추가.

### 핵심 산출물

1. **GitHub public repo**: [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT)
2. **GT corpus**: `data/ground_truth/combined_labels.json` (n=19, self 15 + MASTG 4)
3. **AAOS / MASVS / TARA 매핑 표**: `data/reports/aaos_mapping_table.{md,json}`
4. **TARA 시나리오 + Risk Matrix**: `data/reports/tara_artifact.{md,json}`
5. **사례 연구 5건**: `docs/02_case_studies.md`
6. **6개 시각화 차트**: `data/viz/01~06_*.png`

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
| G3 | LLM 다단계 검증 (1차 → 2차 → 3차) — reported finding 기준 FP 비율 25% → 12% → 7% |
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
 └─ scripts/decompile.sh (jadx 1.5.5 --deobf)
     └─ data/decompiled/<apk>/sources/...
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
- **Stage 2**: caller chain + manifest + regex rule 기반 검증. AST rule은 설계에는 포함되어 있으나 v0.9-r1에서는 자동화 범위 밖이며, 일부 확인은 수동/LLM 재독으로 보완한다.
- **Stage 2.b**: deep-link audit (Compose Nav route + manifest URI + IntentRouter binding의 3-축 정합성).
- **Stage 3**: 동일 모델 (Opus 4.7)을 다른 시각 3종 (attacker / defender / domain_expert) 으로 재질문하는 **single-model multi-perspective consensus**. ≥2/3 동의 = TP, ≥3/3 = strong TP.

> 본 보고서에서는 Stage 3를 multi-LLM ensemble로 주장하지 않는다. 외부 유료 API와 복수 모델 세션이 없는 환경 제약 때문에, 단일 모델을 여러 보안 관점으로 재질문하는 self-consistency 방식으로 범위를 한정한다.

### 2.4 평가 프레임워크

- **GT 라벨**: `data/ground_truth/self_labels.json` (n=15 PleOS) + `data/ground_truth/mastg/uncrackable_level1.labels.json` (n=3 MASTG) + `data/ground_truth/mastg/uncrackable_level3.labels.json` (n=1 MASTG).
- **측정 코드**: `src/eval.py` (Precision / Recall / F1) + `src/ablation.py` (A 변형 — stage 1/2/3, B 변형 — 합의 임계 1/3-2/3-3/3).
- **시각화**: `src/viz/plot_metrics.py` — 6 차트 (PNG).

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

PleOS self-label은 실제 도메인 특화 finding을 포함한다는 장점이 있지만, 연구자가 직접 라벨링했기 때문에 evaluator bias 가능성이 있다. 이를 완화하기 위해 OWASP MASTG 기반 외부 corpus를 추가했으나 현재 n=4로 작다. 따라서 10~14주차에는 외부 corpus를 DIVA, InsecureBankv2, 추가 MASTG sample로 확장해 self-label 의존도를 낮춘다.

---

## 3. 실험 결과

### 3.1 분석 대상 축소율 / triage reduction (G2)

VehicleControl APK 기준:
- 디컴파일 결과: **1,765 Java files** (`ai/umos` + `ai/pleos`)
- 키워드 매치 후 priority class: **9개**
- triage reduction: **99.49%** (1,765 → 9 priority class)

이 값은 **분석 효율성 지표**이다. 즉, 사람이 우선적으로 검토해야 할 class 수를 크게 줄였다는 의미이며, 제외된 1,756개 class에 취약점이 없음을 보장하는 full-audit recall 지표는 아니다. Stage 2 caller 추적 시 priority 9개 외부의 caller/callee가 추가로 분석될 수 있으며, 최종 v1.0에서는 일부 APK에 대해 broader static scanner 또는 manual audit과 비교해 missed finding 여부를 별도 확인할 필요가 있다.

### 3.2 Stage 1 / Stage 3 후보 기준 FP 비율 (G3) — combined n=19

| 단계 | n | TP | FP | Precision | F1 |
|---|---|---|---|---|---|
| Stage 1 (PleOS-only n=15) | 15 | 11 | 4 | 73.3% | 0.846 |
| Stage 1 (combined n=19) | 19 | 15 | 4 | **78.9%** | **0.882** |
| Stage 1 (MASTG-only n=4) | 4 | 4 | 0 | **100%** | — |
| Stage 3 ≥2/3 (combined n=19) | 19 | 14 | 0 | **100%** | **0.966** |
| Stage 3 ≥3/3 (combined n=19) | 19 | 12 strong | 0 | **100%** | 0.889 |

**핵심 해석**:
- Stage 1은 combined n=19에서 Precision 78.9%, 후보 기준 FP 비율 21.1%로 관찰되었다. 이는 초기 계획서의 Stage 1 목표값 25%보다 낮지만, n=19에 대한 초기 측정값으로만 해석한다.
- Stage 3 ≥2/3 consensus에서는 현재 corpus 기준 FP가 0건이었다. 다만 이 결과는 limited corpus에서의 관찰값이며, 일반화 성능으로 주장하지 않는다.
- 합의 임계 ≥2/3 와 ≥3/3 의 차이는 두 finding 에서 발생한다: `ssl-4` (sync.syslog 의 PII toString) 과 `ucl1-3` (UnCrackable-Level1 의 logging hardening) 가 시각 3종 중 2종에서만 합의되었다. emission 경로가 코드만으로 확정되지 않아 1 시각이 uncertain으로 남았기 때문에, 현재 corpus에서는 ≥2/3가 default threshold로 더 적합하다.

### 3.3 Ablation (combined n=19)

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

**예상과 다른 발견**: PleOS APK 3종은 HIGH 난독화 클래스 비율이 **0.2~0.4%** 로 매우 낮았다. 즉, 본 학기 PleOS sample은 초기 계획서가 가정한 "고난독화 IVI 코드" 시나리오와 정량적으로 달랐다. 따라서 v1.0 narrative에서는 "PleOS 코드 자체의 난독화 대응"보다 "외부 obfuscated corpus에서 Stage 0 feasibility 확인"으로 표현하는 편이 안전하다.

### 3.5 외부 GT 베이스라인 및 pipeline boundary (G8)

self GT (PleOS 자체 라벨)만으로 평가하면 self-referential bias가 생길 수 있다. 이를 완화하기 위해 외부 정답이 공개된 OWASP MASTG Crackmes 3종을 도입하였다.

| Sample | in-scope finding | 결과 |
|---|---|---|
| UnCrackable-Level1 | 3건 | 모두 TP. 단, MASTG-only n=4의 일부이므로 일반화 성능으로 해석하지 않음 |
| UnCrackable-Level2 | 0건 | 핵심 검증 로직이 `libfoo.so` 의 native method, Java 측엔 anti-tamper만 |
| r2pay-v1.0 | 0건 | token 생성이 `libnative-lib.so`, Java 측은 wrapper |
| UnCrackable-Level3 | 1건 | XOR key hardcoded finding 추가 |

**해석**: 본 pipeline은 Java/Kotlin layer의 Android framework misuse, exported component, hardcoded secret, plaintext communication 탐지에는 유용하지만, native library에 핵심 검증 로직이 숨겨진 경우에는 구조적 blind spot을 가진다. 따라서 PleOS 적용 시 Java/Kotlin layer scanner와 native binary scanner를 분리된 stage로 구성해야 한다.

### 3.6 RQ 직접 측정값 (2026-05-06 추가)

본 학기의 4 sub-question 중 3개 (RQ1 sensitivity / RQ2 perspective diversity / RQ3 native boundary) 의 첫 corpus-level 측정. 결정론적 스크립트 (`scripts/research_r{1a,2a,3a}_*.py`) 로 재현 가능.

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

**해석**: Stage 3 합의 임계가 단순 noise 가 아니라 정확한 filtering 임을 직접 입증. 단 표본 우연성 배제는 R1.b bootstrap CI / R1.d 표본 확장 (n ≥ 30) 후 가능. 산출: [`data/reports/stage_transitions.{md,json}`](../data/reports/stage_transitions.md).

#### 3.6.2 RQ2 — Perspective disagreement (multi-prompt diversity 진단)

시각 3종 (attacker / defender / domain_expert) 간 Cohen's κ 측정으로 ensemble 의 diversity 가 진짜인지 검증:

| Pair | agree % | both flag | only A | only B | κ |
|---|---:|---:|---:|---:|---:|
| attacker ↔ defender | 63.2% | 12 | 0 | 7 | **0.0** |
| attacker ↔ domain_expert | 89.5% | 11 | 1 | 3 | **0.759** |
| defender ↔ domain_expert | 73.7% | 14 | 5 | 0 | **0.0** |

**Flag rate per perspective**: attacker 63.2% (12) / **defender 100% (19, universal)** / domain_expert 73.7% (14).

**해석**: defender prompt 가 19건 모두 flag → diversity 측면에서 redundant. 의미 있는 disagreement 는 attacker ↔ domain_expert 사이에서만 (κ=0.759, substantial agreement). 즉 본 multi-perspective ensemble 의 정확도 향상은 사실상 attacker 와 domain_expert 두 시각의 합의에서 온 것이고 defender 는 ceiling 역할만. **Stage 3 prompt 보강 권고** = defender prompt 를 더 selective 하게 다듬어야 ensemble 비용 대비 효율 올라감. 산출: [`data/reports/perspective_agreement.{md,json}`](../data/reports/perspective_agreement.md).

#### 3.6.3 RQ3 — Java-only boundary 의 corpus 인덱스

본 pipeline 이 미커버하는 native lib 비중을 PleOS Connect 207 system APK 에서 직접 측정:

| Origin | n | with native | % |
|---|---:|---:|---:|
| PleOS (`ai.umos.*` / `ai.pleos.*`) | 138 | 14 | **10.1%** |
| AOSP (Android framework / Google) | 64 | 7 | 10.9% |
| third-party | 5 | 1 | 20.0% |
| **Overall** | **207** | **22** | **10.6%** |

**Top 5 native-heavy APKs**: `ai.pleos.playground.caas` (62 .so), `ai.umos.maps.android.navigation.app` (44), `ai.umos.ambientai` (24), `com.antutu.benchmark.full.lite` (20), `ai.umos.appmarket` (12).

**해석**: 한계 L1 (Java-only) 의 corpus-level 인덱스 = **PleOS 10.1%, 전체 10.6% APK 가 본 pipeline 의 blind spot**. 더 중요한 점은 차량 제어 / 맵 navigation / 음성 비서 같이 **보안 가치가 큰 컴포넌트가 native 비중 top** — 단순히 10% 가 아니라 "위험도 가중 10%" 로 해석해야. RQ3.c (native-bound vuln 정량) 는 radare2 통합 (Future Work) 후 가능. 산출: [`data/reports/native_lib_inventory.{md,json}`](../data/reports/native_lib_inventory.md).

### 3.7 기존 도구 베이스라인 비교

기존 4종 도구 / 방법과 정성+정량 비교:

| 베이스라인 | 자체 정량값 | 본 연구 대비 |
|---|---|---|
| ① jadx + 수동 분석가 | self GT 가 manual baseline (분석가 시간 6~7h) | 본 파이프라인 ~2h (3배 단축). 단, 정확한 시간 측정은 v1.0에서 보강 필요 |
| ② 단일 LLM 1-pass (검증 단계 없이) | Stage 1 자체 (Precision 78.9%) | 제한 corpus에서 Stage 3 ≥2/3 적용 후 reported FP 0건 관찰 |
| ③ android-scanner-ai (X-Vector) | **자체 P/R/F1 측정값 부재** + Gemini API key 의존 | 본 연구가 정량 평가 gap 제공. 직접 재현 비교는 API 제약으로 미완 |
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

상세는 [`02_case_studies.md`](02_case_studies.md). 요약:

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
    a. scripts/decompile.sh APK → jadx 디컴파일
    b. src/deobf/entropy.py → 난독화 수준 측정
    c. (HIGH 난독화일 때만) Stage 0 LLM 이름 복원
    d. configs/keywords.yaml grep → priority class 큐
    e. Stage 1 LLM → finding 후보
    f. Stage 2 caller 분석 + (선택) AST 룰
    g. Stage 3 multi-perspective consensus
    h. src/aaos_map.py → AAOS / MASVS 매핑
    i. src/tara_generate.py → TARA 시나리오 + Risk Matrix

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

1. **GitHub Actions 에 정적 부분만 통합** (외부 LLM 호출 없이): `src/deobf/entropy.py`, keyword grep, `src/eval.py`/`ablation.py`, `src/aaos_map.py`, `src/tara_generate.py` 모두 결정론적이라 PR 마다 자동. LLM 분석만 사람이 트리거.
2. **차량 LLM (PleOS-internal) 활성화 시 Stage 1/2/3 자동화**: 본 파이프라인의 prompts 를 그대로 호출, 외부 송출 없이 in-vehicle 또는 internal cloud 에서 분석 완결. 본 학기 환경 제약 (외부 LLM API 없음) 이 풀림.
3. **후속 학기에 Androidmeda 통합**: Apache 2.0 라이선스, deobfuscation 모듈만 fork → 본 entropy 측정과 cross-check.

### 5.4 IP 보호 주의사항

- 본 학기 GitHub repo 는 scaffold 만 공개. `data/apks/`, `data/decompiled/`, `data/reports/` 의 per-APK 보고서는 gitignored.
- 운영 통합 시에도 PleOS APK 소스가 외부 LLM API 에 송출되지 않도록 차단 필수. 현재는 환경 제약으로 자연스럽게 만족, 향후 cloud LLM 도입 시 별도 가드 필요.
- TARA 산출물 (자산 카탈로그, 위협 시나리오) 은 contract IP — repo public commit 대상에서 제외, 보고서에만 포함.

---

## 6. 일반화 평가 (G9)

본 절은 PleOS (Android 14 + AAOS 변형) 환경에서 검증한 정적 분석 파이프라인이 **QNX / Linux 기반 IVI** 같은 다른 차량용 OS 로 일반화 가능한지를 평가한다. 평가는 (1) 도구 / (2) 키워드 카테고리 / (3) AAOS 매핑 / (4) TARA 자산의 4축으로 진행.

### 6.1 OS-종속 vs OS-독립 컴포넌트

| 컴포넌트 | OS-독립 | OS-종속 (Android/AAOS) | 비고 |
|---|---|---|---|
| `scripts/decompile.sh` | ✗ | jadx (Java/Kotlin → DEX/APK 전용) | QNX/Linux 는 ELF |
| `src/deobf/entropy.py` | ✓ | — | 식별자 entropy 는 OS-독립 |
| `configs/prompts/stage1_detect.md` | 부분 | 일부 Android API 언급 | 룰 기반 보강 가능 |
| `configs/prompts/stage0_deobfuscate.md` | ✓ | — | 이름 복원은 OS-독립 |
| `src/eval.py` / `src/ablation.py` | ✓ | — | GT 라벨 스키마만 동일 |
| `configs/keywords.yaml` | 부분 | Android-specific 패턴 (`android:exported` 등) | 카테고리는 보편 |
| `configs/aaos_mapping.yaml` | ✗ | AAOS 섹션 번호 | OS별 가이드라인으로 swap |
| `src/tara_generate.py` | ✓ | — | ISO/SAE 21434 는 OS-독립 |
| `src/aaos_map.py` | 부분 | — | mapping yaml 만 swap |
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

본 절은 v1.0 제출 전 교수 리뷰에서 공격받을 수 있는 지점을 명시적으로 정리한다. 현재 결과는 pipeline feasibility를 보이는 데에는 충분하지만, 일반화 성능 주장으로 해석하기에는 아직 제한이 있다.

### 7.1 Internal validity — 평가 절차 내부의 편향 가능성

- **Self-label bias**: PleOS 자체 라벨 n=15는 실제 도메인 특화 finding을 포함한다는 장점이 있지만, 연구자가 수동 분석으로 만든 라벨이므로 evaluator bias 가능성이 있다. 외부 MASTG corpus를 추가했으나 현재 n=4로 작다.
- **Same-model verification bias**: Stage 3는 multi-LLM ensemble이 아니라 동일 모델을 여러 시각으로 재질문하는 방식이다. 따라서 모델 고유의 blind spot이 세 시각 모두에 공유될 수 있다.
- **Stage 2 upper-bound 해석 주의**: Ablation의 Stage 2 F1 1.000은 GT 기반 P-ceiling 시뮬레이션이며, 실제 자동 Stage 2의 독립 성능으로 해석하면 안 된다.

### 7.2 External validity — 다른 APK / 다른 IVI 환경으로의 일반화 한계

- **표본 크기**: combined n=19로 확장됐지만 통계적 일반화에는 여전히 부족하다. 추가 MASTG sample (certificatePinningXamarin, certificatePinning 등) + 의도적 취약 corpus (DIVA, InsecureBankv2) 도입이 필요하다.
- **PleOS APK 3종 편향**: 본 실험은 보안 가치가 높은 3개 APK를 우선 선택했다. 무작위 APK sample이나 전체 207개 APK에 대한 성능은 아직 측정하지 않았다.
- **PleOS-internal 사용자 base 추정 어려움**: 본 corpus의 attack feasibility는 정적 분석 단계 추정이다. 실차 시나리오 (네트워크 위치, 권한 grant 경로, 실제 app deployment policy) 는 반영되지 않았다.
- **난독화 corpus 편향**: UnCrackable Level1/2 의 `sg.vantagepoint` 는 hand-crafted anti-tamper helper이다. real-world commercial ProGuard'd 코드에서는 contextual hint가 약해 정확도 하락이 예상된다.

### 7.3 Construct validity — 측정 지표가 실제 보안 효과를 얼마나 반영하는가

- **오탐률 정의**: 본 보고서의 오탐률은 `FP/(TP+FP)`로, 전체 negative 대비 false positive rate가 아니라 reported finding 기준 false discovery rate이다.
- **Triage reduction과 recall의 분리**: 99.49% 축소율은 분석 효율성 지표이며, 제외된 class에 취약점이 없다는 의미가 아니다. 최종 v1.0에서는 일부 sample에 대해 full manual audit 또는 broader static scanner와 비교해 missed finding을 측정할 필요가 있다.
- **Severity / TARA risk의 주관성**: Critical/High 등급은 정적 분석 evidence와 도메인 가정을 기반으로 산정했다. 실차 네트워크 위치, 권한 모델, 배포 정책이 달라지면 feasibility와 risk level이 바뀔 수 있다.

### 7.4 Tooling boundary — 분석 도구와 계층의 구조적 한계

- **Java-only 정적 분석**: native lib 의존 패턴 (anti-tamper, RASP, crypto validation) 은 미커버된다. 외부 corpus 도입 시 UnCrackable-Level2 / r2pay-v1.0 두 sample 에서 in-scope finding 0건이 도출되었고, 이는 Java/Kotlin scanner의 구조적 blind spot을 보여준다.
- **디컴파일 artifact 의존성**: 본 pipeline은 jadx output을 입력으로 삼는다. jadx가 control/data-flow를 잘못 복원하거나 synthetic wrapper를 생성하면 LLM 판단에도 영향을 줄 수 있다.
- **Compose Navigation 의존 finding**: `vc-3` / `vc-4` 의 4중 차단 분석은 Android Compose Navigation 특화이다. 다른 UI framework 로 그대로 외삽할 수 없다.

### 7.5 v1.0 보강 계획

- 외부 corpus 확장: DIVA, InsecureBankv2, MASTG 추가 sample.
- 일부 APK에 대한 full-audit 또는 broader scanner 비교로 missed finding 측정.
- Stage 3 명칭을 최종적으로 `single-model multi-perspective consensus`로 통일.
- native boundary를 한계가 아니라 architecture requirement로 재서술: Java/Kotlin scanner + native binary scanner의 2-track 구조 제안.

---

## 8. 결론

본 학기 9주차 시점에 Phase A (환경 구축) → Phase B (Stage 1/2/3 검증 단계 적용) → Phase C 초기 측정 → Phase D (AAOS / TARA 매핑 + 사례 연구 + 통합 + 일반화 평가) 까지 완료하였다.

본 연구의 현재 결론은 “LLM scanner가 완벽한 취약점 탐지기”라는 것이 아니다. 더 안전한 결론은 다음과 같다.

> **LLM을 deterministic keyword triage와 caller/manifest 기반 도메인 검증 사이의 reasoning component로 배치하면, 제한된 PleOS/MASTG corpus에서 IVI APK 보안 리뷰의 후보 검증 비용을 줄이고 FP를 줄이는 pipeline을 구성할 수 있다.**

**주요 성과**:
1. 제한된 combined corpus n=19에서 Stage 1 후보 기준 FP 비율 21.1%, Stage 3 ≥2/3 후보 기준 FP 비율 0%가 관찰되었다.
2. Stage 3 ≥2/3 consensus에서 **Precision 100% / Recall 93.3% / F1 0.966**이 관찰되었으나, 이는 일반화 성능이 아니라 초기 feasibility 측정값으로 해석한다.
3. 자체 GT (n=15) + OWASP MASTG (n=4) combined corpus 로 외부 베이스라인 비교 체계를 구축하였다.
4. UnCrackable-Level2 / r2pay-v1.0 두 sample 에서 Java-only 정적 분석의 in-scope finding 0건을 확인하여 native boundary를 정량적으로 드러냈다. 이는 단순 한계가 아니라, 향후 PleOS 보안 점검 아키텍처에서 Java/Kotlin scanner와 native binary scanner를 분리해야 한다는 설계 근거가 된다.
5. AAOS / TARA 자동 매핑 + 5건 사례 연구 + 통합 아키텍처 권고 + 일반화 평가 등 학기 deliverable을 정리하였다.

**남은 작업 (10~14주차)**:
- 표본 확장 (MASTG 추가 sample, 의도적 취약 corpus 도입)
- 운영 비용 평가 (Claude Code 정액제 사용 시 정확한 시간 측정)
- 일부 APK에 대한 full-audit 또는 기존 scanner 비교로 missed finding 확인
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
| 본 보고서 + 보충 doc | `docs/{01_report, 02_case_studies, 03_charts, 04_limitations_and_costs, README}.md` |
| 자동 생성 산출물 | `data/reports/{aaos_mapping_table, tara_artifact}.{md, json}`, `data/viz/01~06_*.png` |
| Per-APK 보고서 | `data/reports/<apk>_<date>.{md, json}` (IP 보호로 비공개, 로컬 한정) |
| Raw 측정 노트 (시점 스냅샷) | `docs/archive/` (로컬 한정 — 본 보고서가 인용하는 1차 출처) |
| 공개 저장소 | [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT) |

## Appendix B — 주요 결정 사항

| 항목 | 결정 | 이유 |
|---|---|---|
| 에뮬레이터 이미지 | PleOS Connect v2.0.5 x86_64 | 본 과제 정합성 |
| 1차 분석 타겟 APK | `ai.umos.vehiclecontrol` | system UID + 13 위험 권한 + 차량 제어 |
| 3차 검증 방식 | 단일 모델 multi-perspective consensus (Claude Opus 4.7 + 시각 3종) | Claude Code 단일 모델 세션 제약 + 외부 유료 API 미보유. Multi-LLM ensemble로 주장하지 않음 |
| Ground truth 출처 | 자체 라벨링 + OWASP MASTG | 베이스라인 비교 + PleOS 특화 케이스 |

## Appendix C — PPT 계획서 vs 실측 정량 표

(학기 진척 표 + Phase D 측정값. 모든 수치는 combined n=19 기준의 초기 feasibility 결과이며, 일반화 성능으로 해석하지 않는다.)

| 지표 | PPT 가설 / 목표 | 실측 / 현재 해석 |
|---|---|---|
| 1차 후보 기준 FP 비율 | 25% | 21.1% (n=19, `FP/(TP+FP)` 기준) |
| 2차 후보 기준 FP 비율 | 12% | A.2 P-ceiling 1.000은 GT 기반 upper bound. 실제 Stage 2 독립 성능 주장 아님 |
| 3차 후보 기준 FP 비율 | 7% | 0% (≥2/3 consensus, limited corpus) |
| Precision (Full) | 0.93 | 1.00 (≥2/3, limited corpus) |
| F1 (Stage 1) | — | 0.882 |
| F1 (Stage 3 ≥2/3) | — | 0.966 |
| 분석 대상 축소율 | 30-40% | 99.49% triage reduction. 제외 class의 full-audit recall은 미검증 |
| 난독화 정확도 (5주차) | 40% | 100% (hand-crafted MASTG corpus, upper-bound 성격) |
| 난독화 정확도 (6주차) | 65% | 100% (동일 caveat) |
| 난독화 정확도 (8주차) | 78% | 100% (동일 caveat) |
| 처리 시간 (APK 1개) | 8~25분 | 측정 미완 |
| 비용 (APK 1개) | $0.40~1.20 | N/A (Claude Code 정액제) |

---

_본 보고서는 자율주행연구프로젝트1 9주차 시점의 v0.9-r1 리뷰 반영본. 지도교수 1차 리뷰 후 v1.0 업데이트 예정 (10주차 이후)._
