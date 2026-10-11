# claude_resume.ps1 — a reliable headless resume the watchdog can call.
#
# Why this exists. The ad-hoc watchdog restart was `claude -c -p`, which is wrong
# twice over:
#   1. `-c` continues "the most recent conversation in this directory" -- it does
#      not name the stalled session, so it can latch onto a different transcript
#      and exit with nothing to say (the "silent exit"), or sit waiting on a
#      session that is in no state to continue (the "hang").
#   2. It inherited the ambient environment of whatever shell launched it. A
#      stale process-scoped ANTHROPIC_API_KEY shadows the working
#      ANTHROPIC_AUTH_TOKEN, and the gateway answers 401 Invalid API key even
#      though both keys are individually valid. `run_mission.ps1` solved this by
#      normalising the four ANTHROPIC_* vars from the User scope -- copying the
#      User value and REMOVING the process value when the User one is absent.
#      This script reuses that normalisation verbatim; that is the 401 fix.
#
# It never names a model. The model id is derived from the same source the
# interactive Claude session on this machine uses (User ANTHROPIC_MODEL, else the
# `model` field of the User settings.json) and passed as an explicit --model. If
# it cannot be derived the script aborts loudly rather than letting `claude -p`
# fall back to a catalog default the gateway does not serve.
#
# It never resumes blindly. `claude -c` means "the most recent conversation in
# this directory", which on this machine is the *interactive* session -- resuming
# that from a headless writer interleaves turns into a transcript a person is
# driving. So there is no newest-transcript guess at all. The caller names the
# session, either directly or by the runner's mission id, whose runlog records
# the session id of every attempt. Resolution is fail-loud: no session recorded,
# no resume.
#
# It never hangs: the resume runs in a background job with a hard timeout. A
# stalled process is stopped and reported as TIMEOUT instead of blocking the
# watchdog's loop forever.
#
# Exit codes, chosen so the watchdog can branch without re-parsing text:
#   0  delivered a reply (the caller decides whether the reply is a verdict)
#   2  infra/quota/auth failure -- the session never ran; NOT chargeable
#   3  no reply / ran out of turns / timed out -- chargeable, resume again
#   4  configuration error (no model, no session) -- fix the host, do not retry
#
# Usage:
#   .\claude_resume.ps1 -MissionId 10                 # resolve the session from the runner's runlog
#   .\claude_resume.ps1 -SessionId fc3bc167-...       # resume a named one
#   .\claude_resume.ps1 -MissionId 10 -MaxTurns 1 -ResumeMessage 'Reply with: OK' -DryRun

