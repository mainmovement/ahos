# ==============================================================================
# AHOS Windows Post-Merge Reconcile (ONE SHOT)
#
# What this does:
#   1) Fetches origin/main
#   2) Syncs the laptop repo to origin/main while PRESERVING owner-local files
#   3) Runs READ-ONLY Postgres forensics via docker exec
#   4) Prints a REPORT block to paste back into Cursor
#
# What this NEVER does:
#   - npm run db:migrate / db:push / db:generate
#   - git reset --hard
#   - git stash
#   - DROP / ALTER / TRUNCATE / DELETE / UPDATE / INSERT
#   - Lane-A edits
#   - force-push
#
# Usage (from G:\robat\ahos):
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1
#
# Encoding contract: ASCII-only punctuation (WinPS 5.1 safe).
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [string]$PostgresContainer = "ahos_postgres_win",
    [string]$PostgresUser = "ahos_user",
    [string]$PostgresDb = "ahos"
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host ("==> " + $Message) -ForegroundColor Cyan
}

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw ("Required command not found on PATH: " + $Name)
    }
}

function Get-FileSha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return "MISSING" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Invoke-Git([string[]]$GitArgs) {
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw ("git " + ($GitArgs -join " ") + " failed with exit " + $LASTEXITCODE)
    }
}

# ------------------------------------------------------------------------------
# Resolve repo root
# ------------------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows post-merge reconcile (safe / read-mostly)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB, reset, stash, or force-push." -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

Assert-Command "git"

$Protected = @(
    ".gitignore",
    "deployment/docker-compose.windows.yml",
    "reports/backup_restore_drill.json"
)

$Report = [ordered]@{
    schema = "ahos.windows_post_merge_reconcile.v1"
    started_utc = (Get-Date).ToUniversalTime().ToString("o")
    repo_root = $RepoRoot
    protected_files = $Protected
    pre = @{}
    sync = @{}
    docker = @{}
    postgres = @{}
    verdict = "UNKNOWN"
    next_action = ""
    errors = @()
}

# ------------------------------------------------------------------------------
# PREFLIGHT
# ------------------------------------------------------------------------------
Write-Step "PREFLIGHT git state"

$branch = (git branch --show-current 2>$null | Out-String).Trim()
$head = (git rev-parse HEAD 2>$null | Out-String).Trim()
Invoke-Git @("fetch", "origin", "main")
$originMain = (git rev-parse origin/main 2>$null | Out-String).Trim()
$leftRight = (git rev-list --left-right --count ("HEAD...origin/main") 2>$null | Out-String).Trim()
$statusShort = @(git status --short 2>$null)

$Report.pre = [ordered]@{
    branch = $branch
    head = $head
    origin_main = $originMain
    left_right_ahead_behind = $leftRight
    status_short = $statusShort
}

Write-Host ("  branch     : " + $branch)
Write-Host ("  HEAD       : " + $head)
Write-Host ("  origin/main: " + $originMain)
Write-Host ("  ahead/behind HEAD...origin/main: " + $leftRight)
Write-Host "  git status --short:"
$statusShort | ForEach-Object { Write-Host ("    " + $_) }

# Classify dirty paths
$dirtyPaths = @()
foreach ($line in $statusShort) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    # status format: XY <path> or XY origin -> path
    $path = $line.Substring(3).Trim()
    if ($path -match " -> ") { $path = ($path -split " -> ")[-1].Trim() }
    $dirtyPaths += $path
}
$unexpectedDirty = @($dirtyPaths | Where-Object { $Protected -notcontains $_ })
$Report.pre["dirty_paths"] = $dirtyPaths
$Report.pre["unexpected_dirty"] = $unexpectedDirty

if ($unexpectedDirty.Count -gt 0) {
    $msg = "STOP - unexpected dirty paths (not in owner-protected set): " + ($unexpectedDirty -join ", ")
    $Report.errors += $msg
    $Report.verdict = "BLOCKED_OWNER_DECISION"
    $Report.next_action = "Classify or commit/clean unexpected dirty files, then re-run this script."
    Write-Host $msg -ForegroundColor Red
    Write-Host ""
    Write-Host "===== BEGIN REPORT (paste into Cursor) =====" -ForegroundColor Yellow
    $Report | ConvertTo-Json -Depth 8
    Write-Host "===== END REPORT =====" -ForegroundColor Yellow
    exit 2
}

# ------------------------------------------------------------------------------
# PRESERVE owner files, sync to origin/main, re-apply owner files
# ------------------------------------------------------------------------------
Write-Step "SYNC to origin/main (preserve owner files)"

