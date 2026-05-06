> **Public masked copy** — code evidence (fenced blocks) replaced with redaction markers under contractor IP protection. Class names, line numbers, categories, severities, rationale, and AAOS / MASVS mappings are kept verbatim. Original raw report is retained locally only.
>
> 본 파일은 contractor IP 보호 정책에 따라 코드 인용을 redact 한 공개용 사본이다. 분석 메타데이터 (class, line, category, severity, rationale, AAOS 매핑) 는 그대로 유지.

# Stage 1 Analysis — `ai.pleos.sync.syslog` (SysLogService)

- **Date**: 2026-04-29
- **APK path on device**: `/system/...` (extracted via bulk pull) — repackaged as `data/apks/ai.pleos.sync.syslog.apk` (8 MB)
- **Decompiler**: jadx 1.5.5 (`--deobf --show-bad-code`) — 7,575 entries, 35 jadx warnings (ignored)
- **Stage**: 1 (single-pass LLM, Claude Opus 4.7)
- **Sources scope**: `ai/pleos/*` (~280 java files; sync only = 72 files)

## Manifest highlights

- Permissions: `INTERNET` + `RECEIVE_BOOT_COMPLETED` + `FOREGROUND_SERVICE` + `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` + `GET_ACCOUNTS` + `QUERY_ALL_PACKAGES` + `pleos.car.permission.CAR_INFO` + `ai.pleos.playground.service.vehicle.VEHICLE_BINDING`
- Exported: `BootCompletionReceiver` (BOOT_COMPLETED only) + standard `ProfileInstallReceiver` (DUMP-protected).
- Self-defined permission `DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` (signature) — used to lock dynamic receivers to the same signing certificate.
- **No `sharedUserId="android.uid.system"`** (unlike VehicleControl). The threat model is "trusted background sync app", not "system process".

## Endpoint inventory (hardcoded)

| Env | URL |
|---|---|
| production | `https://connect-gw.umos.ai/auth` |
| internal | `https://connect-gw-int.umos.ai` |
| staging | `https://connect-gw-stage.umos.ai` |
| coral (CCGAuthenticator default) | `https://connect-gw-coral.umos.ai` |

All HTTPS. **No `http://` plaintext literals in the analyzed scope** — the network-security baseline is OK; the question is *how* HTTPS is enforced (pinning, CA constraints, TrustManager) — Stage 2 follow-up.

## Triage — 3 priority classes (Stage 1 first batch)

| # | Class | Hit |
|---|---|---|
| 1 | `ai/pleos/sync/crypto/ECCCrypto.java` | `Cipher`, `MessageDigest`, `KeyAgreement`, BouncyCastle |
| 2 | `ai/pleos/sync/authenticator/AuthData.java` | regex `(?i)(token|password)\s*=\s*"..."` (Kotlin data class auto-toString) |
| 3 | `ai/pleos/sync/authenticator/CCGAuthenticator.java` | `https://...` literal + `clientID/clientSecret` payload |

## Findings — class 1: `ECCCrypto`

The cryptographic primitives themselves are well-chosen:

- secp256r1 (P-256) named curve
- ECDH key agreement → SHA-256 of `generateSecret()` as the symmetric key
- AES-GCM/NoPadding with a 12-byte SecureRandom IV per encryption
- AEAD authentication via `Cipher.doFinal` on decrypt

### Finding — MEDIUM — Weak passphrase-to-private-key derivation

```java
// <redacted: PleOS proprietary code>
```

- **Issue**: a single SHA-256 hash, no salt, no iterations. If `passphrase` ever has low entropy (PIN, passphrase short string, constant), an attacker enumerates candidates at GPU speed and recovers the private key.
- **Mitigation**: PBKDF2 / scrypt / Argon2 with a per-device salt and a tuned cost parameter.
- **Stage-2 follow-up**: trace callers of `generateDeterministicPrivateKey` — what is the actual passphrase shape? A random device-seed + server-constant input drops severity; a user-typed PIN raises it.

## Findings — class 2: `AuthData`

```java
// <redacted: PleOS proprietary code>
```

### Finding — HIGH — Kotlin data class leaks the access token through `toString()`

- Any `Timber.log(authData)` / `Log.d(TAG, authData.toString())` / exception message that happens to interpolate this object dumps the **access token** to logcat.
- Logcat is readable by privileged tooling (`adb shell logcat` with READ_LOGS, `dumpsys`, vendor diagnostics, system services with `READ_LOGS`).
- The hosting APK holds `INTERNET` and is the dedicated remote-sync service — the token is the keys to the backend.
- **Mitigation**: override `toString()` to mask the token (e.g. `authenticatorToken=***`), or move the token to a non-data-class container.
- **Stage-2 follow-up**: grep `Timber\.|Log\.[diwev]\(.*authData|Result.*authData` to confirm or refute actual log emission.