param(
  [string]$MissionId,             # the runner's -n; resolves the session from its runlog
  [string]$SessionId,
  [string]$ResumeMessage,
  [string]$Tag,
  [int]$MaxTurns = 300,
  [int]$TimeoutSec = 1500,        # hang guard; CLAUDE_CODE_PRINT_BG_WAIT_CEILING is 1800
  [int]$LiveWindowSec = 60,       # a transcript fresher than this is a session a live claude owns
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-Location 'G:\robat\ahos'
$proj = Join-Path $env:USERPROFILE '.claude\projects\G--robat-ahos'
$tools = 'Bash Read Edit Write Glob Grep'
if (-not $Tag) { $Tag = if ($MissionId) { "resume_$MissionId" } else { 'resume' } }
$log = "reports\grok\_claude_${Tag}_runlog.txt"
$errFile = "reports\grok\_claude_${Tag}_stderr.txt"
$out = "reports\grok\_claude_${Tag}_result.txt"

function Log([string]$line) {
  # Never let a logging failure kill the script: the result line is the one thing
  # that must survive, and a dead logger must not turn a reportable outcome into
  # an unexplained crash -- that is the "silent exit" this script exists to end.
  try { "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss') $line" | Out-File -Append -Encoding utf8 $log } catch { }
  Write-Host $line
}

# ------------------------------------------------- environment + model -------
# Verbatim from run_mission.ps1: copy from the User scope, and REMOVE a stale
# process-scoped value when the User one is absent. This is what stops the 401.
$envUser = @{}
foreach ($v in 'ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY','ANTHROPIC_MODEL') {
  $x = [Environment]::GetEnvironmentVariable($v,'User')
  $envUser[$v] = $x
}

$env:PYTHONIOENCODING = 'utf-8'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = '1800000'
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS = '110000'
$env:API_TIMEOUT_MS = '900000'
$env:CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT = '1'

$model = $envUser['ANTHROPIC_MODEL']
if (-not $model) {
  $s = "$env:USERPROFILE\.claude\settings.json"
  if (Test-Path $s) {
    try { $j = Get-Content $s -Raw -Encoding UTF8 | ConvertFrom-Json; $model = $j.model } catch { }
  }
}
if (-not $model) {
  Log 'CONFIG-ERROR: cannot derive the model. Set the User-scoped ANTHROPIC_MODEL to the id the interactive Claude session uses.'
  exit 4
}

# ------------------------------------------------- session resolution --------
# No guessing. `claude -c` on this machine resolves to the interactive session's
# transcript, and a headless resume of that would interleave turns into a
# conversation a person is driving. The caller must name the session: by id, or
# by the runner's mission id, whose runlog records the session id of every
# attempt it made.
if (-not $SessionId -and $MissionId) {
  $runlog = "reports\grok\_claude_${MissionId}_runlog.txt"
  if (Test-Path $runlog) {
    # The runlog records `attemptN mode=.. session=<id> ..` per attempt; take the
    # last one that names a real transcript -- that is the session the runner was
    # last actually working in.
    Get-Content $runlog -Encoding UTF8 |
      ForEach-Object {
        if ($_ -match 'session=([0-9a-f-]{36})') { $matches[1] }
      } |
      ForEach-Object {
        if (Test-Path (Join-Path $proj "$_.jsonl")) { $_ }
      } |
      Select-Object -Last 1 | ForEach-Object { $SessionId = $_ }
  }
  if (-not $SessionId) {
    Log "CONFIG-ERROR: mission $MissionId has no resumable session in $runlog -- the mission never reached a session, or its runlog is gone."
    exit 4
  }
  Log "MISSION $MissionId -> session $SessionId (from its runlog)"
}
if (-not $SessionId) {
  Log 'CONFIG-ERROR: no session to resume. Pass -MissionId <n> (the runner''s -n) or -SessionId <id>. This script deliberately does not guess the newest transcript.'
  exit 4
}
$transcript = Join-Path $proj "$SessionId.jsonl"
if (-not (Test-Path $transcript)) {
  Log "CONFIG-ERROR: session $SessionId has no transcript at $transcript."
  exit 4
}
# A transcript fresher than the live window is a session a live claude is writing
# right now. Resuming it from a second writer interleaves turns. The window is
# short on purpose: it must not swallow a session that merely finished a turn a
# minute ago.
$age = ((Get-Date) - (Get-Item $transcript).LastWriteTime).TotalSeconds
if ($age -lt $LiveWindowSec) {
  Log "CONFIG-ERROR: session $SessionId was written ${age}s ago -- a live claude owns that transcript. Refusing to resume it."
  exit 4
}

if (-not $ResumeMessage) {
  $ResumeMessage = @"
Continue exactly where you stopped. If your last turn ended while waiting on a background task, that task was killed when the process exited -- claude -p is one-shot, so ending a turn exits the process and its completion notification never arrives. Re-run any suite you still need and POLL it inside this same turn (short sleeps reading its output file) until it finishes; never end your turn while a background task is still running. Check git status and git log first, do not redo finished work, keep committing incrementally, and finish with the required final output.
"@
}

Log "RESUME session=$SessionId model=$model turns=$MaxTurns timeout=${TimeoutSec}s dryrun=$([bool]$DryRun)"

if ($DryRun) {
  Log 'DRY-RUN: model derived, session resolved, environment prepared. No API call made.'
  exit 0
}

# ------------------------------------------------- the resume, with a hang guard
# The same classifiers as run_mission.ps1, so both scripts agree on what a
# platform failure looks like and a quota outage is never escalated to an owner
# gate as though it were a mission failure.
function IsInfraFailure([string]$t) {
  return ($t -match 'Token quota exhausted|quota exceeded|usage limit|credit balance|Request rejected \(429\)|unrecognized_model|invalid api key|authentication_error|rate[- ]?limited|Failed to authenticate')
}
function IsFail([string]$t) {
  return ($t -match 'API Error|408 status|overloaded|ECONNRESET|socket hang|issue with the selected model|Reached max turns')
}

# The claude.ps1 shim on Windows writes its captures as UTF-16LE, so a naive
# UTF-8 read turns `API Error` into `A\0P\0I\0...`. The classifier regexes still
# matched by accident for pure-ASCII output, but the logged text was mojibake and
# any non-ASCII detail would have been lost. Read the bytes and pick the encoding
# from the BOM, falling back to UTF-8.
function Read-Any([string]$path) {
  $b = [IO.File]::ReadAllBytes($path)
  if ($b.Length -ge 2 -and $b[0] -eq 0xFF -and $b[1] -eq 0xFE) {
    return [Text.Encoding]::Unicode.GetString($b, 2, $b.Length - 2)
  }
  if ($b.Length -ge 2 -and $b[0] -eq 0xFE -and $b[1] -eq 0xFF) {
    return [Text.Encoding]::BigEndianUnicode.GetString($b, 2, $b.Length - 2)
  }
  if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) {
    return [Text.Encoding]::UTF8.GetString($b, 3, $b.Length - 3)
  }
  return [Text.Encoding]::UTF8.GetString($b)
}

