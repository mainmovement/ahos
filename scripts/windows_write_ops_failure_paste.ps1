#Requires -Version 5.1
<#
.SYNOPSIS
  Write OWNER_PASTE diagnostic when Windows ops fails mid-bat (before gate).

Does NOT invent PRE_SOAK / OPERATOR_READY. Does NOT db:migrate.
Always safe to paste into Cursor so the agent can remediate.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [Parameter(Mandatory = $true)][string]$Stage,
  [string]$Detail = "",
  [int]$ExitHint = 2
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location $RepoRoot

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

$reports = Join-Path $RepoRoot "reports"
if (-not (Test-Path -LiteralPath $reports)) {
  New-Item -ItemType Directory -Path $reports -Force | Out-Null
}

$envPath = Join-Path $RepoRoot ".env"
$tok = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"
$pub = Get-EnvValue -Path $envPath -Key "NEXT_PUBLIC_AHOS_WEB_API_TOKEN"
$db = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
$gw = Get-EnvValue -Path $envPath -Key "AHOS_GATEWAY_URL"
$pgPass = Get-EnvValue -Path $envPath -Key "POSTGRES_PASSWORD"

$head = "UNKNOWN"
$branch = "UNKNOWN"
try { $head = (& git rev-parse --short HEAD 2>$null).Trim() } catch {}
try { $branch = (& git rev-parse --abbrev-ref HEAD 2>$null).Trim() } catch {}

$dockerDaemon = "unknown"
$pgRunning = "unknown"
try {
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    & docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $dockerDaemon = "ok"
      $names = (& docker ps --format "{{.Names}}" 2>$null) -join " "
      $pgRunning = if ($names -match "ahos_postgres_win") { "yes" } else { "no" }
    } else {
      $dockerDaemon = "down"
      $pgRunning = "no"
    }
  } else {
    $dockerDaemon = "docker_missing"
    $pgRunning = "docker_missing"
  }
} catch {
  $dockerDaemon = "error"
  $pgRunning = "error"
}

$censusLine = "n/a"
try {
  $py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $py)) { $py = "python" }
  $censusLine = & $py -c @"
import json
try:
  from architecture.learning.prediction_lifecycle import lifecycle_status
  st = lifecycle_status()
  obs = sum(int(v) for v in (st.get('observation_state') or {}).values())
  print('discovery=%s predictions=%s observation_state_total=%s' % (
    st.get('discovery_observations'), st.get('local_predictions'), obs))
except Exception as e:
  print('error=%s:%s' % (type(e).__name__, e))
"@
} catch { $censusLine = "census_failed" }

$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$logPath = Join-Path $reports "windows_ops_last_run.log"
$logTail = @()
if (Test-Path -LiteralPath $logPath) {
  $logTail = Get-Content -LiteralPath $logPath -Tail 80 -ErrorAction SilentlyContinue
}

# Infer the PRE_SOAK (G1-G10) blocker without inventing PASS/READY.
$likely = "unknown"
$nextAction = "Re-run AHOS_WINDOWS_OPS.bat after fixing FAILs; paste OWNER_PASTE."
$tokenOk = -not [string]::IsNullOrWhiteSpace($tok)
$gwOk = -not [string]::IsNullOrWhiteSpace($gw)
if ($Stage -eq "wait_web_api" -or $Detail -match "api/chat" -or $Detail -match "500") {
  if ($dockerDaemon -ne "ok" -or $pgRunning -ne "yes") {
    $likely = "G2_blocked_by_docker_postgres"
    $nextAction = "Start Docker Desktop (green), confirm docker ps + ahos_postgres_win, restart Next, re-run bat."
  } else {
    $likely = "G2_chat_error_with_postgres_up"
    $nextAction = "Check Next window errors; confirm AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat; re-run bat."
  }
} elseif (-not $tokenOk) {
  $likely = "token_unset"
  $nextAction = "Run windows_ensure_web_api_token.ps1 then restart Next / re-run bat."
} elseif (-not $gwOk) {
  $likely = "gateway_url_empty"
  $nextAction = "Run windows_ensure_web_api_token.ps1 (fills AHOS_GATEWAY_URL) then re-run bat."
} elseif ($dockerDaemon -ne "ok") {
  $likely = "docker_daemon_down"
  $nextAction = "Start Docker Desktop Linux Engine, wait green, docker ps, re-run bat."
}

