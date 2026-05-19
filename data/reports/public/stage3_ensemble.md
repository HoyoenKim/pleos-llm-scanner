> **Public masked copy** — only PleOS-prefixed findings (vc-/ssl-/lmp-) had their evidence redacted. MASTG findings (ucl1-/ucl3-) are public corpus and kept verbatim. Per-perspective rationales / attack chains / missing controls / vehicle assets are kept.
>
> 본 파일은 PleOS 코드 인용만 redact 한 공개용 사본. MASTG 외부 corpus는 그대로 유지.
>
> **Sync note (2026-05-14)**: this public copy intentionally remains the initial redacted n=12 snapshot. The current full Stage 3 result is n=47 with `>=2/3` Precision 100.0%, Recall 97.4%, F1 98.7%, McNemar p_exact=0.0215. Full n=47 details remain in the local-only `data/reports/local/stage3_ensemble.md/json` until R1.d.2~d.5 public redaction review is done.

# Stage 3 — Multi-prompt ensemble first application (2026-04-29)

- **모델**: Claude Opus 4.7 (1M context) — 단일 모델, 다중 시각
- **시각 3종**: attacker (`stage3_attacker.md`) / defender (`stage3_defender.md`) / domain_expert (`stage3_domain_expert.md`)
- **합의 규칙**: `stage3_consensus.md` — 3/3 strong TP, 2/3 TP, 1/3 uncertain, 0/3 clean
- **입력**: 12 stage1 findings (3 APK)
- **결과 JSON**: [`stage3_ensemble.json`](stage3_ensemble.json)

## 합의 분포

| 합의 | 수 | 분류 |
|---|---|---|
| 3/3 | 4 | strong TP |
| 2/3 | 2 | TP |
| 1/3 | 6 | uncertain |
| 0/3 | 0 | clean |

### Strong TP (3/3 시각 일치)
1. **`vc-5` GleoActionSender → IntentRouter chain** (MEDIUM) — 외부 `NAVIGATE_TO_SETTING` intent → 응답 implicit broadcast 정보 disclosure
2. **`vc-6` VehicleBroadcastReceiver `macAddress`** (HIGH ↑ 격상) — exported=true confirmed, 페어링 디바이스 spoofing
3. **`lmp-1` PromptsContentProvider** (HIGH) — LLM system prompt 외부 노출 → jailbreak 채널
4. **`lmp-2` LLMModelProviderReceiver** (MEDIUM) — DoS: 모델 파일 삭제 + process kill

### TP (2/3 일치)
5. **`ssl-2` AuthData.toString token leak** (HIGH) — defender + domain_expert. attacker는 log emission 검증 대기로 abstain
6. **`ssl-3` CCGAuthenticator pinning** (MEDIUM) — defender + domain_expert. attacker는 pinning 위치 확인 대기로 abstain

### Uncertain (1/3 — defender only)
7~12. `vc-1`, `vc-2` (HtmlWebView), `vc-3`, `vc-4` (AppPermissionManager), `vc-7` (Broadcasts flag), `ssl-1` (ECCCrypto KDF) — 모두 defender의 hardening 의제만 인정. attacker/domain_expert는 외부 trust boundary 또는 차량 영향 확정 못함.

## 시각별 평가 패턴

| 시각 | 적극 보고 (HIGH+MEDIUM) | abstain/uncertain | 미보고 |
|---|---|---|---|
| attacker | 4 (vc-5, vc-6, lmp-1, lmp-2) | 4 (ssl-1, ssl-2, ssl-3, vc-3) | 4 (vc-1, vc-2, vc-4, vc-7) |
| defender | 12 (모두 — hardening 의제) | 0 | 0 |
| domain_expert | 6 (vc-5, vc-6, lmp-1, lmp-2, ssl-2, ssl-3) | 4 (ssl-1, vc-3, vc-4, vc-1) | 2 (vc-2, vc-7) |

→ **defender가 가장 적극, attacker가 가장 보수**. 합의 규칙이 attacker의 적극성을 상쇄해 false positive를 자연스레 demote.

## 정량 변화 (stage1 → stage3)

| 지표 | stage1 (n=12, self GT) | stage3 (n=12, ensemble) | 비고 |
|---|---|---|---|
| TP | 6 | 6 (strong 4 + TP 2) | 동일 — Recall 100% |
| FP | 4 | **0** | 4 self-GT FP 모두 stage3 uncertain으로 강등됨 |
| uncertain | 2 | 6 | self-GT FP 4건이 uncertain으로 reclassified |
| Precision (lenient) | 0.60 | **1.00** | strong+TP만 채택 시 0% FP |
| 1차 오탐률 | 40~50% | **0% (strong+TP)** / 50% (uncertain → FP) | 합의 규칙으로 single-perspective FP 차단 |

### 핵심 발견
- **D3=(B)의 합의 규칙이 정량 효과 입증** — stage1의 4건 self-GT FP가 모두 stage3에서 uncertain으로 강등 (1/3 — defender만 보고).
- 합의 임계 2/3 적용 시 **Precision 1.00 (n=6 채택)** + Recall 100% (모든 self-GT TP 회수).
- 단 표본 n=12 단일 세션 작성이라 통계적 의미 약함. **OWASP MASTG 도입 후 외부 GT 기반 재측정 필요**.

## PPT 가설 vs 실측 갱신 (PPT 수정 가이드 보강용)

| PPT 가설 | 측정 (이전) | 측정 (Stage 3 적용) | 비고 |
|---|---|---|---|
| 1차 오탐률 25% | 40~50% (n=12) | 그대로 | stage1 단계 |
| 2차 오탐률 12% | 미측정 | 부분 적용 | caller 추적/manifest 매핑으로 4건 잠정 FP 식별 |
| 3차 오탐률 7% | 미측정 | **0% (n=6 채택, n=12 입력)** | strong+TP 채택 시. 표본 작음 |
| Precision 0.93 | 0.60 (lenient) | **1.00 (n=6, strong+TP)** | 합의 임계 적용. 표본 작음 |

## 다음 작업 (follow-up)

1. **uncertain 6건 정밀화**:
   - `ssl-2` AuthData: `Timber.|Log\.[diwev]\(.*authData` grep — 실제 log emission 확인
   - `ssl-3` CCGAuthenticator: `CCGTokenProvider` 또는 `network_security_config.xml`의 pinning 확인 (Phase B-3.c)
   - `ssl-1` ECCCrypto: `generateDeterministicPrivateKey(passphrase)` caller 추적 → passphrase 출처
   - `vc-1`/`vc-2`/`vc-3`/`vc-4`: deep-link 등록 여부 manifest 정밀 검사
2. **OWASP MASTG 도입** (Phase B-4.c) — 외부 GT 기반 Precision/Recall 재측정 → 본 결과의 통계적 의미 확정
3. **합의 임계 sensitivity 분석** — 1/3, 2/3, 3/3 채택 시 P/R 변화 계산 → ablation study의 한 항목
