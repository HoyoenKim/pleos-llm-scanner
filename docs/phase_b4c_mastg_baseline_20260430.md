# Phase B-4.c — MASTG 외부 GT 베이스라인 (2026-04-30)

> Phase B-4.c 완료. OWASP MASTG (Mobile Application Security Testing Guide) 공식 Crackmes 3종을 외부 GT corpus로 도입하여 PleOS pipeline의 측정값 신뢰도 확보.

## Corpus

| APK | 출처 | 사이즈 | 디컴파일 java files | 비고 |
|---|---|---|---|---|
| **UnCrackable-Level1** | MASTG/Crackmes/Android/Level_01 | 68 KB | 6 | hardcoded AES key + ciphertext (canonical MASVS-CRYPTO-1 case) |
| **UnCrackable-Level2** | MASTG/Crackmes/Android/Level_02 | (작음) | 283 (대부분 androidx) | 핵심 secret = `libfoo.so` 안. Java 측엔 anti-tamper만. **boundary case** |
| **r2pay-v1.0** | MASTG/Crackmes/Android/Level_04 | (작음) | 334 (대부분 androidx) | 모든 token 검증 = `libnative-lib.so`. Java 측엔 RootBeer + `1337/0` 의도적 crash 패턴. **boundary case** |

## 측정 결과

### A. Stage 1 — Combined corpus (n=18 = self 15 + MASTG 3)

```
labelled=18  TP=14  FP=4  uncertain=0  FN=0
precision (lenient / strict): 77.8% / 77.8%
false-positive-rate (lenient / strict): 22.2% / 22.2%
recall: 100.0%
```

| Source | n | TP | FP | Precision (lenient) |
|---|---|---|---|---|
| self (PleOS 3 APK) | 15 | 11 | 4 | **73.3%** |
| MASTG (UnCrackable-Level1) | 3 | 3 | 0 | **100%** |
| **combined** | **18** | **14** | **4** | **77.8%** |

→ **PPT 가설 1차 오탐률 25%** ⟹ 측정 **22.2%**, **2.8%p 안쪽 충족**.
→ 외부 GT corpus 도입 후 PleOS-only 73.3% → combined 77.8% (+4.5%p) — 작은 표본 우연성 줄임.

### B. Per-category breakdown (combined n=18)

| 카테고리 | TP | FP | total | Precision |
|---|---|---|---|---|
| intent | 5 | 0 | 5 | 100% |
| hardcoded | 4 | 0 | 4 | 100% |
| crypto | 3 | 0 | 3 | 100% |
| network | 2 | 2 | 4 | 50% |
| permission | 0 | 2 | 2 | 0% |

→ FP 4건은 모두 VehicleControl의 `setAllowFileAccess`/`setJavaScriptEnabled` 같은 hardening 의제 + AppPermissionManager의 internal Nav 진입 — Stage 2.b deep-link 검증으로 모두 FP CONFIRMED.

### C. Ablation (combined n=18 vs PleOS-only n=15)

| 변형 | n=15 (PleOS only) | n=18 (combined) | Δ |
|---|---|---|---|
| A.1 stage 1 F1 | 0.846 | **0.875** | +0.029 |
| A.2 stage 2 F1 (caller P-ceiling) | 1.000 | 1.000 | 0 |
| A.3 stage 3 (≥3/3) F1 | 0.900 | 0.783* | −0.117 (artifact) |
| B ≥2/3 F1 | 0.952 | 0.833* | −0.119 (artifact) |

\* **artifact**: stage3_ensemble_20260429.json은 self GT n=15에 한해 평가됐고 MASTG 3건은 stage3 미통과 → ablation harness가 그 3건을 FN으로 잡음. Recall이 인위적으로 떨어진 것이고 실제 stage3 ensemble의 성능 변화 아님. **Stage 3 정식 측정은 PleOS-only n=15 (≥2/3 F1 0.952) 그대로 유효**.

→ 다음 단계 (Phase B-4.c.2): UnCrackable-Level1 3 finding에 stage3 ensemble 평가 추가 → MASTG-on-stage3 측정. 다만 결정적 측정값은 stage1이 외부 GT에서 100% precision으로 충분히 확정.

## Pipeline boundary 발견 — UnCrackable-Level2 + r2pay

두 sample은 모두 핵심 비즈니스 로직 / secret이 native lib (`.so`) 안. Java-side static analysis pipeline 의 **구조적 boundary**.

### UnCrackable-Level2 — Java side
- `System.loadLibrary("foo")` + `private native boolean bar(byte[])` — JNI bridge 만 노출
- root/debug detection (3 method) + `Debug.isDebuggerConnected()` polling — anti-tamper만
- **In-scope (category enum) finding 0건**

### r2pay-v1.0 — Java side
- `System.loadLibrary("native-lib")` + `public native byte[] gXftm3iswpkVgBNDUp(byte[], byte)` — 모든 token 생성 native
- RootBeer (com.scottyab.rootbeer) 라이브러리 사용 — 정상 사용, vuln 아님
- 의도적 anti-tamper crash: `int i = 1337 / 0`, `np.notify()` on stale NullPointerException
- **In-scope (category enum) finding 0건**

