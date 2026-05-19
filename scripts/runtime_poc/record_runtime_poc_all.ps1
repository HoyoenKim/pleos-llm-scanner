param(
    [string[]]$Scenarios = @("install", "lmp1", "map1", "acc4", "am1", "vc6", "static"),
    [int]$Seconds = 22
)

$ErrorActionPreference = "Stop"

python scripts/runtime_poc/research_runtime_poc_harness.py --build
if ($LASTEXITCODE -ne 0) {
    throw "harness build failed"
}
adb uninstall org.codex.pleos.poc 2>$null | Out-Null
adb install -r data/_local/runtime_poc_harness/poc-harness-signed.apk | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "harness install failed"
}

foreach ($scenario in $Scenarios) {
    powershell -ExecutionPolicy Bypass -File scripts/runtime_poc/record_runtime_poc_scenario.ps1 -Scenario $scenario -Seconds $Seconds -SkipBuild
}
