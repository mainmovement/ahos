#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure .env DATABASE_URL can run One-Brain snapshot queries (STATE B / no migrate).

  M10 (2026-10-07): the native embedded backend is the default. Two backends,
  selected by the DATABASE_URL scheme (db/index.ts):

    postgresql://user:pass@host:5432/db   node-postgres Pool (Docker / standalone)
    pglite:<dataDir>                      embedded PostgreSQL 16 (PGlite), no port,
                                         no service - the native default

  Strategy (unchanged for the Postgres path, new for the native path):
    1) If DATABASE_URL is set, probe it FIRST. A working URL is never
       overwritten, even when it differs from POSTGRES_* text (the container
       volume may still use the original password).
    2) If DATABASE_URL is set AND is a pglite: URL AND the probe fails, the
       script does NOT fall back to the POSTGRES_* synthesis - that would
       silently flip the backend the owner chose. It reports and points at the
       store-init tooling instead.
    3) If DATABASE_URL is empty, prefer the native backend: write
       pglite:<AHOS_PGLITE_DATA_DIR> and probe it. Only when the native path is
       unavailable does it fall back to the POSTGRES_* synthesis.
    4) Never overwrite a working DATABASE_URL. Never wipe a store. Never create
       a store without the -InitializePglite opt-in (an empty directory is not a
       store; only PG_VERSION proves PGlite initialised it).

  Does NOT db:migrate / db:push. Does NOT touch Lane-A. Does NOT claim READY.
  Never prints a password (the pglite URL carries none).
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$NoWrite,
  [switch]$InitializePglite
)

$ErrorActionPreference = "Stop"

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

function Set-EnvValue([string]$Path, [string]$Key, [string]$Value) {
  $lines = @()
  $found = $false
  if (Test-Path -LiteralPath $Path) {
    foreach ($line in (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
      $t = $line.Trim()
      if (-not $t.StartsWith("#") -and ($t.IndexOf("=") -ge 1)) {
        $k = $t.Substring(0, $t.IndexOf("=")).Trim()
        if ($k -eq $Key) {
          $lines += ($Key + "=" + $Value)
          $found = $true
          continue
        }
      }
      $lines += $line
    }
  }
  if (-not $found) {
    $lines += ""
    $lines += ($Key + "=" + $Value)
  }
  $utf8Bom = New-Object System.Text.UTF8Encoding $true
  [System.IO.File]::WriteAllLines($Path, $lines, $utf8Bom)
}

function Encode-PgUrlPart([string]$Raw) {
  if ($null -eq $Raw) { return "" }
  return [Uri]::EscapeDataString($Raw)
}

function Test-IsPgliteUrl([string]$Url) {
  return (-not [string]::IsNullOrWhiteSpace($Url)) -and $Url.Trim().ToLower().StartsWith("pglite:")
}

function Get-PgliteDataDir {
  # Opt-in, in priority order: process env (one-off override without editing
  # .env), .env (persistent operator config), then the documented default,
  # which lives outside the repo and is never committed.
  $fromProcess = [Environment]::GetEnvironmentVariable("AHOS_PGLITE_DATA_DIR", "Process")
  if (-not [string]::IsNullOrWhiteSpace($fromProcess)) { return $fromProcess.Trim() }
  $fromEnv = Get-EnvValue -Path $envPath -Key "AHOS_PGLITE_DATA_DIR"
  if (-not [string]::IsNullOrWhiteSpace($fromEnv)) { return $fromEnv.Trim() }
  return "G:/robat/ahos_runtime/pglite/ahos"
}

function Test-PgliteStoreInitialized([string]$DataDir) {
  # PG_VERSION is what PGlite writes when it first opens a store. Presence of
  # *any* file is not enough - the launcher's permanent gate uses the same test
  # (launcher/components.py::pglite_needs_schema_init), so an empty directory is
  # never mistaken for a usable store.
  return (Test-Path -LiteralPath (Join-Path $DataDir "PG_VERSION"))
}

function Initialize-PgliteStore([string]$Root, [string]$DataDir) {
  # Schema-only restore - the same one-shot the launcher performs on first start
  # (M10.1). Creates the store and the canonical tables; inserts no rows.
  # Identical invocation to package.json `db:restore-pglite`.
  $init = Join-Path $Root "scripts\pglite_restore.ts"
  if (-not (Test-Path -LiteralPath $init)) {
    Write-Host ("WARN: " + $init + " missing; cannot initialise the store") -ForegroundColor DarkYellow
    return $false
  }
  if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "WARN: node not on PATH; cannot initialise the store" -ForegroundColor DarkYellow
    return $false
  }
  Write-Host ("==> schema-only PGlite init at " + $DataDir + " (no rows; no --dump)") -ForegroundColor Cyan
  & node --experimental-strip-types $init --dataDir $DataDir | Out-Host
  return ($LASTEXITCODE -eq 0)
}

