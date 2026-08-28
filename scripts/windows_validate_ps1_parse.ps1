#Requires -Version 5.1
<#
.SYNOPSIS
  Parse-check all scripts/windows_*.ps1 before AHOS_WINDOWS_OPS continues.

Fails fast with a clear message if PS 5.1 cannot parse a script (encoding/syntax).
Does NOT invent READY. Does NOT db:migrate.
Exit 0 = all parse OK; 2 = parse failure.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows PS1 parse preflight (no READY claim)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$scripts = Get-ChildItem -LiteralPath (Join-Path $RepoRoot "scripts") -Filter "windows_*.ps1" -ErrorAction SilentlyContinue |
  Sort-Object Name

if (-not $scripts -or $scripts.Count -eq 0) {
  Write-Host "  [FAIL] no scripts\windows_*.ps1 found" -ForegroundColor Red
  exit 2
}

$fail = 0
foreach ($f in $scripts) {
  $tokens = $null
  $errors = $null
  try {
    $null = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errors)
  } catch {
    Write-Host ("  [FAIL] " + $f.Name + " - parser exception: " + $_.Exception.Message) -ForegroundColor Red
    $fail++
    continue
  }
  if ($errors -and $errors.Count -gt 0) {
    Write-Host ("  [FAIL] " + $f.Name) -ForegroundColor Red
    foreach ($e in $errors) {
      Write-Host ("         line " + $e.Extent.StartLineNumber + ": " + $e.Message) -ForegroundColor DarkYellow
    }
    $fail++
  } else {
    Write-Host ("  [OK] " + $f.Name) -ForegroundColor Green
  }
}

if ($fail -gt 0) {
  Write-Host ("PARSE_PREFLIGHT_FAIL count=" + $fail) -ForegroundColor Red
  Write-Host "Fix encoding/syntax (ASCII + UTF-8 BOM), then re-run AHOS_WINDOWS_OPS.bat" -ForegroundColor Yellow
  Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
  exit 2
}

Write-Host ("PARSE_PREFLIGHT_OK count=" + $scripts.Count) -ForegroundColor Green
exit 0
