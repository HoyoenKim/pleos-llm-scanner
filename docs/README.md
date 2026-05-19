# docs/ — 문서 인덱스

본 디렉토리는 reader-facing / methodology 문서 10 개와 local-only 작성 보조 문서 1 개로 구성된다. **[01_report.md](01_report.md)** 가 근거 저장소이고, **[08_project_final_brief.md](08_project_final_brief.md)** 가 처음 보는 평가자용 압축 최종본이다. 정리 기준선은 **[10_project_inventory_20260519.md](10_project_inventory_20260519.md)** 를 따른다.

| 순서 | 파일 | 무엇 |
|---|---|---|
| 1 | [01_report.md](01_report.md) | **★ 통합 보고서 v1.4 supplement** — 본 학기 연구 (Phase A~E) + 학기 외 Future Work A~E + Codex 3-model cross-read 보충 결과 통합. Notation & Glossary + 8장 + Appendix. 외부 reader 가 처음 읽는 곳. |
| 2 | [02_case_studies.md](02_case_studies.md) | 사례 연구 10건 — 정적 5건 (하드코딩 자격증명 / 권한 우회 FP 4중 차단 / 평문 통신 / exported ContentProvider / 차량 제어 spoofing) + 학기 외 D Dynamic 5건 (Case 6~10). 각 카드에 코드 evidence + 재현 path. |
| 3 | [03_charts.md](03_charts.md) | 6개 차트 (`data/viz/01~06_*.png`) 의 해석 + 재현 명령. 차트는 n=18/n=19 시점 스냅샷 — 현재 corpus n=47 은 01_report.md § 3.2 참조. |
| 4 | [04_limitations_and_costs.md](04_limitations_and_costs.md) | 본 파이프라인의 6 한계 카테고리 (L1~L6) + 운영 비용 평가 (시간 / 금전 / 메모리 / 확장성) + 트레이드오프 종합. |
| 5 | [05_future_work.md](05_future_work.md) | 학기 외부 후속 작업 17 종 (4 카테고리). 학기 외 A~E 진행 현황은 06 이 canonical. |
| 6 | [06_future_work_implementations.md](06_future_work_implementations.md) | Future Work 도달도 매트릭스 + 설계 명세 + **학기 외 A~E 작업 (2026-05-14) 완료 결과** (R1.d.5 n=47 / RAG / native / Dynamic / Multi-model Codex cross-read). |
| 7 | [07_research_extension_plan.md](07_research_extension_plan.md) | v1.4 supplement 이후 연구 확장 계획. RAG end-to-end ablation / Dynamic runtime / Native deep dive / public redaction / n≥60 / true multi-vendor 비교의 우선순위와 done criteria. |
| 8 | [08_project_final_brief.md](08_project_final_brief.md) | **처음 보는 평가자용 최종 요약 보고서** — 프로젝트 배경, Stage 0~3 파이프라인, combined n=47 결과, 대표 사례, 확장 실험, 한계와 결론만 압축 정리. 2026-05-18 runtime PoC/RQ5 보강은 별도 track으로 표시. |
| 9 | [09_stage2_methodology.md](09_stage2_methodology.md) | Stage 2 contextual verification 방법론 — caller chain, manifest, permission, route, data-origin, sink-specific rule check를 어떻게 TP/FP/uncertain으로 정리했는지 설명. |
| 10 | [10_project_inventory_20260519.md](10_project_inventory_20260519.md) | 프로젝트 파일 inventory + git/history 요약 + commit/local-only/archive 분류 + 정리 실행 순서. |

## local-only 작성 보조

- `ppt_revision_guide.md` — 발표/PPT 작성자용 내부 가이드. `.gitignore`로 비공개 유지.

## 흡수된 doc

- 통합 아키텍처 권고 → `01_report.md` § 5
- 일반화 평가 (QNX / AGL) → `01_report.md` § 6

## archive (local-only)

각 측정 시점의 raw 노트 5종 (caller-chain verification, ablation results, 외부 corpus 도입, baseline 비교, 난독화 전처리). GitHub 에는 push 되지 않으며 작성자 로컬에만 보관 — 시점 스냅샷이라 갱신하지 않고 파일명에 작성일 유지. 본 보고서가 인용하는 1차 출처. 필요 시 작성자에게 문의.

## 파일명 컨벤션

- 메인 docs: `<번호>_<topic>.md` 로 reading order 명시. 갱신은 본문 끝 변경 이력 섹션에 누적.
- archive 측정 노트 (시점 스냅샷): `<topic>_<YYYYMMDD>.md` — 작성일 유지.

## 관련 산출물 (docs/ 밖)

- 측정 데이터: `../data/ground_truth/` (combined_labels.json n=47), `../data/reports/`, `../data/deobf/`, `../data/viz/`
- 결정론 스크립트: `../src/eval.py`, `../src/ablation.py`, `../src/aaos_map.py`, `../src/tara_generate.py`, `../src/deobf/entropy.py`, `../src/viz/plot_metrics.py`
- 학기 외 산출 스크립트: `../src/native_analyze.py` (C) · `../src/rag/{build_index,retrieve,ablation}.py` (B) · `../src/dynamic/state_machine.py` + `../src/dynamic/hooks/` Frida script (D)
- 연구 측정 스크립트: `../scripts/research_r{1a,2a,3a}_*.py`, `../scripts/research_r2c_codex_multimodel.py` (E)
- 프롬프트: `../configs/prompts/{stage0_deobfuscate,stage1_detect,stage3_attacker,stage3_defender,stage3_domain_expert,stage3_consensus}.md` + `stage1_detect_rag.md` (B) + `codex_multimodel_cross_read.md` (E)
- 매핑 데이터: `../configs/keywords.yaml`, `../configs/aaos_mapping.yaml`
- local-only runtime evidence: `../data/poc_evidence/`, `../data/runtime_poc_*`, `../data/reports/_raw/`, `../data/reports/prompt_leak_attack_poc/`

## Parent workspace inventory

- [11_parent_workspace_inventory_20260519.md](11_parent_workspace_inventory_20260519.md) documents the non-git parent workspace, local-only PPT/APK/runtime artifacts, and the push boundary for `pleos-llm-scanner/`.
