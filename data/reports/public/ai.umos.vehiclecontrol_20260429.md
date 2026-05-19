> **Public masked copy** — code evidence (fenced blocks) replaced with redaction markers under contractor IP protection. Class names, line numbers, categories, severities, rationale, and AAOS / MASVS mappings are kept verbatim. Original raw report is retained locally only.
>
> 본 파일은 contractor IP 보호 정책에 따라 코드 인용을 redact 한 공개용 사본이다. 분석 메타데이터 (class, line, category, severity, rationale, AAOS 매핑) 는 그대로 유지.
>
> **Final archive note**: this is a historical 2026-04-29 Stage 1/2 snapshot. Inline "follow-up" labels below record what was still open at that date; they are not current remaining work. Final 15-week conclusions are summarized in `../../../docs/01_final_report.md` and `../../../docs/03_case_studies.md`.

# Stage 1 Analysis — `ai.umos.vehiclecontrol` (VehicleControl.apk)

- **Date**: 2026-04-29
- **Source device**: PleOS Connect v2.0.5 emulator (Android 14, x86_64)
- **APK path on device**: `/system/priv-app/VehicleControl/VehicleControl.apk` (92.2 MB)
- **Decompiler**: jadx 1.5.5 (`--deobf --show-bad-code`)
- **Stage**: 1 (single-pass LLM, Claude Opus 4.7)

## Manifest highlights

- `android:sharedUserId="android.uid.system"` — runs with the **system UID**, dramatically widening the impact of any vulnerability.
- Privileged permissions: `WRITE_SECURE_SETTINGS`, `READ_WIFI_CREDENTIAL`, `BLUETOOTH_PRIVILEGED`, `MODIFY_PHONE_STATE`, `READ_PRIVILEGED_PHONE_STATE`, `MANAGE_USERS`, `INTERACT_ACROSS_USERS`, `NETWORK_SETTINGS`, `NETWORK_STACK`.
- Vehicle-control permissions: `android.car.permission.CAR_POWERTRAIN`, `CAR_CONTROL_AUDIO_VOLUME`, `CAR_CONNECT_VENDOR_CONTROL`, `CAR_ENERGY`, `CAR_ENERGY_PORTS`.
- Self-defined permissions (`system|signature`): `READ_VEHICLE_PREFERENCES`, `WRITE_VEHICLE_PREFERENCES`, `READ_SYSTEM_FONT`.
- Holds `INTERNET` — i.e. the same process that controls the powertrain can also reach the internet.
- Exported components (activity / receiver / provider) seen in the manifest: 12+.

## Triage — keyword grep over `ai/umos` + `ai/pleos` (1,765 Java files)

| # | Class | Hit |
|---|---|---|
| 1 | `feature/information/p026ui/common/HtmlWebViewKt.java` | WebView, `setAllowFileAccess` |
| 2 | `feature/applications/data/permission/AppPermissionManager.java` | `checkPermission` |
| 3 | `feature/bluetooth/data/VehicleBroadcastReceiver.java` | broadcast |
| 4 | `Broadcasts.java` | `sendBroadcast` |
| 5 | `orda/Manager.java` | broadcast |
| 6 | `orda/BroadcastManager.java` | broadcast |
| 7 | `VehicleControlActivity.java` | broadcast |
| 8 | `p051ui/screens/GleoActionSender.java` | `sendBroadcast` |
| 9 | `playground/navi/helper/utils/C0014b.java` | (obfuscated) crypto/network keyword |

Hardcoded-secret regex hits: 3 — all are `password` field references inside Kotlin data classes' auto-generated `toString()` (low risk if logs are filtered, but worth a follow-up that those classes never reach a logger).

## Findings — class 1: `HtmlWebViewKt`

### Finding 1 — HIGH — WebView `setAllowFileAccess(true)` under system UID

```java
// <redacted: PleOS proprietary code>
```