$job = Start-Job -ScriptBlock {
  param($model, $sess, $msg, $tools, $maxTurns, $out, $errFile, $envUser, $wd)
  Set-Location $wd
  foreach ($v in 'ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY','ANTHROPIC_MODEL') {
    if ($envUser[$v]) { Set-Item env:$v $envUser[$v] }
    elseif (Test-Path env:$v) { Remove-Item env:$v }
  }
  $env:PYTHONIOENCODING = 'utf-8'
  $env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = '1800000'
  $env:CLAUDE_CODE_MAX_CONTEXT_TOKENS = '110000'
  $env:API_TIMEOUT_MS = '900000'
  $env:CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT = '1'
  $msg | claude -p --model $model --resume $sess --permission-mode acceptEdits `
    --allowedTools $tools --max-turns $maxTurns --output-format text `
    > $out 2> $errFile
} -ArgumentList $model, $SessionId, $ResumeMessage, $tools, $MaxTurns, $out, $errFile, $envUser, (Get-Location).Path

$t0 = Get-Date
$timedOut = $false
if (-not (Wait-Job $job -Timeout $TimeoutSec)) {
  $timedOut = $true
  Log "TIMEOUT after ${TimeoutSec}s -- stopping the stalled resume."
  # Kill the job and the claude.exe it spawned. `Stop-Job` alone does not
  # terminate a job's child processes in PS 5.1 -- a claude.exe left behind keeps
  # its transcript open and its API call running, which is the original "hang".
  try { Stop-Job $job } catch { }
  try {
    # CIM, not Get-Process: PS 5.1's Get-Process has no CommandLine property, so
    # a filter on it matches nothing. A headless `claude -p` has no window;
    # interactive sessions do, so the windowed guard makes it structurally
    # impossible to kill a session a person is driving.
    Get-CimInstance Win32_Process -Filter "Name='claude.exe'" -ErrorAction SilentlyContinue |
      Where-Object { ($_.CommandLine -like "*--resume $SessionId*") -and ($_.CommandLine -like '* -p *') } |
      ForEach-Object {
        $win = (Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue).MainWindowHandle
        if ($win -ne 0) {
          Log "REFUSED to kill windowed claude.exe PID $($_.ProcessId) -- it is an interactive session, not the stalled resume."
        } else {
          Log "KILL claude.exe PID $($_.ProcessId) (stalled --resume $SessionId)"
          Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
      }
  } catch { Log "kill-sweep failed: $($_.Exception.Message)" }
}
$dur = ((Get-Date) - $t0).TotalSeconds
try { Remove-Job $job -Force } catch { }

$txt = if (Test-Path $out) { Read-Any $out } else { '' }
$err = if (Test-Path $errFile) { Read-Any $errFile } else { '' }

# Classify on the stdout reply, and fold stderr in ONLY when there is no reply.
# The gateway serves a single model id the local catalog does not describe, so
# the CLI prints an `unrecognized_model` notice to stderr on every run -- a
# notice, not a refusal. Folding it in unconditionally would match
# IsInfraFailure and report a fully successful resume as a platform outage, the
# exact M10/M12 shape that escalated a healthy run to an owner gate.
$cls = $txt
if ((-not $txt -or -not $txt.Trim()) -and $err) { $cls = $err }

if ($timedOut) {
  Log "RESULT TIMEOUT dur=$([int]$dur)s -- the session hung; chargeable, resume again."
  exit 3
}
if (IsInfraFailure $cls) {
  $m = @('Token quota exhausted','quota exceeded','usage limit','credit balance','Request rejected (429)','unrecognized_model','invalid api key','authentication_error','Failed to authenticate','rate-limited','rate limited') |
    Where-Object { $cls -match $_ } | Select-Object -First 1
  Log "RESULT INFRA dur=$([int]$dur)s match='$m' -- quota/auth/model failure; the session never ran, NOT chargeable."
  exit 2
}
if (-not $txt -or -not $txt.Trim()) {
  Log "RESULT EMPTY dur=$([int]$dur)s stderr=$($err.Length)chars -- a silent exit, not a verdict."
  exit 3
}
if (IsFail $cls) {
  Log "RESULT FAIL dur=$([int]$dur)s -- a recoverable API error; chargeable."
  exit 3
}
Log "RESULT OK dur=$([int]$dur)s chars=$($txt.Length)"
exit 0
