# PPT 수정 가이드 (2026-04-29)

> **CLAUDE.md 정책**: 본 디렉토리의 `.pptx`/`.pdf`는 제출본이므로 직접 덮어쓰지 X.
> 새 버전이 필요하면 별도 파일로 (예: `<project>_5주차_<id>_<name>_v2.pptx`).
>
> 본 가이드는 **사용자가 직접 PPT 수정할 때 참고**하는 매핑 표. 수정 사유는 두 가지:
> 1. **3차 검증 방식 변경**: 멀티 모델(Claude+GPT-4) 가정 → **멀티 프롬프트**(동일 모델 + 시각 3종)로 대체. 외부 환경 제약 명시.
> 2. **정량 수치를 가설에서 실측으로**: 1차 오탐률 25% → 40~50% 등

## 1. 변경 사유 요약

### 3차 검증 방식 변경 사유 (멀티 모델 → 멀티 프롬프트)
- 본래 PPT는 "Claude + GPT-4 멀티 LLM 앙상블"을 가정 (4주차/8주차 PPT 등).
- 환경 제약: 외부 유료 API 미보유 + Claude Code 단일 모델 세션 한계 (Phase B-2에서 발견).
- 자체 자동화 가능한 **단일 LLM × 다중 프롬프트** 앙상블로 대체.
- 시각 3종: 공격자 / 방어자 / IVI 도메인 전문가 — `pleos-llm-scanner/configs/prompts/stage3_*.md` 참조.

### 수치 갱신 사유
- PPT의 25% / 12% / 7% / 40% / 65% / 78% / 0.93 등은 **선작성된 가설** (CLAUDE.md 정책: "가짜·추정 정량 수치 보고서에 기록 X").
- 2026-04-29 첫 실측 (3 APK / 12 findings):
  - 1차 오탐률 = **40.0% (lenient) / 50.0% (strict)**  ← 가설 25% 대비 +15~25%p
  - Precision = **0.60 (lenient) / 0.50 (strict)**  ← 가설 0.93 대비 -0.33~0.43
  - Recall = 100% (단 GT가 stage1 결과 superset이라 의미 약함)
  - 분석 대상 축소율 = **99.49%** (1,765 → 9 priority class — VehicleControl 단일 APK 기준) ← 가설 30~40% 대비 매우 큼

## 2. 주차별 PPT 수정 항목 매핑

> 정확한 슬라이드 번호는 본인이 PPT 열어 확인. 아래는 **수정해야 할 항목의 종류**와 **새 권장 표기**.

### 4주차 PPT — 도구 비교 + 환경 구축

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| 디컴파일러 | jadx-ai-mcp (1순위) | jadx 1.5.5 CLI (jadx-ai-mcp는 도입 보류, Future Work 명시) |
| 환경 | (가정) | Intel Core Ultra 7 155H + Win11 Home 26200 + GPU 없음 + WHPX 가속. PleOS Connect v2.0.5 x86_64 emulator |

### 5주차 PPT — 코드 분할 + PleOS APK 3종 초기 분석

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| 분석 대상 축소율 | 30~40% | **99.49% (실측, VehicleControl ai/umos+ai/pleos 1,765 java → 9 priority class)** + caveat: 단일 APK·priority 정의 보수적 |
| PleOS APK 3종 | (개념적) | 실측: ① `ai.umos.vehiclecontrol` (system UID, 13 위험 권한) ② `ai.pleos.sync.syslog` (외부 송출, INTERNET) ③ `ai.pleos.llm.model.provider` (LLM 게이트웨이) |
| 1차 분석 결과 | (예상) | **12 findings (HIGH 5 / MEDIUM 6 / LOW 1)** — 카테고리: intent 8, network 3, permission 2, hardcoded 1, crypto 1 |

### 6주차 PPT — 2차 검증 + 난독화 전처리

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| 1차 → 2차 오탐률 | 25% → 12% | **잠정 측정 1차 40~50% (3 APK / 12 findings)** + caveat: 표본 작음, OWASP MASTG 확장 후 재측정 |
| 난독화 전처리 정확도 | 40% → 65% | **Phase 미진척 — Future Work에 별도 명시** |
| 2차 검증 방식 | regex + AST | regex (Phase B-2 일부 적용) + AST (javalang/tree-sitter, Phase B-2 후속 도입 예정) + caller graph 추적 |

