#Requires -Version 5.1
<#
.SYNOPSIS
  Push Windows gate OWNER_PASTE + report JSON to a durable evidence branch.

Uses a temporary git index + commit-tree so the owner's current branch/worktree
is NOT checked out away (avoids dirty-tree checkout failures).

Creates/updates branch cursor/windows-gate-evidence-4bde and opens/updates a PR
so Cloud agents can fetch evidence without chat paste.

Does NOT invent PRE_SOAK / OPERATOR_READY. Does NOT db:migrate.
Never force-pushes main. Uses --force-with-lease only on the evidence branch.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$EvidenceBranch = "cursor/windows-gate-evidence-4bde",
  [string]$PastePath = "",
  [string]$SlimPath = "",
  [string]$LatestPath = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location -LiteralPath $RepoRoot

function Write-Step([string]$Msg) {
  Write-Host ("[gate-evidence] {0}" -f $Msg) -ForegroundColor Cyan
}

$git = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $git) {
  Write-Host "[gate-evidence] git missing -- skip push; Ctrl+V paste still required." -ForegroundColor DarkYellow
  exit 0
}

$reports = Join-Path $RepoRoot "reports"
if ([string]::IsNullOrWhiteSpace($PastePath)) {
  $PastePath = Join-Path $reports "OWNER_PASTE_WINDOWS_GATE.txt"
}
if ([string]::IsNullOrWhiteSpace($SlimPath)) {
  $SlimPath = Join-Path $reports "OWNER_PASTE_WINDOWS_GATE_SLIM.txt"
}
if ([string]::IsNullOrWhiteSpace($LatestPath)) {
  $LatestPath = Join-Path $reports "LATEST_WINDOWS_GATE.txt"
}

if (-not (Test-Path -LiteralPath $PastePath) -and -not (Test-Path -LiteralPath $LatestPath)) {
  Write-Host "[gate-evidence] no paste/latest to push -- skip." -ForegroundColor DarkYellow
  exit 0
}

# Stage copies under a tracked path (OWNER_PASTE* is gitignored at reports root)
$evDir = Join-Path $reports "windows_gate_evidence"
if (-not (Test-Path -LiteralPath $evDir)) {
  New-Item -ItemType Directory -Path $evDir -Force | Out-Null
}
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$utf8 = New-Object System.Text.UTF8Encoding $false

if (Test-Path -LiteralPath $PastePath) {
  Copy-Item -LiteralPath $PastePath -Destination (Join-Path $evDir ("OWNER_PASTE_" + $stamp + ".txt")) -Force
  Copy-Item -LiteralPath $PastePath -Destination (Join-Path $evDir "OWNER_PASTE_WINDOWS_GATE.txt") -Force
}
if (Test-Path -LiteralPath $SlimPath) {
  Copy-Item -LiteralPath $SlimPath -Destination (Join-Path $evDir "OWNER_PASTE_WINDOWS_GATE_SLIM.txt") -Force
}
if (Test-Path -LiteralPath $LatestPath) {
  Copy-Item -LiteralPath $LatestPath -Destination (Join-Path $evDir "LATEST_WINDOWS_GATE.txt") -Force
}

$newestJson = Get-ChildItem -LiteralPath $reports -Filter "operator_validation_report_windows_*.json" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
if ($null -eq $newestJson) {
  # G2-only validate path writes g2_validate_windows_*.json
  $newestJson = Get-ChildItem -LiteralPath $reports -Filter "g2_validate_windows_*.json" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
}
if ($null -ne $newestJson) {
  Copy-Item -LiteralPath $newestJson.FullName -Destination (Join-Path $evDir $newestJson.Name) -Force
  Copy-Item -LiteralPath $newestJson.FullName -Destination (Join-Path $evDir "operator_validation_report_windows_LATEST.json") -Force
}

$pointer = Join-Path $evDir "README_EVIDENCE.md"
$readme = @(
  "# Windows gate evidence (not a READY claim)",
  "",
  ("- generated_utc: " + $stamp),
  "- STATE B: do not db:migrate / db:push",
  "- OPERATOR_READY: NOT claimed by this push",
  "- pre_soak_entry_ok: only if LATEST / JSON says so on a real Windows host",
  "",
  "Files in this folder are produced by AHOS_WINDOWS_OPS.bat / gate runner.",
  "Agents: read OWNER_PASTE_WINDOWS_GATE.txt and operator_validation_report_windows_LATEST.json."
)
[System.IO.File]::WriteAllText($pointer, ($readme -join "`n") + "`n", $utf8)

