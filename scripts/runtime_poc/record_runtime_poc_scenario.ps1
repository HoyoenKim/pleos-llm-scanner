param(
    [ValidateSet("install", "lmp1", "map1", "acc4", "am1", "vc6", "static")]
    [string]$Scenario = "lmp1",
    [string]$OutputDir = "data/_local/runtime_videos/runtime_poc_recordings",
    [int]$Seconds = 22,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$Activity = "org.codex.pleos.poc/.PocActivity"
$Marker = "codex_probe_20260515"

function Wait-Boot {
    $deadline = (Get-Date).AddSeconds(180)
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
            # Emulator may briefly disappear while loading a snapshot.
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "emulator did not reach sys.boot_completed=1"
}

function Build-And-Install {
    if ($SkipBuild) {
        return
    }
    python scripts/runtime_poc/research_runtime_poc_harness.py --build
    if ($LASTEXITCODE -ne 0) {
        throw "harness build failed"
    }
    adb uninstall org.codex.pleos.poc 2>$null | Out-Null
    adb install -r data/_local/runtime_poc_harness/poc-harness-signed.apk | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "harness install failed"
    }
}

function Launch-Showcase([string]$Action, [hashtable]$Extras = @{}) {
    $args = @("shell", "am", "start", "-W", "-n", $Activity, "-a", "org.codex.pleos.poc.$Action")
    foreach ($key in $Extras.Keys) {
        $value = ([string]$Extras[$key]) -replace "\s+", "_" -replace "[^A-Za-z0-9_=.,:/-]", "_"
        $args += @("--es", $key, $value)
    }
    & adb @args | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "failed to launch $Action"
    }
}

function Start-Recording([string]$Name) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $remote = "/sdcard/${Name}_${stamp}.mp4"
    $local = Join-Path $OutputDir "${Name}_${stamp}.mp4"
    adb shell rm -f $remote
    $proc = Start-Process -FilePath adb -ArgumentList @("shell", "screenrecord", "--time-limit", "$Seconds", $remote) -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    return [pscustomobject]@{ Process = $proc; Remote = $remote; Local = $local }
}

function Stop-Recording($Recording) {
    try {
        if (-not $Recording.Process.HasExited) {
            Wait-Process -Id $Recording.Process.Id
        }
    } catch {
        # screenrecord may already have exited at its time limit.
    }
    adb pull $Recording.Remote $Recording.Local | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "video pull failed"
    }
    adb shell rm -f $Recording.Remote
    Write-Host "VIDEO=$($Recording.Local)"
}

function Ensure-Frida {
    adb root | Out-Null
    Start-Sleep -Seconds 2
    adb push tools/frida/frida-server-17.9.8-android-x86_64 /data/local/tmp/frida-server | Out-Null
    adb shell chmod 755 /data/local/tmp/frida-server
    adb shell "pkill -f frida-server || true" | Out-Null
    adb shell "nohup /data/local/tmp/frida-server >/data/local/tmp/frida-server.log 2>&1 &" | Out-Null
    Start-Sleep -Seconds 2
}

Wait-Boot
Build-And-Install

$name = "poc_$Scenario"

if ($Scenario -eq "am1") {
    adb emu avd snapshot save codex_pre_am1_video | Out-Host
}
if ($Scenario -eq "vc6") {
    Ensure-Frida
}

adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
$recording = Start-Recording $name

try {
    switch ($Scenario) {
        "install" {
            Launch-Showcase "SHOWCASE_INSTALL"
        }
        "lmp1" {
            Launch-Showcase "SHOWCASE_LMP1"
        }
        "map1" {
            Launch-Showcase "SHOWCASE_MAP1"
        }
        "am1" {
            Launch-Showcase "SHOWCASE_AM1"
        }
        "static" {
            Launch-Showcase "SHOWCASE_STATIC" @{
                observed = "amb-1 and am-3: credential-shaped constants found by APK reverse/decompile; full values redacted"
                preview = "amb-1: sk-<redacted> in LlmHandler production path; am-3: OAuth client_secret=<redacted> in AppMarket/account domain"
            }
        }
        "acc4" {
            adb logcat -c
            Launch-Showcase "SHOWCASE_ACC4" @{ observed = "pending trigger..." }
            Start-Sleep -Seconds 2
            adb shell am start -W -n $Activity -a org.codex.pleos.poc.ACC4_START | Out-Host
            Start-Sleep -Seconds 3
            $log = adb logcat -d -t 500 | Out-String
            $dumpsys = adb shell dumpsys activity activities 2>$null | Out-String
            $observed = "launch_result=started;marker_seen_logcat=$($log.Contains($Marker));marker_seen_dumpsys=$($dumpsys.Contains($Marker));secret_key_seen_dumpsys=$($dumpsys.Contains('user-client-secret'))"
            adb shell am force-stop org.codex.pleos.poc
            Launch-Showcase "SHOWCASE_ACC4" @{
                observed = $observed
                preview = "benign_user-client-secret_marker_hash_only;no_marker_literal_in_report"
            }
        }
        "vc6" {
            $pidTarget = (adb shell pidof ai.umos.vehiclecontrol | Out-String).Trim().Split(" ")[0]
            $logDir = "data/_local/runtime_poc_harness/logs"
            New-Item -ItemType Directory -Force -Path $logDir | Out-Null
            $stdout = Join-Path $logDir "vc6_video_frida_stdout.txt"
            $stderr = Join-Path $logDir "vc6_video_frida_stderr.txt"
            Remove-Item $stdout, $stderr -ErrorAction SilentlyContinue
            Launch-Showcase "SHOWCASE_VC6" @{ observed = "pending trigger; target_pid=$pidTarget" }
            $frida = Start-Process -FilePath frida -ArgumentList @("-U", "-p", $pidTarget, "-l", "src/dynamic/hooks/vc-6_vehicle_broadcast_receiver_dry_run.js", "--runtime=v8") -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
            Start-Sleep -Seconds 4
            $broadcast = adb shell am broadcast -n ai.umos.vehiclecontrol/ai.umos.vehiclecontrol.feature.bluetooth.data.VehicleBroadcastReceiver -a ai.umos.android.intent.action.DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS --es macAddress 02:00:00:00:00:01 2>&1 | Out-String
            Start-Sleep -Seconds 6
            if (-not $frida.HasExited) {
                Stop-Process -Id $frida.Id -Force
            }
            $fridaOut = Get-Content $stdout -ErrorAction SilentlyContinue | Out-String
            $observed = "broadcast_result0=$($broadcast.Contains('result=0'));hook_loaded=$($fridaOut.Contains('dry_run_hook_loaded'));onReceive_blocked=$($fridaOut.Contains('dry_run_onReceive_blocked'));db_mutation=false"
            adb shell am force-stop org.codex.pleos.poc
            Launch-Showcase "SHOWCASE_VC6" @{
                observed = $observed
                preview = "action=DEVICE_SUPPORT_ANDROID_AUTO_WIRELESS;macAddress=02:00:00:00:00:01;original_onReceive_blocked"
            }
        }
    }
    Stop-Recording $recording
} finally {
    if ($Scenario -eq "am1") {
        adb emu avd snapshot load codex_pre_am1_video | Out-Host
        Wait-Boot
    }
}
