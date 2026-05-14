/* Frida hook for lmp-1 — Exported PromptsContentProvider returns the LLM system-prompt
 * corpus to any caller.
 *
 * Static finding: ai.pleos.llm.model.provider.PromptsContentProvider
 *   line 62 — query() returns a MatrixCursor of every prompt without caller verification
 *   or URI segment validation. Manifest: provider android:exported="true" with no
 *   android:permission attribute.
 *
 * Dynamic verification:
 *   1. Hook PromptsContentProvider.query — capture every call's calling UID, package,
 *      URI selection args, and the row count returned.
 *   2. UID >= 10000 (non-system) AND non-empty cursor returned ⇒ static_TP_dynamic_confirmed.
 *   3. UID == 1000 (system) only ⇒ static_FP_dynamic_system_only.
 *
 * Run:
 *   frida -U -n ai.pleos.llm.model.provider -l lmp-1_prompts_provider_query.js
 */

"use strict";

Java.perform(function () {
    const Provider = Java.use("ai.pleos.llm.model.provider.PromptsContentProvider");
    const Binder = Java.use("android.os.Binder");

    Provider.query.overload(
        "android.net.Uri",
        "[Ljava.lang.String;",
        "java.lang.String",
        "[Ljava.lang.String;",
        "java.lang.String"
    ).implementation = function (uri, projection, selection, selectionArgs, sortOrder) {
        const cursor = this.query(uri, projection, selection, selectionArgs, sortOrder);
        let rowCount = -1;
        try {
            rowCount = cursor ? cursor.getCount() : 0;
        } catch (e) { /* ignore */ }
        const uid = Binder.getCallingUid();
        const pid = Binder.getCallingPid();

        send({
            type: "lmp-1",
            event: "query",
            uri: uri ? uri.toString() : null,
            calling_uid: uid,
            calling_pid: pid,
            selection: selection,
            row_count_returned: rowCount,
            verdict: (uid >= 10000 && rowCount > 0)
                ? "static_TP_dynamic_external_read_confirmed"
                : (uid === 1000 ? "static_FP_dynamic_system_only" : "uncertain")
        });
        return cursor;
    };

    send({ type: "lmp-1", event: "hook_loaded" });
});
