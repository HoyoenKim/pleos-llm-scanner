# 프로젝트 이해용 최종 요약 보고서

_작성일: 2026-05-14 / 대상: 교수·평가자 / 기준: `docs/01_final_report.md` v1.4 supplement + local result artifacts_

## 1. 한 문장 결론

LLM을 단독 취약점 탐지기로 쓰기보다, `jadx` 기반 정적 분석·키워드 triage·caller/manifest 검증 규칙 사이의 **reasoning component**로 배치하면 IVI APK 보안 점검에서 실용적인 정적 분석 파이프라인을 만들 수 있었다.

최종 combined GT `n=47` 기준 1차 탐지는 모든 실제 취약점을 넓게 잡았고(Recall 100.0%), 3차 다중 시각 합의는 오탐 9건을 모두 제거해 Precision 100.0%, Recall 97.4%, F1 98.7%를 달성했다. Stage 1 대비 Stage 3 개선은 McNemar exact test `p=0.0215`로 통계적으로 유의했다.

## 2. 연구 배경

PleOS는 Android Automotive 계열 IVI 플랫폼이다. IVI 앱은 차량 제어, 사용자 계정, 위치, 음성/메시지, OTA 업데이트와 연결되어 있어 일반 모바일 앱보다 보안 영향이 크다. 동시에 APK 수가 많고 Java/Kotlin 코드량이 크기 때문에 수동 jadx 분석만으로는 반복 점검이 어렵다.

본 연구의 핵심 질문은 다음과 같다.

> 자동차 IVI APK 보안 점검에서 LLM을 black-box detector가 아니라 deterministic triage와 도메인 검증 규칙 사이의 reasoning component로 사용하면, 재현 가능한 정적 분석 파이프라인을 만들 수 있는가?

### 2.1 연구 질문별 답변

| RQ | 질문 | 답변 |
|---|---|---|
| RQ1 | Stage 1 → Stage 2/3 multi-stage 검증이 실제로 오탐을 줄이는가? | **그렇다.** Stage 1은 Recall 100.0%로 실제 취약점 38건을 모두 후보로 잡았고, Stage 3 `>=2/3` consensus는 FP 9건을 모두 제거해 Precision 100.0%, Recall 97.4%, F1 98.7%를 달성했다. paired McNemar exact test도 `p=0.0215`로 Stage 1 대비 개선이 통계적으로 유의했다. |
| RQ2 | multi-perspective consensus와 Codex multi-model cross-read 중 무엇이 더 강한 근거인가? | **현재 산출물 기준으로는 Claude Code multi-perspective Stage 3가 더 강했다.** Codex 2/3 consensus는 Precision 100.0%를 유지했지만 Recall 76.3%, F1 86.6%로 낮았다. 결론은 모델 수 자체보다 prompt calibration과 evidence packaging이 중요하다는 것이다. |
| RQ3 | Java/Kotlin static pipeline의 blind spot은 어느 정도이며 native 분석은 무엇을 보였는가? | PleOS Connect 207 APK 중 native library 보유 APK는 22개(10.6%)였고, PleOS 자체 패키지로 좁히면 14/28(50.0%)였다. native sample `n=4` 정적 분석에서는 추가 native-bound 취약점 0건이었지만, Go runtime/JNI/syscall 흐름은 static-only 한계로 남아 Frida/Ghidra 후속이 필요하다. |
| RQ4 | 이 결과가 hand-crafted sample 밖에서도 일반화되는가? | **부분적으로만 그렇다.** NewPipe real-world deobfuscation/plausibility sample `n=6`에서 GOOD+ 67%를 얻어 hand-crafted corpus의 100% exact match가 upper bound임을 확인했다. 따라서 실제 적용에서는 Stage 0 deobfuscation, ProGuard-heavy APK, manifest-only scan을 별도 한계로 다뤄야 한다. |
| RQ5 | 정적 finding이 emulator runtime PoC primitive로 이어지는가? | **일부는 그렇다.** `navi-1`은 same-device 앱이 no-permission `NaviService` Binder를 통해 Maps route preview를 만들 수 있어 L3 user-visible route UI injection으로 확인되었다. `vs-1`은 custom `normal` permission으로 보호된 `VehicleService`에 bind해 reversible `MIRROR_FOLD` property를 `before=false → set=true → after=true → restore=false`로 바꿔 V3 property mutation으로 확인되었다. 다만 이것은 full vehicle takeover나 실차 주행 제어 증명이 아니다. |

환경 제약은 명확했다. 로컬 GPU가 없고 외부 유료 API를 분석 자동화 코드에 넣지 않았으며, Java/Kotlin APK 분석은 `jadx`를 기준 도구로 사용했다. LLM 판정은 Codex/Claude Code 세션 안에서 수행했고, 스크립트는 디컴파일, 키워드 추출, 평가, 리포트 생성 같은 결정론적 작업에 한정했다.

## 3. 분석 파이프라인

| 단계 | 역할 | 구현/판정 방식 |
|---|---|---|
| Stage 0 | 난독화 전처리 | class/method entropy와 jadx naming pattern으로 난독화 수준 측정. 고난독화 클래스는 LLM 이름 복원 후보로 분리 |
| Stage 1 | 1차 탐지 | 보안 키워드와 LLM 판정으로 `network`, `permission`, `intent`, `crypto`, `hardcoded`, `reflection_dynamic` finding 후보 생성 |
| Stage 2 | 규칙 검증 | manifest exported/permission, protected broadcast, caller chain, Compose Nav route, `setPackage`/`setComponent` 같은 blocking control 확인 |
| Stage 3 | 다중 시각 합의 | 동일 Claude Code 모델을 공격자/방어자/IVI 도메인 전문가 시각으로 재판정. `>=2/3 report`만 최종 보고 유지 |

이 구조의 의도는 LLM이 “모든 것을 맞히는 탐지기”가 아니라, 정적 근거를 읽고 보안 의미를 판단하는 reasoning layer가 되도록 하는 것이다. 오탐 제거는 Stage 2의 결정론적 blocking-control 확인과 Stage 3의 합의 규칙이 담당했다.

## 4. 데이터셋과 라벨

최종 평가는 combined GT `n=47` finding으로 구성했다.

| Origin | n | TP | FP | Precision | 의미 |
|---|---:|---:|---:|---:|---|
| PleOS-customized (`ai.umos.*`, `ai.pleos.*`) | 30 | 23 | 7 | 76.7% | 실제 적용 대상. 사용자/차량/계정/음성 앱의 취약 패턴과 오탐을 함께 포함 |
| OWASP MASTG | 4 | 4 | 0 | 100.0% | 외부 공개 GT. hardcoded key, crypto, SSL pinning sample |
| InsecureBankv2 | 9 | 9 | 0 | 100.0% | 의도적으로 취약한 Android benchmark |
| AOSP-derived | 4 | 2 | 2 | 50.0% | OS/framework-level mitigation이 많아 Stage 1 오탐이 자주 발생 |
| **Total** | **47** | **38** | **9** | **80.9%** | Stage 1 기준 combined GT |

