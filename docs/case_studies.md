# PleOS IVI 정적 분석 — 사례 연구 5건

_작성일: 2026-04-30 / 출처: data/ground_truth/combined_labels.json + data/reports/_

본 문서는 본 파이프라인이 발견한 18개 라벨 중 초기 계획서의 5건 사례 연구
카테고리에 매핑되는 대표 finding을 케이스 카드로 정리한다. 각 카드는 실제 측정값과
재현 가능한 evidence path를 포함한다. (finding ID 정의는 [`report_v0.9.md`](report_v0.9.md) 의 Notation 섹션 참조)

| # | 카테고리 | Finding | APK | 심각도 | Risk |
|---|---|---|---|---|---|
| 1 | 하드코딩 자격증명 | ssl-5 + ucl1-1 (비교) | sync.syslog + UnCrackable | HIGH+HIGH | High+High |
| 2 | 권한 우회 (FP — multi-stage 효과 입증) | vc-3 / vc-4 | vehiclecontrol | HIGH(stage1)→FP | n/a (FP) |
| 3 | 평문 통신 | ssl-6 | sync.syslog | HIGH (격상) | High |
| 4 | 불필요/위험 Exported 컴포넌트 | lmp-1 | llm.model.provider | HIGH | High |
| 5 | 차량 제어 영향 ⊕ Spoofing | vc-6 | vehiclecontrol | HIGH (TP 격상) | Critical |

---

## Case 1 — 하드코딩 자격증명 (Self vs MASTG 비교 케이스)

### 1A) `ssl-5` — BuildConfig.IDENTIFIER을 KDF passphrase로 사용

| 항목 | 내용 |
|---|---|
| Finding ID | ssl-5 |
| APK | `ai.pleos.sync.syslog` (PleOS 자체 패키지) |
| Class | `ai.pleos.sync.config.SyncConfigsProvider` |
| Line | 83 |
| Stage 1 시각 | hardcoded / HIGH (자동 탐지) |
| AAOS | §4.2 Credential Protection |
| MASVS | MASVS-STORAGE-2, MASVS-CRYPTO-1, MASVS-AUTH-2 |
| TARA Asset | 사용자 자격증명 (Major) |
| Risk | High → Mitigate (current sprint) |

**발견 경로**:
- Stage 1 키워드 매치: `'(?i)(api[_-]?key|secret|token|password)\s*=\s*"[^"]{16,}"'`
  + `KeyStore|SecretKeySpec` (crypto 카테고리와 cross-hit)
- 1차 LLM 시각: BuildConfig 상수가 KDF passphrase로 흘러들어가는 호출 그래프
- Stage 3 (≥2/3 합의): attacker / defender / domain_expert 모두 TP 동의
- self_GT 라벨링: `is_real=true`, true_severity=HIGH

**근본 원인**:
- `BuildConfig.IDENTIFIER`는 빌드 시 결정되는 상수 → APK reverse engineering으로 모든
  device가 같은 값을 사용함이 자명.
- 이 값을 `ECCCrypto.deriveKey(passphrase)` (ssl-1)에 흘려보내 → ECC private key가
  결정적으로 도출됨.
- 차량 syslog의 ECC 서명은 동일한 키 한 쌍으로 모든 차량이 사용 → 한 차량 키 추출이
  전체 fleet 공격으로 연결.

**권장 조치**:
- BuildConfig 상수를 KDF passphrase로 사용하지 말 것. Per-device entropy 도입
  (Android Keystore에 device-bound key 생성).
- 빌드 타임 randomization은 fix이 아님 — APK 1개만 분석되면 전체 fleet 노출.
- 호환성 유지를 위해 v2 키 도입 + 점진적 rotation (OTA 업데이트와 연동).

### 1B) `ucl1-1` — UnCrackable Level 1 hardcoded AES key (외부 GT 베이스라인)

| 항목 | 내용 |
|---|---|
| Finding ID | ucl1-1 |
| APK | UnCrackable-Level1 (OWASP MASTG 공식 challenge) |
| Class | `sg.vantagepoint.uncrackable1.C0005a` |
| Line | 15 |
| Stage 1 시각 | hardcoded / HIGH (자동 탐지) |
| MASVS (외부 GT 라벨) | MASVS-CRYPTO-1, MASVS-STORAGE-2 |

**비교 의의**:
- ssl-5는 self GT, ucl1-1은 외부 OWASP 공식 challenge.
- 두 케이스 모두 본 파이프라인 stage 1에서 **자동 탐지**.
- ucl1-1은 OWASP가 의도적으로 박은 취약점이므로 본 파이프라인의 키워드 + LLM 1-pass가
  외부 corpus(OWASP MASTG)에서도 작동함을 입증.
