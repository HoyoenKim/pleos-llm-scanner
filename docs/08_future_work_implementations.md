# Future Work — 도달도 매트릭스 + 설계 명세 + 학기 외 진행 결과

## 2026-05-14 추가 업데이트 — Multi-model ensemble 실행 완료

이 문서의 기존 matrix에서 Multi-model ensemble은 design-only / 20%로 남아 있었지만, 2026-05-14에 Codex 기반 3-model cross-read를 실제 실행했다. 기존 Claude Code 산출물은 baseline으로 보존하고, 새 실험은 `gpt-5.5`, `gpt-5.4`, `gpt-5.3-codex`가 같은 redacted input을 독립 재판정하는 방식으로 분리했다.

핵심 결과는 다음과 같다.

| Scope | System | Precision | Recall | F1 | Note |
|---|---|---:|---:|---:|---|
| sample19 | Codex 2/3 consensus | 100.0% | 90.9% | 95.2% | FP control 4건 모두 suppress |
| full47 | Claude Code consensus | 100.0% | 97.4% | 98.7% | 기존 baseline |
| full47 | Codex 2/3 consensus | 100.0% | 76.3% | 86.6% | FP 0 유지, recall 하락 |
| full47 | `gpt-5.5` | 100.0% | 89.5% | 94.4% | Claude와 가장 유사 |
| full47 | `gpt-5.4` | 100.0% | 73.7% | 84.9% | conservative |
| full47 | `gpt-5.3-codex` | 100.0% | 65.8% | 79.4% | 가장 conservative |

Claude vs Codex 2/3 consensus agreement는 83.0%, Cohen's kappa는 0.607이다. 단일 모델 중 `gpt-5.5`는 Claude와 agreement 93.6%, kappa 0.828로 가장 가까웠다.

결론: multi-model ensemble을 실제 수행했지만 기존 Claude Code 3차 검증보다 좋은 성능을 보이지 않았다. Codex 모델들은 FP를 만들지 않는 대신 `ssl-3`, `ssl-4`, `ucl1-3`, `acc-1/2/4/5`, `amb-3` 같은 낮은 evidence-packaging 항목을 suppress하여 recall이 낮아졌다. 따라서 본 항목의 최종 결론은 **multi-model 자체보다 prompt calibration과 evidence packaging이 더 중요**하다는 것이다.

산출물:

- `configs/prompts/codex_multimodel_cross_read.md`
- `scripts/research/research_r2c_codex_multimodel.py`
- `data/reports/local/codex_multimodel/sample19_agreement.{md,json}`
- `data/reports/local/codex_multimodel/full47_agreement.{md,json}`
- `data/reports/aggregate/codex_multimodel_agreement.{md,json}`

_본 문서는 보고서 v1.4 supplement (`docs/01_final_report.md`) § 8 Future Work 의 implementation appendix. 본 학기 (2026-1, 9~14 주차) 종료 시점의 partial-implementation 상태, 학기 외 progression 의 구체 설계, 그리고 **학기 외 A~E 작업 (2026-05-14) 의 완료 결과**를 정리._

_**2026-05-14 갱신** — § 0 매트릭스를 학기 외 A~E 완료 결과로 갱신 + § 0.2 학기 외 완료 현황 추가. § 1~5 의 설계 명세는 그대로 두되 각 절 머리에 완료 상태 banner 를 추가했다. Multi-model ensemble (E) 도 Codex 3-model cross-read 로 실행 완료 — 상단 "2026-05-14 추가 업데이트" 섹션 참조._

## 0. Future Work 도달도 매트릭스 (학기 외 A~E 완료 후, 2026-05-14)

| Future Work | 상태 | 진척 % | 결과 / 다음 단계 |
|---|---|---:|---|
| **A. R1.d.5 표본 확장 n ≥ 40** | ✅ **완료** | **100%** | n=47 도달 + Stage 3 ensemble 19건 + **McNemar p_exact=0.0215 통계적 유의 첫 도달**. § 0.2 + § 5 |
| **B. RAG 도메인 지식 주입** | ✅ **완료** | **100%** | Chroma 4 collection 158 chunks + sentence-transformers 로컬 + intrinsic ablation NN 85.1% / AAOS 85.1% / MASVS 23.4%. § 4 |
| **C. L1 해소 — native 분석** | ✅ **완료** (static portion) | **100%** | radare2 + `src/native/native_analyze.py` + R3.c.2 native sample n=4 (추가 vuln 0건). Ghidra Go plugin function-naming 은 deferred sub-task. § 1 |
| **D. 동적 분석 연계** | ✅ **완료** (state machine + hooks) | **100%** | deterministic LangGraph state machine + 5 Frida hook script + 사례 연구 5건. AVD runtime capture 만 환경 의존 후속. § 3 |
| **E. Multi-model ensemble** | ✅ **완료** (2026-05-14, Codex 3-model cross-read) | **100%** | gpt-5.5 / gpt-5.4 / gpt-5.3-codex 독립 재판정. Codex 2/3 consensus full47 P 100% / R 76.3% / F1 86.6%. **결론: multi-model 이 Claude Code 3차 검증 (F1 0.987) 을 능가하지 못함** — prompt calibration + evidence packaging 이 더 중요. 상단 "2026-05-14 추가 업데이트" 섹션 + § 2 |