Write-Step "fetch origin (for main base + evidence lease)"
& git fetch origin main 2>&1 | Out-Null
& git fetch origin $EvidenceBranch 2>&1 | Out-Null
$base = ""
try { $base = (& git rev-parse origin/main 2>$null).Trim() } catch {}
if ([string]::IsNullOrWhiteSpace($base)) {
  try { $base = (& git rev-parse HEAD 2>$null).Trim() } catch {}
}
if ([string]::IsNullOrWhiteSpace($base)) {
  Write-Host "[gate-evidence] cannot resolve base commit -- Ctrl+V paste still required." -ForegroundColor Yellow
  exit 0
}

$remoteLease = ""
try { $remoteLease = (& git rev-parse ("origin/" + $EvidenceBranch) 2>$null).Trim() } catch {}

# Temporary index: do not disturb current branch / dirty worktree
$idx = Join-Path $RepoRoot (".git\ahos-evidence-index-" + $stamp)
$env:GIT_INDEX_FILE = $idx
try {
  Write-Step ("temp index from " + $base.Substring(0, [Math]::Min(7, $base.Length)))
  & git read-tree $base 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[gate-evidence] read-tree failed -- Ctrl+V paste still required." -ForegroundColor Yellow
    exit 0
  }

  & git add -- "reports/windows_gate_evidence" 2>&1 | Out-Host
  $staged = (& git diff --cached --name-only 2>$null)
  if ([string]::IsNullOrWhiteSpace(($staged | Out-String))) {
    Write-Host "[gate-evidence] nothing staged -- skip." -ForegroundColor DarkYellow
    exit 0
  }

  $tree = (& git write-tree 2>$null).Trim()
  if ([string]::IsNullOrWhiteSpace($tree)) {
    Write-Host "[gate-evidence] write-tree failed -- Ctrl+V paste still required." -ForegroundColor Yellow
    exit 0
  }

  $msg = @"
Windows gate evidence bundle ($stamp).

Not a PRE_SOAK or OPERATOR_READY claim. STATE B: no migrate.
Interpret LATEST / JSON honestly on agent side.
"@
  $commit = (& git commit-tree $tree -p $base -m $msg 2>$null).Trim()
  if ([string]::IsNullOrWhiteSpace($commit)) {
    Write-Host "[gate-evidence] commit-tree failed -- Ctrl+V paste still required." -ForegroundColor Yellow
    exit 0
  }

  Write-Step ("update-ref " + $EvidenceBranch + " -> " + $commit.Substring(0, 7))
  & git update-ref ("refs/heads/" + $EvidenceBranch) $commit 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[gate-evidence] update-ref failed -- Ctrl+V paste still required." -ForegroundColor Yellow
    exit 0
  }
} finally {
  Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue
  if (Test-Path -LiteralPath $idx) {
    Remove-Item -LiteralPath $idx -Force -ErrorAction SilentlyContinue
  }
}