- self/MASTG 둘 다 동일 카테고리 (hardcoded → 4.2 Credential Protection)로 매핑됨 →
  AAOS 매핑 일관성 검증.

**시각화**: `data/viz/02_apk_severity_heatmap.png` (4 APK × HIGH/MEDIUM/LOW grid).

---

## Case 2 — 권한 우회 (False Positive 4중 차단) — multi-stage 검증의 효과 입증

### vc-3 / vc-4 — `AppPermissionManager.grantRuntimePermission` / `revokeRuntimePermission`

| 항목 | 내용 |
|---|---|
| Finding ID | vc-3, vc-4 |
| APK | `ai.umos.vehiclecontrol` |
| Class | `ai.umos.vehiclecontrol.feature.applications.data.permission.AppPermissionManager` |
| Line | 124, 149 |
| Stage 1 시각 | permission / HIGH (자동 탐지) |
| Stage 2.b 결과 | **FP CONFIRMED** (4중 차단 발견) |
| AAOS | §3.7 Permission Model |
| MASVS | MASVS-PLATFORM-1, MASVS-PLATFORM-3 |
| TARA Asset | 사용자 자격증명 (would-be Major) → 외부 진입 불가로 Risk 무효화 |

**Stage 1 왜 HIGH로 보였는가**:
- system UID 컨텍스트에서 `PackageManager.grantRuntimePermission(packageName, ...)`
  호출. `packageName` 은 caller-controlled로 보였음.
- LLM 1-pass: "외부 앱이 임의의 packageName으로 호출 시 정상 앱의 권한을 강제 회수
  가능 → DoS / 권한 우회"

**Stage 2 caller 분석**:
- `AppPermissionManager` 호출처 추적 → `ApplicationDetailsViewModel` (Hilt-injected).
- `packageName`은 Compose Navigation route argument에서 옴 (`ApplicationDetails`
  화면의 SavedStateHandle).

**Stage 2.b deep-link audit (2026-04-30 결정적 단계)**:
4중 차단으로 외부 진입 불가능 확정:
1. **Manifest URI deep-link 0건** — `AndroidManifest.xml`의 `<activity>` 항목에
   `<data android:scheme="..." android:host="..."/>` 정의 없음.
2. **Compose Nav route는 NavGraphBuilder 내부 등록만** — `navDeepLink {...}`
   미사용. 외부 intent로 직접 진입 불가.
3. **IntentRouter `LinkProvider.createLink`는 항상 path segment 1개** — 외부에서
   `NAVIGATE_TO_SETTING` intent를 보내도 `subPathRoute` 호출 자체가 안 됨
   (`pathSegments.size() > 1` 조건 미충족).
4. **NavRouter binding map에 `APPLICATIONS` 키 부재** — NavRouter 구현체는
   `VehicleInformationNavRouter` + `ConvenienceNavRouter` 단 2개. 외부 intent가
   `NAVIGATE_TO_SETTING` 으로 들어와도 ApplicationsScreen까지만 도달하고
   ApplicationDetails 진입 못 함.

**의의 — 본 파이프라인의 가치**:
- Stage 1 단독이면 FP 2건이 HIGH로 보고됨 (Precision 떨어뜨림).
- Stage 2 caller + Stage 2.b deep-link audit 합쳐서 **FP CONFIRMED**.
- 측정값으로 정량화: stage 1 P 77.8% → stage 3 ≥2/3 P 100% (+22.2%p, n=18).
  초기 계획서의 Precision 0.93 가설 도달.
- 산출: `docs/archive/stage2b_deeplink_verification_20260430.md`.

**교훈**:
- Permission API + system UID 만 보고 HIGH 단정 X.
- Compose Nav 시대 IVI는 **Compose Nav route + manifest deep-link + IntentRouter
  binding** 의 3-축 정합성 확인이 필수.
- 본 케이스를 PPT에서 "단계적 검증 효과" 사례로 인용 가능.

---

## Case 3 — 평문 통신 (gRPC `.usePlaintext()`)

### `ssl-6` — `SysLogService` gRPC 채널 TLS off

| 항목 | 내용 |
|---|---|
| Finding ID | ssl-6 |
| APK | `ai.pleos.sync.syslog` |
| Class | `ai.pleos.sync.syslog.SysLogService` |
| Line | 76 |
| Stage 1 시각 | network / MEDIUM → Stage 3에서 **HIGH 격상** |
| Stage 3 verdict | strong TP (3/3 합의) |
| AAOS | §5.1 Communication Security |
| MASVS | MASVS-NETWORK-1, MASVS-NETWORK-2 |
| TARA Asset | 진단/시스템 로그 (Moderate → severity HIGH로 격상되어 Major impact) |
| Risk | High → Mitigate (current sprint) |
| TARA Threats | I (Info Disclosure), T (Tampering) |