카테고리 분포는 `intent` 18, `hardcoded` 11, `network` 9, `crypto` 5, `permission` 3, `reflection_dynamic` 1이다. 오탐은 주로 `intent`, `network`, `permission`에서 발생했고, 이는 manifest/caller-chain 같은 Android framework-level blocking control을 Stage 2에서 봐야 하기 때문이다.

## 5. 핵심 정량 결과

### 5.1 Stage 1 vs Stage 3

| System | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage 1 initial detection | 38 | 9 | 0 | 0 | 80.9% | 100.0% | 89.4% |
| Stage 3 `>=2/3` consensus | 37 | 0 | 9 | 1 | 100.0% | 97.4% | 98.7% |

Stage 1은 실제 취약점 38건을 모두 잡았지만 오탐 9건도 함께 보고했다. Stage 3는 오탐 9건을 모두 제거했고, 실제 취약점 1건만 보수적으로 누락했다. 따라서 최종 보고용 판단 기준은 Stage 3 `>=2/3` consensus가 가장 강하다.

### 5.2 Bootstrap CI

`n=47` 기준 Stage 1 precision의 bootstrap 95% CI는 `[70.2%, 91.5%]`, F1의 95% CI는 `[82.5%, 95.6%]`이다. 초기 `n=19` 대비 precision CI 폭은 36.8%p에서 21.3%p로 줄었다. 표본 확장이 단순히 point metric을 올린 것이 아니라, 측정 불확실성을 줄였다는 점이 중요하다.

### 5.3 McNemar paired test

Stage 1과 Stage 3의 같은 finding에 대한 paired correctness를 비교했다.

| Cell | Count | 의미 |
|---|---:|---|
| a | 37 | Stage 1과 Stage 3 모두 정답 |
| b | 1 | Stage 1은 정답, Stage 3는 오답 |
| c | 9 | Stage 1은 오답, Stage 3는 정답 |
| d | 0 | 둘 다 오답 |

`b+c=10`, exact binomial two-tailed `p=0.0215`이다. 즉 Stage 3가 Stage 1 대비 오탐을 줄인 효과는 우연으로 보기 어렵다.

## 6. 대표 사례

### 6.1 실제 취약점으로 유지된 사례

| ID | APK | 근거와 흐름 | 왜 보고 유지인가 | 최종 의미 |
|---|---|---|---|---|
| `amb-1` | `ai.umos.ambientai` | `LlmHandler` production call path에서 외부 LLM API 호출에 쓰이는 `sk-...` 형태 key가 APK 안에 포함되어 있었다. 같은 APK에는 microphone/SMS/contact 계열 PII와 LLM SDK 사용 흔적도 함께 있어 단순 test artifact로 보기 어렵다. | APK reverse만으로 credential prefix와 사용 위치를 확인할 수 있고, release-shipped test handler(`amb-2`)에도 같은 계열 key가 반복되어 있었다. Stage 3에서도 3/3 strong TP로 유지되었다. | 외부 LLM API credential 탈취, billing abuse, 사용자 음성/메시지/연락처 맥락의 privacy risk. full secret literal은 보고서에서 redaction 유지. |
| `am-3` | `ai.umos.appmarket` | AppMarket APK 내부 Bundle/constant path에 HMG OAuth `client_id`와 `client_secret`이 함께 존재했다. 별도 account APK의 SSO flow(`acc-4`)와 동일 credential domain으로 이어지는 cross-APK 패턴이다. | 단일 문자열 노출이 아니라 appmarket/account 사이에 같은 OAuth secret 취급 방식이 반복되어 systematic hardcoded credential pattern으로 판단했다. Stage 3 3/3 strong TP, Codex cross-read에서도 report 유지. | 한 APK 유출이 다른 PleOS-customized credential domain까지 확장될 수 있는 global client identity leak. 서버 측 client secret rotation과 APK 내 secret 제거 필요. |
| `acc-4` | `ai.pleos.playground.account` | `SsoActivity`가 exported 상태에서 `user-client-secret`을 Intent extra로 수신한다. SSO/OAuth 흐름의 민감 값이 Activity boundary를 통해 전달되는 구조다. | Intent extra는 crash dump, logcat, dumpsys, instrumentation, 악성 same-device app 관찰면에 노출될 수 있다. Codex 보충 실험에서는 보수적으로 suppress되었지만, baseline Stage 3에서는 account/auth APK의 민감 flow로 TP 유지했다. | KeyStore-bound secret 저장, signature permission, explicit trusted caller, in-process/bound service channel 같은 보호가 필요하다. |
| `ssl-6` | `ai.pleos.sync.syslog` | `SysLogService` gRPC channel 생성부에서 `.usePlaintext()`가 확인되었다. 송신 대상은 logcat/syslog proxy 계열이며 차량/systemID/진단 로그가 경로에 포함될 수 있다. | 단순 HTTP 문자열이 아니라 gRPC transport builder에서 TLS off가 명시된 케이스다. Stage 1 MEDIUM에서 Stage 3 HIGH로 격상되었고 3/3 strong TP였다. | 차량/시스템 로그 전송 경로의 confidentiality/integrity risk. TLS/ALPN, channel credential, 인증서 pinning 또는 prod/dev endpoint 분리가 필요하다. |
| `lmp-1` | `ai.pleos.llm.model.provider` | `PromptsContentProvider`가 exported 상태이며 permission gate 없이 LLM system prompt/corpus query를 반환하는 구조로 확인되었다. | IVI LLM의 system prompt, guardrail, 내부 schema가 외부 앱에 읽히면 jailbreak prompt 설계나 prompt injection 준비 자료가 된다. Stage 3 3/3 strong TP로 유지되었다. | 일반 Android 정보 노출을 넘어 IVI LLM prompt/corpus disclosure risk다. provider 비공개화 또는 signature-level read permission이 필요하다. |
| `vc-6` | `ai.umos.vehiclecontrol` | `VehicleBroadcastReceiver`가 exported receiver로 동작하며 intent extra의 `macAddress`를 충분히 검증하지 않고 차량/Bluetooth 관련 저장·처리 흐름에 연결한다. | 외부 sender가 MAC-like payload를 주입하면 pairing 대상 또는 차량 제어 보조 데이터가 오염될 수 있다. 차량 제어 자산과 연결되므로 TARA에서 Severe impact × High feasibility로 Critical concern이다. | vehicle-control spoofing/tampering risk. receiver internal-only, caller signature permission, MAC format 검증, trusted sender whitelist가 필요하다. |

위 finding들은 “바로 차량 탈취 exploit”이라기보다, APK reverse와 Android IPC misuse로 이어지는 보안 취약점 또는 보안 약점이다. TARA 관점에서는 credential leakage, information disclosure, spoofing, tampering, transport security risk로 해석된다.

### 6.2 상세 Case Study

