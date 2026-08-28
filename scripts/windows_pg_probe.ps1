#Requires -Version 5.1
<#
.SYNOPSIS
  Probe DATABASE_URL / Docker Postgres for One-Brain snapshot queries (STATE B).

Used when scripts/ahos_pg_probe.mjs is not yet unlocked onto the working tree
(main unlock bats historically checkout only scripts/windows_*.ps1).

Exit 0 = ahos_system_state readable.
Exit 2 = blocked.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$JsonOut = "",
  [string]$ContainerName = "ahos_postgres_win"
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

function Redact-Url([string]$Url) {
  if ([string]::IsNullOrWhiteSpace($Url)) { return "" }
  try { return [regex]::Replace($Url, '(:[^:@/]+)@', ':***@') } catch { return "(set)" }
}

$envPath = Join-Path $RepoRoot ".env"
$dbUrl = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
$pgUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
$pgDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "ahos_user" }
if ([string]::IsNullOrWhiteSpace($pgDb)) { $pgDb = "ahos" }

$report = [ordered]@{
  schema = "ahos.pg_probe.v1"
  ok = $false
  database_url_set = -not [string]::IsNullOrWhiteSpace($dbUrl)
  database_url_redacted = (Redact-Url $dbUrl)
  error_class = $null
  error = $null
  system_state_rows = $null
  ahos_table_count = $null
  probe_via = $null
  note = "STATE B: no db:migrate / db:push"
}

# Prefer node probe when present (matches Next pg driver).
$mjs = Join-Path $RepoRoot "scripts\ahos_pg_probe.mjs"
if ((Test-Path -LiteralPath $mjs) -and (Get-Command node -ErrorAction SilentlyContinue)) {
  $tmp = Join-Path $RepoRoot "reports\pg_probe_latest.json"
  New-Item -ItemType Directory -Force -Path (Split-Path $tmp) | Out-Null
  $out = & node $mjs --json-out $tmp 2>&1 | Out-String
  $code = $LASTEXITCODE
  try {
    $j = $out | ConvertFrom-Json
    $report.ok = [bool]$j.ok
    $report.error_class = $j.error_class
    $report.error = $j.error
    $report.system_state_rows = $j.system_state_rows
    $report.ahos_table_count = $j.ahos_table_count
    $report.database_url_redacted = $j.database_url_redacted
    $report.probe_via = "node_ahos_pg_probe_mjs"
  } catch {
    $report.error_class = "CONFIG_OR_TIMEOUT"
    $report.error = ("node probe parse failed: " + $_.Exception.Message)
    $report.probe_via = "node_ahos_pg_probe_mjs"
  }
  if ($code -eq 0) { $report.ok = $true }
} else {
  # Fallback: docker exec psql inside ahos_postgres_win (unlock-safe; no mjs required).
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $report.error_class = "CONFIG_OR_TIMEOUT"
    $report.error = "docker not on PATH and ahos_pg_probe.mjs unavailable"
    $report.probe_via = "none"
  } else {
    $running = (& docker ps --format "{{.Names}}" 2>$null)
    if ($running -notmatch [regex]::Escape($ContainerName)) {
      $report.error_class = "CONN_REFUSED"
      $report.error = ($ContainerName + " not running")
      $report.probe_via = "docker_exec_missing_container"
    } else {
      $sql = "SELECT COUNT(*)::int AS n FROM ahos_system_state; SELECT COUNT(*)::int AS n FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'ahos_%';"
      $raw = & docker exec $ContainerName psql -U $pgUser -d $pgDb -t -A -c $sql 2>&1 | Out-String
      if ($LASTEXITCODE -ne 0) {
        $report.error_class = "QUERY_OR_OTHER"
        $msg = $raw.Trim()
        if ($msg -match "password authentication failed") { $report.error_class = "AUTH_FAILED" }
        if ($msg -match "does not exist") { $report.error_class = "RELATION_MISSING" }
        $report.error = $msg
        $report.probe_via = "docker_exec_psql"
      } else {
        $nums = @()
        foreach ($line in ($raw -split "`n")) {
          $t = $line.Trim()
          if ($t -match '^\d+$') { $nums += [int]$t }
        }
        if ($nums.Count -ge 1) { $report.system_state_rows = $nums[0] }
        if ($nums.Count -ge 2) { $report.ahos_table_count = $nums[1] }
        $report.ok = $true
        $report.probe_via = "docker_exec_psql"
        # Note: docker exec proves container SQL; host Next still needs matching DATABASE_URL.
      }
    }
  }
}

$json = ($report | ConvertTo-Json -Depth 5 -Compress:$false)
# After container-ok, also verify HOST DATABASE_URL (what Next uses) via inline node+pg.
if ($report.ok -and $report.probe_via -eq "docker_exec_psql" -and -not [string]::IsNullOrWhiteSpace($dbUrl)) {
  if (Get-Command node -ErrorAction SilentlyContinue) {
    $inline = @'
const { config } = require("dotenv");
const path = require("path");
config({ path: path.join(process.cwd(), ".env") });
const pg = require("pg");
const url = (process.env.DATABASE_URL || "").trim();
(async () => {
  const c = new pg.Client({ connectionString: url, connectionTimeoutMillis: 8000 });
  try {
    await c.connect();
    const r = await c.query("SELECT COUNT(*)::int AS n FROM ahos_system_state");
    console.log(JSON.stringify({ ok: true, n: r.rows[0].n }));
    await c.end();
    process.exit(0);
  } catch (e) {
    console.log(JSON.stringify({ ok: false, error: String(e.message || e) }));
    process.exit(2);
  }
})();
'@
    $tmpJs = Join-Path $RepoRoot "reports\_pg_host_probe_tmp.js"
    New-Item -ItemType Directory -Force -Path (Split-Path $tmpJs) | Out-Null
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tmpJs, $inline, $utf8NoBom)
    $hostOut = & node $tmpJs 2>&1 | Out-String
    Remove-Item -LiteralPath $tmpJs -Force -ErrorAction SilentlyContinue
    try {
      $hj = $hostOut | ConvertFrom-Json
      if (-not $hj.ok) {
        $report.ok = $false
        $report.probe_via = "docker_ok_host_DATABASE_URL_fail"
        $msg = [string]$hj.error
        $report.error = $msg
        if ($msg -match "password authentication failed") { $report.error_class = "AUTH_FAILED" }
        elseif ($msg -match "ECONNREFUSED") { $report.error_class = "CONN_REFUSED" }
        elseif ($msg -match "does not exist") { $report.error_class = "RELATION_MISSING" }
        else { $report.error_class = "QUERY_OR_OTHER" }
      } else {
        $report.probe_via = "docker_exec_plus_host_node_pg"
        $report.system_state_rows = $hj.n
      }
    } catch {
      # Keep docker ok if host inline probe could not parse; still useful signal.
      $report.probe_via = "docker_exec_psql_host_probe_unparsed"
    }
    $json = ($report | ConvertTo-Json -Depth 5 -Compress:$false)
  }
}

if (-not [string]::IsNullOrWhiteSpace($JsonOut)) {
  $dir = Split-Path -Parent $JsonOut
  if (-not [string]::IsNullOrWhiteSpace($dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($JsonOut, $json + "`n", $utf8)
}
Write-Output $json
if ($report.ok) { exit 0 } else { exit 2 }