**발견 경로**:
- Stage 1 키워드: `HttpURLConnection|OkHttp|Retrofit` 와 `TrustManager|HostnameVerifier`
  로 검색. gRPC도 추가 키워드 후보 (후속 보강 대상).
- Code evidence:
  ```java
  ManagedChannelBuilder
      .forTarget(BuildConfig.LOGCAT_PROXY_SERVER_URL)
      .usePlaintext()  // ← TLS off
      .build();
  ```
- Stage 1 LLM: "gRPC `.usePlaintext()` 호출 — 평문 채널 (MEDIUM)"
- Stage 2 confirmation: `SysLogService:76` 위치 확인 + caller가 차량
  syslog를 외부 proxy로 송출하는 경로임을 확인 → MEDIUM → HIGH 격상.
- Stage 3: 시각 3종 (attacker / defender / domain_expert) 모두 TP 동의.

**시나리오에서의 영향**:
- 차량 syslog는 systemID, 네트워크 상태, 업데이트 history, 진단 코드를 포함.
- 평문 채널이면 같은 Wi-Fi/이동통신 경로 상의 공격자가 syslog 페이로드 관찰 가능.
- Tampering threat 추가 — proxy URL 바뀌면 가짜 telemetry 주입 가능.

**권장 조치**:
- `usePlaintext()` 제거. Default secure transport (TLS + ALPN) 사용.
- 인증서 pinning 적용 (`ChannelCredentials` 명시).
- BuildConfig.LOGCAT_PROXY_SERVER_URL의 변경 가능성 평가 — 빌드별 prod/dev/staging
  분리 (지금은 단일 endpoint hardcoded → ssl-3과 같은 패턴).

**측정 의의**: Stage 3 격상으로 PPT 가설 "3차 검증 후 7% FP rate"의 **반대 방향**
(MEDIUM → HIGH 격상)으로 작용한 사례. ssl-4와 더불어 `≥2/3 ≠ ≥3/3` 분리를
만들어 ablation B 결과의 F1 0.952 (≥2/3) > 0.900 (≥3/3) 차이를 설명.

---

## Case 4 — 위험한 Exported 컴포넌트 (LLM Corpus 외부 노출)

### `lmp-1` — `PromptsContentProvider` exported, no permission gate

| 항목 | 내용 |
|---|---|
| Finding ID | lmp-1 |
| APK | `ai.pleos.llm.model.provider` |
| Class | `ai.pleos.llm.model.provider.PromptsContentProvider` |
| Line | 62 |
| Stage 1 시각 | intent / HIGH |
| AAOS | §3.7 Permission Model |
| MASVS | MASVS-PLATFORM-1, MASVS-PLATFORM-2 |
| TARA Asset | LLM 시스템 프롬프트 / 모델 (Moderate criticality + sev HIGH → Major impact) |
| Risk | High → Mitigate (current sprint) |
| TARA Threats | I (Information Disclosure) |

**발견 경로**:
- Stage 1 키워드: `'android:exported="true"'` (intent 카테고리) + ContentProvider
  manifest 검색.
- Code evidence: ContentProvider가 `query()` 메서드에서 LLM system prompt corpus
  (텍스트)를 caller에게 그대로 반환. `<provider android:exported="true">` +
  `android:permission` 미설정.

**시나리오에서의 영향 (PleOS-specific)**:
- IVI에 탑재된 ai.pleos.llm 모델이 사용하는 system prompt corpus에는 차량 도메인
  특화 instruction (예: "당신은 차량 음성 비서, 운전자에게 ..."), guardrail 규칙,
  내부 데이터 schema가 포함될 수 있음.
- 외부 앱이 `ContentResolver.query(Uri.parse("content://ai.pleos.llm.prompts/..."))`
  로 system prompt를 통째로 받아갈 수 있음.
- 공격 chain:
  1. system prompt 추출 → 모델 jailbreak prompt 설계
  2. 다른 IVI 화면에서 LLM에 "이 차량의 시스템 명령으로 ..." 의 prompt injection
  3. car action API (Gleo)에 잘못된 사용자 의도 전달 가능

**권장 조치**:
- `android:exported="false"` 명시 또는
- `android:permission="ai.pleos.llm.READ_PROMPTS"` 같은 signature-level 권한 가드
- 가장 안전: ContentProvider 자체를 외부 노출하지 않고 in-process API로 변경

**의의**:
- PleOS-specific 컴포넌트 (LLM gateway). 일반 Android 앱 분석에서는 잘 안 나오는
  IVI 도메인 특수 finding.