Write-Step ("push --force-with-lease origin " + $EvidenceBranch)
$pushOk = $false
if (-not [string]::IsNullOrWhiteSpace($remoteLease)) {
  $leaseSpec = ("refs/heads/" + $EvidenceBranch + ":" + $remoteLease)
  & git push --force-with-lease=$leaseSpec -u origin $EvidenceBranch 2>&1 | Out-Host
  $pushOk = ($LASTEXITCODE -eq 0)
} else {
  & git push -u origin $EvidenceBranch 2>&1 | Out-Host
  $pushOk = ($LASTEXITCODE -eq 0)
}
if (-not $pushOk) {
  Write-Host "[gate-evidence] leased push failed -- retry plain force-with-lease" -ForegroundColor DarkYellow
  & git fetch origin $EvidenceBranch 2>&1 | Out-Null
  & git push --force-with-lease -u origin $EvidenceBranch 2>&1 | Out-Host
  $pushOk = ($LASTEXITCODE -eq 0)
}
if (-not $pushOk) {
  Write-Host "[gate-evidence] push failed -- Ctrl+V Desktop AHOS_PASTE_TO_CURSOR.txt into Cursor." -ForegroundColor Yellow
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($pushOk -and ($null -ne $gh)) {
  try {
    & gh auth status 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $existing = & gh pr list --head $EvidenceBranch --state open --json number -q ".[0].number" 2>$null
      if ([string]::IsNullOrWhiteSpace($existing)) {
        & gh pr create --base main --head $EvidenceBranch `
          --title "LEAVE OPEN: Windows gate evidence wake (not READY)" `
          --body "Auto-pushed OWNER_PASTE / gate JSON from laptop.`n`n**Please leave this PR open** so agents wake on updates. Merging closes the wake path.`n`nNot an OPERATOR_READY claim. STATE B: no migrate. Agent: read ``reports/windows_gate_evidence/``." `
          2>&1 | Out-Host
        $existing = & gh pr list --head $EvidenceBranch --state open --json number -q ".[0].number" 2>$null
      } else {
        Write-Host ("[gate-evidence] evidence PR already open #" + $existing) -ForegroundColor Green
      }
      # Notify open unlock/evidence PRs so subscribed agents wake on new evidence
      if (Test-Path -LiteralPath $LatestPath) {
        $notify = @(
          "Windows gate evidence pushed to ``origin/" + $EvidenceBranch + "`` (stamp " + $stamp + ").",
          "Not a READY claim. STATE B: no migrate.",
          "--- LATEST_WINDOWS_GATE ---"
        )
        $notify += Get-Content -LiteralPath $LatestPath -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $PastePath) {
          $notify += "--- OWNER_PASTE_HEAD ---"
          $notify += (Get-Content -LiteralPath $PastePath -TotalCount 40 -ErrorAction SilentlyContinue)
        }
        $notifyFile = Join-Path $evDir ("NOTIFY_UNLOCK_" + $stamp + ".txt")
        [System.IO.File]::WriteAllText($notifyFile, ($notify -join "`n") + "`n", $utf8)
        $notifyTargets = New-Object System.Collections.Generic.List[string]
        # Durable open sink first (survives inbox merges).
        [void]$notifyTargets.Add("38")
        if (-not [string]::IsNullOrWhiteSpace($existing)) {
          if (-not ($notifyTargets -contains [string]$existing)) { [void]$notifyTargets.Add([string]$existing) }
        }
        try {
          $open = & gh pr list --state open --limit 20 --json number,headRefName 2>$null | ConvertFrom-Json
          foreach ($p in $open) {
            if ($p.headRefName -match 'windows|harden|unlock|ops|gate|pre.?soak|g2|evidence|lease|inbox|sink|retarget') {
              $n = [string]$p.number
              if (-not ($notifyTargets -contains $n)) { [void]$notifyTargets.Add($n) }
            }
          }
        } catch {}
        # Always try the dedicated evidence inbox heads if open.
        foreach ($inboxHead in @(
          "cursor/windows-evidence-inbox-open-sink-4bde",
          "cursor/windows-main-evidence-push-4bde",
          "cursor/windows-evidence-notify-retarget-4bde",
          "cursor/windows-evidence-inbox-stay-open-4bde",
          "cursor/windows-evidence-inbox-live-4bde",
          "cursor/windows-evidence-inbox-open-4bde",
          "cursor/windows-evidence-inbox-4bde",
          "cursor/windows-presoak-unblock-4bde"
        )) {
          try {
            $inbox = & gh pr list --head $inboxHead --state open --json number -q ".[0].number" 2>$null
            if (-not [string]::IsNullOrWhiteSpace($inbox) -and -not ($notifyTargets -contains [string]$inbox)) {
              [void]$notifyTargets.Add([string]$inbox)
            }
          } catch {}
        }
        # Prefer current unlock tip if listed; keep #38 as durable sink
        foreach ($prNum in $notifyTargets) {
          & gh pr comment $prNum --body-file $notifyFile 2>&1 | Out-Host
        }
      }
    }
  } catch {}
}

if ($pushOk) {
  Write-Host "[gate-evidence] OK -- agents can fetch origin/cursor/windows-gate-evidence-4bde" -ForegroundColor Green
  Write-Host "[gate-evidence] owner branch unchanged (temp-index push)." -ForegroundColor DarkGray
} else {
  Write-Host "[gate-evidence] incomplete -- Ctrl+V paste still required." -ForegroundColor Yellow
}
exit 0
