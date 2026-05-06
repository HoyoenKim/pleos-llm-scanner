# Future Work — 학기 외부 작업 목록

_작성: 2026-06-07 / 본 보고서 v1.0 의 Future Work 섹션과 함께 사용._

본 학기 (2026-1) 안 완료한 RQ 측정값과 정직한 한계를 [`01_report.md`](01_report.md) § 7 / § 8 에 정리했다. 본 문서는 그 한계를 해소하는 **학기 외부 후속 작업 17 종** 을 4 카테고리로 정리한다.

## 0. 본 학기 안 완료한 RQ 측정 (참고)

| RQ | 본 학기 측정 | 한계 |
|---|---|---|
| RQ1 | R1.a transition + R1.b bootstrap CI (n=19, n=28) + R1.c paired McNemar (p=0.375) + R1.d 표본 확장 (n=19→28) + random baseline (28× bias) | n=28 으로 paired test power 부족, n ≥ 50 표본 확장 필요 |
| RQ2 | R2.a disagreement matrix + R2.b' defender prompt 효과 (κ 0.0 → 0.9) | 외부 vendor cross-read 미실시 — 단일 벤더 (Anthropic) 한정 |
| RQ3 | R3.a 207 APK native lib inventory (10.6%) + boundary 4 sample | Native-bound vuln 정량 미측정 — radare2 통합 필요 |
| RQ4 | NewPipe entropy + Stage 0 semantic plausibility (~33% GOOD) | Exact accuracy 측정 불가 — ProGuard mapping 부재 |

---

## 1. RQ 외부 의존 작업 (4 종)

각 RQ 의 한계를 정량 해소하는 후속 측정.

### F1. R1.d 더 확장 (n=28 → n ≥ 50)

**의존**:
- DIVA gradle build (Android SDK + Java 17)
- 추가 commercial APK 다운로드 환경 (proxy / IP 보호 정책)
- 외부 GT corpus 라벨링 시간

**추정 시간**: 1~2주

**측정 가치**:
- bootstrap CI 폭 추가 감소 (n=28 ±10%p → n=50+ ±5%p 가능)
- paired McNemar 의 power 향상 → R1.c 재측정 시 통계적 유의성 도출 가능 (현재 p=0.375)
- 본 학기의 "Stage 3 향상이 우연이 아닌가" 질문에 대한 통계적 검정 결론

### F2. R2.b — Multi-vendor LLM ensemble

**의존**:
- Anthropic + OpenAI + Google API budget
- IP 보호 정책 (PleOS 코드 외부 송출 제한) 협의 — InsecureBankv2 / NewPipe 같은 공개 corpus 만 사용한다면 정책 우회 가능

**추정 시간**: 1주

**측정 가치**:
- 본 학기의 single-model multi-prompt 와 진짜 multi-vendor multi-model 의 정량 비교
- 모델 고유 blind spot 의 공유 여부 측정 (RQ2 의 핵심 미답 질문)
- D3 = (A) 멀티 모델 의 자동화 가능성 첫 입증

### F3. R3.c — Native-bound vuln 정량 추정

**의존**:
- radare2 headless (MIT, 외부 API 의존 없음) — 본 학기 환경 제약과 호환
- LLM wrapper for symbol enumeration / disassembly 분석

**추정 시간**: 2~3주

**측정 가치**:
- Boundary 4 sample (UnCrackable-L2, r2pay, HelloWord-JNI, certPinXamarin) 의 in-scope finding 측정
- 한계 L1 (Java-only) 의 정량 수치화 — "10.6% APK 의 native vuln 중 몇 % 가 보안 가치 있는가"
- PleOS 207 APK 의 native 측 보안 분석 첫 단계

### F4. R4 — Exact accuracy 측정

**의존**:
- NewPipe 같은 OSS APK 의 ProGuard mapping file 확보 (release notes 또는 debug build 다운로드)
- 또는 closed-source commercial APK (GT 라벨링 어려움)

**추정 시간**: 1주

