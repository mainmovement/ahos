# AHOS Claude autopilot: runs CLAUDE_AUTOPILOT_QUEUE.md missions one by one via run_mission.ps1, independent of Grok.
#
# ---------------------------------------------------------------------------
# Repair 2026-10-05 -- root cause J (runner orchestration failure)
# ---------------------------------------------------------------------------
# The original line 24 used `Start-Process powershell.exe ... -Wait`, an UNBOUNDED
# blocking primitive. On 2026-10-05 it never returned after the M11.2 child exited
# at 09:34:15Z even though `_claude_ap_M11_2_result.txt` already contained a
# perfectly parseable `AUTOPILOT_RESULT: DONE`. The runner idled with zero CPU for
# 34h+, never consumed the result, never advanced the queue, and never logged again.
#
# UTF-16LE encoding was NOT the root cause and is documented as DISPROVEN:
# .NET `[IO.File]::ReadAllText(path, [Text.Encoding]::UTF8)` honours a leading
# FF FE BOM and decodes UTF-16LE regardless of the supplied label, so the OLD
# parser already returned DONE on the real file. The result decoder below makes
# that BOM handling explicit and byte-exact, so correctness no longer depends on
# that .NET behaviour being an implementation detail.
#
# The repair:
#   * line 24's `-Wait` is replaced by a BOUNDED `HasExited` poll, so the parent
#     always retains control and can distinguish child-running / exited-ok /
#     exited-badly / timeout / internal-error (Phase 1);
#   * a durable `autopilot/active.json` is written BEFORE launch, so a later
#     runner can tell child-still-running from exited-but-unconsumed and never
#     re-launches an in-flight attempt (Phase 2);
#   * result decoding is explicit and fail-closed, and consumption is idempotent
#     via markers under `autopilot/consumed/` -- a result is applied at most once
#     (Phase 3);
#   * `autopilot/heartbeat.json` is written every loop iteration and every poll,
#     so a future stall is observable instead of silent for hours (Phase 4);
#   * a mission at NEEDS_REVIEW is an unresolved OWNER GATE and holds every later
#     row until the owner resolves it. BLOCKED_OWNER stays "(human gate; skipped)"
#     per the queue header and does NOT hold (Phase 6 / Phase 9).
#
# Test seam: set AHOS_RUNNER_TEST_MODE=1, and optionally AHOS_RUNNER_TEST_ROOT and
# AHOS_RUNNER_CHILD_SCRIPT, then dot-source this file. Only the functions are
# defined; the singleton guard and control loop are not entered.
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Continue'

# Paths are overridable so the state machine can be exercised against an isolated
# sandbox. In production this resolves to the real reports/grok tree unchanged.
if ($env:AHOS_RUNNER_TEST_ROOT) { $g = $env:AHOS_RUNNER_TEST_ROOT } else { $g = 'G:\robat\ahos\reports\grok' }
$qf             = "$g\CLAUDE_AUTOPILOT_QUEUE.md"
$ap             = "$g\autopilot"
$log            = "$ap\autopilot_log.txt"
$stateFile      = "$ap\state.json"          # per-mission attempt counters
$activeFile     = "$ap\active.json"         # durable in-flight mission record
$heartbeatFile  = "$ap\heartbeat.json"      # runner liveness / stall visibility
$consumedDir    = "$ap\consumed"            # idempotent result-application markers
$childScript    = if ($env:AHOS_RUNNER_CHILD_SCRIPT) { $env:AHOS_RUNNER_CHILD_SCRIPT } else { "$g\run_mission.ps1" }

$CHILD_POLL_SEC    = 15        # deterministic poll interval, never a busy spin
$CHILD_TIMEOUT_SEC = 21600     # 6h ceiling; M11.2 took 2.35h, so this is generous
$HOLD_HOURS        = 6         # Grok review hold, auto-expiring (unchanged)
$MAX_ATTEMPTS      = 3         # retries before a mission escalates to NEEDS_REVIEW
$IDLE_SLEEP_SEC    = 1800
$GATE_SLEEP_SEC    = 120
$LIMIT_SLEEP_SEC   = 1800