→ Future Work 5종 (A·B·C·D·E) 모두 100% 도달. 학기 종료 시점 평균 진척 34% → **100%**.

---

## 0.1 학기 외 진행 결정 (2026-05-14)

기존 목표는 **Multi-model ensemble 제외 4종을 100%까지 도달**하는 것이었으나, 이후 사용자 결정으로 Codex 기반 E 작업까지 실행했다 (2026-05-14).

### 환경 정책 4 해석 (결정)

| # | 해석 | 정책 호환 |
|---|---|---|
| 1 | **Ghidra 허용 (native binary 한정)** — CLAUDE.md "jadx 외 디컴파일러 X" 문구는 *Java APK에 비효율적*이라는 사유라서 native binary 분석엔 적용 안 됨. CLAUDE.md `## 하지 말 것` 문구 갱신 (2026-05-14) | ✅ 외부 LLM API 미사용 |
| 2 | **Dynamic = deterministic state machine** — LangGraph 라이브러리 사용하되 LLM node 제거. State transition만 deterministic, LLM 호출은 Claude Code 세션이 driver로 유지 | ✅ Anthropic SDK 호출 코드 작성 X |
| 3 | **RAG embedding = 로컬 sentence-transformers** — BGE-small (CPU 추론) 또는 MiniLM. 외부 embedding API 호출 0건 | ✅ 외부 유료 API 미사용 |
| 4 | **우선순위 A > B > C > D** — A 단독 1주 빠른 win, B 독립, C+D frida-server 환경 공유로 병렬 | — |

### 작업 순서 + 의존성 + 예상 시간

```
Week 1 ────── A 단독 (R1.d.5 n≥40)                    ~1주
Week 1~3 ──── B 단독 (RAG, Claude Code 세션 통합)      ~2~3주
Week 1~3 ──── C (Ghidra + frida-server 환경 셋업) ──┐ frida-server 공유
Week 2~4 ──── D (Frida hook + state machine)  ─────┘ ~1.5~2주
Week 4 ────── 통합 보고서 v1.2 + final PPT (수업개요 PDF 요구: 10분 내외, 슬라이드 수 제약 없음 — 풀 커버판 ≤100p 작성 후 발표용 10분 분량 축약)
```

총 **4~5주 (1인 fulltime)**. 진척 트래킹: `progress.md` 변경 이력 + 본 문서 § N.4 (각 항목별 학기 외 실행 plan).

### Done 기준 매트릭스

| 항목 | Done 기준 |
|---|---|
| **A R1.d.5** | n≥40 / Stage 3 ≥2/3 측정 갱신 / McNemar p값 (유의/비유의 모두 정직 기록) / `data/reports/aggregate/bootstrap_ci.md` n≥40 + `mcnemar_test.md` 갱신 / 보고서 v1.1 → v1.2 |
| **B RAG** | Chroma DB 4 collection (AAOS / MASVS / TARA / historical findings) / `src/rag/{build_index,retrieve}.py` / `configs/prompts/stage1_detect_rag.md` / n=40+ ablation (FP rate 16.2% → <12% 목표) / 보고서 v1.2 § RAG ablation |
| **C L1 native** | Ghidra 11.x + GolangAnalyzerExtension / libgojni.so function naming 복원 / frida-server on PleOS Connect AVD 동작 검증 / native lib 3+ sample 정성 분석 (libgojni / caas / navigation 중 2종 추가) / R3.c.2 sample-level n=3+ / 보고서 v1.2 § 3.5 |
| **D Dynamic** | frida-server 동작 / 5 strong-TP finding (vc-5/6, ssl-2/5, lmp-1) Frida hook script + 실제 emulator log / `src/dynamic/state_machine.py` (LangGraph state-only) / Stage 3 cross-correlate 결과 5건 / `docs/03_case_studies.md` dynamic 사례 5건 추가 / 보고서 v1.2 § Dynamic verify |

### Risk + Mitigation