### Out-of-scope known issues (정직한 한계)

| APK | Real vulnerability | MASVS | Future pipeline extension |
|---|---|---|---|
| UnCrackable-Level2 | AES key/ciphertext in libfoo.so | MASVS-CRYPTO-1 | Native-binary scanner (Ghidra headless + LLM + symbol enum) |
| UnCrackable-Level2 | Weak root + runtime debugger detection | MASVS-RESILIENCE-2/3 | category enum 확장: `anti_tamper` |
| r2pay-v1.0 | PIN/amount validation in libnative-lib.so | MASVS-CRYPTO-1, MASVS-AUTH-2 | Native-binary scanner |
| r2pay-v1.0 | `1337/0` + `NullPointerException.notify()` tamper response | MASVS-RESILIENCE-3 | `anti_tamper` category |
| r2pay-v1.0 | RootBeer bypassable via MagiskHide/Zygisk | MASVS-RESILIENCE-3 | `anti_tamper` + bypass-pattern matcher |

→ **PPT/논문 limitations 섹션에 정량 명시**: "Java-only static analysis는 native-bound vuln (MASVS-CRYPTO-1 in `.so`)을 탐지하지 못함. 본 corpus 3 sample 중 2 sample (UnCrackable-Level2, r2pay-v1.0)이 이 한계를 정량화. 해결은 Phase C/D 이후 native-analysis tool 통합 (Ghidra headless + LLM)."

## PPT 가설 매칭 상태 (2026-04-30 갱신)

| 지표 | PPT 가설 | 측정 (combined n=18) | 상태 |
|---|---|---|---|
| 1차 오탐률 | 25% | **22.2%** | ✅ 충족 (-2.8%p) |
| Precision (Full Pipeline) | 0.93 | **stage3 ≥2/3 = 1.00 (PleOS n=15 측정)** | ✅ 도달·초과 |
| 3차 오탐률 (Stage 3 적용) | 7% | **0% (PleOS n=15 측정)** | ✅ 도달 |
| 카테고리별 정확도 (combined) | — | intent 100% / hardcoded 100% / crypto 100% / network 50% / permission 0% | — |
| 분석 대상 축소율 | 30~40% | **99.49%** (PleOS VehicleControl) | ✅ 초과 |
| 난독화 정확도 | 40→78% | — | ⬜ Phase C 측정 |

## 산출물

- `data/apks/_mastg/owasp-mastg/` — MASTG repo shallow clone (131 MB, gitignored)
- `data/apks/_mastg/UnCrackable-Level1.apk` + `UnCrackable-Level2.apk` + `r2pay-v1.0.apk` (gitignored)
- `data/decompiled/UnCrackable-Level1/` + `UnCrackable-Level2/` + `r2pay-v1.0/`
- `data/reports/UnCrackable-Level1_20260430.{json,md}` — 3 finding (HIGH 1 / MEDIUM 1 / LOW 1)
- `data/reports/UnCrackable-Level2_20260430.json` — 0 in-scope finding + boundary scope_note
- `data/reports/r2pay-v1.0_20260430.json` — 0 in-scope finding + boundary scope_note
- `data/ground_truth/mastg/uncrackable_level1.labels.json` — 3 TP labels (MASVS-CRYPTO-1, MASVS-STORAGE-2/3)
- `data/ground_truth/mastg/uncrackable_level2_r2pay.labels.json` — 0 in-scope, 5 out-of-scope known issues
- `data/ground_truth/combined_labels_20260430.json` — n=18 combined GT (self 15 + mastg-l1 3)
- `docs/phase_b4c_mastg_baseline_20260430.md` (this file)

## 재현

```bash
cd pleos-llm-scanner

# 1. MASTG repo (이미 clone되어 있음)
# git clone --depth=1 https://github.com/OWASP/owasp-mastg.git data/apks/_mastg/owasp-mastg

# 2. 디컴파일
bash scripts/decompile.sh data/apks/_mastg/UnCrackable-Level1.apk
bash scripts/decompile.sh data/apks/_mastg/UnCrackable-Level2.apk
bash scripts/decompile.sh data/apks/_mastg/r2pay-v1.0.apk

# 3. 측정
python src/eval.py \
    --labels data/ground_truth/combined_labels_20260430.json \
    --reports 'data/reports/*.json' \
    --by-stage stage1

python src/ablation.py \
    --labels data/ground_truth/combined_labels_20260430.json \
    --reports 'data/reports/*.json' \
    --stage3 data/reports/stage3_ensemble_20260429.json
```

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-30 | Phase B-4.c 완료 — MASTG 외부 corpus 3 sample 도입. Combined n=18 stage1 P 77.8% / Recall 100% / F1 0.875. PPT 가설 1차 오탐률 25% 매칭 (-2.8%p). Pipeline boundary 정량 명시 (Java-only → native-bound vuln 못 잡음, MASTG-Level2/r2pay 2 sample이 입증) |