아래 6개 사례는 최종 발표에서 “실제 취약점으로 유지된 대표 사례”로 사용할 수 있는 수준으로 상세화한 것이다. 모든 사례는 full secret literal이나 내부 원문 payload 전체값을 노출하지 않고, 평가자가 재검토할 수 있는 evidence type과 보안 판단 흐름만 남긴다.

아래 코드 블록은 실제 `jadx --deobf` 디컴파일 결과에서 필요한 줄만 축약한 것이다. 난독화 상태는 APK마다 달랐다. AmbientAI, SysLog, LLMModelProvider, VehicleControl은 의미 있는 package/class name이 상당 부분 남아 있었고, AppMarket/Account는 R8 synthetic class와 난독화된 field name이 섞여 있었다. 그래도 Android API, manifest component, Intent extra key, `Bundle.putString`, gRPC builder 같은 보안 판단에 필요한 구조는 복원되었다. Kotlin/R8 decompile artifact 때문에 synthetic class name이나 `Intrinsics` 호출이 보일 수 있으며, credential literal과 내부 payload 값은 모두 redaction했다.

#### Case 1. `amb-1` — AmbientAI production LLM API key hardcoding

| 항목 | 내용 |
|---|---|
| Finding ID | `amb-1` |
| APK | `ai.umos.ambientai` |
| 주요 컴포넌트 | `LlmHandler` production LLM call path |
| 카테고리 | `hardcoded` / credential exposure |
| Stage verdict | Stage 3 strong TP, 3/3 합의 |
| 핵심 자산 | 외부 LLM API credential, 사용자 음성/메시지/연락처 맥락 |
| 주요 위협 | Information Disclosure, credential theft, billing abuse, privacy exposure |

**발견 경로.**
Stage 1에서 `sk-` 계열 API key 패턴과 LLM SDK import/call-site를 함께 탐지했다. 단순히 “문자열 하나가 보인다”가 아니라, production LLM call path 안에서 외부 LLM API 호출에 사용되는 key prefix가 확인되었고, 같은 APK 안에서 microphone, SMS, contact 계열 PII 권한/데이터 흐름과 LLM SDK 사용 흔적이 같이 관찰되었다. 이 조합 때문에 테스트용 더미 문자열로 보기 어렵다.

**근거 패키지.**

- `LlmHandler`의 production call path에서 외부 LLM API 호출에 사용되는 `sk-...` 형태 credential prefix가 확인됨.
- release-shipped test handler 성격의 `amb-2`에서도 같은 계열 key가 반복되어, 단일 오타나 dead string이 아니라 APK 빌드 산출물에 credential이 들어간 패턴으로 판단됨.
- AmbientAI 앱의 기능 맥락상 음성 비서/LLM 호출과 사용자 입력 데이터가 결합될 가능성이 있어, 단순 API key leakage보다 privacy/billing impact가 커짐.

**디컴파일 근거.**

```java
// data/_local/decompiled/ai.umos.ambientai/.../LlmHandler.java
static {
    Duration.Companion companion = Duration.INSTANCE;
    openAI = OpenAIKt.OpenAI$default(
        "sk-<REDACTED>",
        null,
        new Timeout(null, null,
            Duration.m9178boximpl(DurationKt.toDuration(60, DurationUnit.SECONDS)),
            3,
            null),
        null, null, null, null, null, null, 506, null);
    client = HttpClientKt.HttpClient(CIO.INSTANCE, ...);
}
```

이 evidence의 핵심은 `sk-...` 문자열 자체보다 위치다. key prefix가 단순 resource string이 아니라 `OpenAI` client 초기화 지점에 들어가 있어, 실제 외부 LLM 호출을 위한 credential handling 문제로 해석했다.

**왜 보고 유지했는가.**
Stage 3의 attacker, defender, domain expert 시각이 모두 report로 판정했다. defender 관점에서도 key prefix, 사용 위치, SDK call path, release build 포함 정황이 함께 있어 “false positive 가능성”보다 “credential handling failure” 가능성이 높다고 보았다. 특히 같은 APK의 test handler에도 같은 계열 key가 남아 있어, “사용되지 않는 문자열”이라는 방어 논리를 약화시켰다.

**위험 시나리오.**
공격자는 APK reverse만으로 key prefix와 사용 위치를 확인할 수 있다. full key가 그대로 존재하면 외부 LLM API 호출 비용을 발생시키거나, 앱이 사용하는 모델/프로젝트 credential domain을 추정할 수 있다. 더 큰 문제는 AmbientAI가 음성/메시지/연락처 맥락의 앱이라는 점이다. credential 노출이 곧바로 개인정보 유출을 의미하지는 않더라도, 외부 LLM 호출 경로와 사용자 데이터 처리 경로가 한 앱 안에 결합되어 있다는 사실은 privacy review와 data-flow audit이 필요한 신호다.

**권장 조치.**

- APK에 외부 API key를 포함하지 않는다. backend token broker 또는 short-lived scoped token을 사용한다.
- 이미 배포된 key는 즉시 revoke/rotate하고, billing anomaly와 API usage log를 확인한다.
- release build에서 test handler와 test credential이 포함되지 않도록 build flavor와 shrink rule을 분리한다.
- LLM call path에 PII minimization, explicit user consent, request logging redaction을 적용한다.

**잔여 한계.**
본 보고서는 full secret literal을 의도적으로 쓰지 않았다. 따라서 이 case study는 “credential 값 자체의 유효성 검증”이 아니라 “APK 안에 production call path와 credential prefix가 함께 존재했다”는 정적 근거에 기반한다. 실제 abuse 가능성은 server-side revocation 상태와 API provider log로 최종 확인해야 한다.

#### Case 2. `am-3` — AppMarket HMG OAuth client secret cross-APK exposure

| 항목 | 내용 |
|---|---|
| Finding ID | `am-3` |
| APK | `ai.umos.appmarket` |
| 주요 컴포넌트 | AppMarket OAuth/client configuration path |
| 카테고리 | `hardcoded` / OAuth credential exposure |
| Stage verdict | Stage 3 strong TP, 3/3 합의. Codex cross-read에서도 report 유지 |
| 핵심 자산 | HMG OAuth client identity, appmarket/account credential domain |
| 주요 위협 | Credential leakage, identity misuse, cross-APK secret reuse |

**발견 경로.**
AppMarket APK 내부 Bundle/constant path에서 OAuth `client_id`와 `client_secret`이 함께 확인되었다. 이 자체만으로도 Android client에 secret을 박아 넣은 문제가 되지만, 더 중요한 점은 별도 `ai.pleos.playground.account` APK의 SSO flow(`acc-4`)와 같은 credential domain으로 이어진다는 것이다.

**근거 패키지.**

- AppMarket APK 내부에 OAuth client identifier와 secret이 함께 존재함.
- Account APK의 SSO flow에서도 유사한 secret 전달/취급 구조가 관찰됨.
- 두 APK가 PleOS-customized application tier에 속하며, 계정/앱마켓이라는 인증·배포 경계에 함께 연결됨.

**디컴파일 근거.**

