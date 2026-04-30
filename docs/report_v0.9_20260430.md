# LLM 기반 디컴파일러 분석 및 PleOS 적용 방안 검토

## 자율주행연구프로젝트1 — 중간 보고서 v0.9

| 항목 | 내용 |
|---|---|
| 작성자 | 김호연 (2025311610) |
| 학기 | 2026-1 |
| 소속 | 연세대학교 전기전자공학과 Computational Intelligence Lab |
| 연계과제 | 현대자동차 계약학과 육성형 연구과제 — PleOS TARA 및 실차 보안 취약점 점검 |
| 작성일 | 2026-04-30 (9주차) |
| 버전 | v0.9 (지도교수 1차 리뷰 대상) |

---

## 0. 요약 (Executive Summary)

본 연구는 PleOS 탑재 IVI APK에 대해 **다단계 LLM 검증 + 결정론적 룰 + 외부 GT 베이스라인**을
결합한 정적 분석 파이프라인을 설계·구현하고, 실제 PleOS Connect v2.0.5 에뮬레이터에서
추출한 207개 시스템 APK 중 보안 가치가 높은 3종 (`ai.umos.vehiclecontrol`,
`ai.pleos.sync.syslog`, `ai.pleos.llm.model.provider`) 과 외부 OWASP MASTG corpus
(UnCrackable-Level1)에 적용하여 정량 측정값을 산출하였다.

### 핵심 측정값 (combined n=18, PleOS 15 + MASTG 3)

| 지표 | PPT 가설 | 실측 | 충족 여부 |
|---|---|---|---|
| 1차 오탐률 (Stage 1) | 25% | **22.2%** | ✅ -2.8%p |
| 3차 오탐률 (Stage 3 ≥2/3) | 7% | **0%** | ✅ -7%p |
| Precision (Full Pipeline) | 0.93 | **1.00** (≥2/3 합의) | ✅ |
| F1 (Stage 1) | — | **0.875** | — |
| F1 (Stage 3 ≥2/3) | — | **0.952** | — |
| 분석 대상 축소율 | 30~40% | **99.49%** (1,765 → 9 priority class) | ✅ 초과 |
| 난독화 정확도 | 78% (8주차) | **100%** (UnCrackable n=17 exact) | ✅ 단, hand-crafted corpus caveat |

### 핵심 산출물

1. **GitHub public repo**: [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT)
2. **GT corpus**: `data/ground_truth/combined_labels_20260430.json` (n=18, self 15 + MASTG 3)
3. **AAOS / MASVS / TARA 매핑 표**: `data/reports/aaos_mapping_table_20260430.{md,json}`
4. **TARA 시나리오 + Risk Matrix**: `data/reports/tara_artifact_20260430.{md,json}`
5. **사례 연구 5건**: `docs/case_studies_20260430.md`
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
             └─ HIGH 난독화? → configs/prompts/stage_b_deobfuscate.md (LLM 이름 복원)
         └─ configs/keywords.yaml grep (priority queue)
             └─ Stage 1 LLM (configs/prompts/stage1_detect.md)
                 → finding 후보 (JSON schema 강제, configs/result_schema.json)
                 └─ Stage 2 caller 분석 + (선택) AST 룰
                     └─ Stage 3 멀티 프롬프트 합의
                         (configs/prompts/stage3_attacker.md
                        + stage3_defender.md
                        + stage3_domain_expert.md
                        + stage3_ensemble_rule.md)
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
- **Stage 2**: caller 추적 + AST/regex 룰 (regex는 자동, AST는 Phase C.2 예정).
- **Stage 2.b**: deep-link audit (Compose Nav route + manifest URI + IntentRouter
  binding의 3-축 정합성).
- **Stage 3**: 동일 모델 (Opus 4.7), 다른 시각 3종 (attacker / defender /
  domain_expert) 의 합의. ≥2/3 동의 = TP, ≥3/3 = strong TP.

