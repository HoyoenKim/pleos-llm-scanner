/* Frida hook for vc-5 — GleoActionSender implicit broadcast (PleOS / Vehiclecontrol).
 *
 * Static finding: ai.umos.vehiclecontrol.feature.applications.action.GleoActionSender
 *   line 40 — sendBroadcast(Intent) with no setPackage / setComponent.
 *
 * Dynamic verification goal: confirm that, at runtime, the constructed Intent has
 * neither a component nor a package set — i.e. the broadcast is truly implicit and
 * any third-party app with a matching receiver could observe it.
 *
 * Run on PleOS Connect AVD (userdebug build, frida-server-arm64 pushed):
 *   frida -U -n ai.umos.vehiclecontrol -l vc-5_gleo_action_sender.js
 */

"use strict";

Java.perform(function () {
    const Intent = Java.use("android.content.Intent");
    const Sender = Java.use("ai.umos.vehiclecontrol.feature.applications.action.GleoActionSender");
    const Log = Java.use("android.util.Log");

    Sender.sendVehicleCommand.overload("java.lang.String", "java.lang.String").implementation = function (action, payload) {
        const result = this.sendVehicleCommand(action, payload);
        Log.d("vc-5-hook", "sendVehicleCommand action=" + action + " payload.len=" + (payload ? payload.length : 0));
        return result;
    };

    /* Generic: hook every Intent constructor + setPackage/setComponent + send to learn
     * which intents originate from GleoActionSender. We tag any Intent that flows through
     * sendBroadcast inside its stack.                                                 */
    const ContextImpl = Java.use("android.content.ContextWrapper");
    ContextImpl.sendBroadcast.overload("android.content.Intent").implementation = function (intent) {
        try {
            const action = intent.getAction();
            const component = intent.getComponent();
            const pkg = intent.getPackage();
            const stack = Java.use("java.lang.Throwable").$new().getStackTrace();
            const inGleo = stack.some(function (frame) {
                return frame.toString().indexOf("GleoActionSender") >= 0;
            });
            if (inGleo) {
                send({
                    type: "vc-5",
                    event: "sendBroadcast",
                    finding: "GleoActionSender implicit broadcast",
                    runtime_action: action,
                    runtime_component: component ? component.toString() : null,
                    runtime_package: pkg,
                    /* TP if both component AND package are null (implicit); FP otherwise. */
                    verdict: (component || pkg) ? "static_FP_dynamic_explicit" : "static_TP_dynamic_confirmed"
                });
            }
        } catch (e) {
            send({ type: "vc-5", event: "hook_error", error: e.toString() });
        }
        return this.sendBroadcast(intent);
    };

    send({ type: "vc-5", event: "hook_loaded" });
});