# The harness overrides these so TESTS A-I complete in seconds, not hours. In
# production every one of them stays at the value above.
if ($env:AHOS_RUNNER_TEST_MODE -eq '1') {
  $CHILD_TIMEOUT_SEC = 30; $IDLE_SLEEP_SEC = 1; $GATE_SLEEP_SEC = 1; $LIMIT_SLEEP_SEC = 1; $CHILD_POLL_SEC = 1
}

# --- logging -----------------------------------------------------------------
function L($m){ "$(Get-Date -f s) $m" | Out-File -Append -Encoding utf8 $log }

# --- queue model --------------------------------------------------------------
# Parses the queue table in document order. Document order is load-bearing: it is
# what makes "one by one" and the review-gate hold well defined.
function Get-MissionRows {
  $c = [IO.File]::ReadAllText($qf, [Text.Encoding]::UTF8)
  $rows = [regex]::Matches($c, '(?m)^\| (M[\w.\-]+|BL) \| ([A-Z_]+) \| (.+?) \|\s*$')
  $i = 0
  foreach ($r in $rows) {
    [pscustomobject]@{ Index=$i; Id=$r.Groups[1].Value; Status=$r.Groups[2].Value; Title=$r.Groups[3].Value }
    $i++
  }
}

function SetStatus($id, $st) {
  $c = [IO.File]::ReadAllText($qf, [Text.Encoding]::UTF8)
  $e = [regex]::Escape($id)
  $c = [regex]::Replace($c, "(?m)^\| $e \| [A-Z_]+ \|", "| $id | $st |")
  [IO.File]::WriteAllText($qf, $c, (New-Object Text.UTF8Encoding $false))
  L "$id -> $st"
}

# Returns one of:
#   @{ Held=$false; Mission=<row> }                       -- launchable now
#   @{ Held=$true;  Gate=<id>; Blocked=<id> }             -- owner gate holds the queue
#   @{ Held=$true;  Gate=$null; Blocked=$null }           -- nothing launchable at all
#
# The owner-gate rule: a row at NEEDS_REVIEW that sits ABOVE the first launchable
# row is an unresolved human review and holds everything below it. BLOCKED_OWNER is
# documented in the queue header as "(human gate; skipped)", so it does not hold --
# this preserves the existing skip semantics rather than inventing new ones.
function Select-NextMission($rows) {
  $launchable = @($rows | ?{ $_.Status -in 'PENDING','PARTIAL' })
  if ($launchable.Count -eq 0) { return @{ Held=$true; Gate=$null; Blocked=$null } }
  $first = $launchable[0]
  $gate = @($rows | ?{ $_.Index -lt $first.Index -and $_.Status -eq 'NEEDS_REVIEW' })
  if ($gate.Count -gt 0) { return @{ Held=$true; Gate=$gate[0].Id; Blocked=$first.Id } }
  return @{ Held=$false; Mission=$first }
}

# --- attempt state -------------------------------------------------------------
function Load-AttemptState {
  $h = @{}
  if (Test-Path -LiteralPath $stateFile) {
    try {
      $o = Get-Content -Raw -LiteralPath $stateFile | ConvertFrom-Json
      foreach ($p in $o.PSObject.Properties) { $h[$p.Name] = [int]$p.Value }
    } catch { L "state load err $_" }
  }
  return $h
}

function Save-AttemptState($state) {
  $state | ConvertTo-Json | Out-File -Encoding utf8 $stateFile
}

# --- result decoding (Phase 3) --------------------------------------------------
# Explicit, byte-exact BOM detection. Missing or ambiguous input is never success.
function Read-MissionResult([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return @{ Found=$false; Verdict='MISSING'; Text='' } }
  $bytes = [IO.File]::ReadAllBytes($Path)
  if     ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) { $text = [Text.Encoding]::Unicode.GetString($bytes, 2, $bytes.Length - 2) }
  elseif ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $text = [Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3) }
  else  { $text = [Text.Encoding]::UTF8.GetString($bytes) }
  return @{ Found=$true; Verdict='PRESENT'; Text=($text -replace "`r`n", "`n") }
}