- API 30+ defaults `setAllowFileAccess` to `false`. The explicit `true` re-enables the `file://` scheme inside the WebView.
- The hosting APK runs as **`android.uid.system`** with `WRITE_SECURE_SETTINGS` and `READ_WIFI_CREDENTIAL`. If `htmlContentPath` (the parameter passed into the composable) ever resolves to a `file://` URL pointing at a privileged file (e.g. `/data/data/<app>/...` or `/system/...`), the WebView reads it under the system UID's authority.
- **Mitigation candidates**: drop the explicit `setAllowFileAccess(true)` (use `setAllowFileAccess(false)` plus `WebViewAssetLoader` with an `assets://` prefix), or restrict by `WebViewClient.shouldOverrideUrlLoading` to a scheme allow-list.
- **AAOS mapping**: §5.1 Communication Security (WebView safe-config).

### Finding 2 — MEDIUM — `loadUrl(htmlContentPath)` with no scheme validation

```java
// <redacted: PleOS proprietary code>
```

- `htmlContentPath` is a `String` parameter of the composable, forwarded directly to `WebView.loadUrl` with no scheme allow-list, prefix check, or `WebViewAssetLoader` indirection.
- Combined with **Finding 1**, an untrusted producer of `htmlContentPath` (e.g. an `Intent` extra reaching this screen) can pivot to local-file disclosure. Trust of the caller cannot be confirmed inside this file alone.
- **Follow-up**: grep for `HtmlWebView(` invocations and walk back to the data source.
- **AAOS mapping**: §5.1 Communication Security.

### Negative confirmations (not reported as findings, but worth recording)

- `setJavaScriptEnabled` is **not** called in this file. The WebView's JavaScript stays at the framework default (`false`).
- No hardcoded keys or `http://` literals in this class.

## Findings — class 2: `AppPermissionManager`

This class is a **privileged primitive**: it can grant or revoke runtime permissions on any package, courtesy of the host APK's system UID + platform signature. Internally it does *no* validation of the target `packageName` beyond Hilt-injecting it through the constructor.

### Finding 1 — HIGH — `grantRuntimePermission` driven by caller-supplied `packageName`

```java
// <redacted: PleOS proprietary code>
```

- `this.packageName` is the constructor argument — the class itself never sanitises it.
- Reaching this from an untrusted producer (e.g. a `packageName` extra on an `Intent` that lands in the applications-permission UI) lets an attacker grant any runtime permission to any installed app, with the operation attributed to the system UID.
- **Follow-up**: trace producers → confirm whether any exported activity/service in the manifest routes external input into this feature.

### Finding 2 — HIGH — Symmetric `revokeRuntimePermission`

```java
// <redacted: PleOS proprietary code>
```

- Same trust-boundary issue. Practical impact: silently strip `ACCESS_FINE_LOCATION` from a safety-critical app, or `BLUETOOTH_CONNECT` from the keyless-entry app.

### Notes

- `isPermissionGranted` (line 107) uses `packageManager.checkPermission(perm, this.packageName) == -1` correctly; not flagged.
- The class only mutates an internal `MutableStateFlow` after the OS-level call succeeds — i.e. there is no fail-open path.

## Findings — class 3: `GleoActionSender` (PleOS Gleo AI 응답 송출)

```kotlin
// <redacted: PleOS proprietary code>
```

### Finding — MEDIUM — Implicit broadcast carries response payload

- `sendBroadcast` 가 `setPackage()` 미지정 + receiver permission 미지정으로 송출됨. **모든 앱이 receiver를 등록하면 `status`/`message`/`response` JSON 을 관찰 가능**.
- system UID에서 송출되는 정보 단방향 채널. response가 사용자 음성 명령 결과 / 차량 속성을 포함하면 정보 disclosure.
- **Mitigation**: `setPackage(<pleos-package>)` 또는 signature-protected permission 추가.

## Findings — class 4: `VehicleBroadcastReceiver` (Bluetooth/AndroidAuto)

```kotlin
// <redacted: PleOS proprietary code>
```

### Finding — MEDIUM — Untrusted `macAddress` extra persisted without validation

- `macAddress` 가 형식 검증 없이 `PairedDeviceRepository.insertDevice` 로 저장.
- Manifest에 `android:exported="true"` receivers 다수 존재 — 이 receiver가 그 중 하나면 외부 앱이 임의 `macAddress` 주입 가능.
- **Follow-up**: manifest의 receiver 12개 중 어느 것이 `VehicleBroadcastReceiver` 인지 확인. 또한 `IntentPackageName.RFCOMM` 의 패키지명을 확인 (외부 메시징의 트러스트 boundary).