```java
// data/_local/decompiled/ai.umos.appmarket/.../AppMarketActivity.java
Bundle bundle = new Bundle();
bundle.putString("user-client-id", "<REDACTED_CLIENT_ID>");
bundle.putString("user-client-secret", "<REDACTED_CLIENT_SECRET>");
bundle.putString("user-client-name", "hmg-kr-42dot-appmarket");

AccountManager accountManager = AccountManager.get(this);
Account[] accountsByType = accountManager.getAccountsByType("HMG");
...
accountManager.addAccount(
    "HMG",
    "ai.pleos.playground.account.authentication.qr",
    null,
    bundle,
    null,
    ...);
```

동일한 `user-client-id` / `user-client-secret` / `user-client-name` bundle tuple은 `AppMarketActivity`뿐 아니라 AppMarket의 interceptor, auth view model, terms flow, clear-token flow에서도 반복된다. 따라서 한 곳의 우연한 literal이 아니라 account/appmarket 인증 흐름에 걸친 반복 패턴으로 보았다.

**왜 보고 유지했는가.**
단일 hardcoded 문자열은 때때로 dev/staging artifact나 non-secret identifier일 수 있다. 그러나 `am-3`은 `client_id`와 `client_secret`이 함께 존재하고, 별도 account APK의 SSO flow와 연결되는 cross-APK 패턴을 보였다. 따라서 Stage 3는 이를 systematic hardcoded credential pattern으로 판단했다. Codex multi-model 보충 실험에서도 이 항목은 report로 유지되어, 모델 provenance가 달라도 위험 판단이 크게 흔들리지 않았다.

**위험 시나리오.**
한 APK의 reverse로 얻은 OAuth client secret이 같은 credential domain의 다른 PleOS-customized 앱 흐름을 이해하거나 모방하는 실마리가 될 수 있다. 특히 앱마켓은 앱 배포, 추천, 업데이트, 계정 세션과 연결될 수 있어 client identity가 노출되면 서버 측 trust boundary가 약해진다. 이 secret이 public client용 placeholder가 아니라 confidential client secret이면, 모바일 앱에 포함된 순간 보안 속성을 상실한다.

**권장 조치.**

- 모바일 APK에 confidential OAuth client secret을 포함하지 않는다.
- OAuth flow를 PKCE 기반 public client 모델로 전환하거나, backend-mediated exchange로 분리한다.
- account/appmarket 사이의 credential reuse 여부를 점검하고, 동일 secret domain이면 server-side rotation을 수행한다.
- crash/log/dumpsys에 client secret이 재노출되지 않는지 별도 검사한다.

**잔여 한계.**
정적 분석은 secret의 server-side 권한 범위와 현재 유효성을 알 수 없다. 따라서 최종 severity는 OAuth server 설정, scope, rotation 상태, token exchange policy를 함께 확인해야 한다. 그럼에도 APK 내부에 `client_secret` 성격의 값이 존재하는 것 자체는 release artifact hygiene 관점에서 보고 가치가 충분하다.

#### Case 3. `acc-4` — Exported SSO Activity receiving `user-client-secret` through Intent extras

| 항목 | 내용 |
|---|---|
| Finding ID | `acc-4` |
| APK | `ai.pleos.playground.account` |
| 주요 컴포넌트 | `SsoActivity` |
| 카테고리 | `intent` / sensitive data across Activity boundary |
| Stage verdict | Claude Code Stage 3 baseline에서 TP 유지. Codex 보충 실험에서는 보수적 suppress |
| 핵심 자산 | SSO/OAuth secret, account session context |
| 주요 위협 | Intent exposure, local observation surface, credential misuse |

**발견 경로.**
Account/Auth APK의 priority class 분석에서 `SsoActivity`가 exported 상태이며, `user-client-secret` 성격의 값을 Intent extra로 수신하는 구조가 확인되었다. 이는 secret이 단순 내부 변수에 머무르지 않고 Android component boundary를 통과한다는 의미다.

**근거 패키지.**

- `SsoActivity`가 외부에서 도달 가능한 component boundary에 놓여 있음.
- `user-client-secret`이라는 명명과 SSO/OAuth 맥락이 결합되어 민감 값으로 분류됨.
- `am-3`의 AppMarket OAuth secret 노출과 함께, PleOS-customized account/appmarket credential handling이 반복 패턴을 보임.

**디컴파일 근거.**

```xml
<!-- data/_local/decompiled/ai.pleos.playground.account/resources/AndroidManifest.xml -->
<activity
    android:theme="@style/AppTheme"
    android:name="ai.pleos.playground.account.login.SsoActivity"
    android:exported="true"
    android:excludeFromRecents="true"
    android:launchMode="singleTop"/>
```

```java
// data/_local/decompiled/ai.pleos.playground.account/.../SsoActivity.java
String stringExtra = getIntent().getStringExtra("user-client-id");
...
this.f6897G = stringExtra;

String stringExtra2 = getIntent().getStringExtra("user-client-secret");
...
this.f6898H = stringExtra2;

String stringExtra3 = getIntent().getStringExtra("user-client-name");
...
this.f6899I = stringExtra3;
```

manifest에서는 `SsoActivity`가 exported이고, decompiled Java에서는 secret 성격의 extra가 Activity boundary를 통해 수신된다. 그래서 이 case는 “secret 값이 하드코딩되어 있다”보다 “민감값 전달 boundary가 부적절하다”에 가깝다.

**왜 보고 유지했는가.**
Codex 보충 실험은 이 항목을 일부 suppress했다. 이유는 “실제 외부 caller가 해당 extra를 읽거나 탈취하는 경로가 명확히 증명되었는가”에 보수적으로 반응했기 때문이다. 그러나 본 연구의 baseline Stage 3는 account/auth APK의 민감 flow와 exported Activity boundary를 더 중요하게 보았다. Intent extra는 Android에서 crash dump, logcat, instrumentation, dumpsys, same-device malicious app, accessibility/debug surface 등 여러 관찰면에 걸릴 수 있다. 따라서 민감 secret을 Activity extra로 주고받는 구조는 release artifact에서 보고할 가치가 있다고 판단했다.

**위험 시나리오.**
공격자가 곧바로 secret을 탈취한다는 뜻은 아니다. 핵심은 secret이 보호된 저장소나 in-process boundary에 머무르지 않고, Intent 기반 component boundary를 지난다는 점이다. exported component가 포함되면 caller 검증, referrer 검증, signature permission, explicit package restriction이 없을 때 외부 앱이 flow를 호출하거나 비정상 payload로 상태를 교란할 여지가 생긴다.

**권장 조치.**

- `SsoActivity`가 외부 공개가 필요 없다면 `android:exported="false"`로 제한한다.
- 외부 공개가 필요하면 signature-level permission과 explicit trusted caller 검증을 적용한다.
- secret은 Intent extra로 전달하지 않고 Android Keystore, bound service, in-process repository, backend-mediated token exchange로 이동한다.
- dumpsys/logcat/crash report에 extra 값이 포함되지 않도록 redaction rule을 적용한다.

