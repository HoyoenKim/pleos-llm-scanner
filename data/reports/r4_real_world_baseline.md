# R4 — Real-world 난독화 baseline (NewPipe 보강 측정, 2026-06-07)

_본 학기 RQ4 의 두 번째 측정. 13주차의 entropy density 측정에 이어, Stage 0 LLM rename 의 semantic plausibility 까지 정량화._

## Setup

- 대상 APK: NewPipe v0.27.6 (real-world OSS, ProGuard 활성, 12 MB)
- 디컴파일: jadx 1.5.5 → 2,520 비-framework 클래스
- Sample 선정: composite_obf_score ≥ 0.8 클래스 중 3 sample (j$.* desugar library 패키지에 집중)

## Surprising finding 1 — NewPipe 비즈니스 코드는 거의 난독화되지 않았다

| 패키지 | non-framework class 수 | HIGH (composite ≥ 0.7) | 비율 |
|---|---:|---:|---:|
| 비즈니스 (`org.schabi.newpipe.*`) | 973 | **1** | **0.1%** |
| Desugar library (`p004j$.*`, `j$.*`) | ~150 (추정) | ~41 | ~27% |
| 기타 | ~1,397 | 0 | 0% |

→ **NewPipe 전체 HIGH 1.7% (42 / 2520) 는 사실상 모두 desugar library 의 jadx-prefix 클래스**. 사용자 application code 는 가독성을 거의 그대로 유지.

이는 ProGuard 활성 OSS 라도 **release engineering 정책에 따라 application code 는 의미적 이름을 유지하는 경우가 흔함** 을 시사한다. RQ4 의 narrative 가 "real-world commercial APK 일반화" 에서 "library 측 난독화 vs application 측 난독화의 분리 측정 필요" 로 갱신됨.

## Surprising finding 2 — entropy 측정은 source obfuscation 강도와 다른 차원

NewPipe 의 HIGH 클래스 (예: `C1302f`, `C1112a`, `C1289p`) 는 jadx 가 자체 prefix `C0001a` 를 부여한 클래스. 원본 source 에서는 단일 char 또는 짧은 식별자 (`f`, `a`, `p`) 였다 (`/* JADX INFO: renamed from: j$.util.f */` 주석으로 확인 가능).

즉 본 학기 entropy 측정은 **jadx-output 의 식별자 entropy** 이지, 원본 source 의 ProGuard 압축 강도와 직접 매핑되지 않는다.

## Stage 0 sample 적용 결과 (3 sample)

| Sample | confidence (class) | semantic plausibility | hint 평가 |
|---|---:|---|---|
| `C1302f` (RuntimeException helper) | 0.55 | PARTIAL | "Unsupported " literal prefix + RuntimeException 상속만 |
| **`C1112a`** (Unsafe accessor) | **0.85** | **GOOD** | `Unsafe.class` import + `'theUnsafe'` literal + Singleton 패턴 |
| `C1289p` (Concurrent node) | 0.45 | POOR | Field-only 클래스, 인접 클래스 (C1285l/C1288o) 시그니처 부재 |

상세는 [`data/deobf/NewPipe_renames_20260607.json`](../deobf/NewPipe_renames_20260607.json).

### 정확도 비교 (hand-crafted vs real-world)

| Corpus | sample | confidence avg | plausibility |
|---|---:|---:|---|
| Hand-crafted MASTG (UnCrackable Level1/2, sg.vantagepoint) | 17 | 0.92 | **100% exact** match (Log.d "CodeCheck", "test-keys" 등 string literal) |
| **Real-world OSS (NewPipe desugar library)** | 3 | 0.62 | **33% GOOD** plausibility |
| 추정 비율 | — | — | **약 3배 정확도 하락** |

본 학기 Stage 0 의 일반화 성능 = corpus 의 **contextual hint density 에 강하게 의존**. Hand-crafted MASTG 는 OWASP 가 의도적으로 anti-tamper helper 에 hint (string literal, 명확한 role) 를 강하게 심은 챌린지 corpus 라 100% exact match 가능. 반면 desugar library 는 interface 패턴 + 인접 클래스 의존이 강해 hint 가 약함.

## RQ4 implication

1. **본 학기 첫 정량 측정**: Stage 0 LLM rename 의 정확도가 corpus 종류에 따라 ~3배 변동.
2. **hand-crafted vs real-world** 의 차이를 처음으로 측정 — hand-crafted 100% exact 는 upper bound, real-world plausibility ~33% 는 lower bound.
3. **Future Work**: closed-source commercial APK 의 ProGuard mapping 확보 후 exact accuracy 측정으로 진짜 baseline 정착. NewPipe 같은 OSS 는 application code 가 가독성 유지라 R4 의 적합 sample 이 아닐 수 있음.
4. **R4 narrative 정정 권고**: "real-world ProGuard'd 코드의 정확도" 보다 "library 측 jadx-output 난독화의 plausibility" 로 표현하는 편이 더 정확.

## 한계

- Sample 3 — 통계적 일반화 불가. 단 3 sample 이 모두 desugar library (j$.*) 라 desugar 한정 측정.
- Plausibility 평가는 본인 (Claude Code) 의 직접 판단 — 외부 reviewer 또는 NewPipe maintainer 의 검증이 추가되어야 객관성 강화.
- Exact accuracy 측정 불가 (ProGuard mapping file 부재). 본 측정은 semantic plausibility 만.

## 재현

```bash
python scripts/_r4_pick_targets.py    # NewPipe 비즈니스 vs desugar HIGH 클래스 분류
# → top 3 desugar HIGH sample 확인
# Stage 0 LLM rename = Claude Code 세션에서 직접 적용 (configs/prompts/stage0_deobfuscate.md)
# 결과는 data/deobf/NewPipe_renames_20260607.json 에 수동 commit
```