## Findings — class 5: `Broadcasts` (utility)

```kotlin
// <redacted: PleOS proprietary code>
```

### Finding — LOW — `registerReceiver` flag 미지정

- API 34+에서 `RECEIVER_EXPORTED` / `RECEIVER_NOT_EXPORTED` 명시 권장. lint 억제로 default behavior 유지.
- 모든 `Broadcasts.observe(...)` caller가 이 default를 상속.

## Findings — class 6 / 7 / 8 / 9: 안전 (no findings)

- **`ai.umos.orda.BroadcastManager`**: `LocalBroadcastManager` 기반 — process-internal broadcast, 외부 노출 없음. (LocalBroadcastManager 자체는 deprecated이지만 보안 측면 안전.)
- **`ai.umos.orda.Manager`**: 클라이언트 hashmap 관리 + `BroadcastManager` (위 LocalBroadcast 기반). 외부 입력/송출 없음.
- **`ai.pleos.playground.navi.helper.utils.C0014b`** (난독화 명): `checkSelfPermission` 후 `SecurityException` throw. 표준 권한 가드 패턴.
- **`ai.umos.vehiclecontrol.VehicleControlActivity`**: `registerReceiver(receiver, filter, 2)` — flag=2 (`RECEIVER_NOT_EXPORTED`) 명시. 좋은 패턴. `triggerRebirth` 의 `Runtime.exit(0)` 는 self-restart 의도된 동작.

## 종합 통계 (Stage 1, 9 priority 클래스)

| 카테고리 | HIGH | MEDIUM | LOW | 클래스 |
|---|---|---|---|---|
| network | 1 | 1 | — | HtmlWebViewKt |
| permission | 2 | — | — | AppPermissionManager |
| intent | — | 2 | 1 | GleoActionSender, VehicleBroadcastReceiver, Broadcasts |
| **합계** | **3** | **3** | **1** | 4 클래스에 분산 |

- 분석한 클래스 9개 중 4개에서 finding, 5개는 clean.
- 평균 confidence: 0.55 (Stage 2 caller 분석으로 0.85+ 끌어올릴 대상)
- 모든 finding의 trust boundary는 caller 측에 있음 — Stage 2의 핵심 의제.

## Output artefacts

- JSON (machine-readable, schema = `configs/result_schema.json`): `data/reports/ai.umos.vehiclecontrol_20260429.json`
- Markdown (this file): `data/reports/ai.umos.vehiclecontrol_20260429.md`

## Stage 2 — Caller analysis (2026-04-29 same session)

### Manifest exported component mapping (B-2.a)

검증 결과: `VehicleBroadcastReceiver` 가 `android:exported="true"` 로 manifest에 등록됨 (4번째 receiver entry). **stage1의 trust 가정이 검증됨**.

추가 발견된 exported attack surface (Phase B-3 후속 분석 후보):
- `RebootReceiver` (exported=true) — 외부 reboot trigger 가능성?
- `VehiclePreferenceContentProvider` (exported=true) — vehicle preferences provider 노출
- `LockPinChangeReceiver` (exported=true) — PIN 변경 receiver
- `BluetoothPairingRequest` (exported=true)

### Caller traces (B-2.b/c/d)

