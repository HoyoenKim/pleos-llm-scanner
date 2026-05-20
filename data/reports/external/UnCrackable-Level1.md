# Stage 1 Analysis — UnCrackable-Level1 (OWASP MASTG Crackmes / Level_01)

- **Date**: 2026-04-30
- **Source**: `data/_local/apks/_mastg/owasp-mastg/Crackmes/Android/Level_01/UnCrackable-Level1.apk` (68 KB)
- **Authors (upstream)**: Bernhard Mueller / Vantage Point Security (OWASP MASTG)
- **Decompiler**: jadx 1.5.5 (`--deobf --show-bad-code`)
- **Stage**: 1 (single-pass LLM, Claude Opus 4.7)
- **Purpose**: External MASTG ground-truth baseline — measure PleOS pipeline accuracy on a publicly-labelled corpus.

## Decompiled scope

6 Java files (1,711-row repo notwithstanding, the APK itself is tiny):

| # | File | Role |
|---|---|---|
| 1 | `owasp/mstg/uncrackable1/R.java` | Android resource ids (auto-generated) |
| 2 | `sg/vantagepoint/uncrackable1/MainActivity.java` | Entry activity + verify button handler |
| 3 | `sg/vantagepoint/uncrackable1/C0005a.java` | Verification logic (AES decrypt + compare) |
| 4 | `sg/vantagepoint/p000a/C0000a.java` | AES wrapper |
| 5 | `sg/vantagepoint/p000a/C0001b.java` | Debug-flag check |
| 6 | `sg/vantagepoint/p000a/C0002c.java` | Root detection (3 heuristics) |

Class names are jadx-deobfuscated; the original ProGuard mapping (`a.a`, `a.b`, `a.c`) is preserved as `C0000a`, `C0001b`, `C0002c`.

## Findings

### F1 — HIGH — Hardcoded AES key + ciphertext (verification routine)

```java
// C0005a.java:15
bArrM0a = C0000a.m0a(m7b("8d127684cbc37c17616d806cf50473cc"),
                     Base64.decode("5UJiFctbmgbDoLXmpL12mkno8HT4Lv8dlat8FxR2GOc=", 0));
```

- 16-byte AES key (hex literal) + ciphertext (base64 literal) baked into the verify routine.
- Decompiling the APK ⇒ extracting both ⇒ decrypt locally ⇒ recover the secret string. No runtime instrumentation needed.
- This is the **canonical** OWASP MASTG hardcoded-secret pattern (MASVS-CRYPTO-1 / MASVS-STORAGE-2).
- **Mitigation**: derive key from a server-issued, per-session value; never compile static key material into the APK.
- **AAOS mapping**: §4.2 Credential Protection.

### F2 — MEDIUM — AES default mode (Cipher.getInstance("AES") = ECB)

```java
// C0000a.java:15
SecretKeySpec secretKeySpec = new SecretKeySpec(bArr, "AES/ECB/PKCS7Padding");
Cipher cipher = Cipher.getInstance("AES");   // ← provider-default mode = AES/ECB/PKCS5Padding
```

- The `Cipher.getInstance("AES")` argument controls the actual mode; the algorithm string passed to `SecretKeySpec` is ignored by the JCE provider.
- Default = AES/ECB/PKCS5Padding ⇒ deterministic, no IV, identical plaintext blocks produce identical ciphertext. Pattern leakage.
- MASVS-CRYPTO-1.
- **Mitigation**: `Cipher.getInstance("AES/GCM/NoPadding")` with a per-message IV/nonce.

### F3 — LOW — Crypto exception detail logged via Log.d

```java
// C0005a.java:17
Log.d("CodeCheck", "AES error:" + e.getMessage());
```

- Crypto error reaches logcat. On debuggable / userdebug builds (and on devices granting `READ_LOGS` to vendor diagnostics) this is readable by other apps.
- Information disclosure of internal crypto state — MASVS-STORAGE-3.

## Negative confirmations (out-of-scope but worth noting)

- **MainActivity root / debug detection** (`onCreate` checks `C0001b.m1a` + `C0002c.m2a/m3b/m4c`) — anti-tamper category not currently in `result_schema.json` enum (`crypto`/`network`/`permission`/`intent`/`hardcoded`/`reflection_dynamic`). Scope extension: add `anti_tamper` once MASVS-RESILIENCE coverage is in scope.
- **INTERNET / external comms**: 0 hits (no HttpClient / URL / OkHttp / Retrofit / WebView usage).
- **IPC**: no ContentProvider, BroadcastReceiver, Service.
- **Manifest** is single-Activity; nothing else exported.

## Stage-1 stats

| 카테고리 | HIGH | MEDIUM | LOW | 합 |
|---|---|---|---|---|
| hardcoded | 1 | — | — | 1 |
| crypto    | — | 1 | 1 | 2 |
| **합** | **1** | **1** | **1** | **3** |

## Output artefacts

- JSON: `data/reports/external/UnCrackable-Level1.json`
- Markdown (this file): `data/reports/external/UnCrackable-Level1.md`

## Next: ground-truth labelling

`data/ground_truth/mastg/uncrackable_level1.labels.json` 작성 — MASVS official answer 기반 라벨 (in-scope findings 한정). 라벨 후 `src/evaluation/eval.py` + `src/evaluation/ablation.py`에 merge.
