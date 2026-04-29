# Stage 2.b — Deep-link Verification (VehicleControl, 2026-04-30)

> Phase B-2 follow-up. 첫 회 stage 2 caller 분석에서 "잠정 FP" 로 남았던 4건 (vc-1~4) 의 deep-link 진입 가능성을 manifest + Compose Navigation + IntentRouter 동선으로 정밀 검증.

## 검증 대상 (Stage 1/2 재확인)

| ID | Class:line | Stage 1 verdict | Stage 2.a 1차 결과 |
|---|---|---|---|
| vc-1 | `HtmlWebViewKt:58` `setAllowFileAccess(true)` | HIGH (network) | 잠정 FP — internal Compose screens (HtmlPopupScreenKt, ReleaseNotesKt) |
| vc-2 | `HtmlWebViewKt:82` `loadUrl(htmlContentPath)` | MEDIUM (network) | 잠정 FP — same caller chain |
| vc-3 | `AppPermissionManager:149` `grantRuntimePermission` | HIGH (permission) | 잠정 FP — internal Nav arg (`SavedStateHandle`) |
| vc-4 | `AppPermissionManager:124` `revokeRuntimePermission` | HIGH (permission) | 잠정 FP — symmetric to vc-3 |

## 검증 방법론

3 축으로 deep-link 진입 가능성을 닫음:

1. **Manifest URI 매칭자 부재 확인** — `android:scheme` / `android:host` / `deepLink` / `data` 자식 element 검색.
2. **Compose Navigation graph 등록 확인** — 화면별 `NavigationKt.applicationDetailsScreen` 등록 위치 + nav route 패턴.
3. **IntentRouter 외부 진입 → Compose route 도달 가능성** — `NAVIGATE_TO_SETTING` action handler가 NavController 어디까지 routing.

## 증거

### A. Manifest grep 결과

```
$ grep -nE "android:scheme|android:host|deepLink|<data" \
  pleos-llm-scanner/data/decompiled/VehicleControl/resources/AndroidManifest.xml
(0 matches)
```

`AndroidManifest.xml` (315 lines, 12+ exported components, 27 intent-filter blocks) 내 **URI scheme/host 기반 deep-link 정의 0건**. 모든 intent-filter는 system action 기반 (`MAIN`, `BLUETOOTH_SETTINGS`, `WIFI_SETTINGS`, `BOOT_COMPLETED`, `PAIRING_REQUEST`, `DEVICE_ADMIN_ENABLED`, `ai.umos.android.intent.action.ANDROID_AUTO_REQUEST_*` 등).

외부 앱이 진입 가능한 activity는 단 1개:

```xml
<activity
    android:name="ai.umos.vehiclecontrol.VehicleControlActivity"
    android:exported="true"
    android:launchMode="singleTop">
    <intent-filter><action android:name="android.intent.action.MAIN"/>
                  <category android:name="android.intent.category.LAUNCHER"/></intent-filter>
    <intent-filter><action android:name="android.settings.BLUETOOTH_SETTINGS"/>...</intent-filter>
    ...
    <intent-filter>
      <action android:name="ai.umos.vehiclecontrol.NAVIGATE_TO_SETTING"/>
      <category android:name="android.intent.category.DEFAULT"/>
    </intent-filter>
    ...
</activity>
```

→ 외부 진입은 **`VehicleControlActivity` + 7개 action**에 한정. URI deep-link는 없음.

### B. Compose Navigation route 등록

`NavigationKt.applicationDetailsScreen` (`feature/applications/applicationDetails/.../NavigationKt.java:38`):

```java
NavGraphBuilderExtKt.composableNoTransition(navGraphBuilder,
    "application_details_route/{app_package_name}",
    listOf(navArgument("app_package_name", { type = NavType.StringType })),
    ...);
```

진입 navigation:

```java
public static final void navigateToApplicationDetails(NavHostController, AppInfo appInfo) {
    NavController.navigate$default(navHostController,
        "application_details_route/" + URLEncoder.encode(appInfo.getPackageName(), URL_CHARACTER_ENCODING),
        ...);
}
```

→ `application_details_route/{package}` 는 **single-activity Compose Navigation 내부 route**. `NavigationKt`에 deep-link 등록 (`navDeepLink {...}`) 호출 0건. 외부 Intent → 이 route 직접 도달 불가.

`HtmlPopupScreenKt` / `ReleaseNotesKt` 도 같은 패턴 (manifest 부재 + Compose 내부 등록만).

### C. IntentRouter 동선 — `NAVIGATE_TO_SETTING` 처리 chain

`IntentRouter.java:80-89`:

```java
case 1243580457:
    if (action.equals("ai.umos.vehiclecontrol.NAVIGATE_TO_SETTING")) {
        String navigationPath = getNavigationPath(intent);
        ...
        return buildCategoryEvent(navigationPath);
    }
```

`getNavigationPath` 흐름:

1. Intent extra `ACTION_PARAM` (JSON) → `ActionParam` 객체 deserialize
2. `LinkProvider.getLink(actionParam.category, actionParam.subcategory)` → URI 문자열
3. `LinkProvider.createLink` (`LinkProvider.java:137`):
    ```java
    Uri.Builder builder = new Uri.Builder().path(categoryKey);
    if (subCategoryKey != null) builder.appendQueryParameter("section", subCategoryKey);
    return builder.build().toString();
    ```
   → **path segment 1개 (`categoryKey` 만)** + query parameter (`?section=`).

`buildCategoryEvent` (`IntentRouter.java:124-160`):

