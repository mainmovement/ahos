#Requires -Version 5.1
<#
.SYNOPSIS
  Extract exact /api/chat HTTP 500 root cause (stack/message) on Windows.

Compares:
  1) POST /api/chat body (sanitizePublicError + stack_top after fix)
  2) GET /api/command soft-fail lastError (same commandSnapshot path)
  3) node scripts/ahos_pg_probe.mjs against DATABASE_URL

STATE B: no migrate. Lane-A untouched. Does not invent PRE_SOAK/READY.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$ChatUrl = "http://127.0.0.1:3000/api/chat",
  [string]$CommandUrl = "http://127.0.0.1:3000/api/command"
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location -LiteralPath $RepoRoot

function Get-EnvValue([string]$Path, [string]$Key) {
  if (-not (Test-Path -LiteralPath $Path)) { return "" }
  foreach ($line in (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
    $t = $line.Trim()
    if ($t.StartsWith("#") -or ($t.IndexOf("=") -lt 1)) { continue }
    $k = $t.Substring(0, $t.IndexOf("=")).Trim()
    if ($k -ne $Key) { continue }
    $v = $t.Substring($t.IndexOf("=") + 1).Trim()
    if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
      $v = $v.Substring(1, $v.Length - 2)
    }
    return $v
  }
  return ""
}

function Invoke-Json([string]$Method, [string]$Url, [hashtable]$Headers, [string]$Body) {
  $result = @{
    ok = $false
    status = 0
    body = ""
    error = ""
  }
  try {
    if ($Method -eq "GET") {
      $r = Invoke-WebRequest -Uri $Url -Method GET -Headers $Headers -UseBasicParsing -TimeoutSec 45
    } else {
      $r = Invoke-WebRequest -Uri $Url -Method POST -Headers $Headers -Body $Body -UseBasicParsing -TimeoutSec 45
    }
    $result.ok = $true
    $result.status = [int]$r.StatusCode
    $result.body = [string]$r.Content
  } catch {
    $result.error = $_.Exception.Message
    try {
      $resp = $_.Exception.Response
      if ($null -ne $resp) {
        $result.status = [int]$resp.StatusCode
        $stream = $resp.GetResponseStream()
        if ($null -ne $stream) {
          $reader = New-Object System.IO.StreamReader($stream)
          $result.body = $reader.ReadToEnd()
          $reader.Close()
        }
      }
    } catch {}
  }
  return $result
}

$envPath = Join-Path $RepoRoot ".env"
$tok = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"
$headers = @{ "Content-Type" = "application/json" }
if (-not [string]::IsNullOrWhiteSpace($tok)) {
  $headers["Authorization"] = "Bearer " + $tok
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS /api/chat 500 forensics (G2 only / STATE B)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$probe = Join-Path $RepoRoot "scripts\ahos_pg_probe.mjs"
$probeOut = Join-Path $RepoRoot "reports\pg_probe_latest.json"
$pgJson = ""
if (Test-Path -LiteralPath $probe) {
  Write-Host "==> pg probe (DATABASE_URL)" -ForegroundColor Cyan
  $pgJson = & node $probe --json-out $probeOut 2>&1 | Out-String
  Write-Host $pgJson
}

Write-Host ("==> POST " + $ChatUrl) -ForegroundColor Cyan
$chat = Invoke-Json -Method "POST" -Url $ChatUrl -Headers $headers -Body '{"message":"ping","locale":"fa"}'
Write-Host ("chat_http=" + $chat.status) -ForegroundColor Yellow
if ($chat.body) { Write-Host ("chat_body=" + $chat.body.Substring(0, [Math]::Min(800, $chat.body.Length))) }

Write-Host ("==> GET " + $CommandUrl) -ForegroundColor Cyan
$cmd = Invoke-Json -Method "GET" -Url $CommandUrl -Headers $headers -Body ""
Write-Host ("command_http=" + $cmd.status) -ForegroundColor Yellow
$cmdSnippet = ""
if ($cmd.body) {
  try {
    $j = $cmd.body | ConvertFrom-Json
    $cmdSnippet = "lastCycleStatus=" + $j.state.lastCycleStatus + " lastError=" + $j.state.lastError
    if ($j.health -and $j.health.dimensions -and $j.health.dimensions.Count -gt 0) {
      $cmdSnippet += " health0=" + $j.health.dimensions[0].evidenceFa
    }
  } catch {
    $cmdSnippet = $cmd.body.Substring(0, [Math]::Min(400, $cmd.body.Length))
  }
  Write-Host ("command_diag=" + $cmdSnippet)
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reports = Join-Path $RepoRoot "reports"
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$paste = Join-Path $reports ("OWNER_PASTE_CHAT_500_" + $stamp + ".txt")
$lines = @()
$lines += "===== BEGIN WINDOWS CHAT 500 FORENSICS PASTE ====="
$lines += ("generated_local=" + (Get-Date -Format "o"))
$lines += "focus=G2_/api/chat_only"
$lines += "STATE_B=no_db_migrate_no_db_push"
$lines += ("chat_url=" + $ChatUrl)
$lines += ("chat_http=" + $chat.status)
$lines += ("chat_body=" + $(if ($chat.body) { $chat.body.Substring(0, [Math]::Min(1200, $chat.body.Length)) } else { $chat.error }))
$lines += ("command_http=" + $cmd.status)
$lines += ("command_diag=" + $cmdSnippet)
$lines += "pg_probe_json="
$lines += $pgJson.Trim()
$lines += "remediation_if_AUTH_FAILED=powershell -ExecutionPolicy Bypass -File .\\scripts\\windows_ensure_database_url.ps1 then windows_restart_next_dev.ps1"
$lines += "remediation_if_CONN_REFUSED=scripts\\windows_ensure_postgres_win.ps1 then restart Next"
$lines += "===== END WINDOWS CHAT 500 FORENSICS PASTE ====="
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines($paste, $lines, $utf8Bom)
Write-Host ("Wrote " + $paste) -ForegroundColor Green

# Classify exit: 0 only if chat is non-5xx
if ($chat.status -ge 200 -and $chat.status -lt 500) {
  Write-Host "CHAT_OK (non-5xx) -- G2 path likely unblocked" -ForegroundColor Green
  exit 0
}
Write-Host "CHAT_5XX -- paste file above into Cursor (includes exact error message / stack_top)" -ForegroundColor Red
exit 2
