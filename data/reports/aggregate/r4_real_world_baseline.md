# R4 — Real-world 난독화 baseline (NewPipe 보강 측정)

_본 학기 RQ4 의 두 번째 측정. 13주차의 entropy density 측정에 이어, Stage 0 LLM rename 의 semantic plausibility 까지 정량화._

_초기 측정 (n=3) 2026-05-06, 확장 측정 (n=6) 2026-05-11._

## Setup

- 대상 APK: NewPipe v0.27.6 (real-world OSS, ProGuard 활성, 12 MB)
- 디컴파일: jadx 1.5.5 → 2,520 비-framework 클래스
- Sample 선정: composite_obf_score ≥ 0.85 클래스 중 n=6 (모두 p004j$.* desugar library)
- Sample 분산: util / sun.misc / util.concurrent (n=3, 초기) + desugar.sun.nio.fs / time.format / util.concurrent (n=3, 확장)

## Surprising finding 1 — NewPipe 비즈니스 코드는 거의 난독화되지 않았다

| 패키지 | non-framework class 수 | HIGH (composite ≥ 0.7) | 비율 |
|---|---:|---:|---:|
| 비즈니스 (`org.schabi.newpipe.*`) | 973 | **1** | **0.1%** |
| Desugar library (`p004j$.*`) | ~150 (추정) | ~41 | ~27% |
| 기타 | ~1,397 | 0 | 0% |

→ **NewPipe 전체 HIGH 1.7% (42 / 2520) 는 사실상 모두 desugar library 의 jadx-prefix 클래스**. 사용자 application code 는 가독성을 거의 그대로 유지.

이는 ProGuard 활성 OSS 라도 **release engineering 정책에 따라 application code 는 의미적 이름을 유지하는 경우가 흔함** 을 시사한다. R4 의 narrative 가 "real-world commercial APK 일반화" 에서 "library 측 난독화 vs application 측 난독화의 분리 측정 필요" 로 갱신됨.

## Surprising finding 2 — entropy 측정은 source obfuscation 강도와 다른 차원

NewPipe 의 HIGH 클래스 (예: `C1302f`, `C1112a`, `C1289p`) 는 jadx 가 자체 prefix `C0001a` 를 부여한 클래스. 원본 source 에서는 단일 char 또는 짧은 식별자 (`f`, `a`, `p`) 였다 (`/* JADX INFO: renamed from: j$.util.f */` 주석으로 확인 가능).

즉 본 학기 entropy 측정은 **jadx-output 의 식별자 entropy** 이지, 원본 source 의 ProGuard 압축 강도와 직접 매핑되지 않는다.

## Surprising finding 3 (2026-05-11 추가) — desugar library 안에서도 plausibility 가 표본별 변동

n=3 → n=6 확장 결과 plausibility 분포가 크게 변동. 추가 sample 3종 중 2종이 **Java standard public/internal API 와 method-level 1:1 매칭 가능** (DateTimeFormatterBuilder, ConcurrentHashMap.TreeBin) — Stage 0 의 ceiling 이 표본의 standard library 매칭 가능성에 강하게 의존함을 직접 확인.

## Stage 0 sample 적용 결과 (n=6, 2026-05-11 확장)

| ID | Sample | Conf (class) | Plausibility | 핵심 hint |
|---|---|---:|---|---|
| np-1 | `C1302f` | 0.55 | PARTIAL | "Unsupported " literal prefix + RuntimeException 상속만 |
| np-2 | `C1112a` (Unsafe wrapper) | 0.85 | GOOD | `Unsafe.class` + 'theUnsafe' literal + Singleton |
| np-3 | `C1289p` (concurrent node) | 0.45 | POOR | Field-only, 인접 클래스 시그니처 부재 |
| **np-4** | `C1017a` (nio attr builder) | **0.80** | **GOOD** | `'*'` wildcard + 'not recognized' + unmodifiableMap return |
| **np-5** | `C1188w` (time format builder) | **0.95** | **EXCELLENT** | Java `DateTimeFormatterBuilder` 와 27 method 중 19 (70%) 1:1 매칭. static HashMap pattern char → ERA/YEAR/... 매핑 |
| **np-6** | `C1290q` (CHM TreeBin) | **0.95** | **EXCELLENT** | Java `ConcurrentHashMap.TreeBin` 과 9 method 모두 1:1 매칭. `lockState` 필드명까지 jadx 가 복원 |

상세 entry 는 [`data/deobf/NewPipe_renames_20260511.json`](../deobf/NewPipe_renames_20260511.json) (초기 3 sample 포함).

### Plausibility 분포 (n=3 → n=6)