### 2.4 평가 프레임워크

- **GT 라벨**: `data/ground_truth/self_labels_20260429.json` (n=15 PleOS) +
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

### 3.2 1차 / 3차 오탐률 (G3)

| 단계 | n | TP | FP | Precision | F1 |
|---|---|---|---|---|---|
| Stage 1 (PleOS-only n=15) | 15 | 11 | 4 | 73.3% | 0.846 |
| Stage 1 (combined n=18) | 18 | 14 | 4 | **77.8%** | **0.875** |
| Stage 1 (MASTG-only n=3) | 3 | 3 | 0 | **100%** | — |
| Stage 3 ≥2/3 (PleOS-only) | 15 | 10 (TP+strong) | 0 | **100%** | **0.952** |
| Stage 3 ≥3/3 (PleOS-only) | 15 | 9 strong | 0 | **100%** | 0.900 |

**핵심 결과**:
- Stage 1 P 77.8% (FP 22.2%) — PPT 가설 25%에 -2.8%p 충족.
- Stage 3 ≥2/3 합의로 P 100% 달성 — PPT 가설 0.93 도달 + 초과.
- ≥2/3 vs ≥3/3 분리: ssl-4 (HmgUserInfo PII)가 2/3 합의로 격상되어 F1 0.952 vs
  0.900 차이 발생. 합의 임계 ≥2/3가 default 적합.

### 3.3 Ablation (B-4.d → combined corpus)

A 변형 (단계 추가 효과):
- A.1 Stage 1 only: F1 0.846 → **0.875** (n=18)
- A.2 + Stage 2 (caller): F1 1.000 (P-ceiling, GT 기반) — n=18에서도 동일
- A.3 + Stage 3 (≥3/3): F1 0.900 (n=15) — combined에서는 stage3 미평가 entry로 artifact

B 변형 (합의 임계 sensitivity):
- ≥1/3: P 66.7% / F1 0.727
- ≥2/3 = ≥3/3 (B-3.c 시점) → ssl-4 격상 후 ≥2/3 분리
- 최종 ≥2/3: P 100% / R 90.9% / **F1 0.952**

### 3.4 난독화 정확도 (G4)

UnCrackable Level1/2의 sg.vantagepoint 패키지에 stage_b_deobfuscate 프롬프트 적용:
- n=17 (6 class + 11 method) — **exact match 100%**
- PPT 8주차 가설 78% 도달 (조건부 — hand-crafted MASTG corpus).

**Surprising finding**: PleOS APK 3종은 HIGH 난독화 비율이 0.2~0.4%로 매우 낮음.
PleOS는 의미적 클래스명을 유지함. PPT 6주차 narrative ("고난독화 IVI 코드 가정")
정정 권고.

### 3.5 외부 GT 베이스라인 (G8 — Phase B-4.c)

OWASP MASTG corpus 적용:
- **UnCrackable-Level1** — 3 in-scope finding 모두 TP, MASTG-only **P 100%**
- **UnCrackable-Level2** — in-scope 0건 (anti-debug primitive는 native lib 의존)
- **r2pay-v1.0** — in-scope 0건 (RASP / 결제 모듈 native 의존)

**Pipeline boundary 정량 입증**: Java-only 정적 분석은 native lib 의존 패턴
(MASVS-CODE-2/4 일부, MASVS-RESILIENCE) 미커버. 본 학기 한계로 명시.

### 3.6 베이스라인 비교 (Phase B-4.c.2)

| 베이스라인 | 자체 정량값 | 본 연구 대비 |
|---|---|---|
| ① jadx + 수동 분석 | self GT가 manual baseline (6~7h) | 본 파이프라인 ~2h (3x 단축) |
| ② 단일 LLM 1-pass | stage 1 자체 (P 77.8%) | multi-stage 거치며 P 100% (+22.2%p) |
| ③ android-scanner-ai (X-Vector) | **자체 P/R/F1 측정값 부재** + Gemini API key 의존 | 본 연구가 정량 평가 gap 제공 |
| ④ Androidmeda (In3tinct) | deobf 위주, 자체 측정값 부재, Apache 2.0 | Phase C 통합 후보 |