**잔여 한계.**
이 finding은 Codex 보충 실험에서 suppress된 discordance case다. 따라서 최종 보고 시에는 “즉시 exploit confirmed”가 아니라 “민감 credential이 exported component boundary를 통과하는 insecure design”으로 표현하는 것이 정확하다.

#### Case 4. `ssl-6` — Syslog gRPC channel uses plaintext transport

| 항목 | 내용 |
|---|---|
| Finding ID | `ssl-6` |
| APK | `ai.pleos.sync.syslog` |
| 주요 컴포넌트 | `SysLogService` |
| 카테고리 | `network` / transport security |
| Stage verdict | Stage 1 MEDIUM → Stage 3 HIGH 격상, 3/3 strong TP |
| AAOS / MASVS | AAOS §5.1 Communication Security / MASVS-NETWORK-1, MASVS-NETWORK-2 |
| TARA | 진단/시스템 로그, Information Disclosure + Tampering, High risk |

**발견 경로.**
초기 네트워크 키워드 검색은 HTTP/OkHttp/Retrofit 중심이었지만, 후속 검증에서 gRPC `ManagedChannelBuilder` 계열 transport 설정을 확인했다. `SysLogService`의 channel 생성부에서 `.usePlaintext()` 호출이 확인되어 TLS가 명시적으로 꺼져 있는 케이스로 분류했다.

**근거 패키지.**

- gRPC channel builder에서 plaintext transport를 선택하는 API 호출이 확인됨.
- 송신 대상은 logcat/syslog proxy 계열로, 차량 또는 시스템 진단 로그가 이동하는 경로일 수 있음.
- Stage 2에서 위치와 사용 맥락을 재확인했고, Stage 3에서 세 시각 모두 TP로 유지했다.

**디컴파일 근거.**

```java
// data/_local/decompiled/ai.pleos.sync.syslog/.../SysLogService.java
public SysLogService() {
    ManagedChannel managedChannel =
        ManagedChannelBuilder
            .forTarget(BuildConfig.LOGCAT_PROXY_SERVER_URL)
            .usePlaintext()
            .build();

    this.managedChannel = managedChannel;
    this.logcatProxyStub =
        new LogcatProxyGrpcKt.LogcatProxyCoroutineStub(managedChannel, null, 2, null);

    this.standaloneConfigBuilder =
        Logcat.StandaloneLogcatConfig.newBuilder()
            .setServerUrl(BuildConfig.SERVER_URL)
            .setNotificationUrl(BuildConfig.NOTIFICATION_URL);
}
```

여기서는 `http://` 문자열 매칭보다 근거가 강하다. transport builder 자체가 `.usePlaintext()`를 선택하므로 TLS off가 코드 레벨에서 드러난다.

**왜 보고 유지했는가.**
단순히 `http://` 문자열이 있는 경우에는 dead config, dev endpoint, local-only endpoint일 수 있다. 반면 `ssl-6`은 transport builder의 보안 선택이 `.usePlaintext()`로 명시되어 있었다. 즉 “문자열 기반 의심”이 아니라 “TLS off API call”이다. 그래서 Stage 1의 MEDIUM network finding을 Stage 3에서 HIGH로 격상했다.

**위험 시나리오.**
차량 syslog에는 systemID, 네트워크 상태, 업데이트 이력, 진단 코드, 앱 동작 흔적이 포함될 수 있다. plaintext channel이면 같은 네트워크 경로의 관찰자 또는 중간자 위치의 공격자가 telemetry를 읽거나 변조할 가능성이 생긴다. 또한 log proxy endpoint가 빌드 설정에 고정되어 있으면 dev/prod 분리가 흐려져 운영 로그가 의도치 않은 경로로 나갈 수 있다.

**권장 조치.**

- `.usePlaintext()`를 제거하고 TLS 기반 channel credential을 사용한다.
- ALPN, certificate validation, 필요 시 certificate pinning을 명시한다.
- log proxy endpoint를 prod/dev/staging으로 분리하고 release build에서 plaintext transport가 불가능하도록 build-time guard를 둔다.
- telemetry payload에 PII 또는 token이 포함되지 않는지 별도 redaction audit을 수행한다.

**잔여 한계.**
정적 분석은 실제 runtime endpoint, 네트워크 위치, TLS termination 여부를 관찰하지 못한다. 따라서 Frida/network capture 기반 dynamic validation이 있으면 risk statement를 더 강하게 만들 수 있다. 다만 static evidence만으로도 plaintext gRPC transport 선택은 보고 가능한 보안 약점이다.

#### Case 5. `lmp-1` — Exported prompt provider leaks IVI LLM system prompt corpus

| 항목 | 내용 |
|---|---|
| Finding ID | `lmp-1` |
| APK | `ai.pleos.llm.model.provider` |
| 주요 컴포넌트 | `PromptsContentProvider` |
| 카테고리 | `intent` / exported provider information disclosure |
| Stage verdict | Stage 3 strong TP, 3/3 합의 |
| AAOS / MASVS | AAOS §3.7 Permission Model / MASVS-PLATFORM-1, MASVS-PLATFORM-2 |
| TARA | LLM 시스템 프롬프트/모델, Information Disclosure, High risk |

**발견 경로.**
Stage 1의 exported component 검색에서 `ContentProvider`가 외부 공개되어 있고, permission gate 없이 query 결과를 반환하는 구조가 확인되었다. 이 provider는 일반 preference나 cache가 아니라 LLM system prompt/corpus와 관련된 데이터를 제공하는 역할로 해석되었다.

**근거 패키지.**

- manifest/provider 설정상 외부 query 가능성이 있음.
- `query()` 흐름에서 LLM prompt/corpus 성격의 데이터를 반환하는 구조가 있음.
- provider-level read permission 또는 signature-level gate가 확인되지 않음.

**디컴파일 근거.**

```xml
<!-- data/_local/decompiled/ai.pleos.llm.model.provider/resources/AndroidManifest.xml -->
<provider
    android:name="ai.pleos.llm.model.provider.PromptsContentProvider"
    android:exported="true"
    android:authorities="ai.pleos.playground.llm.model.provider.prompts"
    android:grantUriPermissions="true"/>
```

```java
// data/_local/decompiled/ai.pleos.llm.model.provider/.../PromptsContentProvider.java
public Cursor query(Uri uri, String[] projection, String selection,
                    String[] selectionArgs, String sortOrder) {
    Context context = getContext();
    if (context == null) {
        return null;
    }
    String promptsJson = readPromptsJson(context);
    MatrixCursor matrixCursor = new MatrixCursor(new String[]{"content"});
    matrixCursor.addRow(new String[]{promptsJson});
    return matrixCursor;
}

private final String readPromptsJson(Context context) {
    InputStream inputStreamOpen = context.getAssets().open("prompts.json");
    ...
    return TextStreamsKt.readText(bufferedReader);
}
```