# First-match semantics, identical to the pre-repair parser. The mission template
# requires the final output to end with exactly one AUTOPILOT_RESULT line, so the
# first match is the mission's own verdict.
function Classify-MissionResult([string]$Text) {
  $m = [regex]::Match($Text, 'AUTOPILOT_RESULT:\s*(DONE|PARTIAL|BLOCKED_OWNER)(.*)')
  if (-not $m.Success) { return @{ Verdict='MALFORMED'; Argument='' } }
  return @{ Verdict=$m.Groups[1].Value; Argument=$m.Groups[2].Value }
}

# --- bounded child wait (Phase 1) ------------------------------------------------
# Replaces `Start-Process -Wait`. The parent polls HasExited at a fixed interval,
# publishes a heartbeat on every poll, and surrenders control after $TimeoutSec.
# Outcomes: EXITED / TIMEOUT / ERROR, with an exit code where one is available.
function Wait-ForChildBounded($Process, [int]$TimeoutSec, [int]$PollSec, [string]$Mission, [int]$ChildPid) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($true) {
    try {
      if ($Process.HasExited) {
        $sw.Stop()
        $code = $null
        try { $code = $Process.ExitCode } catch { }
        return @{ Outcome='EXITED'; ExitCode=$code; WaitedSec=[int]$sw.Elapsed.TotalSeconds }
      }
    } catch {
      $sw.Stop()
      return @{ Outcome='ERROR'; ExitCode=$null; WaitedSec=[int]$sw.Elapsed.TotalSeconds; Error="$_" }
    }
    if ($sw.Elapsed.TotalSeconds -gt $TimeoutSec) {
      $sw.Stop()
      return @{ Outcome='TIMEOUT'; ExitCode=$null; WaitedSec=[int]$sw.Elapsed.TotalSeconds }
    }
    Write-Heartbeat 'WAITING_FOR_CHILD' $Mission $ChildPid ([int]$sw.Elapsed.TotalSeconds)
    Start-Sleep -Seconds $PollSec
  }
}

function Write-Heartbeat([string]$Phase, [string]$Mission, [int]$ChildPid, [int]$WaitedSec, [string]$Note) {
  try {
    @{ ts=(Get-Date -Format o); pid=$PID; phase=$Phase; mission=$Mission; child_pid=$ChildPid; waited_sec=$WaitedSec; note=$Note } |
      ConvertTo-Json -Compress -Depth 5 | Out-File -Encoding utf8 $heartbeatFile
  } catch { L "heartbeat err $_" }
}

# --- durable active state (Phase 2) -----------------------------------------------
function Write-ActiveState($rec) {
  $rec | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $activeFile
}
function Clear-ActiveState { if (Test-Path -LiteralPath $activeFile) { Remove-Item -LiteralPath $activeFile -Force } }

# Idempotent consumption: a result is applied to the queue at most once. The marker
# is written BEFORE the queue write so a crash between the two leaves a re-run able
# to see the verdict instead of re-applying it.
function Write-ConsumedMarker([string]$Safe, $info) {
  if (-not (Test-Path -LiteralPath $consumedDir)) { New-Item -ItemType Directory -Force -Path $consumedDir | Out-Null }
  $info | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 "$consumedDir\$Safe.json"
}
function Test-Consumed([string]$Safe) { Test-Path -LiteralPath "$consumedDir\$Safe.json" }

