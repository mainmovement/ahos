#Requires -Version 5.1
# Self-test: ops-artifact dirty paths must NOT block reconcile re-runs.
# Encoding: ASCII-only + UTF-8 BOM (WinPS 5.1 safe).
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $ScriptDir "windows_post_merge_reconcile.ps1"
if (-not (Test-Path -LiteralPath $Target)) { throw "missing $Target" }

$raw = Get-Content -LiteralPath $Target -Raw
$start = $raw.IndexOf("function Test-AllowedOpsDirtyPath")
if ($start -lt 0) { throw "Test-AllowedOpsDirtyPath not found in reconcile script" }
$brace = $raw.IndexOf("{", $start)
$depth = 0
$end = -1
for ($i = $brace; $i -lt $raw.Length; $i++) {
    $ch = $raw[$i]
    if ($ch -eq "{") { $depth++ }
    elseif ($ch -eq "}") {
        $depth--
        if ($depth -eq 0) { $end = $i; break }
    }
}
if ($end -lt 0) { throw "could not find end of Test-AllowedOpsDirtyPath" }
$fn = $raw.Substring($start, $end - $start + 1)

$Protected = @(
    ".gitignore",
    "deployment/docker-compose.windows.yml",
    "reports/backup_restore_drill.json"
)
Invoke-Expression $fn

$mustAllow = @(
    "reports/windows_post_merge_reconcile_20260828_231950.json",
    "reports/windows_post_merge_reconcile_20260828_231950.normalized.json",
    "reports/windows_ops_last_run.log",
    "reports/LATEST_WINDOWS_GATE.txt",
    "reports/OWNER_PASTE_WINDOWS_GATE.txt",
    "reports/windows_gate_evidence/OWNER_PASTE_WINDOWS_GATE.txt",
    ".gitignore",
    "deployment/docker-compose.windows.yml",
    "reports/backup_restore_drill.json"
)
$mustBlock = @(
    "scripts/hack.ps1",
    "web_api_auth.ts",
    "app/page.tsx",
    "reports/other_owner_notes.md"
)

$fail = 0
foreach ($p in $mustAllow) {
    if (-not (Test-AllowedOpsDirtyPath $p)) {
        Write-Host ("FAIL allow: " + $p) -ForegroundColor Red
        $fail++
    } else {
        Write-Host ("OK allow: " + $p) -ForegroundColor Green
    }
}
foreach ($p in $mustBlock) {
    if (Test-AllowedOpsDirtyPath $p) {
        Write-Host ("FAIL block: " + $p) -ForegroundColor Red
        $fail++
    } else {
        Write-Host ("OK block: " + $p) -ForegroundColor Green
    }
}

# Reproduce owner evidence status line classification
$statusShort = @("?? reports/windows_post_merge_reconcile_20260828_231950.json")
$dirtyPaths = @()
foreach ($line in $statusShort) {
    $path = $line.Substring(3).Trim()
    $dirtyPaths += $path
}
$unexpected = @($dirtyPaths | Where-Object { -not (Test-AllowedOpsDirtyPath $_) })
if ($unexpected.Count -ne 0) {
    Write-Host ("FAIL owner-evidence should be allowed; unexpected=" + ($unexpected -join ",")) -ForegroundColor Red
    $fail++
} else {
    Write-Host "OK owner-evidence dirty path allowed (no STOP)" -ForegroundColor Green
}

if ($fail -gt 0) {
    Write-Host ("FAILED checks=" + $fail) -ForegroundColor Red
    exit 1
}
Write-Host "ALL OK -- reconcile dirty allowlist covers ops artifacts" -ForegroundColor Cyan
exit 0