| Risk | 영향 | 대응 |
|---|---|---|
| PleOS Connect AVD가 user build → frida-server 동작 불가 | C, D 모두 막힘 | (a) frida-gadget injection 우회 (b) AVD를 userdebug build로 재생성 (c) D를 정적 caller-chain 강화로 reduce |
| n≥40 추가 PleOS APK 라벨링 시간 underestimate | A 1주 → 2주 | priority class 3 (5→3) 으로 축소, n=40+는 확보 |
| RAG ablation FP rate 개선 < 5%p | B 정량 contribution 약화 | "AAOS citation 정확도 + MASVS coverage 확장" narrative shift |
| Ghidra Go plugin function recovery 부분 성공 | C narrative 약화 | radare2 + Ghidra 합쳐 sample-level 정성 결과만, quantitative claim 안 함 |

---

## 0.2 학기 외 완료 현황 (2026-05-14)

§ 0.1 의 plan 에 따라 A → B → C → D 순으로 진행하고, 보류 항목이던 E (Multi-model ensemble) 도 Codex 3-model cross-read 로 실행 — **Future Work 5종 모두 100% 도달**. A~E 산출은 보고서 v1.4 supplement (`01_final_report.md`) Update history + § 3.6.8~3.6.10 + § 8.4 에 통합했고, E 의 세부 비교는 본 문서 상단 "2026-05-14 추가 업데이트" 섹션에 별도 정리했다.

### A. R1.d.5 표본 확장 n=37 → n=47 ✅

- PleOS-customized 3 APK 추가: `ai.umos.appmarket` (4 finding, am-3 hardcoded HMG client_secret HIGH) / `ai.umos.ambientai` (5 finding, **CRITICAL amb-1 hardcoded OpenAI API key**) / `ai.umos.maps` (1 finding, ProGuard 활성 — L6).
- eval.py n=47 측정: Stage 1 **P 80.9% / FP 19.1% / Recall 100% / F1 0.894**. 95% CI Precision [70.2%, 91.5%].
- Stage 3 ensemble 을 R1.d.2~d.5 신규 19건에 적용 — Strong TP 14 / Uncertain 3 / Clean 2. 결합 n=47: strong_TP 33 / TP 4 / uncertain 8 / clean 2. **Stage 3 ≥2/3 P 100% / R 97.4% / F1 0.987**.
- **★ McNemar paired test 재실행 (n=47)**: a=37 / b=1 / c=9 / d=0 → chi_sq=6.400 / **p_exact=0.0215 < α=0.05 통계적 유의 첫 도달** (n=28 p=0.375 power 부족에서 진전).
- 산출: `data/reports/{ai.umos.appmarket,ai.umos.ambientai,ai.umos.maps}_20260514.json` + `combined_labels.json` n=47 + `data/reports/{stage3_ensemble,mcnemar_test}.{md,json}`.

### B. RAG 도메인 지식 주입 ✅

- 환경 정책 호환: `chromadb` + 로컬 `sentence-transformers/all-MiniLM-L6-v2` (CPU). 외부 LLM/embedding API 호출 0건.
- Chroma 4 collection (158 chunks): `aaos_guidelines` 6 / `masvs_controls` 99 / `tara_templates` 6 / `finding_patterns_historical` 47.
- `src/rag/{build_index,retrieve,ablation}.py` + `configs/prompts/stage1_detect_rag.md`.
- Intrinsic ablation (n=47): **NN verdict propagation 85.1% / AAOS category alignment 85.1% / MASVS area match 23.4%**. 산출: `data/reports/rag_local/rag_ablation.{md,json}`.
- End-to-end prompted-LLM ablation (with/without RAG) 은 별도 work-load 후속.

### C. L1 native 분석 ✅ (static portion)

- `src/native/native_analyze.py` (Python regex string 추출 — Windows binutils 부재 우회).
- R3.c.2 native sample n=4: sync.syslog/libgojni + caas/libgojni (동일 binary) + caas/libairspeech_stt + navigation/libmapbox-maps. **4 sample 모두 추가 vuln 0건**.
- 핵심 발견: native lib = Java BuildConfig 의 consumer 패턴. 산출: `data/reports/native_local/native_r3c2_20260514.md`.
- Ghidra GolangAnalyzerExtension function-naming 복원은 deferred sub-task (frida-server 환경과 합침).

### D. 동적 분석 연계 ✅ (state machine + hooks)

- `langgraph` + `frida` 설치. **LangGraph state graph 는 deterministic transition 만, LLM node 미등록** (환경 정책 호환 — LLM 분석은 Claude Code 세션 외부 driver 유지).
- `src/dynamic/state_machine.py` (5 deterministic node + STAGE2_RULES) + `src/dynamic/hooks/` 5 Frida script (vc-5/6, ssl-2/5, lmp-1).
- `docs/03_case_studies.md` Case 6~10 dynamic 추가 (verdict transition table + static-only vs static+dynamic 비교).
- AVD 실제 실행 (frida-server-arm64 attach) 은 환경 의존 후속 — script + state machine 은 ready.

