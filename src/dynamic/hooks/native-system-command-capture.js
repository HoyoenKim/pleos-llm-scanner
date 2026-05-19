/* Frida hook for native-N1 — block-and-log libc system() calls.
 *
 * Static candidate: ai.pleos.playground.caas / libairspeech_stt.so
 *   utility::make_dir(char const*) appears to construct "rm -rf %s" from a
 *   path argument before mkdir(). This is NOT a confirmed vulnerability until
 *   the path argument is proven attacker-controllable.
 *
 * Dynamic verification:
 *   1. Attach only to a local emulator/test device, preferably the CAAS/AIRSpeech process.
 *   2. Replace libc system() with a dry-run callback that logs the command string
 *      and returns success without executing it.
 *   3. Treat a runtime command containing attacker-controlled marker text as the
 *      signal for path-controllability follow-up. Do not execute destructive
 *      payloads.
 *
 * Run example:
 *   frida -U -n ai.pleos.playground.caas -l native-system-command-capture.js
 */

"use strict";

const MAX_COMMAND_PREVIEW = 300;

function previewCommand(cmdPtr) {
    if (cmdPtr.isNull()) {
        return null;
    }
    try {
        const value = cmdPtr.readCString();
        if (value.length <= MAX_COMMAND_PREVIEW) {
            return value;
        }
        return value.slice(0, MAX_COMMAND_PREVIEW) + "...[truncated]";
    } catch (e) {
        return "[readCString failed: " + e.toString() + "]";
    }
}

function installSystemHook() {
    const systemPtr = findExport("libc.so", "system");

    if (!systemPtr) {
        send({
            type: "native-N1",
            event: "hook_error",
            error: "libc system() export not found"
        });
        return;
    }

    Interceptor.replace(systemPtr, new NativeCallback(function (cmdPtr) {
        const command = previewCommand(cmdPtr);
        send({
            type: "native-N1",
            event: "system_call_blocked",
            command_preview: command,
            contains_rm_rf: command ? command.indexOf("rm -rf") !== -1 : false,
            verdict: command && command.indexOf("rm -rf") !== -1
                ? "native_candidate_runtime_sink_reached"
                : "native_system_call_observed"
        });

        /* Dry-run: return success without executing the command. This keeps the
         * PoC observational and prevents destructive rm -rf behavior. */
        return 0;
    }, "int", ["pointer"]));

    send({
        type: "native-N1",
        event: "hook_loaded",
        mode: "dry_run_blocking",
        system_address: systemPtr.toString()
    });
}

function findExport(moduleName, symbolName) {
    if (typeof Module.findExportByName === "function") {
        return Module.findExportByName(moduleName, symbolName);
    }
    if (typeof Module.getGlobalExportByName === "function") {
        try {
            return Module.getGlobalExportByName(symbolName);
        } catch (e) {
            /* Fall through to Process.getModuleByName for Frida 17. */
        }
    }
    try {
        const module = Process.getModuleByName(moduleName);
        if (module && typeof module.getExportByName === "function") {
            return module.getExportByName(symbolName);
        }
        if (module && typeof module.findExportByName === "function") {
            return module.findExportByName(symbolName);
        }
    } catch (e) {
        return null;
    }
    return null;
}

setImmediate(installSystemHook);