# Terminal-vs-retryable split of the marker above. DONE and BLOCKED_OWNER take the row
# out of the launchable set permanently, and TIMEOUT escalates it to NEEDS_REVIEW, so
# their markers are permanent no-re-execution guards. The retryable verdicts (PARTIAL,
# MALFORMED, MISSING, LIMIT) deliberately leave the row at PARTIAL so the next loop
# pass re-launches it; if such a marker blocked re-launch, the retry branch of
# Apply-Verdict would be dead code and the queue would stall on the very first PARTIAL
# -- which is exactly the M11.3 deadlock this fixed (MALFORMED result, PARTIAL row,
# "result already consumed -> skip launch" on every iteration).
function Test-ConsumedTerminal([string]$Safe) {
  $p = "$consumedDir\$Safe.json"
  if (-not (Test-Path -LiteralPath $p)) { return $false }
  try {
    $m = Get-Content -Raw -LiteralPath $p | ConvertFrom-Json
    if ($m.verdict) { return @('DONE','BLOCKED_OWNER','TIMEOUT') -contains $m.verdict }
  } catch { }
  # An unreadable or verdict-less marker is treated conservatively as terminal:
  # refusing to re-run is the fail-closed direction, and it is logged on every pass.
  return $true
}

# Reconciles the in-flight record left by a previous runner generation.
#   child alive + phase LAUNCHED      -> leave it alone, the loop guard will wait
#   child gone  + phase LAUNCHED      -> classify the result now (crash recovery)
#   consumed marker present           -> already applied, do not re-apply
function Reconcile-ActiveState {
  if (-not (Test-Path -LiteralPath $activeFile)) { return $null }
  $a = Get-Content -Raw -LiteralPath $activeFile | ConvertFrom-Json
  if ($a.phase -ne 'LAUNCHED') { return $null }
  $alive = $false
  if ($a.child_pid) { $alive = [bool](Get-Process -Id $a.child_pid -ErrorAction SilentlyContinue) }
  if ($alive) { L "reconcile $($a.mission): child pid $($a.child_pid) still running -> wait"; return @{ Action='WAIT'; Record=$a } }

  if (Test-Consumed $a.safe) {
    L "reconcile $($a.mission): already consumed -> no re-apply"
    return @{ Action='CONSUMED'; Record=$a }
  }
  $r = Read-MissionResult $a.result_path
  if ($r.Found) {
    $c = Classify-MissionResult $r.Text
    Write-ConsumedMarker $a.safe @{ mission=$a.mission; safe=$a.safe; verdict=$c.Verdict; argument=$c.Argument; source='reconcile'; ts=(Get-Date -Format o) }
    L "reconcile $($a.mission): child gone, result $($c.Verdict) -> applied"
    return @{ Action='APPLIED'; Record=$a; Verdict=$c.Verdict; Argument=$c.Argument }
  }
  L "reconcile $($a.mission): child gone, no result -> fail closed to NEEDS_REVIEW"
  return @{ Action='NO_RESULT'; Record=$a }
}

# --- verdict application ------------------------------------------------------------
# Applies one classified verdict to the queue. This is the ONLY place statuses move,
# and it refuses to touch a row that is not still RUNNING, so an owner gate can never
# be overwritten by an execution result.
function Apply-Verdict($state, [string]$Id, [string]$Safe, $verdict, [string]$argument, $wait) {
  $rows = Get-MissionRows
  $row = @($rows | ?{ $_.Id -eq $Id })[0]
  if (-not $row) { L "apply $Id : row vanished from queue -> skip"; return }
  if ($row.Status -ne 'RUNNING') { L "apply $Id : row is $($row.Status) not RUNNING -> owner gate preserved, no change"; return }

  switch ($verdict) {
    'DONE' {
      if ($Id -eq 'M14-M33' -and $argument -notmatch 'NO_REMAINING') { break }
      SetStatus $Id 'DONE'; $state[$Id] = 0
    }
    'BLOCKED_OWNER' { SetStatus $Id 'BLOCKED_OWNER'; L "$Id owner: $argument" }
    'TIMEOUT' {
      # A timeout is an anomaly, not a retryable transient: escalate to the human gate.
      SetStatus $Id 'NEEDS_REVIEW'; L "$Id child timeout after $($wait.WaitedSec)s -> NEEDS_REVIEW (owner gate)"
    }
    default {
      # PARTIAL / MALFORMED / MISSING: retry, capped at $MAX_ATTEMPTS.
      $state[$Id] = [int]$state[$Id] + 1
      if ($state[$Id] -ge $MAX_ATTEMPTS) { SetStatus $Id 'NEEDS_REVIEW' } else { SetStatus $Id 'PARTIAL' }
    }
  }
}