| grade | n=3 (2026-05-06) | n=6 (2026-05-11) | Δ |
|---|---:|---:|---|
| EXCELLENT (standard API 1:1 매칭) | 0 (0%) | **2 (33%)** | +2 |
| GOOD (semantic role + 시그니처) | 1 (33%) | 2 (33%) | +1 |
| PARTIAL (plausible name, hint 부족) | 1 (33%) | 1 (17%) | 0 |
| POOR (인접 클래스 의존) | 1 (33%) | 1 (17%) | 0 |
| **GOOD 이상 합계** | **1 (33%)** | **4 (67%)** | **+33%p** |

### 정확도 비교 (hand-crafted vs real-world)

| Corpus | sample | confidence avg | GOOD 이상 비율 |
|---|---:|---:|---:|
| Hand-crafted MASTG (UnCrackable Level1/2, sg.vantagepoint) | 17 | 0.92 | **100% exact** match (Log.d "CodeCheck", "test-keys" 등 string literal) |
| **Real-world OSS (NewPipe desugar library)** n=6 | 6 | **0.76** | **67% GOOD+** (n=3에서 33% → n=6 확장으로 +33%p) |
| 격차 (hand-crafted vs real-world) | — | -17% | -33%p (exact vs GOOD+) |

본 학기 Stage 0 의 일반화 성능 = corpus 의 **contextual hint density × standard library 패턴 매칭 가능성**. Hand-crafted MASTG 는 OWASP 가 의도적으로 anti-tamper helper 에 hint 를 강하게 심은 챌린지 corpus 라 100% exact match 가능. Real-world desugar library 는 sample 별로 변동 — Java standard API 의 desugar/port 인 경우 EXCELLENT, internal helper / interface 패턴은 PARTIAL~POOR.

## R4 implication

1. **본 학기 첫 정량 측정 (n=6)**: Stage 0 LLM rename 의 정확도가 corpus 종류에 따라 변동.
2. **hand-crafted vs real-world** 의 차이를 처음으로 측정 — hand-crafted 100% exact (upper bound) / real-world plausibility 67% GOOD+ (정확한 floor 는 ProGuard mapping 없이는 미확정).
3. **Future Work**:
   - closed-source commercial APK 의 ProGuard mapping 확보 후 exact accuracy 측정으로 진짜 baseline 정착.
   - NewPipe 같은 OSS 는 application code 가 가독성 유지라 R4 의 application-tier 측정에 적합 sample 이 아닐 수 있음 (HIGH 비즈니스 클래스 1/973 = 0.1%).
   - 상업 ProGuard 활성 APK (banking / messenger) 에서 application-tier sample 확보가 본 RQ4 의 진짜 floor 측정.
4. **R4 narrative 정정 권고**: "real-world ProGuard'd 코드의 정확도" 보다 "library 측 jadx-output 의 plausibility (standard API 매칭 가능성에 강하게 의존)" 로 표현하는 편이 더 정확.

## 한계

- Sample n=6 — 통계적 일반화 불가. 단 모두 desugar library (p004j$.*) 한정 측정 (NewPipe 의 비즈니스 패키지에는 HIGH 1개라 application-tier sample 확장 불가).
- Plausibility 평가는 본인 (Claude Code) 의 직접 판단 — 외부 reviewer 또는 NewPipe maintainer 의 검증이 추가되어야 객관성 강화.
- Exact accuracy 측정 불가 (ProGuard mapping file 부재). np-5 / np-6 는 Java standard API 와 method 시그니처 매칭이 strong evidence 이지만 'exact' 라고 보장은 못함.
- 본 학기 외부 다운로드 환경 제약 (네트워크 정책에 따른 toggle) 으로 추가 commercial APK 확보 어려움 — 12주차 사용자 결정 사항.

## 재현

```bash
python scripts/_r4_pick_targets.py    # NewPipe 비즈니스 vs desugar HIGH 클래스 분류
# → top 15 HIGH desugar sample 후보 확인
# Stage 0 LLM rename = Claude Code 세션에서 직접 적용 (configs/prompts/stage_b_deobfuscate.md)
# 결과는 data/deobf/NewPipe_renames_20260511.json (n=6 종합)
```

## 변경 이력

| 날짜 | 변경 | n |
|---|---|---:|
| 2026-05-06 | R4 첫 측정 (3 sample, desugar library 한정) | 3 |
| 2026-05-11 | 추가 3 sample (nio attr builder / time formatter / CHM tree bin). 두 sample이 Java standard API 1:1 매칭으로 EXCELLENT plausibility → distribution 갱신 | 6 |
