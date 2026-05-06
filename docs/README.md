# docs/ — 문서 인덱스

모든 측정·분석·통합 문서가 여기 모인다. 처음 보는 사람이라면 **report_v0.9** 부터 읽으면 전체 그림을 가장 빨리 잡을 수 있다.

## 진입점

| 우선 | 파일 | 무엇 |
|---|---|---|
| ★ | [report_v0.9_20260430.md](report_v0.9_20260430.md) | **Phase A–D 통합 중간 보고서**. 지도교수 1차 리뷰 대상. 8장 + Appendix A/B/C. 아래 측정 문서들을 모두 인용. |
| ☆ | [viz_20260430.md](viz_20260430.md) | `data/viz/01~06_*.png` 6 차트의 해석 + 재현 명령. 차트만 빨리 보고 싶을 때. |
| ☆ | [ppt_revision_guide_20260429.md](ppt_revision_guide_20260429.md) | 학기 PPT 슬라이드를 가설 수치 → 실측/Future Work 표기로 옮기는 변경점 가이드. |

## 측정 기록 (Phase별, 시간순)

각 파일은 한 단계의 실험 + 측정값 + 산출물 인덱스 + 재현 명령을 담는다. 보고서 본문이 인용하는 1차 출처.

| 단계 | 파일 | 무엇 |
|---|---|---|
| Phase B-3 / 2.b | [stage2b_deeplink_verification_20260430.md](stage2b_deeplink_verification_20260430.md) | VehicleControl FP 4건(vc-1/2/3/4)을 **4중 차단 동선**(manifest URI 부재 + Compose Nav internal-only + LinkProvider single-segment + NestedNavRouter APPLICATIONS 미binding)으로 FP CONFIRMED. multi-stage 검증의 효과 입증 사례. |
| Phase B-4 | [ablation_results_20260429.md](ablation_results_20260429.md) | A 변형(Stage 1/2/3 ablation) + B 변형(D3=B 합의 임계 ≥1/2/3) F1 측정. ≥2/3가 default 적합 결론. |
| Phase B-4.c | [phase_b4c_mastg_baseline_20260430.md](phase_b4c_mastg_baseline_20260430.md) | **OWASP MASTG 외부 GT corpus** 3 sample 도입(UnCrackable-Level1/2 + r2pay). Combined n=18 stage1 P 77.8% / R 100% / F1 0.875. UnCrackable-Level2/r2pay는 native 의존 → **Java-only pipeline boundary** 정량. |
| Phase B-4.c.2 | [phase_b4c2_baselines_20260430.md](phase_b4c2_baselines_20260430.md) | **4종 베이스라인 비교** — ① jadx 수동(self GT 자체) / ② 단일 LLM 1-pass(stage1 자체) / ③ android-scanner-ai / ④ Androidmeda. ③/④는 README에 자체 P/R/F1 측정 부재 = 본 연구의 차별 gap. |
| Phase C | [phase_c_deobf_baseline_20260430.md](phase_c_deobf_baseline_20260430.md) | 난독화 전처리 — `src/deobf/entropy.py` + `stage_b_deobfuscate` 프롬프트. UnCrackable Level1/2 sg.vantagepoint n=17 exact 100% (PPT 가설 78% 도달). **PleOS HIGH 난독화 0.2~0.4%** corpus-level finding. |

## Phase D 통합 산출물

PPT 10/12주차 deliverable. 측정 기록을 묶어 보고서·발표용으로 정제한 결과.

| 파일 | 무엇 |
|---|---|
| [case_studies_20260430.md](case_studies_20260430.md) | **사례 연구 5건 케이스 카드** — Case 1 하드코딩 자격증명(ssl-5+ucl1-1) / Case 2 권한 우회 FP 4중 차단(vc-3/4) / Case 3 평문 통신(ssl-6) / Case 4 Exported ContentProvider(lmp-1) / Case 5 차량 제어 spoofing(vc-6). |
| [integration_architecture_20260430.md](integration_architecture_20260430.md) | **PleOS 통합 아키텍처 권고** — DEV → CI/CD(pleos-llm-scanner) → PR Gate → TARA Workflow → OTA Gating → Production 흐름. Mermaid + 텍스트. MVP 범위(Static-only)와 운영 전환 차이 표. |
| [generalization_assessment_20260430.md](generalization_assessment_20260430.md) | **QNX / AGL 일반화 평가** — 6 카테고리 중 4 OS-독립(crypto/network/hardcoded/reflection_dynamic), 2 swap(permission/intent). QNX 2-3주, AGL 2-3주 swap 추정. 60-70% OS-독립. |

## 메타·계획

| 파일 | 무엇 |
|---|---|
| [week11_limitations_costs_20260430.md](week11_limitations_costs_20260430.md) | **한계 + 운영 비용** (PPT 11주차 deliverable). L1 native 분석 불가 / L2 표본 작음 / L3 multi-LLM ensemble 미구현 / L4 hand-crafted MASTG / L5 stage3 MASTG 미평가. APK 1개당 시간/메모리/비용 추정 + 트레이드오프. |
| [ppt_revision_guide_20260429.md](ppt_revision_guide_20260429.md) | 9개 PPT 슬라이드(5/6/7/8/9/10/11/13/14주차)에서 가설 수치를 실측/미진척/Future Work 표기로 바꾸는 변경 가이드. v2 작성 시 참조. |
| [viz_20260430.md](viz_20260430.md) | 6 차트(`data/viz/01~06`) 인덱스 + 차트별 해석 + 재현 명령. 차트 04는 2026-05-06 corpus-level view로 재구성됨. |

## 파일명 컨벤션

- `<phase>_<topic>_<YYYYMMDD>.md` — Phase별 측정 기록 (예: `phase_b4c_mastg_baseline_20260430.md`)
- `<topic>_<YYYYMMDD>.md` — 그 외 통합 산출물 (예: `case_studies_20260430.md`)
- 날짜는 **작성일**. 측정값 갱신 시 본문 끝 "변경 이력" 섹션에 추가 (파일명은 그대로).

## 관련 산출물 (이 디렉토리 밖)

- 측정 데이터: `../data/ground_truth/`, `../data/reports/`, `../data/deobf/`, `../data/viz/`
- 결정론 스크립트: `../src/eval.py`, `../src/ablation.py`, `../src/aaos_map.py`, `../src/tara_generate.py`, `../src/deobf/entropy.py`, `../src/viz/plot_metrics.py`
- 프롬프트: `../configs/prompts/{stage1_detect,stage_b_deobfuscate,stage3_attacker,stage3_defender,stage3_domain_expert,stage3_ensemble_rule}.md`
- 매핑 데이터: `../configs/keywords.yaml`, `../configs/aaos_mapping.yaml`
