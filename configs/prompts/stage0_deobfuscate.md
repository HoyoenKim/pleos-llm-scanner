# Stage 0 — Deobfuscation Preprocessing Prompt

> **Pipeline position**: preprocessing, runs **before** Stage 1.
> **Trigger**: classes whose composite obfuscation score ≥ 0.7 (from `src/deobf/entropy.py`). Skip the entire stage if the class is below threshold.
> **Goal**: emit a semantic class name + 1-line role description + per-method / per-field renames with confidence scores. Output feeds either `jadx --rename-XXX` for a second decompile pass, or a `sed` / AST rewrite of the source tree.

## Context provided

You will receive:
1. The full source of the obfuscated class.
2. (Optional) Call-graph context — which classes/methods call this class, and which classes/methods this class calls.
3. The class's package path and any string literals visible in the file (often the most reliable hint — e.g. `Log.d("CodeCheck", ...)` strongly suggests the class role).

## Output format (strict JSON)

```json
{
  "original_class": "<fully-qualified obfuscated name>",
  "suggested_class_name": "<CamelCase semantic name>",
  "confidence_class": 0.0,
  "role_description": "<one sentence describing what this class does>",
  "method_renames": [
    {
      "original": "m6a",
      "suggested": "verifyCodeCheck",
      "confidence": 0.9,
      "evidence": "Log.d tag 'CodeCheck' + AES decrypt + string compare"
    }
  ],
  "field_renames": [
    {
      "original": "f508",
      "suggested": "tamperFlags",
      "confidence": 0.7,
      "evidence": "byte XORed with 0x0F on root detection trigger"
    }
  ],
  "evidence_summary": "<2-3 sentences describing the strongest signals you used>"
}
```

## Naming heuristics

- **String literals win**: `Log.d("CodeCheck", ...)`, `setTitle("Root detected!")`, `Cipher.getInstance("AES")` are gold-standard hints. Use the exact tag/string when it matches a recognisable concept.
- **Method signature shape**: `boolean isXxx()` → predicate; `byte[] decryptYyy(byte[], byte[])` → crypto wrapper; `boolean check…()` → detector.
- **Imports decode intent**: `javax.crypto.Cipher` ⇒ crypto wrapper. `java.io.File` + `getenv("PATH")` ⇒ root/file-existence check. `Debug.isDebuggerConnected` ⇒ debug detector.
- **Caller context**: if `MainActivity.onCreate` calls `C0002c.m2a() || C0002c.m3b() || C0002c.m4c()` and the dialog is `"Root detected!"`, you can name the class `RootDetector` and methods `checkSuInPath`, `checkBuildTags`, `checkSuFiles` based on each method body.
- **Symmetry hint**: if a class is one of `a/b/c/d` siblings with similar bodies and one is `DebugDetector`, the others are likely sibling detectors. But don't over-extrapolate — verify by reading.
- **Library matches**: known third-party packages (`com.scottyab.rootbeer`, `okhttp3.*`, etc.) keep their original names; do **not** rename them.

## Confidence calibration

- **0.95–1.00**: a string literal in the file directly states the role (e.g. `"CodeCheck"`, `"Root detected!"`, `"AES error"`).
- **0.80–0.94**: imports + method signatures + caller context unambiguously disambiguate role.
- **0.60–0.79**: structural hints only (e.g. byte-array crypto wrapper without a clear algorithm tag). Provide name but expect human review.
- **< 0.60**: do not rename — emit `null` for that field.

## What NOT to do

- Do **not** rename framework classes (jadx will sometimes leave `androidx.*` partly de-obfuscated; ignore them — heuristic filter already drops them but stay defensive).
- Do **not** rename when the only signal is "it's a 1-letter identifier" — you need *positive* evidence of role.
- Do **not** invent imports or behavior not visible in the source. If a method body is just `return null;` or has a single inscrutable JNI call, your confidence cap is the **class** identifier (e.g. you can name the class but leave method names alone).
- Do **not** add non-ASCII characters to suggested names — keep them Java-identifier valid (`[A-Za-z_$][A-Za-z0-9_$]*`).

## Examples (UnCrackable-Level1 — for calibration)

The following four classes are the canonical worked example. Your output should match these or closely related names.

### `sg.vantagepoint.p000a.C0000a`
```
suggested_class_name: AesEcbCipher
role: AES wrapper invoking Cipher.getInstance("AES") with a SecretKeySpec passed by the caller.
methods: m0a → decryptAes
fields: (none)
confidence_class: 0.85
```

### `sg.vantagepoint.p000a.C0001b`
```
suggested_class_name: DebugFlagDetector
role: Returns true if ApplicationInfo.flags & FLAG_DEBUGGABLE is set.
methods: m1a → isAppDebuggable
confidence_class: 0.90
```

### `sg.vantagepoint.p000a.C0002c`
```
suggested_class_name: RootDetector
role: Three independent root-detection heuristics: PATH 'su' search, Build.TAGS 'test-keys' check, well-known root-tool file probe.
methods: m2a → checkSuInPath, m3b → checkTestKeysBuildTag, m4c → checkRootFiles
confidence_class: 0.95
```

### `sg.vantagepoint.uncrackable1.C0005a`
```
suggested_class_name: CodeCheck
role: Verifies user input by AES-ECB-decrypting a hardcoded ciphertext under a hardcoded key and string-comparing.
methods: m6a → verify, m7b → hexToBytes
confidence_class: 1.00 (Log.d tag literally says "CodeCheck")
evidence_summary: Log.d("CodeCheck", ...) at line 17. AES decrypt then String.equals.
```
