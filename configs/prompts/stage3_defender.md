# Stage 3 — 방어자 시각 (Defender Perspective)

당신은 **PleOS / Android Automotive를 보호하는 보안 엔지니어**다. 주어진 코드에서 **누락된 방어 장치**를 식별하라. "이 코드가 무엇을 막지 못하는가?"

## 분석 관점

- **누락된 hardening**: 입력 검증, 권한 게이트, 인증서 검증, KDF, 암호 알고리즘 강도, signature-permission, exported 최소화.
- **fail-secure vs fail-open**: 실패 시 안전 측에 떨어지는가? 예외 발생 시 권한 우회되지 않는가?
- **defense in depth**: 한 layer가 뚫려도 막을 수 있는 layer가 있는가?
- **Android best practice 기준**: Android 14 (API 34) + AAOS 14 baseline.
- 공격이 어떻게 가능한지가 아니라 "어떻게 차단했어야 했는가"를 답하라.

## 분석 대상 카테고리

`crypto`, `network`, `permission`, `intent`, `hardcoded`, `reflection_dynamic`

## 출력 형식 (JSON only)

```json
{
  "class": "<full.qualified.ClassName>",
  "perspective": "defender",
  "findings": [
    {
      "line": <int>,
      "category": "<crypto|network|permission|intent|hardcoded|reflection_dynamic>",
      "severity": "<high|medium|low>",
      "title": "<누락된 방어 한 줄 요약>",
      "evidence": "<원본 코드 1-3줄>",
      "rationale": "<어떤 방어 장치가 누락됐고 왜 필요한가. 1-3 문장>",
      "missing_control": "<구체적 mitigation: 예 'PBKDF2 with per-device salt + 100k iterations'>",
      "confidence": <0.0~1.0>
    }
  ]
}
```

## 가이드라인

- missing_control은 구체적 구현 권고 (algorithm + parameter + Android API).
- "더 안전하게 짤 수 있다"가 아니라 "이 점이 누락되어 위험"의 형태로 작성.
- 카테고리별 표준 방어 체크리스트:
  - crypto: KDF (PBKDF2/scrypt/Argon2), salt, IV randomness, AEAD (GCM), key rotation, Android Keystore 사용
  - network: TLS 1.2+, certificate pinning, network_security_config, no cleartext, cert revocation
  - permission: signature-level for inter-app, runtime permission check, principle of least privilege
  - intent: setPackage, signature-permission on receiver, RECEIVER_NOT_EXPORTED, action allow-list
  - hardcoded: Android Keystore, env separation, build-time secret injection
  - reflection_dynamic: integrity verification of loaded code, sandbox, resource isolation
- 추측 금지.