**측정 가치**:
- Hand-crafted MASTG 100% (upper bound) vs Real-world floor 의 exact accuracy
- RQ4 의 진짜 baseline 정착 — 본 학기 33% GOOD plausibility 가 실제로 몇 % exact 인지

---

## 2. 산업 적용 / 운영 전환 작업 (4 종)

본 학기 PoC → 실제 PleOS 차량 SW 라이프사이클 통합.

### F5. Fully-batch 자동화 — CI/CD trigger

**의존**:
- PleOS-internal LLM endpoint 또는 외부 LLM API 정책 합의
- GitHub Actions wrapper script (`src/llm_client.py` 미구현)

**추정 시간**: 2~3주

**산출물**:
- 본 학기 인터랙티브 (~40분/APK) → 자동 8~15분/APK
- PR 이벤트 / nightly batch / OTA pre-flight trigger 가능

### F6. Native binary scanner 통합 (radare2 + LLM)

**의존**: F3 와 동일 + Stage 1 카테고리 enum 확장 (`anti_tamper`, `native_crypto` 등 추가)

**추정 시간**: 4~6주 (F3 후속)

**산출물**:
- Java/Kotlin scanner + native binary scanner 의 2-track architecture 구현
- 본 보고서 § 5 통합 아키텍처 권고의 실제 구현체

### F7. Androidmeda 통합 (Apache 2.0 deobf 모듈)

**의존**: Source fork + 본 `src/deobf/entropy.py` 와 cross-check API 정의

**추정 시간**: 2주

**산출물**:
- 본 entropy 측정 + Androidmeda LLM rename 의 정확도 비교
- Stage 0 의 다양한 backbone 옵션 평가

### F8. OS swap PoC — QNX 또는 AGL

**의존**:
- Ghidra / IDA 도구 체인
- QNX Security Reference Manual 또는 AGL Security Best Practices 매핑 yaml
- 의도적 취약 QNX/AGL corpus (현재 부재)

**추정 시간**: 2~3주

**산출물**:
- 본 보고서 § 6 일반화 평가 의 실제 측정값
- "방법론 OS-독립 60~70%" 추정값을 정량 검증

---

## 3. 학기 발표 / 평가 (사용자 환경 작업, 5 종)

Claude Code 가 직접 못 하는 사용자 환경 의존 작업.

### F9. 라이브 데모 시나리오 (3~5분)

**의존**: 사용자 로컬 환경 (에뮬레이터 + ADB + jadx + Claude Code 세션)

**시나리오 권고**:
1. PleOS Connect 에뮬레이터 부팅 (~30초)
2. `adb shell pm list packages -s | grep -E '<sample>'` (10초)
3. `bash scripts/decompile.sh data/apks/<sample>.apk` (1~2분)
4. Claude Code 세션 진입 → keyword grep + Stage 1 분석 (1~2분)
5. 결과 JSON / md 출력 (즉시)
6. `python src/eval.py --bootstrap 1000` 으로 측정값 표시

### F10. 백업 데모 영상 녹화

**의존**: 사용자 OBS / 화면녹화 도구. 장비 고장 대비.

**추정 시간**: 1시간 (녹화 + 편집)

### F11. 예상 Q&A 정리

**자주 받을 질문 후보**:
- 외부 LLM 보안 리스크 (본 연구 = Claude Code only 로 답변)
- 로컬 LLM 전환 비용 (Future Work)
- 타 IVI 플랫폼 (QNX/AGL) 일반화 — § 6 답변
- TARA 통합 실효성 — § 5 MVP 답변
- Native-bound vuln 미커버 — F3 / F6 답변
- n=28 표본 작음 — R1.c / R1.d 한계로 답변
- multi-LLM 대신 multi-prompt 정당성 — R2.b' 결과 (κ 0.0 → 0.9) 답변

### F12. 운영 비용 stopwatch 측정

**의존**: 사용자 직접 stopwatch — 신규 APK 1개 fully-pipeline 시간 측정