### 7주차 PPT — 전수 분석 파일럿 + 정량 평가 프레임워크

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| 평가 프레임워크 | Precision/Recall/F1 측정 | **`src/eval.py` 작성 완료**. 실측: Precision = 0.60 (lenient) / 0.50 (strict), FP rate = 40% / 50%, Recall = 100% (GT 자체 라벨 superset이라 의미 약함) |
| Ground truth | OWASP MASVS-MASTG + 자체 | **자체 라벨 12건 완료** (`data/ground_truth/self_labels.json`). MASTG 미도입 — Phase B-4.c로 진행 예정 |
| 전수 분석 | 207 APK 분석 완료 | **207 APK 추출 (4.3 GB) 완료, stage 1은 3 APK 만 진행** + Future Work 명시 |
| 처리 시간 | 8~25분 / APK | **측정 시작** — VehicleControl: 디컴파일 ~2분 + grep ~10초 + LLM 분석 (인터랙티브, 클래스당 5~10분) |

### 8주차 PPT — 3차 교차 검증 (FP 12→7%) + 시각화

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| 3차 앙상블 | Claude + GPT-4 (멀티 LLM 앙상블) | **단일 LLM 다중 프롬프트 앙상블** — 동일 Claude Opus 4.7 + 공격자/방어자/도메인 전문가 시각 3종. 외부 환경 제약 명시 (외부 유료 API 미보유, Claude Code 단일 모델 세션 한계) |
| FP 12 → 7% | 가설 | **Phase 미진척 — 측정 후 갱신**. 합의 규칙은 `configs/prompts/stage3_consensus.md` 참조 |
| 시각화 | 차트/히트맵 | Phase 미진척 — Future Work |

### 9주차 PPT — 최종 성능 평가 + Ablation + 베이스라인 비교 (현재 주차)

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| Precision (Full Pipeline) | 0.93 | **0.60 (lenient) / 0.50 (strict)** + caveat: 표본 작음 |
| Ablation | 5종 변형 결과 | **Phase 미진척 — `src/ablation.py` 작성 예정 (Phase B-4.d)** |
| 베이스라인 비교 | jadx 수동 / 단일 LLM 1-pass / android-scanner-ai / Androidmeda | **Phase 미진척 — Phase B-4.c와 함께 진행** |

### 최종보고 PPT — 전체 그림

| 항목 | 기존 표기 (가설) | 수정 권장 |
|---|---|---|
| 멀티 LLM 앙상블 | Claude + GPT-4 | **단일 LLM 다중 프롬프트 앙상블** + 외부 환경 제약 + Future Work에 멀티 모델 도입 명시 |
| 정량 수치 종합 | 가설 (PPT 4~14주) | **모든 정량 수치를 "가설"과 "실측" 두 컬럼으로 분리해 정직하게 제시**. 일부는 표본 작음 caveat 필요 |
| 사례 연구 5건 | 가상 사례 | 실측 (현재까지 후보):  HIGH ① WebView setAllowFileAccess (잠정 FP — caller internal) ② AppPermissionManager grant/revoke (잠정 FP — Nav arg internal) ③ AuthData token leak (HIGH 잠재) ④ PromptsContentProvider exported (HIGH 확정 — LLM system prompt 노출) ⑤ LLMModelProviderReceiver no-permission (MEDIUM 확정 — 모델 파일 DoS) |

## 3. 핵심 수치 변경 매핑 (한 표로)