manifest에서 provider가 exported이고, `query()`가 `assets/prompts.json` 내용을 cursor row로 반환한다. 이 조합 때문에 일반 exported provider보다 IVI LLM prompt/corpus disclosure로 더 강하게 판단했다.

**왜 보고 유지했는가.**
일반 Android 앱에서도 exported provider는 정보 노출 위험이지만, IVI LLM 앱에서는 의미가 더 커진다. system prompt, guardrail, 내부 schema, tool/action instruction이 외부 앱에 노출되면 prompt injection이나 jailbreak prompt 설계의 자료가 된다. 이 finding은 단순 파일 노출이 아니라 “LLM behavior를 조작하기 위한 사전 정보 노출”이라는 도메인 특수성을 가진다.

**위험 시나리오.**
외부 앱이 provider URI를 통해 prompt corpus를 읽고, 차량 음성 비서나 on-device LLM이 어떤 instruction과 guardrail을 갖는지 파악할 수 있다. 이후 공격자는 사용자를 속이는 prompt, guardrail 우회 문장, 내부 schema를 흉내 내는 입력을 설계할 수 있다. 차량 action API와 직접 연결되지 않더라도, IVI LLM의 안전 정책을 우회하는 준비 정보가 된다는 점에서 중요하다.

**권장 조치.**

- provider가 외부 공개될 필요가 없으면 `android:exported="false"`로 닫는다.
- 외부 공개가 필요하면 `signature` 권한 또는 caller UID/package 검증을 적용한다.
- prompt corpus는 provider로 배포하지 않고 in-process API 또는 system service 내부 저장소로 제한한다.
- prompt/corpus 데이터에 보안 정책, internal schema, tool routing 정보가 포함되는지 redaction한다.

**잔여 한계.**
정적 분석은 실제 provider URI가 외부 앱에서 호출 가능한지 runtime permission state까지 완전히 증명하지 못한다. 이를 보강하기 위해 작성된 dynamic hook은 provider `query()` 호출 시 caller UID와 row count를 관찰하도록 설계되어 있다.

#### Case 6. `vc-6` — Exported VehicleBroadcastReceiver accepts untrusted MAC-like payload

| 항목 | 내용 |
|---|---|
| Finding ID | `vc-6` |
| APK | `ai.umos.vehiclecontrol` |
| 주요 컴포넌트 | `VehicleBroadcastReceiver` |
| 카테고리 | `intent` / broadcast receiver spoofing |
| Stage verdict | Stage 1 MEDIUM → true severity HIGH, Stage 3 strong TP |
| AAOS / MASVS | AAOS §3.7 Permission Model / MASVS-PLATFORM-1, MASVS-PLATFORM-2 |
| TARA | 차량 제어 명령, Spoofing + Tampering, Critical risk |

**발견 경로.**
Stage 1에서 exported receiver, intent extra parsing, DB 저장/차량 관련 처리 흐름이 함께 탐지되었다. `VehicleBroadcastReceiver`는 외부 broadcast에 반응할 수 있는 구조였고, `macAddress` 성격의 extra를 충분히 검증하지 않은 채 차량/Bluetooth 관련 저장·처리 흐름으로 연결하는 것으로 해석되었다.

**근거 패키지.**

- receiver가 exported 상태로 관찰됨.
- intent extra에서 MAC-like payload를 읽는 흐름이 있음.
- 해당 payload가 차량/Bluetooth pairing 또는 차량 제어 보조 데이터와 연결될 수 있음.
- TARA에서 차량 제어 명령 자산과 연결되어 Severe impact로 분류됨.

**디컴파일 근거.**

```xml
<!-- data/_local/decompiled/ai.umos.vehiclecontrol/resources/AndroidManifest.xml -->
<receiver
    android:name="ai.umos.vehiclecontrol.feature.bluetooth.data.VehicleBroadcastReceiver"
    android:enabled="true"
    android:exported="true">
    <intent-filter>
        <action android:name="ai.umos.android.intent.action.ANDROID_AUTO_REQUEST_ENABLE_ANDROID_AUTO"/>
        <action android:name="ai.umos.android.intent.action.DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS"/>
    </intent-filter>
</receiver>
```

```java
// data/_local/decompiled/ai.umos.vehiclecontrol/.../VehicleBroadcastReceiver.java
public void onReceive(Context context, Intent intent) {
    super.onReceive(context, intent);
    String action = intent != null ? intent.getAction() : null;

    if (Intrinsics.areEqual(action,
            VehicleBroadcastIntent.DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS.getAction())) {
        String stringExtra = intent.getStringExtra("macAddress");
        if (stringExtra != null) {
            launch(MainScope(), null, null, new C03531(stringExtra, null), 3, null);
            return;
        }
        throw new IllegalArgumentException("Required value was null.");
    }
}

// Coroutine path, simplified from JADX output
if (pairedDeviceRepository.containsDevice(macAddress)) {
    pairedDeviceRepository.updateDevice(macAddress, true, ...);
} else {
    pairedDeviceRepository.insertDevice(new PairedDevice(macAddress, true, false, true, ...));
}
```

외부 broadcast 수신 가능성, caller-controlled `macAddress`, pairing repository update/insert가 한 흐름에 묶여 있다. 따라서 단순한 exported receiver 경고가 아니라 차량/Bluetooth state tampering 후보로 유지했다.

**왜 보고 유지했는가.**
이 finding은 단순 broadcast receiver 노출이 아니다. 외부 sender가 제어 가능한 payload가 차량/Bluetooth 관련 상태에 영향을 줄 수 있다는 점이 핵심이다. 공격 가능성이 “원격 차량 탈취”로 즉시 이어진다고 말할 수는 없지만, IVI 내부에서 차량 제어 또는 페어링 상태를 오염시키는 spoofing/tampering risk로는 충분하다. 그래서 Stage 1 MEDIUM을 최종적으로 HIGH/critical concern으로 격상했다.

**위험 시나리오.**
악성 same-device app 또는 동일 권한을 가진 앱이 receiver에 MAC-like payload를 전달하면, 정상 pairing 대상과 다른 식별자가 저장되거나 차량 제어 보조 상태가 오염될 수 있다. 그 결과 블루투스 페어링, 차량 음향/통화/내비 연동, Gleo action routing 같은 주변 흐름에서 잘못된 대상이 신뢰될 수 있다. 정상 pairing을 방해하는 DoS 성격도 가능하다.

**권장 조치.**

- receiver가 외부 공개될 필요가 없으면 `android:exported="false"`로 닫는다.
- 외부 broadcast가 필요하면 signature-level permission과 trusted package whitelist를 적용한다.
- `macAddress`는 형식 검증뿐 아니라 이미 pairing된 trusted device registry와 대조한다.
- state 변경 전에 caller UID, package signature, user confirmation을 확인한다.
- dynamic validation에서는 receiver `onReceive()` 시 caller UID와 payload를 기록해 외부 trigger 가능성을 확인한다.