**측정 항목**:
- jadx 디컴파일 시간
- keyword grep + priority class 추출 시간
- Stage 1 LLM 분석 시간 (인터랙티브)
- Stage 2 caller 분석 시간
- Stage 3 multi-perspective 시간
- 보고서 / 매핑 / TARA 자동 생성 시간
- **합계 → week11 추정값 (40분/APK) 검증 + fully-batch 변환 시 단축률 추정**

### F13. 보고서 v1.0 → v1.1

**의존**: 지도교수 추가 피드백 (학기 평가 후)

**추정 시간**: 반나절~1일 (피드백 양에 따라)

---

## 4. 후속 연구 / 개념 단계 (4 종)

학기 외 장기 연구 방향.

### F14. Crowdsourced GT corpus

**의존**: 외부 보안 분석가 협업, GT 라벨 sharing 플랫폼

**의의**:
- self-label bias 의 근본 해소 — 외부 라벨러로 검증
- 본 학기 self GT n=15 의 evaluator bias caveat 해소
- 통계적 power n=50+ 자동 달성

### F15. Symbolic execution 통합 (binsec / angr)

**의존**: F3 / F6 후속

**의의**:
- Native ↔ Java boundary 자동 매핑 — 한계 L1 의 깊은 해소
- 결정론적 데이터 흐름 분석 + LLM 의 reasoning 결합

### F16. Stage 1 prompt evolution / chain-of-thought

**의존**: prompt template 자동 학습 framework

**의의**:
- 카테고리별 prompt template 자동 generation
- 본 학기 hardcoded prompt → 적응형 prompt 로 generalize

### F17. TARA workflow 자동 갱신

**의존**: 차량 telemetry 입력 + 머신러닝 incident classifier

**의의**:
- 본 학기 정적 매핑 → 동적 TARA workflow
- 신규 incident 가 기존 scenario 와 매칭 시 자동 update, 신규 scenario 생성

---

## 우선순위 권고

본 보고서의 직접 한계를 가장 빠르게 해소하는 순서:

1. **F12** (운영 비용 측정, 사용자 직접) — 본 학기 추정값 정량 검증, 1시간
2. **F1** (n ≥ 50 확장) — RQ1 의 통계적 유의성 도출, 1~2주
3. **F4** (R4 exact accuracy) — RQ4 의 진짜 baseline, 1주
4. **F3** (radare2 + native vuln) — 한계 L1 정량 수치화, 2~3주
5. **F2** (multi-vendor ensemble) — RQ2 의 미답 질문, 1주

본 5 작업이 본 학기 한계의 ~80% 를 정량 해소할 수 있는 최소 셋. 그 후 산업 적용 (F5~F8) 으로 운영 전환 검증.

---

## 산출물 인덱스 (본 학기 마지막 시점)

학기 외부 작업 시 출발점이 될 본 학기 산출물:

- **GT corpus**: `data/ground_truth/combined_labels.json` (n=28)
- **외부 corpus reports**: `data/reports/{UnCrackable-Level1/2/3, r2pay-v1.0, InsecureBankv2}_*.{md,json}`
- **결정론 측정 스크립트**: `src/{eval, ablation, aaos_map, tara_generate}.py`, `src/deobf/entropy.py`, `src/viz/plot_metrics.py`, `scripts/research_r{1a, 1c, 2a, 2b, 3a}_*.py`, `scripts/research_random_baseline.py`
- **프롬프트 (calibrated)**: `configs/prompts/{stage0_deobfuscate, stage1_detect, stage3_attacker, stage3_defender, stage3_domain_expert, stage3_consensus}.md`
- **AAOS / TARA 매핑**: `configs/aaos_mapping.yaml`, `data/reports/{aaos_mapping_table, tara_artifact}.{md,json}`
- **GitHub repo**: [`HoyoenKim/pleos-llm-scanner`](https://github.com/HoyoenKim/pleos-llm-scanner) (MIT)

본 산출물을 그대로 base 로 외부 환경에서 후속 작업 진행 가능.