$PreserveRoot = Join-Path $env:TEMP ("ahos_owner_preserve_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $PreserveRoot -Force | Out-Null
$backupMeta = @()

foreach ($rel in $Protected) {
    $src = Join-Path $RepoRoot $rel
    $dst = Join-Path $PreserveRoot ($rel -replace "[\\/]", "__")
    $shaBefore = Get-FileSha256 $src
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    $backupMeta += [ordered]@{
        path = $rel
        sha256_before = $shaBefore
        backup = $dst
        backed_up = (Test-Path -LiteralPath $dst)
    }
}
$Report.sync["preserve_dir"] = $PreserveRoot
$Report.sync["backups"] = $backupMeta

# Temporarily align protected paths to HEAD so branch switch cannot refuse
# local modifications that overlap upstream edits. Backups already saved.
foreach ($rel in $Protected) {
    $full = Join-Path $RepoRoot $rel
    $blob = & git show ("HEAD:" + $rel) 2>$null
    if ($LASTEXITCODE -eq 0) {
        $parent = Split-Path -Parent $full
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        # git show output as string array -> join with newlines
        $text = ($blob -join "`n")
        if (-not $text.EndsWith("`n")) { $text = $text + "`n" }
        [System.IO.File]::WriteAllText($full, $text)
    }
}

try {
    # Ensure local main tracks origin/main tip
    $localMainExists = (git show-ref --verify --quiet refs/heads/main; $LASTEXITCODE -eq 0)
    if ($localMainExists) {
        Invoke-Git @("switch", "main")
        Invoke-Git @("merge", "--ff-only", "origin/main")
    } else {
        Invoke-Git @("switch", "-c", "main", "origin/main")
    }
    $Report.sync["method"] = "ff-only-or-create-main"
    $Report.sync["ok"] = $true
} catch {
    $Report.sync["ok"] = $false
    $Report.sync["error"] = $_.Exception.Message
    $Report.errors += ("SYNC_FAILED: " + $_.Exception.Message)
    # Re-apply backups even on failure so owner files are not left at HEAD
    foreach ($item in $backupMeta) {
        if ($item.backed_up) {
            $dest = Join-Path $RepoRoot $item.path
            $parent = Split-Path -Parent $dest
            if (-not (Test-Path -LiteralPath $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null
            }
            Copy-Item -LiteralPath $item.backup -Destination $dest -Force
        }
    }
    $Report.verdict = "BLOCKED_REPOSITORY_RECONCILIATION"
    $Report.next_action = "Paste REPORT. Do not migrate. Owner decision required for sync failure."
    Write-Host ("SYNC FAILED: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host ""
    Write-Host "===== BEGIN REPORT (paste into Cursor) =====" -ForegroundColor Yellow
    $Report | ConvertTo-Json -Depth 8
    Write-Host "===== END REPORT =====" -ForegroundColor Yellow
    exit 3
}

# Re-apply owner-preserved content on top of main
foreach ($item in $backupMeta) {
    if ($item.backed_up) {
        $dest = Join-Path $RepoRoot $item.path
        $parent = Split-Path -Parent $dest
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        Copy-Item -LiteralPath $item.backup -Destination $dest -Force
    }
}

$newHead = (git rev-parse HEAD 2>$null | Out-String).Trim()
$newBranch = (git branch --show-current 2>$null | Out-String).Trim()
$postStatus = @(git status --short 2>$null)
$Report.sync["head_after"] = $newHead
$Report.sync["branch_after"] = $newBranch
$Report.sync["status_after"] = $postStatus
$Report.sync["matches_origin_main"] = ($newHead -eq $originMain)

Write-Host ("  branch after: " + $newBranch) -ForegroundColor Green
Write-Host ("  HEAD after  : " + $newHead) -ForegroundColor Green
Write-Host ("  matches origin/main: " + ($newHead -eq $originMain))
Write-Host "  status after (owner files should still be dirty):"
$postStatus | ForEach-Object { Write-Host ("    " + $_) }

# ------------------------------------------------------------------------------
# DOCKER / READ-ONLY POSTGRES
# ------------------------------------------------------------------------------
Write-Step "DOCKER + READ-ONLY Postgres forensics"

$dockerOk = $false
try {
    Assert-Command "docker"
    $ps = @(docker ps --format "{{.Names}}`t{{.Status}}" 2>$null)
    $Report.docker["ps"] = $ps
    $Report.docker["postgres_running"] = [bool]($ps | Where-Object { $_ -like ($PostgresContainer + "*") })
    $Report.docker["runtime_running"] = [bool]($ps | Where-Object { $_ -like "ahos_runtime_win*" })
    $Report.docker["n8n_running"] = [bool]($ps | Where-Object { $_ -like "ahos_n8n_win*" })
    $dockerOk = $true
    Write-Host "  docker ps:"
    $ps | ForEach-Object { Write-Host ("    " + $_) }
} catch {
    $Report.docker["error"] = $_.Exception.Message
    $Report.errors += ("DOCKER: " + $_.Exception.Message)
    Write-Host ("  docker unavailable: " + $_.Exception.Message) -ForegroundColor Yellow
}

if ($dockerOk -and $Report.docker.postgres_running) {
    function Invoke-PsqlRo([string]$Sql) {
        $out = & docker exec $PostgresContainer psql -U $PostgresUser -d $PostgresDb -v ON_ERROR_STOP=1 -P pager=off -c $Sql 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw ("psql failed: " + ($out | Out-String))
        }
        return ($out | Out-String)
    }

    try {
        # Identity
        $Report.postgres["identity"] = Invoke-PsqlRo "SELECT current_database() AS db, current_user AS usr, version() AS ver;"
        # ahos_* tables
        $Report.postgres["ahos_tables"] = Invoke-PsqlRo "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'ahos_%' ORDER BY tablename;"
        $Report.postgres["ahos_table_count"] = Invoke-PsqlRo "SELECT COUNT(*) AS n FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'ahos_%';"
        # row counts (dynamic safe: only ahos_ prefix from catalog)
        $Report.postgres["row_counts"] = Invoke-PsqlRo @"
SELECT c.relname AS table_name, c.reltuples::bigint AS approx_rows
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname LIKE 'ahos_%'
ORDER BY c.relname;
"@
        # exact counts via DO-less union generated in SQL
        $Report.postgres["exact_row_counts"] = Invoke-PsqlRo @"
SELECT t.tablename,
       (xpath('/row/cnt/text()', query_to_xml(format('SELECT COUNT(*) AS cnt FROM public.%I', t.tablename), false, true, '')))[1]::text::bigint AS row_count
FROM pg_tables t
WHERE t.schemaname='public' AND t.tablename LIKE 'ahos_%'
ORDER BY t.tablename;
"@
        # drizzle migrations table
        $Report.postgres["drizzle_migrations_exists"] = Invoke-PsqlRo @"
SELECT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema='public' AND table_name='__drizzle_migrations'
) AS drizzle_migrations_exists;
"@
        $Report.postgres["drizzle_migrations_rows"] = Invoke-PsqlRo @"
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name='__drizzle_migrations';
"@
        # Try select from migrations only if exists - use to_regclass guard
        $Report.postgres["drizzle_migrations_content"] = Invoke-PsqlRo @"
SELECT CASE WHEN to_regclass('public.__drizzle_migrations') IS NULL
  THEN 'TABLE_ABSENT'
  ELSE (SELECT COALESCE(string_agg(id::text || ':' || hash, ', ' ORDER BY created_at), 'EMPTY')
        FROM public.__drizzle_migrations)
END AS migrations;
"@
        $Report.postgres["ok"] = $true
        Write-Host "  Postgres read-only forensics captured." -ForegroundColor Green
    } catch {
        $Report.postgres["ok"] = $false
        $Report.postgres["error"] = $_.Exception.Message
        $Report.errors += ("POSTGRES_RO: " + $_.Exception.Message)
        Write-Host ("  Postgres forensics failed: " + $_.Exception.Message) -ForegroundColor Yellow
    }
} else {
    $Report.postgres["ok"] = $false
    $Report.postgres["error"] = "postgres container not running or docker unavailable"
    $Report.errors += $Report.postgres["error"]
}

# ------------------------------------------------------------------------------
# VERDICT
# ------------------------------------------------------------------------------
Write-Step "VERDICT"

$syncOk = [bool]$Report.sync.ok -and [bool]$Report.sync.matches_origin_main
$pgOk = [bool]$Report.postgres.ok

if ($syncOk -and $pgOk) {
    $Report.verdict = "SYNCED_FORENSICS_CAPTURED"
    $Report.next_action = "Paste this REPORT into Cursor. Do NOT migrate until Cursor classifies DB STATE A-E."
} elseif ($syncOk -and -not $pgOk) {
    $Report.verdict = "SYNCED_BUT_DB_UNKNOWN"
    $Report.next_action = "Start ahos_postgres_win, re-run script, or paste REPORT for guidance."
} elseif (-not $syncOk) {
    $Report.verdict = "BLOCKED_REPOSITORY_RECONCILIATION"
    $Report.next_action = "Paste REPORT. Do not migrate."
} else {
    $Report.verdict = "UNKNOWN"
    $Report.next_action = "Paste REPORT into Cursor."
}

$Report.finished_utc = (Get-Date).ToUniversalTime().ToString("o")

$ReportPath = Join-Path $RepoRoot ("reports\windows_post_merge_reconcile_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".json")
$ReportDir = Split-Path -Parent $ReportPath
if (-not (Test-Path -LiteralPath $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
}
($Report | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $ReportPath -Encoding UTF8
Write-Host ("  Wrote " + $ReportPath) -ForegroundColor Green

Write-Host ""
Write-Host "===== BEGIN REPORT (paste into Cursor) =====" -ForegroundColor Yellow
Get-Content -LiteralPath $ReportPath -Raw
Write-Host "===== END REPORT =====" -ForegroundColor Yellow

if ($Report.verdict -like "BLOCKED*") { exit 2 }
exit 0