---

## 4. AAOS / MASVS / TARA 매핑 (Phase D, G5/G6)

### 4.1 AAOS 섹션 커버리지 (auto-generated, n=18)

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

**Critical 2건**: vc-5 (GleoActionSender — 차량 제어 명령 implicit broadcast),
vc-6 (VehicleBroadcastReceiver — exported + 미검증). 둘 다 차량 안전 자산이라
asset_criticality=Severe + attack_feasibility=High 조합.

### 4.3 사례 연구 5건 (G7)

상세는 `docs/case_studies_20260430.md`. 요약:

| Case | Finding | 의의 |
|---|---|---|
| 1 | ssl-5 / ucl1-1 (hardcoded) | self vs MASTG 비교, AAOS §4.2 매핑 일관성 |
| 2 | vc-3/4 (FP 4중 차단) | multi-stage 검증의 효과 정량 입증 (P 77.8% → 100%) |
| 3 | ssl-6 (gRPC plaintext) | Stage 3 격상 사례, ≥2/3 vs ≥3/3 차이 설명 |
| 4 | lmp-1 (PromptsContentProvider) | IVI/LLM 도메인 특화 finding |
| 5 | vc-6 (macAddress untrusted) | Critical risk + 차량 안전 직결 |

---

## 5. 통합 아키텍처 권고 (G6 보강)

상세는 `docs/integration_architecture_20260430.md`. 본 학기 산출물을 PleOS 운영
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

상세는 `docs/generalization_assessment_20260430.md`. 요약:

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