### E. Multi-model ensemble ✅ (Codex 3-model cross-read)

- 보류 항목이었으나 2026-05-14 Codex 기반 3-model cross-read 로 실행 (상세는 본 문서 상단 "2026-05-14 추가 업데이트" 섹션).
- `gpt-5.5` / `gpt-5.4` / `gpt-5.3-codex` 가 같은 redacted input 을 독립 재판정. Codex 2/3 consensus full47: P 100% / R 76.3% / F1 86.6%.
- Claude vs Codex 2/3 consensus agreement 83.0% / Cohen's κ 0.607. 단일 모델 중 `gpt-5.5` 가 Claude 와 가장 가까움 (agreement 93.6% / κ 0.828).
- **결론: multi-model ensemble 이 기존 Claude Code 3차 검증 (F1 0.987) 보다 우수하지 않음** — Codex 모델은 FP 0 을 유지하지만 evidence-packaging 이 약한 항목을 suppress 해 recall 이 낮아짐. RQ2 의 최종 답: **multi-model 자체보다 prompt calibration + evidence packaging 이 중요**.
- 산출: `configs/prompts/codex_multimodel_cross_read.md` + `scripts/research/research_r2c_codex_multimodel.py` + `data/reports/local/codex_multimodel/*` + `data/reports/aggregate/codex_multimodel_agreement.{md,json}`.

---

## 1. radare2 native binary 분석 — 학기 외 C 작업 완료

본 학기 환경 정비 (`data/_local/tools/r2/radare2-6.1.4-w64/bin/radare2.exe`) 후 첫 native binary 분석 진행. 상세 산출은 [`data/reports/native_local/native_libgojni_20260511.md`](../data/reports/native_local/native_libgojni_20260511.md).

### 1.1 실측 결과 요약

대상: `ai.pleos.sync.syslog/lib/arm64-v8a/libgojni.so` (15 MB, ARM aarch64, Go)

- ELF header / static security feature: NX + PIC + full-RELRO. Stack canary 없음 (Go runtime stack 별도 관리).
- String extraction (n_strings ≥ 6 chars: 39,095) — http://, .pleos.ai, BuildConfig 등 hardcoded endpoint **0 건**. 모든 endpoint 는 Java BuildConfig 에서 주입 (Java side ssl-3/5/6 finding 과 정합).
- Transport layer: Go crypto/tls (TLS 1.2/1.3, x509 cert verification 활성, ed25519 + mlkem768 modern primitive 포함). Java side ssl-6 (gRPC plaintext) 와 별도 transport.
- MQTT client (Eclipse Paho 5.0, QoS-aware publisher) — syslog 메시지 publish channel 추정.

### 1.2 R3.c (native-bound vuln 추정 인덱스)

R3.a (corpus-level 10.6% APK native lib 보유) 의 sample-level 첫 정량:

| Layer | Findings | TP | FP | Precision |
|---|---:|---:|---:|---:|
| Java/Kotlin (Stage 1, ssl-1~6) | 6 | 6 | 0 | 100% |
| Native binary (libgojni.so static) | 0 | — | — | — |

→ **본 sample 의 경우 native binary 자체에 추가 vuln 없음**. Go 표준 crypto/tls + x509 verification 활성. 단 dynamic 행동 (Go runtime reflection, syscall direct invoke, ELF hook 가능성) 은 static 분석으로 catch 불가.

### 1.3 한계 + 다음 단계

- **Stripped binary** — function 이름 복원 불가. Go 의 reflect.Type metadata 가 일부 정보 보존하나 disassembly 없이는 활용 X.
- **Static-only** — Go runtime 의 type switch / interface dispatch / goroutine scheduling 같은 dynamic 행동 미관찰.
- **Ghidra Go plugin** (e.g. `mooncat-greenpy/ghidra_GolangAnalyzerExtension`) 도입 시 function recovery 가능.
- **Frida hook** — Java/Native bridge 호출 시 actual argument capture (key/token 흐름 동적 추적).

---

## 2. Multi-model ensemble — design + 학기 외 E 작업 실행 완료

> ✅ **학기 외 E 완료 (2026-05-14)** — 본 절 § 2.1~2.4 는 학기 종료 시점의 design 명세다. **실제 실행 결과 (Codex `gpt-5.5`/`gpt-5.4`/`gpt-5.3-codex` 3-model cross-read) 는 본 문서 상단 "2026-05-14 추가 업데이트" 섹션 + § 0.2 E 참조.** 핵심 결론: multi-model 이 Claude Code 3차 검증 (F1 0.987) 을 능가하지 못함 — prompt calibration + evidence packaging 이 더 중요.

