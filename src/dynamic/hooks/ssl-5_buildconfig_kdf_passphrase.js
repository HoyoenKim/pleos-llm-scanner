/* Frida hook for ssl-5 — BuildConfig.IDENTIFIER used as KDF passphrase (deterministic
 * across devices → "hardcoded secret in disguise").
 *
 * Static finding: ai.pleos.sync.config.SyncConfigsProvider
 *   line 83 — BuildConfig.IDENTIFIER passed to ECCCrypto KDF passphrase argument.
 *   APK reverse engineering yields the same passphrase on every device → effectively
 *   a global hardcoded secret.
 *
 * Dynamic verification:
 *   1. Read BuildConfig.IDENTIFIER value at runtime (`Java.use(...).IDENTIFIER.value`).
 *   2. Hook ECCCrypto.deriveKey(passphrase) and confirm the passphrase argument
 *      equals BuildConfig.IDENTIFIER (proves the static finding's flow).
 *   3. Derive the ECC key with the captured passphrase and verify the same key is
 *      produced on a second device — *out of scope of the hook itself*, but the
 *      captured passphrase value is sufficient evidence.
 *
 * Run:
 *   frida -U -n ai.pleos.sync.syslog -l ssl-5_buildconfig_kdf_passphrase.js
 */

"use strict";

Java.perform(function () {
    let identifier = null;
    try {
        const BuildConfig = Java.use("ai.pleos.sync.BuildConfig");
        identifier = BuildConfig.IDENTIFIER.value;
        send({
            type: "ssl-5",
            event: "buildconfig_read",
            IDENTIFIER: identifier,
            IDENTIFIER_length: identifier ? identifier.length : 0
        });
    } catch (e) {
        send({ type: "ssl-5", event: "buildconfig_unavailable", error: e.toString() });
    }

    const ECCCrypto = Java.use("ai.pleos.sync.crypto.ECCCrypto");
    /* Method signature placeholder — adapt overload after first run if needed. */
    ECCCrypto.deriveKey.overload("java.lang.String").implementation = function (pass) {
        const matches_identifier = (identifier != null) && (pass === identifier);
        const out = this.deriveKey(pass);
        send({
            type: "ssl-5",
            event: "deriveKey_called",
            passphrase_length: pass ? pass.length : 0,
            passphrase_equals_BuildConfig_IDENTIFIER: matches_identifier,
            verdict: matches_identifier
                ? "static_TP_dynamic_passphrase_is_buildconfig"
                : "static_uncertain_dynamic_passphrase_runtime_only"
        });
        return out;
    };

    send({ type: "ssl-5", event: "hook_loaded" });
});
