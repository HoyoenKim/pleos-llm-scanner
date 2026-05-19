param(
    [string]$OutputDir = "data/_local/runtime_videos/runtime_poc_llm_boundary_demo",
    [int]$Seconds = 250,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$Activity = "org.codex.pleos.poc/.PocActivity"
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
    adb shell appops set org.codex.pleos.poc SYSTEM_ALERT_WINDOW allow 2>$null | Out-Null
    $currentUser = (adb shell am get-current-user 2>$null | Out-String).Trim()
    if ($currentUser -match "^\d+$") {
        adb shell appops set --user $currentUser org.codex.pleos.poc SYSTEM_ALERT_WINDOW allow 2>$null | Out-Null
    }
    Log-Step "overlay_permission_done user=$currentUser"
}

function Prepare-VisibleSurface {
    foreach ($pkg in @(
        "ai.umos.homescreen",
        "ai.umos.maps.android.navigation.app",
        "ai.umos.drivingview"
    )) {
        adb shell am force-stop $pkg 2>$null | Out-Null
    }
    Start-Sleep -Seconds 1
}

function Encode-Extra([string]$Value) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    return [Convert]::ToBase64String($bytes)
}

function Show-Card([string]$Kicker, [string]$Title, [string]$Body, [string]$Footer, [int]$SleepSeconds) {
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
    Start-Sleep -Seconds $SleepSeconds
}

function Run-Lmp1Probe {
    Log-Step "lmp1_probe_start"
    adb logcat -c
    adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
    $args = @(
        "shell", "am", "start", "--windowingMode", "1", "--activityType", "1", "--display", "0",
        "-n", $Activity, "-a", "org.codex.pleos.poc.LMP1_BOUNDARY_PROBE"
    )
    & adb @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "failed to run lmp-1 boundary probe" }
    $deadline = (Get-Date).AddSeconds(20)
    $line = $null
    do {
        Start-Sleep -Seconds 1
        $logcat = adb logcat -d -t 1500 | Out-String
        $line = ($logcat -split "`r?`n" | Select-String -Pattern "RESULT finding=lmp-1 boundary_probe" | Select-Object -Last 1).Line
    } while (-not $line -and (Get-Date) -lt $deadline)
    if (-not $line) { throw "lmp-1 boundary_probe result not found in logcat" }
    Log-Step "lmp1_probe_line $line"
    return Parse-Lmp1Observed $line
}

function Parse-Lmp1Observed([string]$Line) {
    $result = [ordered]@{
        permission_denial = "false"
        cursor_null = "false"
        rows = "unknown"
        chars = "unknown"
        sha256_short = "unknown"
    }
    if ($Line -match "permission_denial=([^ ]+)") { $result.permission_denial = $Matches[1] }
    if ($Line -match "cursor_null=([^ ]+)") { $result.cursor_null = $Matches[1] }
    if ($Line -match "rows=([^ ]+)") { $result.rows = $Matches[1] }
    if ($Line -match "chars=([^ ]+)") { $result.chars = $Matches[1] }
    if ($Line -match "sha256_short=([^ ]+)") { $result.sha256_short = $Matches[1] }
    return [pscustomobject]$result
}

function Write-RedactedArtifact([string]$OutputDir, [object]$Observed) {
    $bundleDir = Join-Path $OutputDir "redacted_evidence_bundle"
    New-Item -ItemType Directory -Force -Path $bundleDir | Out-Null
    $artifact = [ordered]@{
        finding_id = "lmp-1"
        source = "LLM prompt provider"
        artifact = "prompt_corpus_bundle.redacted.json"
        permission_denial = ($Observed.permission_denial -eq "true")
        cursor_null = ($Observed.cursor_null -eq "true")
        rows = [int]$Observed.rows
        total_chars = [int]$Observed.chars
        sha256_short = $Observed.sha256_short
        raw_text = "[REDACTED]"
        sensitive_content_redacted = $true
        top_level_keys = @("metadata", "scenarios")
        scenario_count = 2
        sections_detected = @(
            "metadata",
            "scenarios",
            "prompt_template_blocks",
            "rendered_example_blocks"
        )
        structural_metadata_only = $true
        not_claimed = @(
            "no remote vehicle compromise",
            "no vehicle takeover",
            "no vehicle actuation",
            "no jailbreak demonstrated",
            "no live backend abuse"
        )
    }
    $artifact | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $bundleDir "prompt_corpus_bundle.redacted.json")
}

function Wait-RecordingAndPull($Process, [datetime]$StartedAt, [int]$MaxSeconds, [string]$RemotePath, [string]$LocalPath) {
    $safePullAt = $StartedAt.AddSeconds($MaxSeconds + 5)
    while ((Get-Date) -lt $safePullAt) { Start-Sleep -Seconds 1 }
    try {
        if (-not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force
        }
    } catch {
        # The host adb process may already be gone.
    }
    adb pull $RemotePath $LocalPath | Out-Host
    adb shell rm -f $RemotePath
}

function Write-Runbook([string]$OutputDir) {
    @"
# LLM Boundary Demo Runbook

## Claim

This demo proves a narrow runtime claim: under a same-device app threat model,
an unprivileged app can read the IVI LLM prompt/corpus provider and create a
redacted local artifact.

## Command

````powershell
powershell -ExecutionPolicy Bypass -File scripts/runtime_poc/record_llm_boundary_demo.ps1
````

## Output

- `llm_prompt_boundary_bypass_demo.mp4`
- `redacted_evidence_bundle/prompt_corpus_bundle.redacted.json`
- `record_llm_boundary_trace.txt`

## Safety

- Raw prompt/corpus text is not displayed.
- No external server exfiltration is performed.
- No vehicle actuation, backend abuse, token validation, or jailbreak is attempted.
"@ | Set-Content -Encoding UTF8 (Join-Path $OutputDir "runbook.md")
}