function Invoke-PgProbe([string]$Root, [string]$OutJson, [switch]$IsPglite) {
  $mjs = Join-Path $Root "scripts\ahos_pg_probe.mjs"
  # The embedded backend has no container, so the docker-exec fallback inside
  # windows_pg_probe.ps1 cannot evidence it - a container probe would report OK
  # for a URL the gateway does not open. Go straight to the node module, which
  # shares the canonical URL parser with db/index.ts.
  if ($IsPglite) {
    if (-not (Test-Path -LiteralPath $mjs)) {
      Write-Host "WARN: scripts\ahos_pg_probe.mjs missing; cannot probe the embedded backend" -ForegroundColor DarkYellow
      return $false
    }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
      Write-Host "WARN: node not on PATH; cannot probe the embedded backend" -ForegroundColor DarkYellow
      return $false
    }
    & node $mjs --json-out $OutJson | Out-Host
    return ($LASTEXITCODE -eq 0)
  }
  $psProbe = Join-Path $Root "scripts\windows_pg_probe.ps1"
  if (Test-Path -LiteralPath $psProbe) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $psProbe -RepoRoot $Root -JsonOut $OutJson | Out-Host
    return ($LASTEXITCODE -eq 0)
  }
  if (Test-Path -LiteralPath $mjs) {
    & node $mjs --json-out $OutJson | Out-Host
    return ($LASTEXITCODE -eq 0)
  }
  Write-Host "WARN: no pg probe script present" -ForegroundColor DarkYellow
  return $false
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS ensure DATABASE_URL (G2 / STATE B / no migrate)" -ForegroundColor Cyan
Write-Host "  M10: native embedded backend preferred, Postgres retained" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$envPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
  Write-Host "FAIL: .env missing" -ForegroundColor Red
  exit 2
}

$current = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
$probeOut = Join-Path $RepoRoot "reports\pg_probe_latest.json"
New-Item -ItemType Directory -Force -Path (Split-Path $probeOut) | Out-Null

