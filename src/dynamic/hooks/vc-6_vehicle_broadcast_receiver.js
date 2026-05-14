/* Frida hook for vc-6 — VehicleBroadcastReceiver exported macAddress acceptance.
 *
 * Static finding: ai.umos.vehiclecontrol.feature.vehicle.VehicleBroadcastReceiver
 *   line 58 — onReceive reads getStringExtra("macAddress") with no validation, writes to DB.
 *   Manifest: receiver android:exported="true".
 *
 * Dynamic verification: at runtime, log every macAddress extra and the calling UID
 * (via PendingIntent / Binder.getCallingUid) to confirm whether external (non-system)
 * UIDs can invoke this receiver.
 *
 * Run:
 *   frida -U -n ai.umos.vehiclecontrol -l vc-6_vehicle_broadcast_receiver.js
 */

"use strict";

Java.perform(function () {
    const Receiver = Java.use(
        "ai.umos.vehiclecontrol.feature.vehicle.VehicleBroadcastReceiver"
    );
    const Binder = Java.use("android.os.Binder");

    Receiver.onReceive.implementation = function (context, intent) {
        try {
            const action = intent ? intent.getAction() : null;
            const macAddr = intent ? intent.getStringExtra("macAddress") : null;
            const callingUid = Binder.getCallingUid();
            const callingPid = Binder.getCallingPid();

            send({
                type: "vc-6",
                event: "onReceive",
                runtime_action: action,
                runtime_macAddress: macAddr,
                calling_uid: callingUid,
                calling_pid: callingPid,
                /* TP if calling UID is non-system (>= 10000) AND macAddress is well-formed
                 * attacker-shape (00:01:02:... or similar). FP if calling UID == 1000 (system). */
                verdict: callingUid >= 10000 ? "static_TP_dynamic_external_caller"
                                              : "static_FP_dynamic_system_only"
            });
        } catch (e) {
            send({ type: "vc-6", event: "hook_error", error: e.toString() });
        }
        return this.onReceive(context, intent);
    };

    send({ type: "vc-6", event: "hook_loaded" });
});
