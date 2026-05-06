# 한계 근본 원인 분석 + 운영 비용 평가 (PPT 11주차 deliverable)

_작성: 2026-04-30 / Phase D 1차 통과 후 작성. 보고서 v0.9의 7장 (Limitations) + 8장 (Cost Analysis) 의 raw 분석 노트._

본 문서는 Phase A~D를 통해 드러난 본 파이프라인의 **구조적 한계**와 그 **근본 원인**, 그리고 운영 시점에서의 **시간/비용 트레이드오프**를 정리한다. 향후 v1.0 보고서 / 발표 / 후속 연구의 input.

---

## 1. 한계 — 근본 원인 분석

### 1.1 한계 카테고리

본 파이프라인이 못 잡거나 약한 영역을 5 카테고리로 분류:

| # | 한계 | 근본 원인 (1차) | 근본 원인 (2차, 환경) | 측정 증거 |
|---|---|---|---|---|
| L1 | **네이티브 코드 분석 불가** | jadx = Java/Kotlin 전용 디컴파일러 | Ghidra/IDA 등 binary 도구 미통합 | UnCrackable-Level2 + r2pay-v1.0 in-scope finding 0건 (`docs/archive/phase_b4c_mastg_baseline_20260430.md`) |
| L2 | **표본 크기 작음 (n=19)** ← 2026-04-30 부분 해소 (n=18→19, UnCrackable-Level3 추가) | self-labeling 시간 cost (PleOS 3 APK = 6~7시간) | 1인 학기 프로젝트, 외부 라벨러 없음 | combined n=19 측정. 추가 sample 도입은 Future Work |
| L3 | **멀티 모델 앙상블 미구현 (멀티 프롬프트로 대체)** | Claude Code 단일 모델 세션 | 외부 유료 API 미사용 정책 → 다른 모델 호출 불가 | 3차 검증 방식을 멀티 모델(Claude+GPT-4 가정) → 멀티 프롬프트(동일 모델 + 시각 3종)로 전환 |
| L4 | **MASTG corpus의 hand-crafted 특성** | UnCrackable / r2pay = OWASP가 의도적으로 hint 강하게 심은 챌린지 | 무료 / 공개된 commercial-grade APK ground truth 부재 | 난독화 정확도 100%(n=17) caveat (`docs/archive/phase_c_deobf_baseline_20260430.md`) |
| L5 | ~~Stage 3 ensemble의 MASTG 미평가~~ ✅ **2026-04-30 해소** | ucl1-1/2/3 + ucl3-1 stage 3 ensemble 평가 추가 완료 | — | ablation A.3 ≥3/3 F1 0.783 → **0.889** (combined n=19), B ≥2/3 F1 0.952 → **0.966** |

### 1.2 L1 — 네이티브 코드 분석 불가 (가장 중요한 한계)

#### 증상
- UnCrackable-Level2: 핵심 검증 로직이 `libfoo.so`의 native method `bar(byte[])`. Java 측엔 anti-tamper만.
- r2pay-v1.0: token 생성이 `libnative-lib.so`의 `gXftm3iswpkVgBNDUp(byte[], byte)`. Java는 wrapper.
- 두 sample 모두 OWASP가 정답으로 인정하는 MASVS-CRYPTO-1 위반이 native에 있음.

#### 근본 원인 (Why)
- jadx = Java/Kotlin DEX → Java source 디컴파일러. `.so` (ELF) 파일은 처리 못 함.
- 본 파이프라인의 entry point가 `scripts/decompile.sh data/apks/<X>.apk` → jadx 호출 → java sources만 출력. ELF는 무시됨.
- LLM 분석 단계도 Java source를 읽도록 설계됨. C/C++/disassembly를 직접 read 안 함.

#### 영향 정량화
- IVI 환경의 네이티브 비중 추정: PleOS 3 APK 중 native lib 보유 — `lib/` 디렉토리 존재 여부 전수 점검 시 측정 가능 (Future Work).
- 본 학기 측정으로는 MASTG-2/r2pay 2 sample = native-bound MASVS 위반의 33% (3 sample 중 2)가 못 잡힘.