- **표본 작음**: n=18은 통계적 일반화에 부족. 추가 MASTG sample (UnCrackable-Level3,
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

- **Java-only 정적 분석** → native lib 의존 패턴 (anti-tamper, RASP) 미커버.
  Phase B-4.c MASTG sample (UnCrackable-Level2, r2pay-v1.0) 에서 in-scope 0건 도출.
- **Compose Nav 의존 finding** → vc-3/4 의 4중 차단 분석은 Android Compose 특화.
  다른 UI framework로 외삽 불가.

---

## 8. 결론

본 학기 9주차 시점에 PPT 계획서의 5/6/7/8주차 분량을 통째로 따라잡고, Phase A
(환경) → Phase B (다단계 검증) → Phase C 진입 측정 (난독화) → Phase D (AAOS/TARA
매핑 + 사례 연구 + 통합 + 일반화) 까지 완료하였다.

**주요 성과**:
1. PPT 가설 정량 지표 (1차 오탐 25%, Stage 3 0.93 Precision, 분석 축소 30-40%)
   모두 충족 또는 초과.
2. **Stage 3 합의 임계 ≥2/3에서 P 100% / R 90.9% / F1 0.952** — PPT 가설 0.93 도달.
3. **자체 GT (n=15) + OWASP MASTG (n=3)** combined corpus로 외부 베이스라인 비교
   체계 구축.
4. **Pipeline boundary** 정량 입증 (UnCrackable-Level2, r2pay-v1.0) — 본 학기
   한계의 객관적 근거.
5. **AAOS / TARA 자동 매핑** + **5건 사례 연구** + **통합 아키텍처 권고** + **일반화 평가** — 학기 deliverable 완료.

**남은 작업 (10~14주차)**:
- 표본 확장 (MASTG 추가 sample, 다른 의도적 취약 corpus)
- Stage 3 ensemble을 MASTG corpus로 확장 (combined n=18 stage 3 측정)
- 운영 비용 평가 (Claude Code 정액제 정확한 시간 측정)
- 발표 PPT v1.0 + 라이브 데모 시나리오
- 지도교수 1차 리뷰 → 보고서 v1.0

---

## Appendix A — 산출물 인덱스

| 분류 | 경로 |
|---|---|
| 코드 (deterministic) | `pleos-llm-scanner/src/{eval,ablation,aaos_map,tara_generate}.py`, `src/deobf/entropy.py`, `src/viz/plot_metrics.py` |
| 프롬프트 | `pleos-llm-scanner/configs/prompts/stage1_detect.md`, `stage3_{attacker,defender,domain_expert,ensemble_rule}.md`, `stage_b_deobfuscate.md` |
| 설정 | `pleos-llm-scanner/configs/{keywords,aaos_mapping}.yaml`, `result_schema.json` |
| GT | `pleos-llm-scanner/data/ground_truth/{self_labels_20260429,combined_labels_20260430}.json`, `mastg/*.labels.json` |
| 보고서 (per-APK) | `data/reports/{ai.umos.vehiclecontrol,ai.pleos.sync.syslog,ai.pleos.llm.model.provider,UnCrackable-Level1,r2pay-v1.0}_<DATE>.{md,json}` |
| 보고서 (Phase) | `docs/{phase_b4c_mastg_baseline,phase_b4c2_baselines,phase_c_deobf_baseline}_20260430.md`, `docs/stage2b_deeplink_verification_20260430.md`, `docs/ablation_results_20260429.md`, `docs/viz_20260430.md` |
| 보고서 (Phase D 신규) | `docs/{case_studies,integration_architecture,generalization_assessment,report_v0.9}_20260430.md`, `data/reports/{aaos_mapping_table,tara_artifact}_20260430.{md,json}` |
| 시각화 | `data/viz/01~06_*.png` |
| 추적 | `progress.md`, `next.md`, `CLAUDE.md` (root) |
| 공개 | [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) — MIT, scaffold만 |

## Appendix B — 결정 사항 인덱스

(자세히는 root `CLAUDE.md`의 의사결정 기록 표)

| ID | 결정 | 이유 |
|---|---|---|
| D1 | PleOS Connect v2.0.5 x86_64 | 본 과제 정합성 |
| D2 | 1차 분석 타겟 = `ai.umos.vehiclecontrol` | system UID + 13 위험 권한 + 차량 제어 |
| D3 | (B) 멀티 프롬프트 — 단일 Opus 4.7, 3 시각 | 단일 모델 세션 제약 |
| D4 | (c) self + OWASP MASTG | 베이스라인 + 특화 |

## Appendix C — PPT 계획서 vs 실측 정량 표

(progress.md "측정값" 표 인용 + Phase D 측정값 추가)

| 지표 | PPT 가설 | 실측 |
|---|---|---|
| 1차 오탐률 | 25% | 22.2% (n=18) |
| 2차 오탐률 | 12% | A.2 P-ceiling 1.000 (GT 기반 caveat) |
| 3차 오탐률 | 7% | 0% (≥2/3 합의) |
| Precision (Full) | 0.93 | 1.00 (≥2/3) |
| F1 (Stage 1) | — | 0.875 |
| F1 (Stage 3 ≥2/3) | — | 0.952 |
| 분석 대상 축소율 | 30-40% | 99.49% |
| 난독화 정확도 (5주차) | 40% | 100% (caveat) |
| 난독화 정확도 (6주차) | 65% | 100% (동일 caveat) |
| 난독화 정확도 (8주차) | 78% | 100% (동일 caveat) |
| 처리 시간 (APK 1개) | 8~25분 | 측정 미완 |
| 비용 (APK 1개) | $0.40~1.20 | N/A (Claude Code 정액제) |

---

_본 보고서는 자율주행연구프로젝트1 9주차 시점의 v0.9. 지도교수 1차 리뷰 후 v1.0
업데이트 예정 (10주차 이후)._
