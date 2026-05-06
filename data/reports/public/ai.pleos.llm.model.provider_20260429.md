> **Public masked copy** — code evidence (fenced blocks) replaced with redaction markers under contractor IP protection. Class names, line numbers, categories, severities, rationale, and AAOS / MASVS mappings are kept verbatim. Original raw report is retained locally only.
>
> 본 파일은 contractor IP 보호 정책에 따라 코드 인용을 redact 한 공개용 사본이다. 분석 메타데이터 (class, line, category, severity, rationale, AAOS 매핑) 는 그대로 유지.

# Stage 1 Analysis — `ai.pleos.llm.model.provider` (PleOS LLM Model Provider)

- **Date**: 2026-04-29
- **APK path on device**: `/system/app/LLMModelProviderSerivce/LLMModelProviderSerivce.apk` (extracted via bulk pull) — repackaged as `data/apks/ai.pleos.llm.model.provider.apk` (small)
- **Decompiler**: jadx 1.5.5 (`--deobf --show-bad-code`) — 2,602 entries, 38 jadx warnings
- **Stage**: 1 (single-pass LLM, Claude Opus 4.7)
- **Sources scope**: `ai/pleos/*` = 22 java files (very compact — provider + receiver + service + helpers)

## Manifest highlights

- **No `INTERNET`** permission. The model is local (the app ships a 1.5 B-parameter `chatbaker-1.5b-16k-d0.3.3-m0.4.0-r250210.gguf` GGUF from `assets/` to `getFilesDir()` and shares the URI via `FileProvider`).
- Permissions: `ai.pleos.caas.EVENT_PERMISSION` (declared but **not used to gate the exported receiver**), `SYSTEM_APPLICATION_OVERLAY`, `SYSTEM_ALERT_WINDOW`, `RECEIVE_BOOT_COMPLETED`.
- Self-defined permission `DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` (signature) — used to lock dynamic receivers to the same signing certificate.
- **Exported components**:
  - `LLMModelProviderReceiver` (BOOT_COMPLETED + `SHARE_FILE_COMPLETE` + `LLM_SERVICE_STARTED`) — **no `permission=`** attribute
  - `PromptsContentProvider` (authority `ai.pleos.playground.llm.model.provider.prompts`, `grantUriPermissions="true"`)
- Non-exported: `LLMModelProviderService`, `FileProvider` (good).

## Findings — class 1: `PromptsContentProvider`

```java
// <redacted: PleOS proprietary code>
```

### Finding — HIGH — Exported provider returns the LLM system-prompt corpus to any caller

- The provider is `exported="true"` with **no signature permission and no path-permission allow-list**.
- `query()` ignores `uri / projection / selection / sortOrder` — for any input it returns a single-row Cursor whose `content` column is the entire `assets/prompts.json`.
- `prompts.json` is the LLM's **system-prompt corpus** — the rules and templates that bind Gleo's vocabulary to vehicle-control commands.
- Any installed app can read it: `getContentResolver().query(Uri.parse("content://ai.pleos.playground.llm.model.provider.prompts/anything"), null, null, null, null)`.
- **Impact**:
  - Prompt-injection / jailbreak with **exact phrasing the model treats as authoritative**.
  - Reverse-engineering of safety guards and vehicle-command guard rails.
- **Mitigation**: signature-level `<permission>`, or remove `exported="true"` and rely on `FLAG_GRANT_READ_URI_PERMISSION` only when an Intent forwards a URI to a trusted consumer.

## Findings — class 2: `LLMModelProviderReceiver`

```java
// <redacted: PleOS proprietary code>
```

### Finding — MEDIUM — Custom actions on an exported receiver gate model-file deletion + process termination, with no caller signature check

- The receiver is `exported="true"`, and the manifest's `<intent-filter>` enumerates the custom actions but **does not attach a `permission=` attribute**.
- A third-party app can send `Intent("ai.pleos.llm.model.provider.intent.action.SHARE_FILE_COMPLETE")` (the action name is enumerated in the manifest's own `<queries>` block — i.e. it is a known string in the public APK metadata):
  - On first hit: the local GGUF model file is deleted and `LLM_MODEL_SHARE_COMPLETE` is persisted (`true`) — meaning subsequent `BOOT_COMPLETED` paths will **early-return without re-shipping the model** (`startService` line 64: "already shared complete").
  - On both hits (also send `PROMPTS_QUERY_COMPLETE`): `Process.killProcess(Process.myPid())`.
- **Net effect**: a non-privileged app can perform a one-shot persistent **denial-of-service** against the on-device LLM (file deleted + completion flag set), and can crash the provider process at will.
- **Mitigation**: gate with `android:permission="ai.pleos.caas.EVENT_PERMISSION"` (this app already declares the permission as a `<uses-permission>` — it should also gate this receiver) or define a signature-level permission and require it on the `<receiver>` element.

## `LLMModelProviderService` — clean

- `exported="false"` → external apps cannot directly start the service.
- The service uses `FileProvider.getUriForFile(...)` and ships the URI to a **specific** consumer with `intent.setComponent(new ComponentName("ai.pleos.playground.caas", "ai.pleos.playground.caas.service.llm.FileShareActivity"))`.
- The Intent flags include `FLAG_GRANT_READ_URI_PERMISSION` (from the constant `268435457 = 0x10000001 = FLAG_ACTIVITY_NEW_TASK | FLAG_GRANT_READ_URI_PERMISSION`).
- `FileProvider` paths are bounded by `res/xml/file_paths.xml`: `<files-path name="shared_files" path="."/>` — limited to the app's `getFilesDir()`.
- This is the textbook way to share a file across packages without exposing `file://` URIs.

## Negative confirmations

- No `INTERNET` permission — the LLM model itself never leaves the device through this APK's process.
- The model artefact lives only inside `getFilesDir()` and is shared via FileProvider URI, not raw filesystem path.
- The chain `Service → CAAS FileShareActivity` uses an explicit `ComponentName`, not an action-based implicit Intent.

## Output artefacts

- JSON: `data/reports/ai.pleos.llm.model.provider_20260429.json`
- Markdown (this file): `data/reports/ai.pleos.llm.model.provider_20260429.md`

## Next steps

1. Confirm the exact `<receiver>` block in `AndroidManifest.xml` to verify the absence of `android:permission=`.
2. Cross-read `ai.pleos.playground.caas.apk` (the consumer of the FileProvider URI) — that's where the model file actually leaves this trust boundary.
3. Phase B-4 entry: build the evaluation framework.