**잔여 한계.**
정적 분석은 실제 pairing state와 runtime caller UID를 직접 관찰하지 못한다. 따라서 이 finding은 “차량 안전 영향이 확정된 exploit”이 아니라 “차량 제어 자산에 연결된 spoofing/tampering design weakness”로 표현하는 것이 정확하다. 다만 TARA 기준에서는 Severe asset과 High feasibility가 결합되어 Critical concern으로 다룰 만하다.

### 6.3 오탐으로 제거된 사례

| ID | 초기 의심 | Stage 2/3에서 제거된 이유 |
|---|---|---|
| `vc-3`, `vc-4` | runtime permission grant/revoke 호출 | external deep-link route가 없고, Compose Nav internal-only이며, caller-controlled path가 privilege path로 연결되지 않음 |
| `usb-2` | USB permission grant가 caller-resolved component로 흐름 | `PackageManager` query + AOAP permission filter + `MANAGE_USB` requirement로 차단 |
| `ss-1` | exported `BOOT_COMPLETED` receiver | `BOOT_COMPLETED`는 protected broadcast라 일반 앱이 fake-trigger 불가 |
| `amb-4` | cross-package broadcast | explicit `setComponent`로 PleOS 내부 수신자에 제한됨 |

이 사례들이 연구의 핵심이다. Stage 1은 위험 API를 넓게 잡고, Stage 2/3는 Android framework-level control을 읽어 실제 보고 여부를 결정했다.

## 7. AAOS/MASVS/TARA 매핑

최종 finding은 AAOS 보안 항목과 MASVS/TARA 관점으로 매핑했다.

| AAOS 관점 | 관련 finding 성격 | 보안 의미 |
|---|---|---|
| §3.7 Permission Model | exported component, implicit broadcast, provider permission | 외부 앱이 IVI 컴포넌트를 호출하거나 민감 데이터를 읽는 위험 |
| §4.2 Credential Protection | API key, OAuth secret, KDF passphrase, PII stringification | APK reverse로 secret/PII가 노출되는 위험 |
| §5.1 Communication Security | plaintext channel, TLS/pinning 판단 | 차량/시스템 로그 또는 계정 트래픽의 MITM/노출 위험 |

TARA 산출물에서는 Critical/High concern이 차량 제어 spoofing, credential leakage, system prompt/corpus exposure, plaintext telemetry 쪽에 집중되었다.

## 8. 확장 실험 결과

### 8.1 RAG 도메인 지식 주입

Chroma + local sentence-transformers `all-MiniLM-L6-v2`로 AAOS/MASVS/TARA/history context를 구성했다. 외부 embedding API는 사용하지 않았다.

| Intrinsic metric | Result |
|---|---:|
| Historical nearest-neighbor verdict propagation | 40/47 = 85.1% |
| AAOS category alignment | 40/47 = 85.1% |
| MASVS area match | 11/47 = 23.4% |

해석: RAG는 AAOS citation과 historical calibration에는 유용하지만, MASVS 문서 chunking은 아직 거칠다. 또한 이 수치는 end-to-end LLM 성능이 아니라 retrieval 자체의 intrinsic quality다.

### 8.2 Native `.so` 분석

결론부터 말하면 “봤는데 결과가 없었다”가 아니라, “이번 범위의 static native scan에서는 추가 native-bound 취약점을 만들 근거가 없었다”가 정확하다. Java/Kotlin APK 본문은 `jadx`로 디컴파일했지만, `.so`는 소스 수준 복원이 아니라 radare2/ELF/string surface와 `src/native/native_analyze.py` 기반의 보수적 정적 분석으로 확인했다. Ghidra Go plugin을 이용한 full decompile은 후속 작업으로 남겨 두었다.

| Native sample | 분석 표면 | 관찰 결과 | 결론 |
|---|---|---|---|
| `ai.pleos.sync.syslog` / `libgojni.so` | Go symbol/string, URL, secret, TLS keyword | Go `crypto/tls` / `x509` 계열 문자열은 확인. hardcoded endpoint/secret은 0건 | Java-side plaintext gRPC finding과 별개로 native 추가 vuln 0건 |
| `ai.pleos.caas` / `libgojni.so` | sync.syslog와 유사한 Go binary surface | URL 0건, `sk-...`/API key/secret 0건, UUID-like 상수 1건은 credential로 보기 어려움 | informational only |
| `ai.pleos.caas` / `libairspeech_stt.so` | STT native library string scan | URL 0건, secret 0건, TLS bypass keyword 0건 | static-only 기준 추가 vuln 0건 |
| `ai.pleos.navigation` / `libmapbox-maps.so` | Mapbox native library string scan | URL 0건, secret 0건, TLS bypass keyword 0건 | endpoint/credential은 Java SDK config 쪽 검증 대상 |

추가로 native deep-dive target pass를 한 번 더 진행했다. high-value APK 17개에서 `.so` 198개를 열람하고 SHA-256 기준 158개 unique native hash로 deduplicate한 뒤, 15개를 추출해 `rabin2` import/hardening surface를 확인했다. 이 단계에서도 confirmed native vulnerability는 0건이지만, `ai.pleos.playground.caas`의 `libairspeech_stt.so`에서 `system()` import와 `utility::make_dir(char const*)`의 `rm -rf %s` command construction 후보가 관찰되었다. 현재는 path argument origin이 증명되지 않아 “보고 확정”이 아니라 candidate로 보류한다.

| Follow-up result | Value |
|---|---:|
| high-value APK scanned | 17 |
| `.so` entries enumerated | 198 |
| unique native hashes | 158 |
| extracted deep-dive targets | 15 |
| `rabin2` network-capable targets | 6 |
| `system`/exec import targets | 1 |
| confirmed additional native vulnerabilities | 0 |
| native candidates requiring validation | 1 |

해석: 이번 sample에서는 native binary가 대체로 secret 저장소라기보다 Java-side 설정과 SDK가 사용하는 helper/runtime에 가까웠다. 따라서 최종 수치에는 “native sample `n=4`, 추가 confirmed 취약점 0건”을 유지하되, follow-up에는 “`libairspeech_stt.so` command-execution primitive 후보 1건”을 별도 보류 항목으로 남긴다. 이 후보는 JNI argument flow, Ghidra caller xref, Frida `system()` hook으로 path controllability를 확인해야 최종 취약점 여부를 판정할 수 있다.

### 8.3 Dynamic 검증 준비

LangGraph는 LLM 자동 호출이 아니라 deterministic state machine으로만 사용했다. 5개 Frida hook script를 작성했다.

| Hook target | 검증 목적 |
|---|---|
| `vc-5` | implicit broadcast가 실제 runtime에서 package/component 제한 없이 나가는지 확인 |
| `vc-6` | receiver caller UID와 external trigger 가능성 확인 |
| `ssl-2` | token `toString()`과 Log emission 실제 발생 여부 확인 |
| `ssl-5` | BuildConfig passphrase가 runtime KDF에 들어가는지 확인 |
| `lmp-1` | exported provider query caller UID와 row count 확인 |

