# ==============================================================================
# Restore owner-preserved files from the reconcile temp backup (optional)
#
# Usage (ONLY if you still have the preserve folder from the script):
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_restore_owner_preserve.ps1 `
#     -PreserveDir "$env:TEMP\ahos_owner_preserve_YYYYMMDD_HHMMSS"
#
# Never runs migrate/reset/stash.
# ==============================================================================

param(
    [Parameter(Mandatory = $true)]
    [string]$PreserveDir,
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}

if (-not (Test-Path -LiteralPath $PreserveDir)) {
    throw ("PreserveDir not found: " + $PreserveDir)
}

$Map = @{
    ".gitignore" = ".gitignore"
    "deployment__docker-compose.windows.yml" = "deployment/docker-compose.windows.yml"
    "reports__backup_restore_drill.json" = "reports/backup_restore_drill.json"
}

Write-Host ("Repo: " + $RepoRoot)
Write-Host ("From: " + $PreserveDir)

foreach ($pair in $Map.GetEnumerator()) {
    $src = Join-Path $PreserveDir $pair.Key
    $dst = Join-Path $RepoRoot $pair.Value
    if (-not (Test-Path -LiteralPath $src)) {
        Write-Host ("  skip missing backup: " + $pair.Key) -ForegroundColor Yellow
        continue
    }
    $parent = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    Write-Host ("  restored " + $pair.Value) -ForegroundColor Green
}

Write-Host "Done. Run: git status --short"