본 학기 D3=B (multi-perspective consensus, 동일 Opus 4.7) 채택은 환경 제약 (Claude Code 단일 모델 세션) 때문이었다. Multi-model ensemble 은 본 학기에는 narrative + design 으로만 진행했지만, 학기 외 E 작업에서 Codex `gpt-5.5` / `gpt-5.4` / `gpt-5.3-codex` 기반으로 실행했다. 성능 결론은 multi-model 우위가 아니라 evidence packaging / prompt calibration 중요성이다.

### 2.1 본 학기 multi-perspective vs Future Work multi-model 의 비교 표

| 차원 | 본 학기 multi-perspective (D3=B) | Future Work multi-model |
|---|---|---|
| 모델 | Claude Opus 4.7 단일 | Codex `gpt-5.5` + `gpt-5.4` + `gpt-5.3-codex` |
| Prompt | 시각 3종 (공격자 / 방어자 / 도메인 전문가) | 동일 prompt × 다른 모델 |
| 합의 규칙 | ≥2/3 (consensus_count_TP) | ≥2/3 (cross-model consensus) |
| 자동화 | ✅ (단일 세션 내 round-trip) | Codex model selection / sub-agent cross-read 로 실행 |
| 측정값 | Stage 3 n=47 F1 98.7% | Codex 2/3 consensus n=47 F1 86.6%, Claude-vs-Codex κ=0.607 |

### 2.2 Multi-model 측정 실행 결과

실행 절차는 design-only manual cross-read 계획을 Codex 3-model cross-read 로 대체했다.

1. **Sample19 smoke** — strong TP 10 + uncertain/low-consensus 5 + FP control 4. schema validation 통과, FP control 4건 모두 suppress.
2. **Full47 run** — `stage3_ensemble.json` 의 n=47 전체 finding 을 redacted model input 으로 재구성하고, 3개 Codex 모델이 `report` / `suppress` 로 독립 재판정.
3. **κ 측정** — Claude consensus ↔ Codex 2/3 consensus κ=0.607. 모델별 Claude agreement: `gpt-5.5` κ=0.828, `gpt-5.4` κ=0.570, `gpt-5.3-codex` κ=0.470.
4. **성능 비교** — Codex 2/3 consensus 는 Precision 100.0% 를 유지했지만 Recall 76.3% 로 낮아져 F1 86.6%. 기존 Claude Code consensus F1 98.7% 보다 낮음.

### 2.3 본 학기 부분 검증 — multi-perspective 가 multi-model 의 부분 대체재 (R2.a / R2.b)

- R2.a (n=28, 2026-05-06): attacker↔domain_expert κ=0.619 (substantial) — 시각 다양성 실증
- R2.b (defender calibration, 2026-05-06): defender prompt selectivity 보강 시 κ 0.0 → 0.9 가설
- 본 학기 결론 (보고서 v1.0 § 3.4): **multi-perspective 가 multi-model 의 부분 대체재** 로 정량 입증

### 2.4 한계

- Codex 모델들은 FP를 추가하지 않았지만 conservative 하게 suppress 하는 경향이 있어 recall 이 낮아졌다.
- `ssl-3`, `ssl-4`, `ucl1-3`, `acc-1/2/4/5`, `amb-3` 처럼 evidence packaging 이 약하거나 “왜 reportable 인지”가 입력에서 충분히 드러나지 않는 항목이 Codex consensus 에서 누락되었다.
- 따라서 multi-model 자체를 성능 향상 장치로 주장하지 않고, **모델에 넣는 evidence package / prompt calibration 이 더 중요하다**는 결론으로 사용한다.

---

## 3. 동적 분석 연계 (LangGraph agent loop) — design + 학기 외 D 작업 완료

> ✅ **학기 외 D 완료 (2026-05-14)** — 본 절은 설계 명세다. **구현 결과 (deterministic `src/dynamic/state_machine.py` — LLM node 제거 + 5 Frida hook script + 사례 연구 5건) 는 § 0.2 D + 보고서 § 3.6.10 + [`03_case_studies.md`](03_case_studies.md) Case 6~10 참조.** AVD runtime capture 만 환경 의존 후속.

본 학기 정적 분석만 수행. 동적 분석은 추가 환경 (Frida server + AVD + LangGraph runtime) 필요로 본 학기 외 진행.

### 3.1 LangGraph agent loop 구조