$lines = @()
$lines += "===== BEGIN WINDOWS OPS FAILURE PASTE (into Cursor) ====="
$lines += ("generated_utc=" + $stamp)
$lines += ("stage=" + $Stage)
$lines += ("detail=" + $Detail)
$lines += ("exit_hint=" + $ExitHint)
$lines += ("git_branch=" + $branch)
$lines += ("git_head=" + $head)
$lines += ("host=windows_ops_bat")
$lines += ("AHOS_WEB_API_TOKEN_set=" + $tokenOk)
$lines += ("NEXT_PUBLIC_match=" + (($pub -eq $tok) -and $tokenOk))
$lines += ("AHOS_GATEWAY_URL_set=" + $gwOk)
if ($gwOk) { $lines += ("AHOS_GATEWAY_URL=" + $gw) } else { $lines += "AHOS_GATEWAY_URL=" }
$lines += ("DATABASE_URL_set=" + (-not [string]::IsNullOrWhiteSpace($db)))
$lines += ("POSTGRES_PASSWORD_set=" + (-not [string]::IsNullOrWhiteSpace($pgPass)))
$lines += ("docker_daemon=" + $dockerDaemon)
$lines += ("ahos_postgres_win=" + $pgRunning)
$lines += ("sqlite_census=" + $censusLine)
$lines += ("likely_pre_soak_blocker=" + $likely)
$lines += ("next_action=" + $nextAction)
$lines += "pre_soak_entry_ok=false"
$lines += "operator_ready=false"
$lines += "STATE B: do not db:migrate / db:push"
$lines += "NOTE: This is a mid-bat failure paste -- not a full G1-G11 gate report."
$lines += "--- windows_ops_last_run.log (tail) ---"
$lines += $logTail
$lines += "===== END WINDOWS OPS FAILURE PASTE ====="

$utf8 = New-Object System.Text.UTF8Encoding $false
$paste = Join-Path $reports "OWNER_PASTE_WINDOWS_GATE.txt"
$slim = Join-Path $reports "OWNER_PASTE_WINDOWS_GATE_SLIM.txt"
$body = ($lines -join "`n") + "`n"
[System.IO.File]::WriteAllText($paste, $body, $utf8)
[System.IO.File]::WriteAllText($slim, $body, $utf8)

$latest = Join-Path $reports "LATEST_WINDOWS_GATE.txt"
$latestLines = @(
  "status=OPS_STAGE_FAIL",
  ("stage=" + $Stage),
  ("detail=" + $Detail),
  ("likely_pre_soak_blocker=" + $likely),
  ("next_action=" + $nextAction),
  "pre_soak_entry_ok=false",
  "operator_ready=false",
  ("git_head=" + $head),
  ("docker_daemon=" + $dockerDaemon),
  ("ahos_postgres_win=" + $pgRunning),
  ("paste=" + $paste)
)
[System.IO.File]::WriteAllText($latest, ($latestLines -join "`n") + "`n", $utf8)

Write-Host ("Wrote failure paste: " + $paste) -ForegroundColor Yellow

$publish = Join-Path $RepoRoot "scripts\windows_publish_owner_paste.ps1"
if (Test-Path -LiteralPath $publish) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $publish -PastePath $paste
} else {
  try {
    Set-Clipboard -Value $body
    Write-Host "Copied failure paste to clipboard -- Ctrl+V into Cursor." -ForegroundColor Green
  } catch {}
  try {
    Start-Process -FilePath "notepad.exe" -ArgumentList $paste | Out-Null
  } catch {}
}

# Best-effort gh comment on open/merged unlock PRs
$postGh = Join-Path $RepoRoot "scripts\windows_post_gate_paste_gh.ps1"
if (Test-Path -LiteralPath $postGh) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $postGh -BodyFile $slim -RepoRoot $RepoRoot
}

$pushEv = Join-Path $RepoRoot "scripts\windows_push_gate_evidence.ps1"
if (Test-Path -LiteralPath $pushEv) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $pushEv -RepoRoot $RepoRoot -PastePath $paste -SlimPath $slim -LatestPath $latest
}

exit 0