# --- startup reconciliation (Phase 6) -------------------------------------------------
# Produces the recovery receipt for results the previous generation never consumed,
# without consuming them and without erasing any owner gate. M11.2 is exactly this
# shape: result=DONE, queue=NEEDS_REVIEW (written by the mission's own commit
# 385a38b), and no durable record because the pre-repair runner never wrote one.
function Write-StartupReconciliation {
  $receipt = @{ ts=(Get-Date -Format o); runner_pid=$PID; entries=@() }
  foreach ($f in (Get-ChildItem -LiteralPath $g -Filter '_claude_ap_*_result.txt' -ErrorAction SilentlyContinue | Sort Name)) {
    # The result file is `_claude_<safe>_result.txt`; strip both the prefix and the
    # trailing _result, then map back to the queue row. TrimStart('_claude_') would
    # treat its argument as a char set rather than a prefix, hence the regexes.
    $safe = [regex]::Replace([IO.Path]::GetFileNameWithoutExtension($f.Name), '^_claude_', '')
    $safe = [regex]::Replace($safe, '_result$', '')
    $r = Read-MissionResult $f.FullName
    if (-not $r.Found) { continue }
    $c = Classify-MissionResult $r.Text
    $rows = Get-MissionRows
    $row = @($rows | ?{ $_.Id -and $safe -like ('ap_' + $_.Id -replace '[^\w]','_') })[0]
    $qstatus = if ($row) { $row.Status } else { 'NOT_IN_QUEUE' }
    # An owner gate is never converted into an execution-complete state. Results whose
    # row has already left PENDING are recorded as evidence only.
    $disposition = if ($qstatus -eq 'PENDING') { 'ELIGIBLE_RETRY' } else { 'OWNER_GATE_PRESERVED' }
    $receipt.entries += [pscustomobject]@{ safe=$safe; result_verdict=$c.Verdict; queue_status=$qstatus; disposition=$disposition }
    L "recovery $safe : result=$($c.Verdict) queue=$qstatus -> $disposition (not consumed, not re-run)"
  }
  $receipt | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 "$ap\startup_reconciliation.json"
  return $receipt
}

