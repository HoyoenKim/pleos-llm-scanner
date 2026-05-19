# Project Inventory And Cleanup Plan

_작성일: 2026-05-19 / 기준: local filesystem + git history + `progress.md` + `next.md`_

## 1. 현재 결론

이 프로젝트는 두 층으로 나뉜다.

| Scope | 역할 | 정리 원칙 |
|---|---|---|
| 상위 디렉토리 `자율주행연구프로젝트1/` | 수업 제출물, 진행 기록, 발표 deck, 일부 runtime harness 산출물 | 제출/발표 관리 공간으로 유지. PPT/PDF는 직접 overwrite하지 않고 버전 폴더에 보관 |
| 하위 repo `pleos-llm-scanner/` | 실제 구현, 측정 코드, 공개 가능한 문서/집계 산출물 | Git 관리 단위. source/config/docs/sanitized aggregate만 commit하고 raw APK/evidence/video는 local-only |

현재 연구 본선은 `docs/01_report.md` v1.4 supplement 기준으로 완료되어 있다. 2026-05-14까지의 정적 분석/RQ 측정 결과가 canonical이고, 2026-05-15~18의 runtime PoC/Binder evidence는 별도 runtime validation/FN expansion track으로 분리한다.

## 2. Source Of Truth

| File | 역할 |
|---|---|
| 상위 `progress.md` | 전체 과제 진행의 단일 진실 출처. 날짜별 durable status와 최신 PoC 진행 기록 포함 |
| 상위 `next.md` | 다음 행동 항목. 연구/RQ 작업과 발표 산출물 작업을 구분 |
| `docs/01_report.md` | v1.4 supplement 통합 보고서. `n=47` 정적 평가와 Future Work A~E 완료 결과의 근거 저장소 |
| `docs/08_project_final_brief.md` | 처음 보는 평가자용 압축 최종본. 2026-05-18 기준 RQ5 runtime PoC 요약 포함 |
| `docs/09_stage2_methodology.md` | Stage 2 contextual verification 방법론 설명 |
| `data/reports/poc_evidence_index.md` | local-only runtime PoC evidence level index. 공개 전 redaction review 필요 |

## 3. 진행 이력 요약

| 날짜 | 큰 변화 |
|---|---|
| 2026-04-29 | repo scaffold, `configs/`, `scripts/pull_apks.sh`, `scripts/decompile.sh`, `src/eval.py`, `src/ablation.py`, self GT 시작 |
| 2026-04-30 | Stage 2 deep-link verification, MASTG baseline, deobf entropy, chart, AAOS/TARA, report v0.9 |
| 2026-05-06 | docs 구조 정리, public masked reports, RQ 측정 scripts, n=28/InsecureBankv2/NewPipe, 10~14주차 PPT script 정리 |
| 2026-05-08 | report self-contained 보강, PPT build scripts untrack |
| 2026-05-14 | Future Work A~E 완료, combined GT `n=47`, RAG/native/dynamic/Codex multi-model, docs v1.4 supplement sync |
| 2026-05-15 | runtime PoC evidence 강화, PoC video pack, final/improved PoC demo videos |
| 2026-05-18 | Binder FN expansion, `navi-1` L3 route UI injection, `vs-1` V3 reversible property mutation, final PPT v5 |

## 4. Directory Inventory

### 상위 디렉토리

