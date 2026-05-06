# configs/prompts/ — LLM 프롬프트 인덱스

본 파이프라인의 LLM 호출 단계별 프롬프트. 모두 **Claude Code 세션에서 직접 적용**되며 별도 SDK 호출 코드는 없다 (CLAUDE.md 정책).

## 호출 순서

```
(필요 시) Stage B → Stage 1 → Stage 2 → Stage 3 (× 3 시각) → 합의 규칙
```

## 단계별 파일

| 단계 | 파일 | 입력 | 출력 | 비고 |
|---|---|---|---|---|
| Stage B (선택) | [stage_b_deobfuscate.md](stage_b_deobfuscate.md) | 고난독화 클래스 (composite obf score ≥ 0.7, `src/deobf/entropy.py` 산출) | semantic class/method name + 1-line role + confidence | jadx 재디컴파일 또는 sed/AST rewrite의 입력. PleOS corpus는 HIGH 0.2~0.4%로 적용 빈도 낮음 |
| Stage 1 | [stage1_detect.md](stage1_detect.md) | 디컴파일된 Java 클래스 1개 | 6 카테고리 (crypto / network / permission / intent / hardcoded / reflection_dynamic) 후보 finding JSON | 키워드 grep 후 priority class에만 적용 |
| Stage 2 | (룰 + 코드 분석, 별도 프롬프트 없음) | Stage 1 후보 + manifest + Hilt graph + caller chain | verdict 갱신 (TP / FP / uncertain) | regex / AST + LLM 재독을 Claude Code 세션에서 인터랙티브 |
| Stage 3 (1/3) | [stage3_attacker.md](stage3_attacker.md) | Stage 1·2 결과 + 디컴파일 코드 | 공격자 시각 verdict (exploit chain 가능성) | D3=(B) 멀티 프롬프트 앙상블 |
| Stage 3 (2/3) | [stage3_defender.md](stage3_defender.md) | 동일 입력 | 방어자 시각 verdict (방어 layer 분석) | |
| Stage 3 (3/3) | [stage3_domain_expert.md](stage3_domain_expert.md) | 동일 입력 | IVI/차량 보안 도메인 전문가 시각 verdict | AAOS / 차량 IPC / OEM 정책 맥락 강조 |
| Stage 3 — 합의 | [stage3_ensemble_rule.md](stage3_ensemble_rule.md) | 위 3종 verdict | 합의 임계 (≥1/3 / ≥2/3 / ≥3/3) 별 final verdict | default = ≥2/3 (ablation 결과 F1 최적) |

## 결정 사항 매핑

- **D3 = (B) 멀티 프롬프트** (외부 환경 제약: 단일 모델 세션, 외부 유료 API 미보유) — 동일 Claude Opus 4.7에 시각 3종 적용
- 합의 임계 default = **≥2/3** — Variant B ablation에서 F1 최적 (combined n=19에서 F1 0.966)

## 산출 스키마

각 프롬프트의 출력 JSON은 `../result_schema.json` 단일 출처를 따른다. Stage 3 합의 결과는 `data/reports/stage3_ensemble_<DATE>.json`.

## 컨벤션

- **stage1**: 1차 탐지 (한국어)
- **stage_b**: deobfuscation pre-processing (영어 — 외부 corpus 시범 적용 시 영문 hint 다수)
- **stage3_***: 3종 시각 + 합의 규칙 (한국어)
- 새 시각 추가 시 `stage3_<perspective>.md` 파일 + `stage3_ensemble_rule.md` 의 임계 표 갱신
