# Stage 3 — 멀티 프롬프트 앙상블 합의 규칙

D3=(B) 결정에 따라 동일 모델(Claude Opus 4.7)에 다른 시각 3종 프롬프트(`stage3_attacker.md`, `stage3_defender.md`, `stage3_domain_expert.md`)를 적용한 후 결과를 합산하는 규칙.

## 합의 규칙 (TP 판정)

같은 `(class, line)` 위치에 대해 3종 perspective 결과를 비교:

| 합의 수 | 분류 | 처리 |
|---|---|---|
| 3/3 | **strong TP** | severity = max(3개 severity), confidence ≥ 0.9 로 보고. 사례 카드 1순위 후보 |
| 2/3 | **TP** | severity = 다수결 (동일 시 max). confidence = 평균 |
| 1/3 | **uncertain → stage 2 재검증 필요** | 단독 perspective 결과는 별도 파일에 보존하되 stage 2 caller 분석 또는 manual review 후 결정 |
| 0/3 | clean | 보고 없음 |

## 합산 결과 JSON 스키마

```json
{
  "class": "...",
  "stage": "stage3",
  "ensemble_strategy": "multi-prompt-D3-B",
  "perspectives_run": ["attacker", "defender", "domain_expert"],
  "findings": [
    {
      "line": <int>,
      "category": "...",
      "consensus_count": <0~3>,
      "consensus_perspectives": ["attacker", "defender"],
      "severity": "...",
      "title": "...",
      "evidence": "...",
      "rationale_merged": "<3종의 rationale을 합쳐 한 단락>",
      "per_perspective": {
        "attacker": { "severity": "...", "rationale": "...", "attack_chain": [...] },
        "defender": { "severity": "...", "rationale": "...", "missing_control": "..." },
        "domain_expert": { "severity": "...", "vehicle_asset": "...", "stride": "...", "tara_impact": "..." }
      },
      "confidence": <0.0~1.0>
    }
  ]
}
```

## 운영 절차

1. **stage 1**: `stage1_detect.md`로 priority 클래스 stage 1 분석 (이미 완료된 단계).
2. **stage 2**: caller 추적, regex/AST 검증 (이미 도입된 단계).
3. **stage 3 진입 조건**: stage 2에서 confidence 0.55~0.75인 잠정 TP 후보를 stage 3 입력으로.
4. **stage 3 실행**: 같은 클래스에 3 prompt 각각 적용 → 3개 perspective 결과 → 위 합의 규칙 적용.
5. **stage 3 출력 위치**: `data/reports/<apk>_<YYYYMMDD>_stage3.json`. stage 1/2 결과와 분리 저장.

## D3=(A) 멀티 Claude 모델 대비

| 항목 | (A) 멀티 Claude 모델 | (B) 멀티 프롬프트 (현재 채택) |
|---|---|---|
| 모델 다양성 | Opus / Sonnet / Haiku | 모두 Opus 4.7 |
| 자동화 | 단일 Claude Code 세션 안에서 불가 (manual) | **자동화 가능** |
| 시각 다양성 | 모델 학습 데이터 차이로 결과 다양 가능 | 프롬프트로 명시적 시각 부여 |
| PPT 서술 정합 | "다중 LLM 앙상블" 직접 매칭 | "단일 LLM 다중 프롬프트 앙상블 (외부 환경 제약)"로 narrative 변경 필요 |
| 보고서 정직성 | manual workflow 명시 필요 | 자체 환경 한계 + 대체 전략 명시 가능 |

## Future Work

- (A) 추가 도입은 외부 SDK / API 인프라 확보 시 가능. 현재 보고서엔 Future Work 섹션에 명시.
- 별도 모델 군 (GPT-4, Gemini 등) 도입 시 같은 합의 규칙 재사용 가능.
