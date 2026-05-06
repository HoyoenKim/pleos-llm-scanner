# docs/ — 문서 인덱스

처음 보는 사람이라면 **report_v0.9** 부터 읽으면 전체 그림을 가장 빨리 잡을 수 있다.

## 진입점

| 우선 | 파일 | 무엇 |
|---|---|---|
| ★ | [report_v0.9.md](report_v0.9.md) | **Phase A–D 통합 중간 보고서**. 8장 + Appendix A/B/C. 아래 측정 문서들을 모두 인용. |
| ☆ | [viz.md](viz.md) | `data/viz/01~06_*.png` 6 차트의 해석 + 재현 명령. 차트만 빨리 보고 싶을 때. |

## Phase D 통합 산출물

PPT 10/12주차 deliverable. 측정 기록(archive/)을 묶어 보고서·발표용으로 정제한 결과.

| 파일 | 무엇 |
|---|---|
| [case_studies.md](case_studies.md) | **사례 연구 5건 케이스 카드** — Case 1 하드코딩 자격증명 / Case 2 권한 우회 FP 4중 차단 / Case 3 평문 통신 / Case 4 Exported ContentProvider / Case 5 차량 제어 spoofing. |
| [integration_architecture.md](integration_architecture.md) | **PleOS 통합 아키텍처 권고** — DEV → CI/CD → PR Gate → TARA Workflow → OTA Gating → Production. Mermaid + 텍스트. MVP 범위(Static-only)와 운영 전환 차이. |
| [generalization_assessment.md](generalization_assessment.md) | **QNX / AGL 일반화 평가** — 6 카테고리 중 4 OS-독립, 2 swap. QNX 2-3주, AGL 2-3주 swap 추정. 60-70% OS-독립. |

## 메타·계획

| 파일 | 무엇 |
|---|---|
| [week11_limitations_costs.md](week11_limitations_costs.md) | **한계 + 운영 비용**. L1 native 분석 불가 / L2 표본 작음 / L3 multi-LLM ensemble 미구현 / L4 hand-crafted MASTG / L5 stage3 MASTG 미평가(해소). APK 1개당 시간/메모리/비용 추정 + 트레이드오프. |

## Raw 측정 노트 (`archive/`, local-only)

각 측정 시점의 raw 노트 5종 (caller-chain verification, ablation results, 외부 corpus 도입, baseline 비교, 난독화 전처리). **GitHub 에는 push 되지 않으며 작성자 로컬에만 보관** 한다 — 시점 스냅샷이라 갱신하지 않고 파일명에 작성일을 유지. 본 보고서 본문이 인용하는 1차 출처. 필요 시 작성자에게 문의.

## 파일명 컨벤션

- 메인 docs (계속 인용·참조): **날짜 없음** — 갱신은 본문 끝 "변경 이력" 섹션에 누적
- archive 측정 노트 (시점 스냅샷): **`<topic>_<YYYYMMDD>.md`** — 작성일 유지

## 관련 산출물 (docs 밖)

- 측정 데이터: `../data/ground_truth/`, `../data/reports/`(gitignored, meta-analysis 표는 예외), `../data/deobf/`, `../data/viz/`
- 결정론 스크립트: `../src/eval.py`, `../src/ablation.py`, `../src/aaos_map.py`, `../src/tara_generate.py`, `../src/deobf/entropy.py`, `../src/viz/plot_metrics.py`
- 프롬프트: `../configs/prompts/{stage1_detect,stage0_deobfuscate,stage3_attacker,stage3_defender,stage3_domain_expert,stage3_consensus}.md`
- 매핑 데이터: `../configs/keywords.yaml`, `../configs/aaos_mapping.yaml`