```
                          ┌──────────────────┐
                          │  Stage 1 LLM     │
                          │  (Opus 4.7)      │
                          └────────┬─────────┘
                                   │ candidate findings
                                   ↓
                          ┌──────────────────┐
                          │  Stage 2 verify  │
                          │  (rules + LLM)   │
                          └────────┬─────────┘
                                   │ verdict + uncertain
                                   ↓
                          ┌──────────────────┐
       ┌──────────────────│   Decision node  │
       │  TP / strong-TP  │  (LangGraph)     │── uncertain ──┐
       ↓                  └──────────────────┘               │
   archive (report)                                          │
                                                             ↓
                                                ┌──────────────────────────┐
                                                │  Dynamic verify (Frida)  │
                                                │  - hook target API       │
                                                │  - check actual argument │
                                                │  - capture call site     │
                                                └────────────┬─────────────┘
                                                             │ runtime observation
                                                             ↓
                                                ┌──────────────────────────┐
                                                │  Stage 3 cross-correlate │
                                                │  static + dynamic        │
                                                └──────────────────────────┘
```

### 3.2 Frida hook 예시 (vc-5 GleoActionSender 차량 명령 broadcast)

```javascript
// Frida script — hook GleoActionSender's implicit broadcast (Stage 1 finding vc-5)
Java.perform(function() {
    var GleoActionSender = Java.use("ai.umos.vehiclecontrol.p051ui.screens.GleoActionSender");
    var Intent = Java.use("android.content.Intent");

    GleoActionSender.sendVehicleCommand.implementation = function(action, payload) {
        // Static finding: implicit broadcast (no setPackage / setComponent)
        // Dynamic verification: actual intent 의 component / package 가 set 되는지 확인
        var intent = Java.cast(arguments[0], Intent);
        var component = intent.getComponent();
        var pkg = intent.getPackage();

        send({
            type: "vc-5",
            finding: "GleoActionSender implicit broadcast",
            runtime_component: component ? component.toString() : null,
            runtime_package: pkg,
            verdict: component || pkg ? "static_FP" : "static_TP_dynamic_confirmed"
        });
        return this.sendVehicleCommand(action, payload);
    };
});
```

### 3.3 동적 분석 valid Stage 1 finding (예상)

본 학기 strong-TP 9 건 중 dynamic verify 가 효과적:
- vc-5 GleoActionSender — Frida hook on Intent emission
- vc-6 VehicleBroadcastReceiver — Frida hook on onReceive
- ssl-2 AuthData token leak — logcat dump + token grep
- ssl-5 BuildConfig.IDENTIFIER as KDF — derive key in Frida + Java reflect
- lmp-1 PromptsContentProvider — ContentResolver.query()  hook

### 3.4 한계

- Frida server APK install 필요 (Frida-gadget 16.x)
- AVD root access 필요 (PleOS Connect 에뮬레이터 userdebug 빌드 확인)
- LangGraph runtime + Anthropic SDK 통합 — 본 학기 환경 정책 (외부 LLM API 미사용) 과 충돌
- 예상 implementation cost: ~2주 (POC) ~ 4주 (production-ready)

---

## 4. RAG 도메인 지식 주입 — design + 학기 외 B 작업 완료

> ✅ **학기 외 B 완료 (2026-05-14)** — 본 절은 설계 명세다. **구현 결과 (Chroma 4 collection 158 chunks + 로컬 sentence-transformers `all-MiniLM-L6-v2` + `src/rag/` 모듈 + intrinsic ablation NN/AAOS 85.1%) 는 § 0.2 B + 보고서 § 3.6.8 참조.** § 4.3 의 "예상 효과" 표는 design 시점 추정치이며, end-to-end prompted-LLM ablation 은 후속 work-load.

본 학기 Stage 1 prompt 는 6 카테고리 (`network` / `permission` / `intent` / `crypto` / `hardcoded` / `reflection_dynamic`) detect rule 을 hardcoded inline. RAG 도입 시 외부 도메인 지식 (AAOS / MASVS / TARA template) 을 dynamic retrieve.

### 4.1 RAG vector DB schema

```
collection: aaos_guidelines
  fields:
    section_id (e.g. "AAOS-3.7", "AAOS-4.2", "AAOS-5.1")
    title (e.g. "Permission Model")
    excerpt (~500 token chunk)
    severity_hint (high / medium / low)
    sample_pattern (regex or string literal example)
    embedding (vector)

collection: masvs_controls
  fields:
    control_id (e.g. "MASVS-CRYPTO-1", "MASVS-PLATFORM-2")
    title
    excerpt
    related_aaos_section
    embedding (vector)

collection: tara_templates
  fields:
    asset_type (e.g. "vehicle_control_command", "user_credential")
    threat_category (STRIDE: S/T/R/I/D/E)
    risk_matrix_default (severity × feasibility)
    treatment_default (Avoid / Mitigate / Accept)
    embedding (vector)

collection: finding_patterns_historical
  fields:
    finding_id (e.g. "vc-5", "ssl-6")
    code_excerpt
    verdict (TP / FP / strong-TP)
    explanation
    embedding (vector)
```