| Stage 1 finding | Caller | Trust | Confidence Δ | 결론 |
|---|---|---|---|---|
| HtmlWebViewKt `setAllowFileAccess(true)` | `HtmlPopupScreenKt`, `ReleaseNotesKt` | **internal** UI screens (popup / release notes) | 0.75 → 0.50 | hardening 의제는 유지하나 현재 기준 LFI 익스플로잇 chain 미발견. **잠정 false-positive 후보**. follow-up: HtmlPopupScreen / ReleaseNotes로 deep link 등록 여부 manifest 재확인 |
| HtmlWebViewKt `loadUrl(htmlContentPath)` | 위와 동일 | **internal** | 0.55 → 0.40 | 위와 같은 결론. 잠정 FP |
| AppPermissionManager `grantRuntimePermission` | `ApplicationDetailsViewModel.grantPermission` ← `ApplicationDetailsScreenKt` UI ← Nav arg `appPackageName` (SavedStateHandle) | **internal navigation arg**. deep link 등록 안 됐으면 internal | 0.55 → 0.45 | follow-up: ApplicationDetails 화면의 deep link 등록 여부. 등록 됐고 IntentRouter의 `NAVIGATE_TO_SETTING` 이 거기로 가면 → 외부 controlled. 그렇지 않으면 FP |
| AppPermissionManager `revokeRuntimePermission` | 위와 동일 | 위와 동일 | 0.55 → 0.45 | 위와 동일 |
| GleoActionSender `respondAction` (implicit broadcast) | **`IntentRouter.toNavigationEvent`** | **외부 controlled** (`NAVIGATE_TO_SETTING` action을 받아 처리 후 응답 송출). `VehicleControlActivity` (exported=true) 가 entry | **0.55 → 0.85** | true positive로 확정 가능. severity **MEDIUM → HIGH** 로 격상 검토 |
| VehicleBroadcastReceiver `macAddress` | manifest 에서 receiver 자체가 `exported=true` | **외부 controlled** | **0.50 → 0.85** | true positive 확정. severity **MEDIUM → HIGH** 로 격상 검토 |
| Broadcasts `UnspecifiedRegisterReceiverFlag` | 광범위 | mixed | 0.50 → 0.50 (변동 없음) | hardening 의제, severity LOW 유지 |

### Stage 2 첫 1차 오탐률 잠정 측정

| Stage 1 finding 수 | Stage 2 잠정 TP | Stage 2 잠정 FP 의심 | LOW 유지 | 잠정 오탐률 |
|---|---|---|---|---|
| 7 | 2 (HIGH 격상) | 4 (HtmlWebView × 2 + AppPermissionManager × 2) | 1 | **4/7 ≈ 57.1%** |

⚠️ 측정 caveat:
- "잠정 FP 4건"은 아직 deep-link 검증을 거치지 않은 상태. ApplicationDetails 화면의 deep link 등록 여부에 따라 1~2건이 다시 TP로 환원될 수 있음.
- 표본 1개 APK / 7 findings 이라 통계적 유의성 매우 약함. **PPT 가설 1차 오탐률 25%** 와 비교는 PleOS 특화 APK 2종 추가 (Phase B-3) 후 다시 측정.
- D3=(A) "멀티 모델 cross-read" 는 당시 Claude Code 단일 모델 세션에서는 **manual workflow**로만 가능했다. 최종 artifact에서는 이 아이디어를 Codex 3-model cross-read 보강 실험으로 별도 완료했다.

### 당시 follow-up 기록 (Phase B-3 진입 직전)

1. ApplicationDetails 화면의 deep link 등록 여부 manifest 재확인 → AppPermissionManager 4건 FP 확정/환원 ← **2026-04-30 Stage 2.b 완료, 아래 참조**
2. HtmlPopupScreen / ReleaseNotes 의 caller 추적 → HtmlWebView 2건 FP 확정/환원 ← **2026-04-30 Stage 2.b 완료, 아래 참조**
3. RebootReceiver / LockPinChangeReceiver / VehiclePreferenceContentProvider — exported 대상 추가 stage1
4. **Phase B-3**: `ai.pleos.sync.syslog` + `ai.pleos.llm.model.provider` 같은 파이프라인 적용. 표본 늘려 오탐률 재측정.

## Stage 2.b — Deep-link verification (2026-04-30)

상세 audit는 `docs/stage2b_deeplink_verification_20260430.md` 참조.

### 검증 결과

| ID | Stage 2.a 잠정 verdict | **Stage 2.b 최종 verdict** | 핵심 근거 |
|---|---|---|---|
| vc-1 HtmlWebView `setAllowFileAccess(true)` | 잠정 FP | **FP CONFIRMED** | manifest URI deep-link 0건 + `htmlContentPath` ← OTA-trusted `ReleaseInfoData` |
| vc-2 HtmlWebView `loadUrl(htmlContentPath)` | 잠정 FP | **FP CONFIRMED** | 위와 동일 caller chain |
| vc-3 AppPermissionManager `grantRuntimePermission` | 잠정 FP | **FP CONFIRMED** | 4중 차단: manifest 부재 + Compose Nav internal-only + LinkProvider single-segment path + NestedNavRouter applications 미binding |
| vc-4 AppPermissionManager `revokeRuntimePermission` | 잠정 FP | **FP CONFIRMED** | 위와 symmetric |