| Path | 상태 | 정리 판단 |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md` | 세션/작업 정책 | 유지. 인코딩 문제 없이 UTF-8로 열어야 함 |
| `progress.md`, `next.md` | canonical 진행 기록 | 유지. 새 작업 후 이 둘을 먼저 갱신 |
| `pptx/` | 주차별 PPT + final v3/v4/v5 | local-only 제출 산출물. 버전 유지, overwrite 금지 |
| `data/apks/_external/` | NewPipe/InsecureBankv2 APK | local-only input corpus |
| `data/runtime_poc_harness/` | 2026-05-18 PoC harness build output | repo 내부 ignored harness와 중복 가능. 정리 시 source만 남기고 build artifacts는 archive/local-only |
| `scripts/` | 상위 PPT/helper script | PPT 산출물용 local helper. repo source와 분리 유지 |
| `tmp_pentest_report.docx` | 외부/임시 문서로 보임 | 프로젝트 정리 전 provenance 확인 필요. 자동 이동/삭제 금지 |

### `pleos-llm-scanner/`

| Path | 상태 | 정리 판단 |
|---|---|---|
| `configs/` | tracked config/prompt | commit 대상. `rag_end_to_end_judge.md`는 RAG 후속 scaffold로 review 후 commit 가능 |
| `src/` | tracked deterministic pipeline | commit 대상. `src/dynamic/hooks/*.js` 신규 hook은 raw secret 없이 review 후 commit 가능 |
| `scripts/` | mixed: reproducible research scripts + presentation helpers | research scripts는 commit 후보. recording/update PPT scripts는 local-only 또는 `scripts/presentation/` 분리 후보 |
| `docs/` | reader-facing docs | commit 대상. 07~10을 인덱스에 포함 |
| `data/ground_truth/` | tracked labels | commit 대상. 정적 평가의 핵심 재현 입력 |
| `data/reports/` | partial tracked | aggregate/sanitized reports만 commit. per-APK/raw runtime evidence는 local-only |
| `data/deobf/` | tracked JSON + ignored md | `DIVA.json`은 public external benchmark entropy라 review 후 commit 가능 |
| `data/viz/` | tracked charts | commit 대상. n=47 재생성본 유지 |
| `data/apks/`, `data/decompiled/` | ignored, very large | local-only. 공개/commit 금지 |
| `data/native*`, `data/rag`, `tools/` | ignored generated/binary | local-only. summary만 docs/reports에 기록 |
| `data/poc_evidence/`, `data/runtime_poc_*` | runtime raw evidence/videos | local-only. redacted summary만 commit 후보 |

## 5. Current Git State Classification

2026-05-19 기준 `pleos-llm-scanner/`는 status/docs/policy 파일 변경분과 신규 docs/scripts/hooks가 남아 있다. 삭제 없이 다음처럼 처리한다.

### Commit 후보

| Group | Examples | 이유 |
|---|---|---|
| docs/status sync | `docs/07_research_extension_plan.md`, `docs/08_project_final_brief.md`, `docs/09_stage2_methodology.md`, `docs/10_project_inventory_20260519.md` | reader-facing 또는 방법론/정리 문서 |
| policy docs | `.gitignore`, `docs/README.md`, `data/README.md` | local-only 경계 명시 |
| sanitized prompt/config | `configs/prompts/rag_end_to_end_judge.md` | 후속 RAG end-to-end scaffold |
| deterministic research scripts | `research_*`, `run_*` 중 raw secret/path 미포함 확인된 파일 | 재현성에 기여 |
| safe aggregate reports | `poc_evidence_index.md`, `binder_fn_expansion_20260518.md`, `navi1_runtime_binder_probe_20260518.md` 등 | raw evidence가 아니라 claim boundary와 evidence level을 정리한 문서. 공개 전 redaction review 필요 |

### Local-only 유지

| Group | Examples | 이유 |
|---|---|---|
| APK/decompiled source | `data/apks/`, `data/decompiled/` | contractor/IP 보호 |
| raw PoC evidence | `data/poc_evidence/`, `data/reports/_raw/` | screenshots/logcat/window dump 포함 |
| videos/previews | `data/runtime_poc_*`, `data/reports/prompt_leak_attack_poc/*.mp4`, preview PNGs | 발표 산출물 또는 민감 context 가능 |
| generated tools/db | `tools/`, `data/rag/`, `data/native_deep_dive/` | binary/generated |
| build output | `data/runtime_poc_harness/classes*`, `*.apk`, `*.dex`, `debug.keystore` | 재생성 가능 산출물 |

### Archive/delete 후보

즉시 삭제하지 않는다. 발표 종료 후 다음만 후보로 둔다.

| Candidate | 처리 |
|---|---|
| 중복 `live_replay_*` run | canonical run 1개와 README만 남기고 나머지는 zip/archive |
| failed/partial run screenshots | evidence index에서 참조하지 않으면 archive |
| `__pycache__/` | 안전 삭제 가능 |
| preview PNG flood | 최종 영상/대표 screenshot 외 archive |
| 상위 `data/runtime_poc_harness` build artifacts | source와 manifest만 남기고 build output archive |

## 6. Cleanup Execution Order

1. **문서 기준선 고정**: `docs/README.md`, `data/README.md`, 이 inventory를 commit 후보로 정리.
2. **ignore 정책 보강**: 새 raw evidence directories를 `.gitignore`에 명시.
3. **public/sanitized 후보 선별**: direct `data/reports/*.md/json` 중 발표/보고서가 참조하는 summary만 review 후 exception 추가 또는 docs로 이동.
4. **PoC evidence index 중심화**: raw evidence는 `data/poc_evidence/`에 두고, PPT/보고서가 인용하는 경로는 `poc_evidence_index.md` 하나에서 관리.
5. **상위/하위 harness 중복 정리**: build output은 local-only, 재생성 script는 repo `scripts/`로 통합.
6. **PPT final pack 구성**: `pptx/v5/` + final demo video + evidence index만 발표용 bundle로 묶고 raw run 전체는 별도 보관.

## 7. Commit 권장 순서

| Commit | 내용 |
|---|---|
| `docs: add project inventory and refresh docs index` | docs 07~10, README/index/status text |
| `chore: mark runtime poc evidence as local-only` | `.gitignore`, `data/README.md` local-only 정책 |
| `research: add runtime poc summary and harness scripts` | redaction review가 끝난 summary reports + deterministic scripts |

## 8. 남은 확인

- `data/reports/poc_evidence_index.md`와 runtime summary reports에 secret/prompt 원문이 없는지 `rg`로 재검사.
- `scripts/research_runtime_poc_harness.py`에 local absolute path, private filename, credential literal이 없는지 확인.
- `pptx/v5`가 final deck인지, `v4`와 비교해 어떤 slide가 달라졌는지 별도 기록.
- `progress.md`와 `next.md`는 v5 기준으로 갱신 완료. 이후에는 발표 전 QA 결과와 제출본 선택만 반영.
