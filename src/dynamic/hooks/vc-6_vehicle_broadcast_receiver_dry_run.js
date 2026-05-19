/* Frida dry-run hook for vc-6 — observe external VehicleBroadcastReceiver trigger
 * without mutating the paired-device database.
 *
 * Static finding: VehicleBroadcastReceiver is exported and accepts the
 * DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS action with a macAddress extra. The
 * normal implementation can insert/update a paired-device row. This dry-run
 * hook intentionally does NOT call the original onReceive() implementation.
 *
 * Run:
 *   frida -U -n ai.umos.vehiclecontrol -l vc-6_vehicle_broadcast_receiver_dry_run.js
 *
 * Then from another shell, send a benign local marker broadcast:
 *   adb shell am broadcast \
 *     -n ai.umos.vehiclecontrol/ai.umos.vehiclecontrol.feature.bluetooth.data.VehicleBroadcastReceiver \
 *     -a ai.umos.android.intent.action.DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS \
 *     --es macAddress 02:00:00:00:00:01
 */

"use strict";

Java.perform(function () {
    const Receiver = Java.use(
        "ai.umos.vehiclecontrol.feature.bluetooth.data.VehicleBroadcastReceiver"
    );
    const Binder = Java.use("android.os.Binder");

    Receiver.onReceive.implementation = function (context, intent) {
        let action = null;
        let macAddr = null;
        try {
            action = intent ? intent.getAction() : null;
            macAddr = intent ? intent.getStringExtra("macAddress") : null;
        } catch (e) {
            send({ type: "vc-6", event: "dry_run_read_error", error: e.toString() });
        }

        send({
            type: "vc-6",
            event: "dry_run_onReceive_blocked",
            runtime_action: action,
            runtime_macAddress: macAddr,
            calling_uid: Binder.getCallingUid(),
            calling_pid: Binder.getCallingPid(),
            verdict: "external_receiver_trigger_observed_without_db_mutation"
        });

        return;
    };

    send({ type: "vc-6", event: "dry_run_hook_loaded" });
});