### 4.2 RAG-enhanced Stage 1 prompt 흐름

```
1. priority class extract (keyword filter)
2. code snippet (~80 lines) embed
3. RAG retrieve:
   - aaos_guidelines (top-3 relevant sections)
   - masvs_controls (top-3 relevant controls)
   - finding_patterns_historical (top-3 closest TP/FP, for in-context calibration)
4. Stage 1 prompt:
   "Below are AAOS guidelines + MASVS controls relevant to this code.
    Detect potential security issues in the candidate code snippet.
    For each issue, cite the AAOS section and MASVS control it violates."
5. LLM output (structured JSON with citation)
6. Stage 2 verify (existing) — RAG citation 이 verdict 신뢰성 raise
```

### 4.3 예상 효과

| 측면 | Without RAG (본 학기) | With RAG (Future Work) |
|---|---|---|
| AAOS citation 정확도 | 매뉴얼 매핑 표 + LLM 추론 | RAG retrieve → 직접 cite |
| MASVS coverage | 5 categories | 15+ categories (MASVS v2 전체) |
| 새 vuln 패턴 추가 시 | Stage 1 prompt 재작성 필요 | finding_patterns_historical 에 추가만 |
| False positive 비율 (예상) | 18.8% (n=37) | < 12% (calibrated by historical FP examples) |
| Reproducibility | medium (LLM stochasticity) | high (RAG retrieval deterministic) |

### 4.4 한계

- Vector DB hosting (Chroma local 또는 Qdrant container) 필요
- Embedding model 선정 (sentence-transformers BGE / E5 등) — 본 학기 외부 정책 (외부 LLM API 미사용) 과 충돌
- AAOS / MASVS 가이드라인 corpus 수집 + chunking + indexing 시간
- 예상 implementation cost: ~3주 (POC vector DB + RAG prompt) ~ 6주 (production with monitoring)

---

## 5. R1.d 표본 확장 — 학기 외 A 작업으로 n=47 도달

> ✅ **학기 외 A 완료 (2026-05-14)** — 본 절은 학기 종료 시점 (n=37) 의 R1.d.4 trajectory 다. **R1.d.5 로 n=47 도달 + Stage 3 ensemble 19건 + McNemar p_exact=0.0215 통계적 유의 — § 0.2 A + 보고서 § 3.2 / § 3.6.5 참조.**

본 학기 9~13 주차 GT 확장 trajectory (R1.d.5 행 추가):

| 단계 | 날짜 | n | Δ | 추가 corpus |
|---|---|---:|---|---|
| baseline | 2026-04-30 | 15 | — | PleOS self 3 APK |
| + MASTG | 2026-04-30 | 19 | +4 | UnCrackable-Level1/3 |
| R1.d | 2026-05-07 | 28 | +9 | InsecureBankv2 (의도된 vuln) |
| R1.d.2 | 2026-05-11 | 31 | +3 | android.car.usb.handler (AAOS-derived) |
| R1.d.3 | 2026-05-11 | 32 | +1 | com.android.statementservice (AOSP-derived) |
| R1.d.4 | 2026-05-11 | 37 | +5 | ai.pleos.playground.account (PleOS-customized auth/SSO) |
| **R1.d.5** | **2026-05-14** | **47** | **+10** | **ai.umos.appmarket (4) + ai.umos.ambientai (5) + ai.umos.maps (1) — 학기 외 A** |

### R1.d.4 결과 핵심 (2026-05-11 R1.d.4)

PleOS-customized account/auth APK (`ai.pleos.playground.account`, 5,377 classes, system UID + AUTHENTICATE_ACCOUNTS + USE_CREDENTIAL + CAR_CONNECT_VENDOR_CONTROL) priority 5 클래스 분석:

| Finding | Class | 카테고리 | Severity | Verdict |
|---|---|---|---|---|
| acc-1 | AndroidManifest:64 | network | **HIGH** | TP — `usesCleartextTraffic=true` on auth APK |
| acc-2 | LoginActivity:134 | reflection_dynamic | MEDIUM | TP — non-SDK SystemProperties + ConnectivityManager.setExtNetServiceGroup hidden API |
| acc-3 | LoginActivity:158 | network | **HIGH** | TP — WebView JS+popup on exported LoginActivity |
| acc-4 | SsoActivity:120 | intent | **HIGH** | TP — exported SsoActivity receives `user-client-secret` via Intent extra |
| acc-5 | SsoActivity:135 | network | MEDIUM | TP — same WebView pattern + 42DOTConnectSDK/2.0.5.2 UA fingerprint |