실제 AVD attach는 환경 의존 작업으로 남았지만, 정적 finding을 dynamic evidence로 강화하거나 약화하는 실험 구조는 준비됐다.

### 8.4 Codex multi-model 보충 실험

본 연구의 기본 Stage 3는 Claude Code 단일 모델의 multi-perspective consensus이다. 이후 보충 실험으로 Codex 3-model cross-read를 수행했다.

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| Claude Code Stage 3 `>=2/3` | 100.0% | 97.4% | 98.7% |
| Codex `gpt-5.5` | 100.0% | 89.5% | 94.4% |
| Codex `gpt-5.4` | 100.0% | 73.7% | 84.9% |
| Codex `gpt-5.3-codex` | 100.0% | 65.8% | 79.4% |
| Codex 2/3 consensus | 100.0% | 76.3% | 86.6% |

Codex consensus는 FP를 추가하지 않았지만 recall이 낮았다. 따라서 “모델 수를 늘리면 무조건 좋아진다”가 아니라, **모델에 제공하는 evidence package와 prompt calibration이 더 중요하다**는 결론을 얻었다.

### 8.5 Runtime PoC 보강: Navigation + VehicleService

PoC 보강은 기존 `n=47` 정적 평가와 섞지 않고 FN expansion / runtime validation track으로 분리했다. 여기서 목표는 “차량 탈취 성공”을 주장하는 것이 아니라, 일반 same-device 앱 하나가 IVI 내부 navigation/service boundary를 실제 runtime에서 건드릴 수 있는지 확인하는 것이다.

| PoC ID | Runtime level | 확인된 효과 | 정확한 claim |
|---|---|---|---|
| `navi-1` | **L3 user-visible route UI injection** | exported/no-permission `NaviService` Binder에 `RequestRoute`를 보내 Maps가 route preview, route candidates, polyline을 표시함. 최초 canonical proof는 `CODEX_SAFE_DEST`였고, 최신 live replay에서는 발표용 marker `HACKED_MALICIOUS_DEST`도 visible route preview로 재현했다. | same-device 앱이 navigation Binder surface를 통해 사용자에게 보이는 route UI state를 만들 수 있다. automatic guidance start나 active-route hijack은 별도 증거가 없으면 주장하지 않는다. |
| `vs-1` | **V3 VehicleService property mutation** | `VEHICLE_BINDING` custom permission이 `normal`이고, PoC 앱이 `VehicleService`에 bind한 뒤 `MIRROR_FOLD before=false → set=true → after=true → restore=false`를 확인했다. | weak normal permission으로 보호된 VehicleService Binder가 reversible vehicle-property write primitive를 노출한다. |
| `vhal-pentest-1` | **별도 ADB-root emulator evidence** | 사용자 pentest attachment에서 `cmd car_service inject-vhal-event 0x21400400 0x0 8`로 `GEAR_POSITION=D` spoofing/DoS 테스트가 정리되어 있다. | emulator/root-level VHAL spoofing 위험을 보여주는 별도 pentest 증거다. same-device 앱 Binder PoC가 gear/speed를 직접 바꿨다는 뜻은 아니다. |

따라서 발표용 결론은 다음처럼 고정한다. **일반 앱 하나가 route UI injection과 reversible vehicle-property mutation을 같은 scenario 안에서 수행할 수 있음을 보였다.** 이는 자율주행/ADAS가 IVI navigation/property state를 신뢰하는 구조라면 compromise chain의 primitive가 될 수 있지만, 본 프로젝트가 remote takeover, 실차 actuation, steering/brake/gear/powertrain 제어를 증명한 것은 아니다.

## 9. 한계와 다음 연구

| 한계 | 현재 상태 | 다음 연구 |
|---|---|---|
| Native dynamic behavior | 정적 sample n=4에서 추가 vuln 0건 | Ghidra Go plugin + Frida syscall/JNI hook |
| 표본 크기 | n=47에서 McNemar 유의 도달 | n>=60 확장으로 power 강화 |
| External model comparison | Codex cross-read는 보충으로 완료 | true multi-vendor API 비교는 IP/budget 정책 해결 후 |
| RAG end-to-end | intrinsic retrieval만 측정 | fresh session에서 no-RAG vs with-RAG prompted judgment |
| ProGuard-heavy APK | priority class yield 감소 확인 | Stage 0 deobfuscation과 manifest-only scan 통합 |
| Runtime PoC chaining | `navi-1` L3 + `vs-1` V3 확인, VHAL spoofing은 별도 ADB-root track | same-device Binder path의 더 강한 user-visible property UI, route guidance state, traffic/VHAL correlation |

## 10. 최종 결론

본 프로젝트의 결론은 네 가지다.

1. IVI APK 정적 분석에서 LLM은 단독 탐지기보다 reasoning component로 둘 때 더 안정적이다.
2. Stage 1은 넓게 잡고, Stage 2/3는 Android/PleOS control을 확인해 오탐을 제거하는 구조가 효과적이다.
3. 최종 `n=47`에서 Stage 3 `>=2/3` consensus는 Precision 100.0%, Recall 97.4%, F1 98.7%를 달성했고, Stage 1 대비 개선은 통계적으로 유의했다.
4. Runtime PoC 보강에서는 `navi-1` L3 route UI injection과 `vs-1` V3 mirror-fold property mutation을 확인했다. 이는 full vehicle takeover가 아니라, same-device malicious app threat model에서 IVI compromise chain을 구성할 수 있는 runtime primitive evidence다.
5. Codex multi-model 보충 실험은 기존 Claude Code 결과를 대체하지 못했으며, 향후 개선 축은 모델 수보다 evidence packaging, RAG calibration, native/dynamic evidence 결합이다.

즉 본 연구는 “LLM으로 APK를 훑어 취약점을 찾았다”가 아니라, **LLM을 검증 가능한 정적 분석 파이프라인 안에 제한적으로 배치했을 때 PleOS/AAOS IVI 보안 점검에 어떤 실용적 근거를 만들 수 있는지**를 보인 프로젝트다.

## 11. 근거 산출물

- 통합 보고서: `docs/01_final_report.md`
- 사례 연구: `docs/03_case_studies.md`
- 한계/비용: `docs/06_limitations_and_costs.md`
- 학기 외 확장 결과: `docs/08_future_work_implementations.md`
- 연구 확장 계획: `docs/09_research_extension_plan.md`
- Combined IVI PoC: `data/reports/runtime_local/combined_ivi_chain_poc_20260518.md`
- PoC evidence index: `data/reports/runtime_local/poc_evidence_index.md`
- Stage 3 결과: `data/reports/local/stage3_ensemble.md/json` (local-only full n=47)
- Bootstrap CI: `data/reports/aggregate/bootstrap_ci.md`
- McNemar test: `data/reports/aggregate/mcnemar_test.md/json`
- Codex multi-model: `data/reports/aggregate/codex_multimodel_agreement.md/json`
- RAG ablation: `data/reports/rag_local/rag_ablation.md/json`
- Native sample: `data/reports/native_local/native_r3c2_20260514.md`