#### 해결 경로 (우선순위 순)
1. **(즉시 가능)** `radare2` headless + Python wrapper 도입 → ELF symbol enumeration + LLM 분석. radare2는 MIT, 외부 API 의존 없음.
2. **(중기)** Ghidra headless + LLM 통합. Ghidra는 NSA Apache 2.0. command-line scriptable.
3. **(장기)** `binsec` / `angle-r` 같은 symbolic execution 도구 통합으로 native ↔ Java boundary 자동 매핑.

#### Future Work 우선순위
이 한계가 **본 학기 보고서 limitations 섹션의 1순위 문장**이 되어야 함. PPT 발표에서도 "Java-only static analysis는 native-bound vuln을 못 잡는다는 점을 외부 corpus 2 sample로 정량 입증"으로 narrative.

### 1.3 L2 — 표본 크기 작음

#### 측정값
- combined n=18 (self 15 + MASTG 3 in-scope)
- 통계적 유의성 caveat 모든 측정값에 동반

#### 근본 원인
- self GT 라벨링 = manual workflow, APK 1개당 2시간 ~ 3시간
- MASTG in-scope sample 부족 — UnCrackable-Level1 외에는 native lib 의존이라 Java-only 파이프라인 scope 밖
- 외부 무료 commercial APK ground truth 부재

#### 해결 경로
1. **(즉시)** 추가 MASTG sample (UnCrackable-Level3, certificatePinningXamarin, HelloWord-JNI, MASTG-DEMO) 도입. native가 아닌 sample 발굴.
2. **(중기)** DIVA, InsecureBankv2 같은 의도적 취약 Android 앱 도입. 이들은 Java 측에 다양한 vuln 있음.
3. **(장기)** crowdsourced ground truth corpus 구축 — 외부 연구자 협업.

### 1.4 L3 — 멀티 모델 앙상블 미구현 (멀티 프롬프트로 대체)

#### 결정 history
- 원래 PPT 가설: Claude + GPT-4 같은 multi-vendor ensemble
- 환경 제약 (외부 유료 API 없음 정책 + Claude Code 단일 모델 세션) 발견 → 멀티 프롬프트(동일 모델 + 시각 3종)로 재결정
- 멀티 프롬프트 결과: ≥2/3 합의에서 P 100% / Recall 90.9% / F1 0.952 — PPT 가설 0.93 도달·초과

#### 그래도 남은 limitation
- multi-vendor ensemble의 진짜 효과 (다른 모델이 같은 코드를 다르게 해석하는 disagreement) 측정 불가
- multi-prompt는 같은 모델의 systematic bias가 모든 시각에 공통 → "진짜 다른 시각" 시뮬레이션의 한계

#### 해결 경로
- 외부 API 정책 변경 시 multi-vendor 측정 가능 (Anthropic + OpenAI + Google 3사 비교)
- 본 학기 scope 밖 — Future Work로 명시

### 1.5 L4 — MASTG corpus의 hand-crafted 특성

#### 증상
- UnCrackable-Level1: `Log.d("CodeCheck", ...)` 가 verify 함수의 역할을 직접 명시. LLM이 100% 정확도로 이름 복원.
- 일반적 commercial ProGuard'd APK는 이런 hint 부재.

#### 영향
- 난독화 정확도 100% (n=17) 측정값은 **upper bound**일 뿐. real-world 적용 시 정확도 하락 예상.
- 보고서 v0.9 / PPT 발표에서 "조건부 도달" caveat 명시 필요.

#### 해결 경로
- 대형 commercial APK 1~2개에 본 deobf 파이프라인 적용해서 정확도 측정 (manual GT 라벨링 + 측정)
- 시간 cost: APK 1개당 4~5시간 추정 (단순 anti-tamper helper보다 클래스 많음)

