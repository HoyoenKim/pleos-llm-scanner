param(
    [string]$OutputDir = "data/poc_evidence",
    [string]$Marker = ("CODEX_SAFE_MARKER_" + (Get-Date -Format "yyyyMMdd_HHmmss")),
    [string]$Am1PackageName = "org.codex.safe.marker.notinstalled",
    [switch]$SkipBuild,
    [switch]$SkipInstall,
    [switch]$SkipUi,
    [switch]$RunVc6
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = "C:\Users\cabin\Miniconda3\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$HarnessScript = Join-Path $RepoRoot "scripts\research_runtime_poc_harness.py"
$HarnessApk = Join-Path $RepoRoot "data\runtime_poc_harness\poc-harness-signed.apk"
$Activity = "org.codex.pleos.poc/.PocActivity"
$Am1Action = "org.codex.pleos.poc.AM1_EVIDENCE_PROBE"
$Am1InsertAction = "org.codex.pleos.poc.AM1_SUGGESTION"
$Am1CleanupAction = "org.codex.pleos.poc.AM1_CLEANUP"
$AppMarketActivity = "ai.umos.appmarket/.MainActivity"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunDir = Join-Path (Join-Path $RepoRoot $OutputDir) ("am-1\" + $RunStamp)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Save-Lines([string]$Path, [string[]]$Lines) {
    $Lines | Set-Content -Encoding UTF8 $Path
}

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

function Save-Screenshot([string]$Path) {
    $cmdPath = $Path.Replace("/", "\")
    cmd /c "adb exec-out screencap -p > `"$cmdPath`""
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
            Save-Lines (Join-Path $RunDir "install.txt") @($installOut, $uninstallOut, $retryOut)
        } else {
            Save-Lines (Join-Path $RunDir "install.txt") @($installOut)
        }
    }

    Invoke-Adb @("logcat", "-c") | Out-Null
    $startOut = Invoke-Adb @(
        "shell", "am", "start", "-W",
        "-n", $Activity,
        "-a", $Am1Action,
        "--es", "marker", $Marker,
        "--es", "am1_package_name", $Am1PackageName
    )
    Start-Sleep -Seconds 2
    $logcat = Invoke-Adb @("logcat", "-d", "-t", "600")
    $resultLine = (($logcat -split "`r?`n") | Select-String -Pattern "RESULT finding=am-1 evidence_probe" | Select-Object -Last 1).Line
    if (-not $resultLine) { $resultLine = "" }

    Save-Lines (Join-Path $RunDir "am1_start.txt") @($startOut)
    Save-Lines (Join-Path $RunDir "am1_logcat_redacted.txt") (($logcat -split "`r?`n") | Select-String -Pattern "CodexPoc|Suggestions" | ForEach-Object { $_.Line })
    Save-Lines (Join-Path $RunDir "am1_result_line.txt") @($resultLine)

    $l2 = $false
    if ($resultLine -match "l2_provider_write_confirmed=true") { $l2 = $true }

    $uiMarkerSeen = $false
    $uiOut = ""
    if (-not $SkipUi) {
        try {
            Invoke-Adb @("logcat", "-c") | Out-Null
            $insertForUiOut = Invoke-Adb @(
                "shell", "am", "start", "-W",
                "-n", $Activity,
                "-a", $Am1InsertAction,
                "--es", "marker", $Marker,
                "--es", "am1_package_name", $Am1PackageName
            )
            Start-Sleep -Seconds 1
            $uiOut = Invoke-Adb @(
                "shell", "am", "start", "-W",
                "-n", $AppMarketActivity,
                "-a", "android.intent.action.SEARCH",
                "--es", "query", $Marker
            )
            Start-Sleep -Seconds 3
            Save-Screenshot (Join-Path $RunDir "am1_ui_search.png")
            Invoke-Adb @("shell", "uiautomator", "dump", "/sdcard/codex_am1_window.xml") | Out-Null
            $uiXml = Invoke-Adb @("exec-out", "cat", "/sdcard/codex_am1_window.xml")
            Save-Lines (Join-Path $RunDir "am1_ui_window.xml") @($uiXml)
            $uiMarkerSeen = $uiXml.Contains($Marker)
            $cleanupOut = Invoke-Adb @(
                "shell", "am", "start", "-W",
                "-n", $Activity,
                "-a", $Am1CleanupAction,
                "--es", "marker", $Marker
            )
            $uiLogcat = Invoke-Adb @("logcat", "-d", "-t", "600")
            Save-Lines (Join-Path $RunDir "am1_ui_insert_cleanup.txt") @($insertForUiOut, $cleanupOut)
            Save-Lines (Join-Path $RunDir "am1_ui_logcat_redacted.txt") (($uiLogcat -split "`r?`n") | Select-String -Pattern "CodexPoc|Suggestions" | ForEach-Object { $_.Line })
        } catch {
            $uiOut = "ui_check_exception=$($_.Exception.GetType().FullName) message=$($_.Exception.Message)"
        }
    }

    Save-Lines (Join-Path $RunDir "am1_ui_start.txt") @($uiOut)

    Save-Lines (Join-Path $RunDir "README.md") @(
        "# am-1 PoC Evidence Run",
        "",
        "- marker: $Marker",
        "- package_name: $Am1PackageName",
        "- provider: content://ai.umos.appmarket.globalsearch.Suggestions",
        "- action: $Am1Action",
        "- l2_provider_write_confirmed: $l2",
        "- l3_ui_impact_confirmed: $uiMarkerSeen",
        "",
        "## Result Line",
        "",
        '```text',
        $resultLine,
        '```',
        "",
        "## Claim",
        "",
        "If `l2_provider_write_confirmed=true`, the allowed claim is: same-device unprivileged app can write/read a provider-local AppMarket suggestion marker.",
        "If `l3_ui_impact_confirmed=true`, the allowed claim is upgraded to: marker became visible in AppMarket/global search UI under lab conditions.",
        "Do not claim install hijack, AppMarket compromise, credential abuse, or full vehicle compromise."
    )

    if ($RunVc6) {
        $vc6Script = Join-Path $RepoRoot "scripts\record_improved_poc_impact_demo.ps1"
        Save-Lines (Join-Path $RunDir "vc6_note.txt") @(
            "Run vc-6 via existing state-check implementation in:",
            $vc6Script,
            "Use its Run-Vc6StateCheck logic: pre-count, benign broadcast, post-count, cleanup."
        )
    }

    Write-Host "RUN_DIR=$RunDir"
    Write-Host "AM1_RESULT=$resultLine"
    Write-Host "L2_PROVIDER_WRITE_CONFIRMED=$l2"
    Write-Host "L3_UI_IMPACT_CONFIRMED=$uiMarkerSeen"
} finally {
    Pop-Location
}
