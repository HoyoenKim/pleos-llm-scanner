# Stage 2 Methodology

## One-Line Definition

**Stage 2는 Stage 1이 낸 취약점 후보를 caller chain, manifest, permission, route, data-origin, sink-specific rule로 재검증하여 `TP / FP / uncertain`으로 낮추거나 유지하는 contextual verification 단계다.**

Stage 2는 별도 LLM prompt로 독립 실행되는 단계가 아니다. Stage 1 후보를 대상으로 Codex/수동 grep/결정론적 증거 확인을 섞어 수행한 검증 절차이며, 최종 성능 주장은 Stage 3 consensus 기준으로 둔다.

## Why Stage 2 Exists

Stage 1은 recall을 우선한다. 그래서 `exported`, `setAllowFileAccess`, `grantRuntimePermission`, `usePlaintext`, `hardcoded value` 같은 위험 패턴을 넓게 잡는다. 하지만 Android/AAOS APK에서는 같은 코드 패턴이라도 다음 조건에 따라 실제 취약점이 아닐 수 있다.

- 외부 앱이 해당 component에 도달할 수 없는 경우
- manifest에서 exported가 false이거나 signature permission으로 막힌 경우
- Compose Navigation 내부 route일 뿐 external deep-link가 아닌 경우
- 위험 값이 OTA-trusted feed 또는 internal-only state에서만 들어오는 경우
- sink는 존재하지만 실제 caller path나 emission path가 없는 경우

Stage 2의 목적은 이 차이를 확인해 Stage 1의 false positive를 줄이는 것이다.

## Inputs And Outputs

| Item | Description |
|---|---|
| Input | Stage 1 finding JSON/Markdown, decompiled Java/Kotlin source, AndroidManifest.xml, resources, package metadata |
| Output | `TP`, `FP`, `uncertain` verdict, true severity, evidence references, Stage 3에 넘길 검증 질문 |
| Unit | finding 단위 |
| Main question | “이 후보가 외부 attacker 또는 relevant trust boundary에서 실제로 도달 가능한가?” |

## Stage 2 Sub-Steps

| Step | Name | What It Checks |
|---|---|---|
| 2.a | Caller / data-origin tracing | sink에 도달하는 caller, source, argument origin 확인 |
| 2.b | Deep-link / route verification | manifest URI, intent action, Compose Nav route, IntentRouter binding 확인 |
| 2.c | Manifest / permission boundary | exported, permission, signature gate, provider authority, receiver/action 확인 |
| 2.d | Sink-specific rule check | TLS/plaintext, WebView flags, crypto mode, hardcoded value usage, log emission 등 |
| 2.e | Verdict normalization | `TP / FP / uncertain`, severity, Stage 3 prompt context 정리 |

## Verification Checklist

### 1. Component Exposure

확인할 것:

- `android:exported`
- `android:permission`, `readPermission`, `writePermission`
- provider authority
- receiver/action intent-filter
- activity launch mode and accepted actions
- dynamic receiver 여부

예시:

- `lmp-1`: `PromptsContentProvider`가 `exported=true`이고 provider-level permission이 없어 runtime query 가능성 유지.
- `amb-5`: signature-level gate가 있으면 외부 앱 exploitability를 낮춤.

### 2. Caller Chain

확인할 것:

- sink 호출 메서드의 직접 caller
- caller가 UI internal route인지 external entrypoint인지
- argument가 external Intent extra, provider row, network response, local trusted state 중 어디서 오는지
- call path가 release build에서 reachable한지

예시:

- `vc-1`, `vc-2`: WebView sink는 있었지만 caller가 internal Compose screen이고 `htmlContentPath`가 OTA-trusted release info path에서만 유입되어 FP로 정리.
- `ssl-2`: token-like value가 `AuthData.toString()` 경유 후 `Log.d()` emission path에 도달하는 것이 확인되어 TP 유지.

### 3. Manifest And Deep-Link Route

Stage 2.b는 VehicleControl FP 제거에서 가장 중요했다.

확인할 것:

- manifest에 URI `scheme`, `host`, `<data>`가 있는가
- exported activity가 해당 route까지 직접 연결되는가
- Compose Navigation route가 external deep-link로 등록되어 있는가
- `IntentRouter`가 path segment, category, subcategory를 어떻게 제한하는가
- Hilt/NavRouter binding map에 target category가 존재하는가

대표 결과:

- `vc-1`~`vc-4`는 Stage 1에서 HIGH/MEDIUM으로 잡혔지만, Stage 2.b에서 4중 차단이 확인되어 FP confirmed.
- 근거 문서: `docs/archive/stage2b_deeplink_verification_20260430.md`

### 4. Sink-Specific Checks

