/* Frida hook for ssl-2 — AuthData Kotlin data-class toString leaks authenticatorToken.
 *
 * Static finding: ai.pleos.sync.authenticator.AuthData
 *   line 82 — Kotlin data class auto-generated toString() includes every field, incl.
 *   `authenticatorToken: String`. Combined with Log.d at SysLogService:170 confirms
 *   the leak path.
 *
 * Dynamic verification:
 *   1. Hook AuthData.toString() — capture full string, tag with token-length.
 *   2. Hook android.util.Log.d / Log.i / Log.e — flag any call whose tag/msg
 *      contains the token substring (catches non-grep-visible emission paths).
 *
 * Run:
 *   frida -U -n ai.pleos.sync.syslog -l ssl-2_auth_data_token_leak.js
 */

"use strict";

Java.perform(function () {
    const AuthData = Java.use("ai.pleos.sync.authenticator.AuthData");
    const Log = Java.use("android.util.Log");

    /* Live token observed via toString — used to scan Log.d args. */
    let observedTokens = [];

    AuthData.toString.implementation = function () {
        const s = this.toString();
        /* Naive: token field is preceded by "authenticatorToken=". */
        const m = /authenticatorToken=([^,\)]+)/.exec(s);
        const tok = m ? m[1] : null;
        if (tok && observedTokens.indexOf(tok) < 0) {
            observedTokens.push(tok);
        }
        send({
            type: "ssl-2",
            event: "AuthData.toString",
            length: s.length,
            token_substring_seen: !!tok,
            token_length: tok ? tok.length : 0,
            verdict: tok ? "static_TP_dynamic_token_in_toString"
                          : "static_FP_dynamic_token_absent"
        });
        return s;
    };

    ["d", "i", "e", "w", "v"].forEach(function (lvl) {
        const orig = Log[lvl].overload("java.lang.String", "java.lang.String");
        orig.implementation = function (tag, msg) {
            try {
                const leaked = observedTokens.some(function (t) {
                    return (msg && msg.indexOf(t) >= 0) || (tag && tag.indexOf(t) >= 0);
                });
                if (leaked) {
                    send({
                        type: "ssl-2",
                        event: "Log." + lvl + "_leak",
                        tag: tag,
                        msg_length: msg ? msg.length : 0,
                        verdict: "static_TP_dynamic_emission_confirmed"
                    });
                }
            } catch (e) { /* swallow */ }
            return orig.call(this, tag, msg);
        };
    });

    send({ type: "ssl-2", event: "hook_loaded" });
});