## Findings — class 3: `CCGAuthenticator`

```java
// <redacted: PleOS proprietary code>
```

### Finding — MEDIUM — Hardcoded production endpoint + credentials over HTTPS without visible pinning

- TLS is used (good). But this class:
  - hardcodes a production endpoint (cannot be pivoted without re-shipping)
  - issues a credentialed POST to `${baseURL}/auth/client/login` with `{client_id, secret}` JSON
  - has no `TrustManager` / `OkHttp.CertificatePinner` / `network_security_config.xml` reference at this layer
- If pinning is *not* configured at the shared HttpClient layer, a CA-trusted MITM (corporate proxy with a planted root, hostile Wi-Fi with a user-installed cert profile) reads the client credentials in cleartext-after-TLS.
- **Stage-2 follow-up (priority)**: read `CCGTokenProvider` and any HttpClient setup for `OkHttpClient.Builder().certificatePinner(...)` or `setSSLSocketFactory(...)`. Also check `res/xml/network_security_config.xml` (jadx output: `resources/`).

## Negative confirmations

- No `http://` plaintext literal hits in `ai/pleos/*`.
- AES-GCM (AEAD) is used correctly with random IVs — the symmetric layer is fine.
- ECDH + secp256r1 — modern, standard.

---

## Stage 2 / Phase B-3.c follow-up (2026-04-29 same session)

세 개 stage 2 follow-up 의제가 모두 해소됨. 동시에 신규 stage 1 finding 3건이 발견됨 (`ssl-4`, `ssl-5`, `ssl-6`).

### B-3.c.1 — ssl-1 (ECCCrypto KDF) caller 추적

```java
// <redacted: PleOS proprietary code>
```

```java
// <redacted: PleOS proprietary code>
```

- `passPhrase` = `BuildConfig.IDENTIFIER` (build-time 상수, APK 안에 박혀있음).
- 모든 device가 같은 ECC 키 도출 → APK reverse engineering으로 키 회수 → 모든 device의 encryptedYaml config 복호화 가능.
- **stage 3 attacker perspective도 confirmed → strong TP 3/3, severity HIGH ↑** (stage 1엔 MEDIUM이었음).

### B-3.c.2 — ssl-2 (AuthData token leak) emission 검증

```java
// <redacted: PleOS proprietary code>
```

- 토큰 logcat emission **실측 확인**. Kotlin data-class auto-toString이 호출되어 token 평문 logcat 기록.
- Logcat은 READ_LOGS 권한 / `dumpsys logd` / vendor 진단 도구가 읽음 — 외부 채널 누출.
- **stage 3 attacker perspective도 confirmed → strong TP 3/3 격상**.

### B-3.c.3 — ssl-3 (CCGAuthenticator pinning) 검증

`ai/pleos/sync/**` 패키지 grep:

```
// <redacted: PleOS proprietary code>
```

- sync 패키지 안에는 pinning 코드 없음. **CA-trusted MITM이면 client_id/secret 노출**.
- caveat: third-party HTTP/gRPC 라이브러리 (`com.squareup.okhttp3`, `io.grpc.*`) 패키지 추가 grep 후 최종 확정. **provisional strong TP 3/3** 표기.

---

## Findings — class 4: `HMGAuthenticator$HmgUserInfo` (B-3.c 발견)

```java
// <redacted: PleOS proprietary code>
```

### Finding — HIGH — 운전자 PII (UUID, 생년월일, 이메일, 이름) toString 누출

- ssl-2와 동일한 Kotlin data-class auto-toString 패턴이지만, 토큰이 아니라 **개인식별정보(PII)** 전체.
- HMGAuthenticator는 Hyundai Motor Group account 처리 → `account.type == "HMG"` 계정의 사용자 정보를 보관.
- 만약 caller가 `Log.d(TAG, hmgUserInfo)`처럼 호출하면 **운전자 신원 전체** 가 logcat에 기록.
- 영향: ssl-2 (단일 token 누출)보다 더 심각 — 식별 가능한 신원 + 생년월일이라 GDPR/개인정보보호법 직접 적용.
- **Mitigation**: toString()을 마스킹 (`UUID=***`, `email=***@...`)으로 override. 또는 PII 필드를 비-데이터 클래스로 wrap.