- 본 파이프라인이 IVI 도메인 특화 흐름 — 차량 LLM corpus, 차량 제어 명령, 차량
  syslog — 까지 다룬다는 증거.

---

## Case 5 — 차량 제어 명령 + Spoofing (Critical Risk)

### `vc-6` — `VehicleBroadcastReceiver` macAddress 미검증 + exported

| 항목 | 내용 |
|---|---|
| Finding ID | vc-6 |
| APK | `ai.umos.vehiclecontrol` |
| Class | `ai.umos.vehiclecontrol.feature.bluetooth.data.VehicleBroadcastReceiver` |
| Line | 58 |
| Stage 1 시각 | intent / MEDIUM → GT 라벨 HIGH (true_severity 격상) |
| AAOS | §3.7 Permission Model |
| MASVS | MASVS-PLATFORM-1, MASVS-PLATFORM-2 |
| TARA Asset | 차량 제어 명령 (Severe criticality) |
| Risk | **Critical** → Avoid (must fix before release) |
| TARA Threats | S (Spoofing), T (Tampering) |

**발견 경로**:
- Stage 1 키워드: `android:exported="true"` (manifest) + `Intent.getStringExtra`
  + DB 저장 패턴.
- Code evidence: BroadcastReceiver의 `onReceive(Context, Intent)` 에서
  `intent.getStringExtra("mac_address")` 를 검증 없이 DB에 저장.
- Manifest: `android:exported="true"` + `intent-filter` 의 action이 임의 외부 앱이
  trigger 가능한 형태.
- Stage 2 caller 분석: 외부 앱이 매크 주입 가능 → DB 오염 → 그 매크가 차량 제어
  명령 (블루투스 페어링) 트리거에 사용될 수 있음.
- GT 라벨링: stage1=MEDIUM이지만 true_severity=HIGH (asset이 차량 제어이므로
  격상).

**시나리오에서의 영향**:
- 공격자가 `am broadcast --es mac_address "AA:BB:..."` 같은 ADB intent 또는 동일
  권한 가진 시스템 앱에서 임의 매크 주입.
- DB의 정상 매크가 공격자 매크로 교체되거나 추가됨 → 차량이 잘못된 BT 디바이스와
  페어링 → 차량 음향/네비/콜 채널 spoofing 가능.
- Tampering: 정상 매크의 신뢰도 저하 → DoS (정상 페어링 차단).

**권장 조치**:
- Receiver의 `android:exported="false"` (또는 internal-only intent action만 허용).
- macAddress 입력 검증 (regex `^([0-9A-F]{2}:){5}[0-9A-F]{2}$`).
- 신뢰된 sender만 허용 — `android:permission` 또는 caller package 화이트리스트.

**의의**:
- TARA Risk Matrix에서 **Critical** 등급 (Severe asset × High feasibility) 2건 중
  하나. 다른 하나는 vc-5 (GleoActionSender implicit broadcast).
- 본 finding이 "차량 안전 손상으로 직결되는 single-finding" 사례 — 정적 분석이
  안전 영향 범위까지 매핑할 수 있음을 보여주는 PPT 시연 케이스.

---

## 요약 표 — 5건의 종합 임팩트

| Case | Finding | Stage 1 → 최종 | AAOS § | TARA Risk | 발견 가치 |
|---|---|---|---|---|---|
| 1A | ssl-5 (BuildConfig as KDF) | HIGH → TP HIGH | 4.2 | High | hardcoded chain 정량 입증 |
| 1B | ucl1-1 (UnCrackable AES) | HIGH → TP HIGH | 4.2 | High | 외부 GT 베이스라인 매칭 |
| 2 | vc-3/4 (caller-controlled perm) | HIGH → **FP** | 3.7 | n/a | multi-stage 검증의 효과 |
| 3 | ssl-6 (gRPC plaintext) | MEDIUM → TP HIGH (격상) | 5.1 | High | Stage 3 격상 사례 |
| 4 | lmp-1 (PromptsContentProvider) | HIGH → TP HIGH | 3.7 | High | IVI/LLM 도메인 특화 |
| 5 | vc-6 (macAddress untrusted) | MEDIUM → TP HIGH (격상) | 3.7 | **Critical** | 차량 안전 직결 |

5건은 초기 계획서의 5개 사례 카테고리에 정확히 매핑되며, 모두 본 파이프라인이
실제로 자동 탐지/검증한 라벨에서만 발췌 — 가짜 수치 없음.

## 재현 path

각 사례는 `data/ground_truth/combined_labels.json`의 라벨 + 본 GT가 가리키는
`data/decompiled/<apk>/sources/<class>` 의 line으로 추적 가능. 외부 corpus
(UnCrackable Level1)는 `data/apks/_mastg/owasp-mastg/Samples/Android/.../` 경로.