# --- mission launch -------------------------------------------------------------------
function Start-MissionAttempt($state, $row) {
  $id = $row.Id; $title = $row.Title
  $safe = 'ap_' + ($id -replace '[^\w]','_')
  $taskPath = "$g\_claude_task_$safe.txt"
  $resultPath = "$g\_claude_${safe}_result.txt"

  # Duplicate-execution guard: an in-flight attempt with a live child is never
  # re-launched, and a result whose verdict was terminal is never executed again. A
  # retryable verdict does NOT block here -- its marker records only that the previous
  # result was applied to the queue, not that the mission may never run again.
  if (Test-ConsumedTerminal $safe) { L "$id : result already consumed with a terminal verdict -> skip launch"; return $false }
  if (Test-Path -LiteralPath $activeFile) {
    $a = Get-Content -Raw -LiteralPath $activeFile | ConvertFrom-Json
    if ($a.safe -eq $safe -and $a.phase -eq 'LAUNCHED' -and $a.child_pid -and (Get-Process -Id $a.child_pid -ErrorAction SilentlyContinue)) {
      L "$id : attempt already in flight (pid $($a.child_pid)) -> no duplicate launch"; return $false
    }
  }

  $p = [IO.File]::ReadAllText("$ap\MISSION_PROMPT_TEMPLATE.txt", [Text.Encoding]::UTF8).Replace('{ID}', $id).Replace('{TITLE}', $title)
  if ($id -eq 'M14-M33') {
    $p += "`n`nSPECIAL: pick the NEXT unfinished mission in M14..M33 (plan order) and deliver it. If every one of M14..M33 is done or owner-blocked, end with AUTOPILOT_RESULT: DONE NO_REMAINING. Otherwise end with AUTOPILOT_RESULT: PARTIAL <which missions remain>."
  }
  [IO.File]::WriteAllText($taskPath, $p, (New-Object Text.UTF8Encoding $false))

  # A retry must not inherit the previous attempt's result file: if the new child died
  # before overwriting it, the stale text would be classified again and the attempt
  # charged against output the child never produced. Move it aside rather than delete,
  # so the record of what the previous attempt actually printed survives as evidence.
  if (Test-Path -LiteralPath $resultPath) { Move-Item -LiteralPath $resultPath -Destination ($resultPath + '.superseded') -Force }

  $cf = ''; if ([int]$state[$id] -gt 0) { $cf = '-continueFresh' }
  SetStatus $id 'RUNNING'

  # Durable record BEFORE launch: if the runner dies here, a later generation can
  # still tell an in-flight attempt from a completed one.
  $childPid = 0
  Write-ActiveState @{ mission=$id; safe=$safe; attempt=[int]$state[$id]; task_path=$taskPath; result_path=$resultPath; launched_at=(Get-Date -Format o); runner_pid=$PID; child_pid=0; phase='LAUNCHED' }

  $proc = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$childScript`" -n $safe $cf"
  $childPid = $proc.Id
  Write-ActiveState @{ mission=$id; safe=$safe; attempt=[int]$state[$id]; task_path=$taskPath; result_path=$resultPath; launched_at=(Get-Date -Format o); runner_pid=$PID; child_pid=$childPid; phase='LAUNCHED' }

  L "launch $id safe=$safe child=$childPid attempt=$([int]$state[$id])"
  Write-Heartbeat 'CHILD_LAUNCHED' $id $childPid 0

  $wait = Wait-ForChildBounded $proc $CHILD_TIMEOUT_SEC $CHILD_POLL_SEC $id $childPid
  Write-Heartbeat 'CHILD_FINISHED' $id $childPid $wait.WaitedSec ($wait.Outcome + ' code=' + $wait.ExitCode)
  L "wait $id : $($wait.Outcome) after $($wait.WaitedSec)s code=$($wait.ExitCode)"

  $r = Read-MissionResult $resultPath
  if ($r.Found -and $r.Text -match 'usage limit|quota exceeded|credit balance') {
    Write-ConsumedMarker $safe @{ mission=$id; safe=$safe; verdict='LIMIT'; ts=(Get-Date -Format o) }
    Apply-Verdict $state $id $safe 'PARTIAL' '' $wait
    Clear-ActiveState
    L "limit hit - sleeping $LIMIT_SLEEP_SEC`s"
    Start-Sleep -Seconds $LIMIT_SLEEP_SEC
    return $true
  }

  $verdict = if ($wait.Outcome -eq 'TIMEOUT') { 'TIMEOUT' }
             elseif ($r.Found) { (Classify-MissionResult $r.Text).Verdict }
             else { 'MISSING' }
  $argument = if ($r.Found) { (Classify-MissionResult $r.Text).Argument } else { '' }

  Write-ConsumedMarker $safe @{ mission=$id; safe=$safe; verdict=$verdict; argument=$argument; wait_outcome=$wait.Outcome; exit_code=$wait.ExitCode; waited_sec=$wait.WaitedSec; source='live'; ts=(Get-Date -Format o) }
  Apply-Verdict $state $id $safe $verdict $argument $wait
  # The in-flight record has served its purpose once its verdict is on the queue and
  # the marker is down; leaving it would make every later pass reconcile a finished
  # mission.
  Clear-ActiveState
  return $true
}