### 1.6 L5 — Stage 3 ensemble의 MASTG 미평가 (✅ 2026-04-30 해소)

#### 증상 (해소 전)
- ablation A.3 (stage 3 ≥3/3) F1 = 0.783 (combined n=18 기준)
- 0.783은 **artifact** — UnCrackable-Level1의 ucl1-1/2/3가 stage 3 ensemble JSON에 entry가 없어서 자동 FN으로 처리됨

#### 해소 결과 (2026-04-30)
- ucl1-1/2/3 + ucl3-1 4건에 attacker/defender/domain_expert 평가 추가 → `data/reports/stage3_ensemble.json` 갱신
- combined n=19 ablation 재실행 결과: A.3 ≥3/3 F1 **0.889** (이전 0.783 → +0.106), B ≥2/3 F1 **0.966** (이전 PleOS-only 0.952 → combined 향상)
- ablation 표 일관성 회복

---

## 2. 운영 비용 평가

### 2.1 시간 cost (APK 분석 1개 기준)

| 단계 | 시간 (자동) | 시간 (수동 baseline) | 단축률 |
|---|---|---|---|
| APK 추출 (ADB pull) | 즉시 | 즉시 | — |
| jadx 디컴파일 | 30초 ~ 5분 (APK 크기 의존) | 동일 | — |
| 키워드 grep + priority 추출 | 1분 | 코드 read 30분 ~ 1시간 | 30~60x |
| Stage 1 LLM 분석 (priority 9 클래스) | ~1시간 (Claude Code 인터랙티브) | manual 코드 분석 3~4시간 | 3~4x |
| Stage 2 caller 추적 | ~30분 | manual grep + 사고 1~2시간 | 2~4x |
| Stage 3 멀티 시각 합의 | ~30분 | n/a (manual엔 없음) | — |
| 보고서 (JSON + MD) 생성 | 즉시 | manual 1~2시간 | ∞ |
| **합계 (3 APK 풀 파이프라인)** | **~2시간** | **6~7시간** | **3~3.5x** |

### 2.2 금전 cost

| 항목 | 본 파이프라인 | 비교 baseline |
|---|---|---|
| LLM API 비용 | $0 (Claude Code 정액제 안에서) | android-scanner-ai: Gemini API key 가격에 연동, OpenAI 기준 APK 1개 추정 $1~3 |
| 디컴파일러 라이선스 | $0 (jadx Apache 2.0) | $0 |
| GT 라벨링 인건비 | self (학생 1인) | 외주 보안 분석가 시급 환산 시 6~7시간 × ₩100,000 ≈ ₩600,000~₩700,000 / APK 3종 |
| GitHub repo | $0 (public free tier) | $0 |
| **APK 1개 분석 비용** | **~$0** (시간 cost만) | **외주 환산 ₩200,000~₩240,000 / APK** |

#### 정액제 cap 고려
- Claude Code 정액제 = 개인 학기 프로젝트 1인 사용 시 충분
- 산업 적용 (회사 내 보안팀 도입) 시 사용량에 따라 enterprise 라이선스 필요 — 정확한 cost projection은 회사 별 평가
- ROI: 외주 baseline 대비 ~₩200K/APK 절감 + 3x 시간 단축 → APK 100개 분석 시 인건비 ~₩20M, 시간 250시간 절감

### 2.3 메모리 / CPU peak

| 단계 | 메모리 peak | 비고 |
|---|---|---|
| jadx 디컴파일 (VehicleControl 92MB) | ~3 GB JVM heap | `JADX_OPTS=-Xmx4g` 권장 |
| Claude Code 세션 | ~500 MB (Node + Python helper) | LLM 추론은 클라우드 |
| python entropy / eval / ablation | ~200 MB | matplotlib + numpy |
| **합계 peak** | **~4 GB** | PPT 가설 (4~8 GB) 충족 |

### 2.4 처리 시간 PPT 가설 vs 실측