| Category | Stage 2 Check |
|---|---|
| WebView | caller origin, URL/path source, JS/file access flag, external route 여부 |
| Intent / receiver | exported, action allow-list, caller identity, extra validation, downstream state mutation |
| Provider | authority, permission gate, query/write path, returned columns, data origin |
| Network | `usePlaintext`, HTTP literal, TLS/pinning/TrustManager/HostnameVerifier, prod/dev endpoint split |
| Crypto | deterministic key derivation, salt/IV/iteration, constant passphrase origin |
| Hardcoded | literal value type, production call path, test artifact 여부, cross-APK reuse |
| Logging | actual log call, sensitive object `toString()`, emission condition |

## Verdict Rules

| Verdict | Meaning | Example |
|---|---|---|
| `TP` | 외부 entrypoint 또는 relevant trust boundary에서 sink/data exposure가 실제 의미를 가짐 | `ssl-6` `.usePlaintext()` transport builder, `lmp-1` exported provider read |
| `FP` | 위험 패턴은 있으나 external reachability 또는 data origin이 차단됨 | `vc-1`~`vc-4` deep-link / internal route FP |
| `uncertain` | sink는 위험하지만 caller/emission/runtime condition이 충분히 확인되지 않음 | emission 미확인 PII/log finding, UI impact 미확인 provider write |

Severity는 Stage 1 severity를 그대로 믿지 않고 Stage 2 evidence에 따라 조정한다.

## Relationship To Stage 3

Stage 2는 Stage 3에 “검증된 evidence package”를 넘긴다.

Stage 3는 같은 후보를 attacker / defender / domain-expert 관점에서 다시 읽고, `2/3` 이상이 report하면 최종 유지한다. 따라서 Stage 2가 모든 것을 자동 확정하는 것이 아니라, Stage 3 consensus의 입력 품질을 높이는 역할을 한다.

## Measurement Caveat

보고서의 ablation에서 `Stage 2 F1 = 1.000`으로 보이는 값은 **실제 독립 Stage 2 자동화 성능이 아니다.**

그 값은 GT 라벨과 caller 분석 결과를 이용해 “Stage 2가 이론적으로 제거할 수 있는 FP 상한”을 본 **oracle-style P-ceiling**이다. 따라서 발표와 보고서에서는 다음처럼 말해야 한다.

Correct:

> Stage 2 caller/manifest verification explained which Stage 1 candidates were FP and provided evidence for Stage 3.

Incorrect:

> Stage 2 자동 검증기가 독립적으로 F1 1.000을 달성했다.

## Representative Cases

| Finding | Stage 1 | Stage 2 Result | Why |
|---|---|---|---|
| `vc-1` | WebView file access risk | FP confirmed | external deep-link 없음, caller internal, OTA-trusted source |
| `vc-3` | runtime permission grant risk | FP confirmed | Compose internal route, `APPLICATIONS` NavRouter binding 없음 |
| `ssl-2` | token/log exposure candidate | TP maintained | `Log.d(... AuthData ...)` emission path 확인 |
| `ssl-6` | plaintext transport candidate | TP escalated | gRPC builder에서 `.usePlaintext()` 확인 |
| `lmp-1` | exported provider disclosure | TP maintained | `PromptsContentProvider` exported + permission gate 없음 + runtime query confirmed |
| `am-1` | suggestion provider write | TP/impact-limited | provider write accepted, UI impact는 Stage 2 이후에도 unconfirmed |

## Artifacts

| Artifact | Role |
|---|---|
| `docs/archive/stage2b_deeplink_verification_20260430.md` | Stage 2.b deep-link audit의 가장 상세한 원문 |
| `data/reports/public/ai.umos.vehiclecontrol_20260429.md` | VehicleControl Stage 2 caller analysis |
| `data/reports/public/ai.pleos.sync.syslog_20260429.md` | Syslog Stage 2 follow-up |
| `data/reports/stage_transitions.md` | Stage 1 → Stage 2 → Stage 3 transition table |
| `docs/01_report.md` § 3.6.1 | 최종 보고서 내 Stage transition 해석 |
| `src/dynamic/state_machine.py` | 학기 외 작업에서 Stage 2 rule 일부를 deterministic state로 모델링 |

## Recommended Presentation Wording

발표에서는 Stage 2를 이렇게 설명한다.

> Stage 2는 LLM이 낸 후보를 바로 취약점으로 받아들이지 않고, manifest, caller chain, deep-link route, permission gate, sink-specific rule로 실제 도달 가능성을 확인하는 검증 단계다. 이 단계는 자동 성능 지표가 아니라 evidence packaging 단계이며, 최종 정량 성능은 Stage 3 consensus 기준으로 보고한다.

## Limitations

- Stage 2는 완전 자동화되어 있지 않다.
- AST rule 자동화는 설계에 포함되어 있으나 이번 결과의 핵심은 manual/Codex-assisted caller tracing이다.
- Stage 2 결과는 후보 기반 검증이지 APK 전체 exhaustive audit이 아니다.
- Stage 2에서 `uncertain`으로 남은 finding은 runtime PoC, Frida hook, UI confirmation, traffic capture 등 후속 검증이 필요하다.