# --- control loop -----------------------------------------------------------------------
function Invoke-RunnerLoop {
  $iterations = 0
  while ($true) {
    $iterations++
    # Test seam: a positive budget makes the loop exit after N iterations.
    if ($script:LoopBudget -gt 0 -and $iterations -gt $script:LoopBudget) { break }
    # Reload every iteration. The on-disk counters are authoritative, and this is the
    # only route by which an out-of-band correction -- an attempt budget voided after a
    # harness defect was fixed -- can reach a runner that is already running. Earlier the
    # load happened once at loop entry, so a live runner kept its stale counters in
    # memory and Save-AttemptState clobbered the correction when the in-flight attempt
    # ended. Save-AttemptState is the sole writer and persists the whole table, so a
    # reload mid-loop returns exactly what the last save wrote.
    $state = Load-AttemptState
    try {
      Write-Heartbeat 'LOOP_START' '' 0 0

      # Never overlap a live mission child, whether ours or Grok's. Match the child
      # script this runner actually spawns rather than a hardcoded name: in production
      # that is run_mission.ps1, and in the test harness it is the generated stub, whose
      # path is unique per harness run. Matching the literal script keeps an unrelated
      # powershell that merely mentions run_mission.ps1 from being mistaken for a mission
      # child -- and, from the other side, stops a sandbox loop from deferring forever to
      # a production mission child that is not its own.
      $me = $PID
      $childRe = [regex]::Escape($childScript)
      if (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ?{ $_.CommandLine -match $childRe -and $_.ProcessId -ne $me }) {
        Write-Heartbeat 'CHILD_RUNNING' '' 0 0 'another mission child is live'
        Start-Sleep -Seconds $CHILD_POLL_SEC; continue
      }

      $h = "$ap\HOLD.flag"
      if ((Test-Path $h) -and (((Get-Date) - (Get-Item $h).LastWriteTime).TotalHours -lt $HOLD_HOURS)) {
        Write-Heartbeat 'HOLD' '' 0 0 'Grok review hold active'
        Start-Sleep -Seconds $GATE_SLEEP_SEC; continue
      }

      # A previous generation's in-flight record is reconciled from durable evidence.
      $rec = Reconcile-ActiveState
      if ($rec -and $rec.Action -eq 'WAIT') { Start-Sleep -Seconds $CHILD_POLL_SEC; continue }

      $rows = Get-MissionRows

      # A RUNNING row with no live child was interrupted out-of-band. Preserve the
      # pre-repair behaviour: hand it to the owner rather than silently re-running it.
      $run = @($rows | ?{ $_.Status -eq 'RUNNING' })[0]
      if ($run) {
        L "$($run.Id) RUNNING with no live child -> NEEDS_REVIEW (owner gate)"
        SetStatus $run.Id 'NEEDS_REVIEW'
        continue
      }

      $sel = Select-NextMission $rows
      if ($sel.Held) {
        if ($sel.Gate) {
          L "owner gate: $($sel.Gate) at NEEDS_REVIEW holds $($sel.Blocked) -> not launched"
          Write-Heartbeat 'OWNER_GATE_HOLD' $sel.Blocked 0 0 "gate=$($sel.Gate)"
        } else {
          L "queue empty - autopilot idle"
          Write-Heartbeat 'IDLE' '' 0 0
        }
        Start-Sleep -Seconds $IDLE_SLEEP_SEC; continue
      }

      $null = Start-MissionAttempt $state $sel.Mission
      Save-AttemptState $state
      Start-Sleep -Seconds 30
    } catch {
      L "err $_"
      Write-Heartbeat 'LOOP_ERROR' '' 0 0 "$_"
      Start-Sleep -Seconds 300
    }
  }
}

# --- entry point -------------------------------------------------------------------------
# Test mode: only the functions above are defined; nothing runs. Production runs the
# singleton guard, the startup reconciliation, then the control loop.
if ($env:AHOS_RUNNER_TEST_MODE -eq '1') { return }

$script:LoopBudget = 0
$me = $PID
if (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ?{ $_.CommandLine -match 'claude_autopilot\.ps1' -and $_.ProcessId -ne $me }) { exit }
if (-not (Test-Path -LiteralPath $ap)) { New-Item -ItemType Directory -Force -Path $ap | Out-Null }
L "autopilot start pid=$me"
Write-StartupReconciliation | Out-Null
Invoke-RunnerLoop
