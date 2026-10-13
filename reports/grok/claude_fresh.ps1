# claude_fresh.ps1 - start a FRESH headless Claude session (no -c, no resume). Used by Soltan's watchdog
# when the interactive session dies with API 400 (overloaded context) or stalls. Portable: no hard-coded user path.
param([int]$MaxTurns = 200, [int]$TimeoutSec = 28800, [int]$StallMin = 30)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
foreach ($v in 'ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY','ANTHROPIC_MODEL') {
  $x = [Environment]::GetEnvironmentVariable($v,'User')
  if ($x) { Set-Item "env:$v" $x } else { Remove-Item "env:$v" -ErrorAction SilentlyContinue }
}
$model = $env:ANTHROPIC_MODEL; if (-not $model) { $model = 'Atria-Dawn-Preview' }
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS = '110000'; $env:API_TIMEOUT_MS = '900000'
$prompt = 'Fresh session started by Soltan watchdog. Read the last 60 lines of reports/grok/queue_2050/README_FOR_CLAUDE.md (STANDING ORDER) and reports/grok/PROGRESS_LOG.md, then follow the STANDING ORDER work loop without stopping. Commit any uncommitted work first (stage ONLY your own files by path, never git add -A, never push). Then continue the binding order there. Keep turns short and commit after every step. Screenshot dashboard steps to reports/dashboard/screens/<mission>/. If an API 400 appears, commit and stop.'
$stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$log = Join-Path $root "reports\grok\_claude_fresh_$stamp.txt"
"$(Get-Date -Format s) start model=$model" | Out-File -Encoding utf8 $log
# Stream output into the log so its mtime reflects activity. Only kill on (a) no log writes for $StallMin min, or (b) the 8h safety cap.
$job = Start-Job -ScriptBlock { param($r,$p,$m,$t) Set-Location $r; & claude -p $p --model $m --max-turns $t --permission-mode bypassPermissions 2>&1 } -ArgumentList $root,$prompt,$model,$MaxTurns
$t0 = Get-Date; $last = Get-Date; $reason = $null
while ($job.State -eq 'Running') {
  Start-Sleep -Seconds 30
  $out = Receive-Job $job
  if ($out) { $out | Out-File -Append -Encoding utf8 $log }
  $w = (Get-Item $log).LastWriteTime; if ($w -gt $last) { $last = $w }
  if (((Get-Date) - $last).TotalMinutes -ge $StallMin) { $reason = "STALLED (no log writes for $StallMin min)"; break }
  if (((Get-Date) - $t0).TotalSeconds -ge $TimeoutSec) { $reason = "TIMEOUT (safety cap $TimeoutSec s)"; break }
}
if ($reason) { Stop-Job $job; Receive-Job $job -EA SilentlyContinue | Out-File -Append -Encoding utf8 $log; "$(Get-Date -Format s) $reason" | Out-File -Append -Encoding utf8 $log }
else { Receive-Job $job | Out-File -Append -Encoding utf8 $log; "$(Get-Date -Format s) done" | Out-File -Append -Encoding utf8 $log }
Remove-Job $job -Force -EA SilentlyContinue

