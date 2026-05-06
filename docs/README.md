# docs/ — 문서 인덱스

본 디렉토리는 4 개 문서로 단순화. **[01_report.md](01_report.md)** 가 진입점이고, 나머지 3 개는 보고서가 인용하는 보충 자료.

| 순서 | 파일 | 무엇 |
|---|---|---|
| 1 | [01_report.md](01_report.md) | **★ 통합 중간 보고서 v0.9-r1** — 본 학기 연구 전체. Notation & Glossary + 8장 + Appendix. 외부 reader 가 처음 읽는 곳. |
| 2 | [02_case_studies.md](02_case_studies.md) | 사례 연구 5건 — 하드코딩 자격증명 / 권한 우회 FP 4중 차단 / 평문 통신 / exported ContentProvider / 차량 제어 spoofing. 각 카드에 코드 evidence + 재현 path. |
| 3 | [03_charts.md](03_charts.md) | 6개 차트 (`data/viz/01~06_*.png`) 의 해석 + 재현 명령. 차트만 빨리 보고 싶을 때. |
| 4 | [04_limitations_and_costs.md](04_limitations_and_costs.md) | 본 파이프라인의 5 한계 카테고리 (L1~L5) + 운영 비용 평가 (시간 / 금전 / 메모리 / 확장성) + 트레이드오프 종합. |

## 흡수된 doc

- 통합 아키텍처 권고 → `01_report.md` § 5
- 일반화 평가 (QNX / AGL) → `01_report.md` § 6

## archive (local-only)

각 측정 시점의 raw 노트 5종 (caller-chain verification, ablation results, 외부 corpus 도입, baseline 비교, 난독화 전처리). GitHub 에는 push 되지 않으며 작성자 로컬에만 보관 — 시점 스냅샷이라 갱신하지 않고 파일명에 작성일 유지. 본 보고서가 인용하는 1차 출처. 필요 시 작성자에게 문의.

## 파일명 컨벤션

- 메인 docs: `<번호>_<topic>.md` 로 reading order 명시. 갱신은 본문 끝 변경 이력 섹션에 누적.
- archive 측정 노트 (시점 스냅샷): `<topic>_<YYYYMMDD>.md` — 작성일 유지.

## 관련 산출물 (docs/ 밖)

- 측정 데이터: `../data/ground_truth/`, `../data/reports/`, `../data/deobf/`, `../data/viz/`
- 결정론 스크립트: `../src/eval.py`, `../src/ablation.py`, `../src/aaos_map.py`, `../src/tara_generate.py`, `../src/deobf/entropy.py`, `../src/viz/plot_metrics.py`
- 연구 측정 스크립트: `../scripts/research_r{1a,2a,3a}_*.py`
- 프롬프트: `../configs/prompts/{stage0_deobfuscate,stage1_detect,stage3_attacker,stage3_defender,stage3_domain_expert,stage3_consensus}.md`
- 매핑 데이터: `../configs/keywords.yaml`, `../configs/aaos_mapping.yaml`