| PPT 가설 | 실측 (2026-04-29) | 표기 권장 |
|---|---|---|
| 1차 오탐률 25% | 40~50% (n=12) | "가설 25% / 1차 측정 40~50% (n=12, 추가 표본 확장 예정)" |
| 2차 오탐률 12% | 미측정 | "가설 12% / 측정 보류 (Stage 2 detail은 caller 추적 부분 적용)" |
| 3차 오탐률 7% | 미측정 | "가설 7% / Stage 3 멀티 프롬프트 앙상블 도입 후 측정 (Phase 진행 중)" |
| 난독화 정확도 40→65→78% | 미진척 | "Future Work — entropy 계산기 + 이름 복원 + 2차 디컴파일 루프 미도입" |
| 분석 대상 축소율 30~40% | **99.49% (단일 APK)** | "VehicleControl 1,765 java → 9 priority = 99.49%. 다른 APK 추가 측정 필요. 가설 30~40%은 더 보수적 priority 정의 가정" |
| Precision 0.93 | 0.60 / 0.50 | "가설 0.93 / 1차 측정 0.50~0.60 (n=12). 가설 도달은 Phase 추가 진행 후 재측정" |
| 처리 시간 8~25분 | 일부 측정 | "디컴파일 ~2분 + grep ~10초 + LLM 분석 ~5~10분/class. 인터랙티브 환경" |
| 비용 $0.40~1.20 | **N/A (정액제)** | "Claude Code 정액제로 외부 LLM 비용 가설 무관" |

## 4. 3차 검증 서술 변경 권장 문구

PPT 안의 "다중 LLM 앙상블" 부분을 다음 표현으로 대체:

> **단일 LLM 다중 프롬프트 앙상블**: 외부 유료 LLM API 미보유 및 Claude Code 단일 모델 세션 환경 제약으로 다중 모델 cross-read는 본 연구 범위에서 자동화 불가. 대안으로 동일 모델(Claude Opus 4.7 1M context)에 다른 시각의 프롬프트 3종 — **공격자**·**방어자**·**IVI 도메인 전문가** — 을 적용하고 시각 간 일치만 TP로 채택. 모델 다양성 측면에서 멀티 모델 대비 약하나 자동화·재현성·정직성 측면에서 본 환경에 가장 적합. 다중 모델 도입은 Future Work.

## 5. Future Work 슬라이드 권장 항목

본 학기 미진척으로 보고서 Future Work에 명시:

1. 멀티 모델 cross-read (Sonnet 4.6 / Haiku 4.5 / 외부 모델) — 인프라 확보 시
2. 난독화 전처리 (entropy 계산 + 이름 복원 + 2차 디컴파일 루프)
3. AST 기반 stage 2 검증 (`javalang` / `tree-sitter-java`) 본격 도입
4. OWASP MASTG 의도적 취약 APK 베이스라인 비교
5. android-scanner-ai / Androidmeda 정량 비교
6. 5종 ablation harness 자동 실행
7. AAOS 가이드라인 매핑 표 완성 (현재 v0 골격) + TARA 산출물 자동 생성
8. 시각화 — 차트/히트맵 (PPT 5~10주차에 가정)
9. 사례 연구 카드 5건 (PPT 10주차에 가정)

## 6. 새 슬라이드 후보 (실측 결과 추가용)

본 학기 첫 실측 결과로 새 슬라이드 만들 가치 있는 항목:

1. **카테고리별 정확도 격차** — `intent` + `hardcoded` 100% TP / `network` + `permission` 100% FP|uncertain. stage1 prompt의 카테고리별 약점 정량 식별 (PPT의 "단계별 검증 필요성" 논거)
2. **Precision-Recall caveat** — Recall 100%은 self-GT가 stage1 superset이라 의미 약함. MASTG 도입 후 본 측정.
3. **3 APK 비교 표** — VehicleControl(7) / sync.syslog(3) / llm.model.provider(2) findings 분포
4. **3차 검증 환경 제약 슬라이드** — 멀티 모델 → 멀티 프롬프트 전환 사유 + Future Work
5. **Phase 진행도 vs 계획** — PPT 4~5주차 Phase A·B-1·B-3 충족 / 6~14주차 일부 미진척 + 일정 재조정

## 7. 사용자 직접 작업 절차 권고

1. 가장 시급한 PPT (예: 9주차 본 학기 발표 자료 또는 최종보고)부터 v2 사본을 만든다 (`*_v2.pptx`).
2. 위 표 기준으로 수치 + 서술 수정.
3. 수정한 슬라이드 목록을 progress.md 변경 이력에 기록 (어느 슬라이드를 어떻게 바꿨는지).
4. 지도교수 1차 리뷰 시 **가설 vs 실측 분리 표기**의 정당성 + Future Work 명시 강조.
5. 본 가이드는 추가 측정 후 갱신.