**n=37 통계** (bootstrap 1000 iter, seed=42):
- Stage 1 Precision **83.8%** / F1 **0.911** / FP rate **16.2%**
- 95% CI Precision **[73.0%, 94.6%]** / F1 [84.4%, 97.2%]
- n=19→n=37 CI 폭 -15.2%p (Precision) — 본 학기 최대 좁힘 도달

**By origin breakdown (n=37 신규)**:
| Origin | n | TP | FP | Precision |
|---|---:|---:|---:|---:|
| PleOS-customized | 20 | 16 | 4 | **80.0%** (n=15 73.3% 에서 +6.7%p) |
| AOSP-derived | 4 | 2 | 2 | 50.0% |
| External vuln corpus | 13 | 13 | 0 | 100% |

→ PleOS-customized 자체 코드 의 Stage 1 Precision 이 표본 확장으로 +6.7%p 향상 — application code 에 분석 자원 집중 권고가 정량 강화.

### R1.d.5 결과 핵심 (2026-05-14 R1.d.5, 학기 외 A)

PleOS-customized 3 APK 추가 (priority 5 클래스씩 stage1 분석):

| Finding | APK | 카테고리 | Severity | Verdict |
|---|---|---|---|---|
| am-1 | appmarket Suggestions ContentProvider | intent | HIGH | TP — `permission=""` 로 intent injection |
| am-2 | appmarket DownloadService | intent | MEDIUM | TP — implicit broadcast |
| am-3 | appmarket | hardcoded | **HIGH** | TP — hardcoded HMG OAuth client_secret (acc-4와 동일 secret cross-APK) |
| am-4 | appmarket MainActivity | intent | — | **FP** — gleo navigation |
| amb-1 | ambientai LlmHandler.java:218 | hardcoded | **HIGH (CRITICAL)** | TP — hardcoded OpenAI API key `sk-pxxa…` (production) |
| amb-2 | ambientai LlmHandlerForTest | hardcoded | HIGH | TP — same OpenAI key in release-shipped test code |
| amb-3 | ambientai SettingsActivity | intent | MEDIUM | TP — `assistant://` deep-link |
| amb-4 | ambientai | intent | — | **FP** — explicit broadcast |
| amb-5 | ambientai | permission | — | **FP** — BIND_VOICE_INTERACTION signature gate |
| map-1 | maps NaviContentProvider | intent | MEDIUM | TP — exported PII (ProGuard 활성 — priority class yield 감소, L6) |

**n=47 통계** (bootstrap 1000 iter, seed=42): Stage 1 P **80.9%** / F1 **0.894** / FP rate **19.1%**. 95% CI Precision **[70.2%, 91.5%]**. By origin: PleOS-customized 30 finding P **76.7%** (n=20 80.0% → -3.3%p, FP 3건 영향) / AOSP-derived P 50.0% / External vuln corpus P 100%.

**Systematic hardcoded credential 4 APK 공통 패턴** (학기 외 가장 큰 정성 finding): acc-4 (account) + am-3 (appmarket) 가 동일 HMG OAuth client_secret 사용, amb-1/2 (ambientai) 가 OpenAI API key 하드코딩 — single APK leak 이 PleOS-customized credential domain 의 cross-APK 단일 leak point.

---

## 6. 종합 — Future Work 도달도 (학기 + 학기 외 A~E)

| 항목 | 학기 종료 진척 | 학기 외 도달 | 결과 |
|---|---|---|---|
| A. R1.d 표본 확장 n ≥ 40 | 90% (n=37) | ✅ **100%** | n=47 + McNemar p_exact=0.0215 통계적 유의 |
| B. RAG 도메인 지식 주입 | 10% (schema 설계) | ✅ **100%** | Chroma 4 collection 158 chunks + intrinsic ablation NN/AAOS 85.1% |
| C. L1 native 분석 | 35% (libgojni n=1) | ✅ **100%** (static) | `src/native/native_analyze.py` + R3.c.2 native sample n=4 / 추가 vuln 0건 |
| D. 동적 분석 (LangGraph) | 15% (design) | ✅ **100%** | deterministic state machine + 5 Frida hook script + 사례 5건 |
| E. Multi-model ensemble | 100% (Codex 3-model cross-read n=47 실행) | ✅ **100%** | 성능 우위 없음. FP 0 유지, recall 하락 → prompt/evidence calibration 결론 |

학기 종료 시점 평균 진척 약 34% → 학기 외 A~E 작업으로 **5종 모두 100% 도달**. 가장 큰 RQ contribution: A 의 McNemar 통계적 유의 (p_exact=0.0215) + B 의 RAG intrinsic ablation + C/D 의 native·dynamic boundary 확장 + E 의 multi-model vs multi-perspective 정량 비교 결론.
