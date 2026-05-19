/*
 * acc-4 safe SSO boundary hook.
 *
 * This script only observes benign marker flow. It does not log raw client
 * secret values, does not alter OAuth state, and does not contact a backend.
 */

Java.perform(function () {
    const Intent = Java.use("android.content.Intent");
    const targetKeys = {
        "user-client-id": true,
        "user-client-secret": true,
        "user-client-name": true
    };

    function isMarker(value) {
        return value !== null && value.indexOf("codex_probe_20260515") >= 0;
    }

    Intent.getStringExtra.overload("java.lang.String").implementation = function (key) {
        const value = this.getStringExtra(key);
        if (targetKeys[String(key)]) {
            send({
                event: "acc4_getStringExtra",
                key: String(key),
                value_len: value === null ? 0 : String(value).length,
                marker_seen: isMarker(value)
            });
        }
        return value;
    };

    try {
        const SsoActivity = Java.use("ai.pleos.playground.account.login.SsoActivity");
        SsoActivity.onCreate.implementation = function (bundle) {
            send({ event: "acc4_sso_onCreate" });
            return this.onCreate(bundle);
        };
        send({ event: "acc4_hook_loaded", target: "SsoActivity" });
    } catch (err) {
        send({ event: "acc4_hook_loaded_partial", error: String(err) });
    }
});