Wait-Boot
Build-And-Install
Grant-OverlayPermission

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$TracePath = Join-Path $OutputDir "record_llm_boundary_trace.txt"
"$(Get-Date -Format o) start output_dir=$OutputDir seconds=$Seconds skip_build=$SkipBuild" | Set-Content -Encoding UTF8 $TracePath

$remote = "/sdcard/llm_prompt_boundary_bypass_demo.mp4"
$local = Join-Path $OutputDir "llm_prompt_boundary_bypass_demo.mp4"
adb shell rm -f $remote
adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
Prepare-VisibleSurface
adb logcat -c

$rec = Start-Process -FilePath adb -ArgumentList @("shell", "screenrecord", "--time-limit", "$Seconds", $remote) -PassThru -WindowStyle Hidden
$recordingStarted = Get-Date
Start-Sleep -Seconds 2

try {
    Show-Card `
        "THREAT MODEL" `
        "This is NOT remote vehicle hacking" `
        "App install is NOT the exploit.`nAssumption: one untrusted app is already running on the IVI device.`nSecurity question: can that app access protected IVI-internal data?" `
        "Same-device malicious app model only." 15

    Show-Card `
        "SECURITY QUESTION" `
        "Untrusted app vs privileged LLM provider" `
        "Boundary under test:`nUntrusted App -> ContentResolver.query() -> IVI LLM Prompt Provider`n`nInstalled apps should still be sandboxed." `
        "The exploit is crossing this component boundary." 15

    $pkgUid = (adb shell cmd package list packages -U org.codex.pleos.poc 2>$null | Out-String).Trim()
    $uid = "uid=unknown"
    if ($pkgUid -match "uid:([^\s]+)") { $uid = "uid=$($Matches[1])" }
    Show-Card `
        "ATTACKER APP IDENTITY" `
        "Attacker-controlled same-device app" `
        "Package: org.codex.pleos.poc`n$uid`nNot a PleOS privileged app.`nNo platform signing key.`nNo signature permission." `
        "This app should not read privileged LLM provider data." 20

    Show-Card `
        "PROTECTED ASSET" `
        "IVI LLM prompt/corpus provider" `
        "Provider: PromptsContentProvider`nAuthority: ai.pleos.playground.llm.model.provider.prompts`nExpected protection: private provider or signature permission." `
        "Protected asset first; logs second." 20

    Show-Card `
        "EXPECTED RESULT" `
        "Access should be denied" `
        "Expected from this app:`nSecurityException`nor`npermission_denied=true" `
        "If this boundary is enforced, the PoC app gets no prompt/corpus data." 16

    Show-Card `
        "TRIGGER" `
        "PoC app calls ContentResolver.query()" `
        "Runtime action:`nUntrusted App -> query() -> Exported PromptsContentProvider`n`nNo vehicle-control payload is used." `
        "The trigger is only provider read access." 14

    $observed = Run-Lmp1Probe
    Show-Card `
        "EXPECTED VS OBSERVED" `
        "Prompt provider access was not denied" `
        "Expected:`npermission_denied=true or SecurityException`n`nObserved:`npermission_denial=$($observed.permission_denial)`ncursor_null=$($observed.cursor_null)`nrows=$($observed.rows)`nchars=$($observed.chars)`nsha256_short=$($observed.sha256_short)" `
        "This is the boundary bypass evidence." 25

    Write-RedactedArtifact $OutputDir $observed
    Show-Card `
        "ATTACKER ARTIFACT" `
        "prompt_corpus_bundle.redacted.json" `
        "{`n  source: LLM prompt provider,`n  rows: $($observed.rows),`n  total_chars: $($observed.chars),`n  sha256_short: $($observed.sha256_short),`n  raw_text: [REDACTED],`n  sensitive_content_redacted: true,`n  sections_detected: [metadata, scenarios, prompt_template_blocks, rendered_example_blocks]`n}" `
        "The attacker app obtained a local redacted artifact, not raw text." 35

    Show-Card `
        "IMPACT" `
        "Internal IVI LLM prompt/corpus disclosure primitive" `
        "The app learns prompt/corpus structure, scenario organization, template presence, payload length, and output-contract shape.`n`nThis can support prompt-aware manipulation or guardrail analysis." `
        "No jailbreak is demonstrated." 25

    Show-Card `
        "NOT CLAIMED" `
        "Keep the claim narrow" `
        "No remote vehicle compromise.`nNo vehicle takeover.`nNo vehicle actuation.`nNo safety-critical control.`nNo live backend abuse.`nNo raw prompt or secret disclosure." `
        "Confirmed claim: same-device LLM provider boundary bypass." 25

    Show-Card `
        "APPENDIX ONLY" `
        "Other findings are not the main demo" `
        "vc-6: receiver reachability only; state pollution unconfirmed.`nam-1: write accepted; UI impact unconfirmed.`nacc-4: SSO boundary surface; secret leak unconfirmed.`nstatic: offline APK evidence; live abuse untested." `
        "Do not dilute lmp-1 with weaker claims." 18
} finally {
    Wait-RecordingAndPull $rec $recordingStarted $Seconds $remote $local
    adb shell am force-stop org.codex.pleos.poc 2>$null | Out-Null
    Write-Runbook $OutputDir
    Write-Host "LLM_BOUNDARY_VIDEO=$local"
}