# ---------------------------------------------------------------------------
# Branch 1: DATABASE_URL is already set -- always probe it first (unchanged).
# ---------------------------------------------------------------------------
$currentOk = $false
if (-not [string]::IsNullOrWhiteSpace($current)) {
  $isPglite = Test-IsPgliteUrl $current
  $label = if ($isPglite) { "embedded backend" } else { "Postgres" }
  $redactedCurrent = $current -replace '(:[^:@/]+)@', ':***@'
  if ($isPglite) { $redactedCurrent = $current }
  Write-Host ("==> probe current DATABASE_URL first (" + $label + ") -> " + $redactedCurrent) -ForegroundColor Cyan
  $currentOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut -IsPglite:$isPglite
  if ($currentOk) {
    Write-Host "OK current DATABASE_URL already runs One-Brain queries -- leaving it unchanged" -ForegroundColor Green
    Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
    Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
    exit 0
  }
  if ($isPglite) {
    # Never clobber the backend the owner explicitly chose. The Postgres
    # synthesis below is a *fallback for an unset URL*, not a repair path for a
    # native store that will not open -- silently rewriting pglite: -> postgresql:
    # would undo the M10 flip and point the gateway back at a dead port.
    Write-Host "FAIL: embedded backend probe failed; NOT falling back to the Postgres synthesis" -ForegroundColor Red
    Write-Host "      (that would silently switch backends; the pglite: URL is left untouched)." -ForegroundColor DarkYellow
    Write-Host "Remediation (pick one; all are non-destructive):" -ForegroundColor Yellow
    Write-Host ("  1) Initialise the store once, schema-only:  npm run db:restore-pglite -- --dataDir <dataDir>") -ForegroundColor Yellow
    Write-Host "     or re-run this script with -InitializePglite (writes the URL only after init succeeds)." -ForegroundColor Yellow
    Write-Host "  2) Start the launcher once -- it initialises the store on first start (M10.1)." -ForegroundColor Yellow
    Write-Host "  3) Seed the store from the verified backup:  see reports\grok\M10_STAGE4_FLIP_RUNBOOK.md" -ForegroundColor Yellow
    Write-Host ("  Probe report: " + $probeOut) -ForegroundColor Yellow
    Write-Host "STATE B: do NOT db:migrate / db:push / do NOT delete the store directory" -ForegroundColor Yellow
    exit 2
  }
  Write-Host "Current DATABASE_URL probe FAILED -- will try POSTGRES_* sync" -ForegroundColor Yellow
} else {
  # -------------------------------------------------------------------------
  # Branch 2: DATABASE_URL is empty -- prefer the native embedded backend.
  # -------------------------------------------------------------------------
  $dataDir = Get-PgliteDataDir
  $nativeUrl = "pglite:" + $dataDir
  Write-Host ("DATABASE_URL empty -- native embedded backend preferred: " + $nativeUrl) -ForegroundColor Cyan

  $nativeOk = $false
  if (Test-PgliteStoreInitialized -DataDir $dataDir) {
    if ($NoWrite) {
      Write-Host ("WARN: NoWrite set; would have written DATABASE_URL=" + $nativeUrl) -ForegroundColor Yellow
    } else {
      Write-Host ("Writing DATABASE_URL=" + $nativeUrl) -ForegroundColor Yellow
      Set-EnvValue -Path $envPath -Key "DATABASE_URL" -Value $nativeUrl
      Write-Host "==> probe DATABASE_URL after write" -ForegroundColor Cyan
      $nativeOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut -IsPglite
    }
  } else {
    Write-Host ("  store NOT initialised at " + $dataDir + " (no PG_VERSION)") -ForegroundColor DarkYellow
    Write-Host "  An empty directory is not a store: writing the URL now would point the gateway" -ForegroundColor DarkYellow
    Write-Host "  at a store PGlite has never opened." -ForegroundColor DarkYellow
    if ($InitializePglite -and -not $NoWrite) {
      $initOk = Initialize-PgliteStore -Root $RepoRoot -DataDir $dataDir
      if ($initOk -and (Test-PgliteStoreInitialized -DataDir $dataDir)) {
        Write-Host ("Writing DATABASE_URL=" + $nativeUrl) -ForegroundColor Yellow
        Set-EnvValue -Path $envPath -Key "DATABASE_URL" -Value $nativeUrl
        Write-Host "==> probe DATABASE_URL after init" -ForegroundColor Cyan
        $nativeOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut -IsPglite
      } else {
        Write-Host "FAIL: schema-only init did not produce PG_VERSION -- .env left untouched" -ForegroundColor Red
      }
    } else {
      Write-Host "  Re-run with -InitializePglite to create the schema (one-shot, no rows), or" -ForegroundColor Yellow
      Write-Host "  start the launcher once -- it initialises the store on first start (M10.1)." -ForegroundColor Yellow
    }
  }

  if ($nativeOk) {
    Write-Host "OK pg probe -- ahos_* readable via the embedded backend" -ForegroundColor Green
    Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
    Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
    exit 0
  }
  if ($NoWrite) { exit 2 }
  Write-Host "Native backend unavailable -- falling back to the Postgres (POSTGRES_*) synthesis" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Branch 3: Postgres. Reached from a failed Postgres probe or the empty-URL
# fallback above. Logic unchanged: sync from POSTGRES_*, then realign via
# docker exec if host auth still fails.
# ---------------------------------------------------------------------------
$pgUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
$pgDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
$pgPass = Get-EnvValue -Path $envPath -Key "POSTGRES_PASSWORD"
if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "ahos_user" }
if ([string]::IsNullOrWhiteSpace($pgDb)) { $pgDb = "ahos" }
if ([string]::IsNullOrWhiteSpace($pgPass)) {
  Write-Host "FAIL: POSTGRES_PASSWORD unset -- required by docker compose postgres" -ForegroundColor Red
  exit 2
}

$expected = "postgresql://{0}:{1}@127.0.0.1:5432/{2}" -f $pgUser, (Encode-PgUrlPart $pgPass), $pgDb
$redactedExpected = $expected -replace '(:[^:@/]+)@', ':***@'