### 4중 차단 동선 (vc-3/4)

1. **Manifest 차단**: `<data android:scheme=...>` / `<deepLink>` 등 URI 매칭자 0건. 외부 진입 가능 activity는 `VehicleControlActivity` 1개 뿐, 모두 action 기반 intent-filter.
2. **Compose Nav 차단**: ApplicationDetails route = `application_details_route/{app_package_name}` — `NavGraphBuilder` 내부 등록만, `navDeepLink {...}` 미사용.
3. **IntentRouter 차단**: 외부 `NAVIGATE_TO_SETTING` 의 `ACTION_PARAM` JSON → `LinkProvider.createLink` → URI는 항상 path segment 1개 (`<categoryKey>?section=<subKey>`). `IntentRouter.buildCategoryEvent`의 `pathSegments.size() > 1` 조건 미충족 → `subPathRoute` 호출 자체 X.
4. **NestedNavRouter 차단**: `NavRouter` 구현체는 `VehicleInformationNavRouter` + `ConvenienceNavRouter` 단 2개. **applications 카테고리 NavRouter binding 없음** → `nestedRoutes.get(APPLICATIONS) == null`.

→ 외부 NAVIGATE_TO_SETTING은 최대 `ApplicationsScreen` (앱 목록 화면) 까지만 도달. **ApplicationDetails (개별 앱 권한 grant/revoke UI) 는 외부 진입 불가.**

### vc-1/2 caller origin

`htmlContentPath` 의 path 출처:
- `VehicleInformationScreenKt:798` → `versionInfo.getHtmlContentPath()` → `ReleaseInfoData.{summaryPath, detailedDescriptionPath, whatsNewPath}`
- `ReleaseNotesKt:113` → `newReleaseInfo.getSummaryPath()`

`ReleaseInfoData`는 OTA flow에서만 업데이트:
- `UpdateBroadcastReceiver` (`exported="false"`, action `ai.ftdot.update.UPDATE_STATE_CHANGED`)
- `EnableUpdateDownloadReceiver` (`exported="false"`, action `ai.umos.vehiclecontrol.action.ENABLE_AUTO_DOWNLOAD`)
- `protected-broadcast` 선언 — 같은 UID/플랫폼 서명 앱만 송출 가능.

→ external-app uncontrolled. `setAllowFileAccess(true)` 는 **defense-in-depth hardening 의제 LOW**로 유지하되 LFI 익스플로잇 chain 부재.

### 결과 측정 영향

GT는 이미 vc-1~4 모두 `is_real=false` 라벨링. 측정값 변동 없음. 단:
- `ssl-6` GT line 120→76 정정 (보고서 정합) 후 재실행
- A.1 stage 1: P 73.3% / FP 26.7% / Recall 100% / **F1 0.846**
- A.2 stage 2 (caller P-ceiling): P 100% / **F1 1.000**
- A.3 stage 3 ≥3/3: P 100% / Recall 81.8% / **F1 0.900**
- B ≥2/3 (default): P 100% / Recall 90.9% / **F1 0.952** ← PPT 가설 0.93 도달·초과


## 당시 next-step 기록 — Stage 2 progression

1. **Manifest exported component triage** — match the 12+ exported receivers/activities/providers to the analyzed classes. Confirms / refutes severity for `VehicleBroadcastReceiver`, `GleoActionSender` callers, and the `Broadcasts` utility risk surface.
2. **Caller traces**:
   - `HtmlWebView(htmlContentPath, …)` callers
   - `AppPermissionManager` Hilt graph + which UI route supplies `packageName`
   - `GleoActionSender.respondAction(...)` producers
3. **Stage 2 regex/AST rules** (codify before re-running on next APK):
   - `setAllowFileAccess(true)` + `loadUrl(<param>)` (false-positive filter for asset-only URLs)
   - `grantRuntimePermission(<param>, ...)` / `revokeRuntimePermission(<param>, ...)`
   - implicit `sendBroadcast(...)` with custom action and no `setPackage` / `permission`
4. **Manual cross-read idea** of the 7 findings (D3=(A) ensemble first application). This was later superseded by the completed Codex 3-model cross-read summarized in `../../../docs/08_completed_reinforcements.md`.