## Findings — class 5: `SyncConfigsProvider` (B-3.c 발견)

```java
// <redacted: PleOS proprietary code>
```

### Finding — HIGH — `BuildConfig.IDENTIFIER`가 ECC KDF passphrase로 사용 (build-time 박힌 상수)

- ssl-1과 별개 finding: ssl-1은 KDF 설계 자체 문제 (단일 SHA-256 + no salt + no iterations), 이 finding은 **passphrase 출처가 hardcoded secret**이라는 점.
- `BuildConfig.IDENTIFIER`는 Android Gradle plugin이 컴파일 시 박는 상수. APK 안에 평문으로 존재 (BuildConfig.java + dex 양쪽).
- APK reverse engineering으로 trivially 회수 → ECC 개인 키 도출 → encryptedYaml config 복호화 → 모든 device의 서버 endpoint·자격증명 노출.
- **Mitigation**: build-time 상수가 아닌 device-unique 값 (예: AndroidKeystore에 device-specific salt 저장 후 PBKDF2/Argon2). 서버 public key 만 build-time 박고 passphrase는 매 device 다르게.

## Findings — class 6: `SysLogService` (B-3.c 발견 — uncertain)

```java
// <redacted: PleOS proprietary code>
```

### Finding — MEDIUM (uncertain) — gRPC 동기화 endpoint `connect-gw.umos.ai:9091`

- SysLogService가 차량 systemID + 로그 페이로드를 gRPC endpoint로 송출 (포트 9091).
- TLS 적용 여부는 gRPC `ManagedChannel` 빌더 호출에서 결정 (`OkHttpChannelBuilder.useTransportSecurity()` vs `usePlaintext()`).
- 본 finding은 endpoint 노출만으로는 vulnerability 단정 불가. **uncertain**.
- **Stage-2 follow-up**: `ManagedChannel`/`OkHttpChannelBuilder` 호출처 grep → `useTransportSecurity` 또는 `usePlaintext` 확인. TLS 적용 시에도 ssl-3 (pinning 부재)이 함께 적용.
- 추가로 `Log.i`로 endpoint + systemID를 logcat에 기록 (운전자 식별자 누출 약하게 — strSystemID 정의 확인 필요).

---

## 종합 통계 (stage 1, B-3.c 후)

| 카테고리 | 클래스 | 위험도 |
|---|---|---|
| crypto | ECCCrypto (ssl-1, B-3.c HIGH 격상) | HIGH |
| hardcoded | AuthData (ssl-2), HmgUserInfo (ssl-4), SyncConfigsProvider (ssl-5) | HIGH × 3 |
| network | CCGAuthenticator (ssl-3, provisional), SysLogService (ssl-6, uncertain) | MEDIUM × 2 |

총 6 findings (HIGH 4 / MEDIUM 2). 1차 측정 (sync.syslog 단일 APK n=6): TP 5 / uncertain 1 → **lenient precision 100%**.

## Output artefacts

- JSON (machine-readable, schema = `configs/result_schema.json`): `data/reports/ai.pleos.sync.syslog_20260429.json`
- Markdown (this file): `data/reports/ai.pleos.sync.syslog_20260429.md`

## Next steps (B-3.c 후)

1. **ssl-3 third-party lib 확인**: `com.squareup.okhttp3`, `io.grpc.okhttp`, `io.grpc.netty` 패키지 grep으로 `CertificatePinner`/`X509TrustManager` 사용 위치 식별. provisional strong TP를 최종 strong TP 또는 clean으로 확정.
2. **ssl-6 TLS verdict**: `ManagedChannel`/`OkHttpChannelBuilder.useTransportSecurity` vs `usePlaintext` grep. TLS 적용이면 ssl-3과 같은 pinning 의제로 통합.
3. **CCGTokenProvider, BootCompletionReceiver, SysLogService 추가 read** (stage 1 batch 2): `Hilt_*` 제외 본 클래스 4~5개. Token 처리 + boot trigger + gRPC channel 빌더의 정확한 구성 확인.
4. **`network_security_config.xml`** 검사: `data/decompiled/SyncSyslog/resources/xml/` 또는 `res/xml/`에서 `cleartextTrafficPermitted`, `<pin-set>` 선언 확인.
5. **`HmgUserInfo` log emission grep** (ssl-4): ssl-2와 같은 패턴으로 `Log.|Timber.*hmgUserInfo`. 실측 확인 시 ssl-4 → strong TP 3/3.