```java
Uri uri = Uri.parse(categoryPath);
...
if (uri.getPathSegments().size() > 1) {
    Function1 subPathRoute = subPathRoute(categoryType2, uri.getLastPathSegment());
    ...
    return new NavigationEvent.Category(categoryType2, subPathRoute, string);
}
return new NavigationEvent.Category(categoryType2, null, categoryPath, 2, null);
```

→ `LinkProvider.createLink`는 **항상 path segment 1개**. `pathSegments.size() > 1` 조건은 외부 진입에서 **결코 만족하지 않음** → `subPathRoute` (= `NestedNavRouter.findRoute`) 호출 자체 없음.

### D. NestedNavRouter binding map — APPLICATIONS 키 부재

`NavRouter` 인터페이스 구현체 grep:

```
$ grep -lr "implements NavRouter" pleos-llm-scanner/data/decompiled/VehicleControl/sources
- VehicleInformationNavRouter
- ConvenienceNavRouter
```

**applications 카테고리에 NavRouter 구현체 0건**. 즉 Hilt `nestedRoutes: Map<CategoryType, NavRouter>` 에 `APPLICATIONS` 키 binding 안 됨 → `nestedRoutes.get(APPLICATIONS) == null` → `NestedNavRouter.findRoute` 즉시 null 반환.

(근거 상호보강: 위 C 동선이 `subPathRoute` 호출 자체에 도달 못 하므로 D는 다중 안전망. 두 layer 모두 외부 진입 차단.)

### E. ReleaseInfoData / VersionInfo 출처

`ReleaseInfoData` (data class, `feature/information/p026ui/model/ReleaseInfoData.java`):
- `summaryPath`, `detailedDescriptionPath`, `whatsNewPath` 모두 `String?` 필드.
- 생성자는 직접 호출 — 외부 Intent extra 매핑 없음.
- 보유처: `UpdateSectionInfoUi.{currentReleaseInfo, newReleaseInfo}` ← `VehicleInformationViewModel` (OTA state observer).

OTA 진입점은 manifest의 두 receiver:
- `UpdateBroadcastReceiver` `exported="false"` action `ai.ftdot.update.UPDATE_STATE_CHANGED`
- `EnableUpdateDownloadReceiver` `exported="false"` action `ai.umos.vehiclecontrol.action.ENABLE_AUTO_DOWNLOAD`

→ ReleaseInfoData는 **OTA backend trusted feed** 만 update 가능. 외부 앱 controlled 아님.

## 결론

| ID | Stage 2.a 잠정 verdict | Stage 2.b 최종 verdict | 근거 |
|---|---|---|---|
| vc-1 (HtmlWebView setAllowFileAccess) | 잠정 FP | **FP CONFIRMED** | A + B + E. `htmlContentPath` 출처는 OTA 신뢰 feed. defense-in-depth 의제는 LOW로 유지. |
| vc-2 (HtmlWebView loadUrl) | 잠정 FP | **FP CONFIRMED** | 위와 동일 caller chain. |
| vc-3 (AppPermissionManager grant) | 잠정 FP | **FP CONFIRMED** | A + B + C + D 4중 차단. 외부 NAVIGATE_TO_SETTING은 ApplicationsScreen (앱 목록) 까지만 진입 가능. ApplicationDetails (개별 앱 권한 grant/revoke UI) 는 도달 불가. |
| vc-4 (AppPermissionManager revoke) | 잠정 FP | **FP CONFIRMED** | 위와 symmetric. |

## 측정값 영향 (재실행 결과)

GT 라벨은 변경 없음 (vc-1~4 이미 `is_real=false`). 측정값 동일.

`ssl-6` GT line 정정 (120 → 76, 보고서 정합) 후 재실행:

| 변형 | 결과 |
|---|---|
| A.1 stage 1 | TP=11 / FP=4 / FN=0 / **P=73.3% / FP-rate=26.7% / Recall=100% / F1=0.846** |
| A.2 + stage 2 (caller P-ceiling) | TP=11 / FP=0 / **P=100% / F1=1.000** |
| A.3 + stage 3 (≥3/3) | TP=9 / FP=0 / FN=2 / **P=100% / Recall=81.8% / F1=0.900** |
| B ≥2/3 (default consensus) | TP=10 / FP=0 / FN=1 / **P=100% / Recall=90.9% / F1=0.952** |

**PPT 가설 매칭 상태**:
- 1차 오탐률 25% → 측정 26.7% (+1.7%p, 사실상 매칭)
- Precision (full pipeline) 0.93 → ≥2/3 합의 임계에서 1.00 (도달·초과)
- 3차 오탐률 7% → ≥2/3 합의에서 0% (도달)

## 부산물: Stage 2.b 자동화 후보 항목

본 검증은 Claude Code 세션 안에서 grep + Read 로 manual 진행. 다음 회 베이스라인 비교 / MASTG 확장 시 다음 과정을 결정론적 스크립트화 가능:

1. `aapt2 dump xmltree <apk>` 또는 manifest 직접 파싱 → URI deep-link 자동 추출
2. NavGraphBuilder route 패턴 grep → Compose Nav route enumeration
3. Custom action ↔ activity 매핑표 자동 생성
4. NavRouter `implements` 구현체 enumeration + Hilt @IntoMap binding 검색

→ `src/stage2b_deeplink_audit.py` (Phase B-4.c 시점에 작성 권장).

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-30 | Stage 2.b 검증 완료 — vc-1~4 FP 확정. GT notes 보강. ssl-6 GT line 120→76 정정. eval/ablation 측정값 stable 확인 |