if ($NoWrite) {
  Write-Host "WARN: NoWrite set; not updating DATABASE_URL" -ForegroundColor Yellow
  exit 2
}

Write-Host "Updating DATABASE_URL from POSTGRES_* (password URL-encoded)..." -ForegroundColor Yellow
Set-EnvValue -Path $envPath -Key "DATABASE_URL" -Value $expected
Write-Host ("  DATABASE_URL=" + $redactedExpected) -ForegroundColor Green

Write-Host "==> probe DATABASE_URL after sync" -ForegroundColor Cyan
$afterOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut
if ($afterOk) {
  Write-Host "OK pg probe -- ahos_* readable via DATABASE_URL" -ForegroundColor Green
  Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
  Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
  exit 0
}

# Host TCP auth failed but container local psql often still works (volume password drift).
# STATE B recovery: ALTER ROLE password to match .env POSTGRES_PASSWORD (no wipe / no migrate).
Write-Host "Host DATABASE_URL probe still failing -- trying docker-exec password realign (STATE B)" -ForegroundColor Yellow
$errorClass = ""
try {
  if (Test-Path -LiteralPath $probeOut) {
    $pj = Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json
    $errorClass = [string]$pj.error_class
  }
} catch {}

$container = "ahos_postgres_win"
$dockerOk = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
  $names = (& docker ps --format "{{.Names}}" 2>$null)
  if ($names -match [regex]::Escape($container)) {
    $ping = & docker exec $container psql -U $pgUser -d $pgDb -t -A -c "SELECT 1" 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $ping.Trim() -match "1") {
      $dockerOk = $true
    } else {
      Write-Host ("docker exec psql failed: " + $ping.Trim()) -ForegroundColor DarkYellow
    }
  } else {
    Write-Host ("container not running: " + $container) -ForegroundColor DarkYellow
  }
}

if ($dockerOk) {
  $tag = "ahospw" + [guid]::NewGuid().ToString("N").Substring(0, 10)
  # Dollar-quote password so special chars cannot break SQL.
  $alterSql = ('ALTER ROLE "' + $pgUser + '" WITH PASSWORD $' + $tag + '$' + $pgPass + '$' + $tag + '$;')
  Write-Host ("==> ALTER ROLE " + $pgUser + " password to match .env POSTGRES_PASSWORD (via docker exec)") -ForegroundColor Cyan
  $alterOut = & docker exec $container psql -U $pgUser -d $pgDb -v ON_ERROR_STOP=1 -c $alterSql 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("ALTER ROLE failed: " + $alterOut.Trim()) -ForegroundColor Red
  } else {
    Write-Host "ALTER ROLE ok -- re-probing host DATABASE_URL" -ForegroundColor Green
    $realignOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut
    if ($realignOk) {
      Write-Host "OK pg probe after password realign -- ahos_* readable via DATABASE_URL" -ForegroundColor Green
      Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
      Write-Host "STATE B: do NOT db:migrate / db:push / do NOT docker volume rm" -ForegroundColor Yellow
      exit 0
    }
  }
} else {
  Write-Host ("docker-exec realign skipped (error_class=" + $errorClass + ")") -ForegroundColor DarkYellow
}

Write-Host "FAIL: Postgres snapshot probe still failing after sync/realign (see reports\pg_probe_latest.json)" -ForegroundColor Red
Write-Host "Remediation:" -ForegroundColor Yellow
Write-Host "  1) Confirm ahos_postgres_win is up (pg_isready)" -ForegroundColor Yellow
Write-Host "  2) If POSTGRES_PASSWORD was changed after first compose up, realign failed -- put the ORIGINAL password into POSTGRES_PASSWORD + DATABASE_URL (do NOT wipe volume under STATE B)." -ForegroundColor Yellow
Write-Host "  3) Or switch to the native embedded backend (M10): DATABASE_URL=pglite:<dataDir>" -ForegroundColor Yellow
Write-Host "     see reports\grok\M10_STAGE4_FLIP_RUNBOOK.md (owner-gated flip)." -ForegroundColor Yellow
Write-Host "  4) scripts\windows_recover_g2_warm.ps1" -ForegroundColor Yellow
Write-Host "STATE B: do NOT db:migrate / db:push / do NOT docker volume rm" -ForegroundColor Yellow
exit 2