| 지표 | PPT 가설 | 실측 | 충족 여부 |
|---|---|---|---|
| 처리 시간 (APK 1개) | 8~25분 | 인터랙티브 ~40분 (priority 9 클래스 기준) | ⚠️ PPT 하한 8분 초과. 단 manual baseline 대비 3x 단축 |
| 메모리 피크 | 4~8 GB | ~4 GB | ✅ 하한 충족 |
| 비용 (APK 1개) | $0.40~1.20 | $0 (Claude Code 정액제) | ✅ 초과 (절감) |

PPT 가설의 8~25분/APK는 fully-batch (백그라운드 LLM 호출) 가정. 본 파이프라인은 인터랙티브 Claude Code 세션이라 사람의 reading time이 포함됨. **fully-batch 자동화로 전환 시 8~15분/APK 도달 가능** — Future Work.

### 2.5 확장성 — APK 100개 분석 추정

| 자원 | 추정값 | 가정 |
|---|---|---|
| 시간 (인터랙티브) | ~70시간 | APK당 ~40분 + 보고서 정리 |
| 시간 (fully-batch) | ~15~25시간 | LLM 호출 자동화, 사람은 검토만 |
| 디스크 | ~50 GB | jadx output (APK 1개 200~500 MB × 100) |
| 메모리 | ~4 GB peak | jadx 단계 |
| 비용 | $0 (Claude Code 정액제 한도 내) 또는 enterprise plan | — |

100 APK 전수 분석은 본 학기 scope 밖이지만, 시간 정량 추정으로 산업 적용 가능성 평가 가능.

---

## 3. 종합 — 한계와 비용의 트레이드오프

| 차원 | 본 파이프라인 위치 | 트레이드오프 |
|---|---|---|
| **정확도** (Precision/Recall/F1) | F1 0.952 (≥2/3 합의), MASTG-only P 100% | 표본 작음 (n=18) caveat |
| **범위** (어떤 vuln을 잡나) | Java 6 카테고리 enum | 네이티브 / anti-tamper / 비-MASVS 카테고리는 못 잡음 |
| **시간** | APK 1개 ~40분, 3 APK ~2시간 | manual 대비 3x 단축 / fully-batch 자동화 가능 |
| **비용** | Claude Code 정액제 안 | 산업 적용 시 enterprise plan + radar2/Ghidra 통합 필요 |
| **재현성** | scripts + GT JSON deterministic | LLM의 비결정성은 stage 3 합의가 흡수 |
| **이식성** | 60~70% OS-독립 (`docs/generalization_assessment_*`) | swap 필요: 디컴파일러 / 키워드 룰셋 / 매핑 yaml |

---

## 4. 11주차 deliverable 매핑 (PPT 계획서 기준)

| PPT 11주차 항목 | 본 문서 위치 | 충족 |
|---|---|---|
| 한계 근본 원인 분석 | §1 (5 한계 카테고리 × 근본 원인 / 영향 / 해결 경로) | ✅ |
| 운영 비용 평가 | §2 (시간 / 금전 / 메모리 / 확장성) | ✅ |
| 트레이드오프 정리 | §3 | ✅ |

→ PPT 11주차 progress report 1페이지 작성 시 본 문서 참조.

---

## 5. 연결 산출물

- `docs/report_v0.9.md` 7장 (Limitations) + 8장 (Cost Analysis) 의 raw 노트
- `docs/archive/phase_b4c_mastg_baseline_20260430.md` (L1 boundary 증거)
- `docs/archive/phase_c_deobf_baseline_20260430.md` (L4 hand-crafted caveat)
- `docs/archive/phase_b4c2_baselines_20260430.md` (운영 시간 cost 비교)
- `docs/generalization_assessment.md` (이식성 trade-off)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-30 | 11주차 deliverable 초안 — 5 한계 + 운영 비용 + 트레이드오프 종합. v1.0 보고서 7/8장 input. |
