# AHOS autopilot runner repair -- test harness for TESTS A-I (Phase 7).
#
# Runs entirely inside an isolated sandbox (AHOS_RUNNER_TEST_ROOT). Nothing here
# touches the real queue, the real reports/grok tree, or any real mission artifact.
# Every assertion is on sandbox state only. A test that fails emits a RESULT: FAIL
# line with a diagnostic; the harness prints one RESULT line per test so the pytest
# wrapper can parse it. Nothing is marked passed without actually running.
#
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File test_runner.ps1 [-Test A]
param([string]$Test = 'ALL')

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path (Split-Path -Parent $here) 'claude_autopilot.ps1'
$realTemplate = Join-Path $here 'MISSION_PROMPT_TEMPLATE.txt'

# Single dispatch stub. The runner binds the child script path once, at dot-source
# time, so swapping it per test would silently not take effect; behaviour is
# selected by STUB_MODE instead, which the stub reads at run time.
#   default  -> write a UTF-8 result ending in AUTOPILOT_RESULT: DONE
#   utf16    -> same, but UTF-16LE with an FF FE BOM (the real M11.2 shape)
#   partial  -> write a UTF-8 result ending in AUTOPILOT_RESULT: PARTIAL
#   noresult -> exit without writing anything
#   infra    -> the real M12 shape: a quota/model death with NO verdict line
$stub = Join-Path $env:TEMP ('ahos_stub_' + [IO.Path]::GetRandomFileName().Replace('.','') + '.ps1')
Set-Content -LiteralPath $stub -Encoding UTF8 @'
param([string]$n, [switch]$continueFresh)
$out = Join-Path $env:AHOS_RUNNER_TEST_ROOT ("_claude_${n}_result.txt")
Start-Sleep -Seconds 1
$mode = $env:STUB_MODE; if (-not $mode) { $mode = 'default' }
switch ($mode) {
  'noresult' { }
  'infra' {
    # The CLI's real quota-death output: a model/429 error and no AUTOPILOT_RESULT
    # line, because the mission never ran. From _claude_ap_M12_result.txt.
    $body = "claude.exe : [claude-code:unrecognized_model] {""model"":""Atria-Dawn-Preview"",""query_source"":""sdk""}`r`n`r`nAPI Error: Request rejected (429) . Token quota exhausted.`r`n"
    [IO.File]::WriteAllText($out, $body, (New-Object Text.UTF8Encoding $false))
  }
  'partial' {
    [IO.File]::WriteAllText($out, "stub partial`r`n`r`nAUTOPILOT_RESULT: PARTIAL remains=stub`r`n", (New-Object Text.UTF8Encoding $false))
  }
  'utf16' {
    $body = "persian test`r`n`r`nAUTOPILOT_RESULT: DONE`r`n"
    $payload = [Text.Encoding]::Unicode.GetBytes($body)
    $bom = New-Object byte[] ($payload.Length + 2)
    $bom[0] = 0xFF; $bom[1] = 0xFE
    [Array]::Copy($payload, 0, $bom, 2, $payload.Length)
    [IO.File]::WriteAllBytes($out, $bom)
  }
  default {
    [IO.File]::WriteAllText($out, "stub result`r`n`r`nAUTOPILOT_RESULT: DONE`r`n", (New-Object Text.UTF8Encoding $false))
  }
}
'@

# One sandbox for the whole run, with mutable state wiped between tests. The runner
# binds its path variables when it is dot-sourced, so a per-test sandbox would need
# a re-dot-source; wiping the mutable state keeps the same binding and is simpler.
$sandbox = Join-Path $env:TEMP ('ahos_runner_test_' + [IO.Path]::GetRandomFileName().Replace('.',''))
$null = New-Item -ItemType Directory -Force -Path (Join-Path $sandbox 'autopilot')
# The runner reads the mission prompt template; the tests need a real one present.
Copy-Item -LiteralPath $realTemplate -Destination (Join-Path $sandbox 'autopilot\MISSION_PROMPT_TEMPLATE.txt') -Force
$env:AHOS_RUNNER_TEST_ROOT = $sandbox
$env:AHOS_RUNNER_TEST_MODE  = '1'
$env:AHOS_RUNNER_CHILD_SCRIPT = $stub

# Dot-source the runner in test mode: functions only, no singleton guard, no loop.
. $runner
$ErrorActionPreference = 'Continue'

$script:results = @()
function Pass([string]$name)  { $script:results += "RESULT: PASS $name"; Write-Host "RESULT: PASS $name" }
function Fail([string]$name, [string]$why) {
  $script:results += "RESULT: FAIL $name -- $why"; Write-Host "RESULT: FAIL $name -- $why"
}

function Clear-SandboxState {
  # Wipe every mutable artifact so tests cannot leak verdicts into each other.
  $apd = Join-Path $sandbox 'autopilot'
  foreach ($f in @('active.json','heartbeat.json','state.json','startup_reconciliation.json','infra_state.json')) {
    $p = Join-Path $apd $f; if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
  }
  $cd = Join-Path $apd 'consumed'; if (Test-Path -LiteralPath $cd) { Remove-Item -LiteralPath $cd -Recurse -Force }
  Get-ChildItem -LiteralPath $sandbox -Filter '_claude_*' -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
  Remove-Item Env:\STUB_MODE -ErrorAction SilentlyContinue
}

function New-Queue([string[]]$rows) {
  $lines = @('# sandbox queue', '', '| ID | STATUS | MISSION |', '|---|---|---|')
  foreach ($r in $rows) { $lines += "| $r |" }
  [IO.File]::WriteAllLines((Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md'), $lines, (New-Object Text.UTF8Encoding $false))
}

function With-StubMode([string]$mode, $body) {
  $env:STUB_MODE = $mode
  try { & $body } finally { Remove-Item Env:\STUB_MODE -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------------------
# TEST A: child exits normally -> runner regains control without hanging.
#         (proves the unbounded -Wait is gone)
# ---------------------------------------------------------------------------
function Test-A {
  Clear-SandboxState
  New-Queue @('M11.3 | PENDING | t3', 'M11.4 | PENDING | t4')
  $state = @{}
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $ok = Start-MissionAttempt $state (Get-MissionRows | Select -First 1)
  $sw.Stop()
  if (-not $ok) { Fail 'A normal_child_exit' 'Start-MissionAttempt returned false'; return }
  if ($sw.Elapsed.TotalMinutes -gt 1) { Fail 'A normal_child_exit' "wait took $($sw.Elapsed.TotalSeconds)s -- still blocking"; return }
  $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
  if ($c -notmatch '\| M11\.3 \| DONE \|') { Fail 'A normal_child_exit' "queue did not reach DONE: $c"; return }
  Pass 'A normal_child_exit'
}

# ---------------------------------------------------------------------------
# TEST B: child writes a UTF-16LE-BOM result -> parsed correctly.
#         (proves the BOM path; the real M11.2 file is exactly this shape)
# ---------------------------------------------------------------------------
function Test-B {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  With-StubMode 'utf16' {
    $state = @{}
    $null = Start-MissionAttempt $state (Get-MissionRows | Select -First 1)
    $bytes = [IO.File]::ReadAllBytes((Join-Path $sandbox '_claude_ap_M11_4_result.txt'))
    if ($bytes[0] -ne 0xFF -or $bytes[1] -ne 0xFE) { Fail 'B utf16le_bom_result' 'file is not UTF-16LE BOM'; return }
    $r = Read-MissionResult (Join-Path $sandbox '_claude_ap_M11_4_result.txt')
    if (-not $r.Found) { Fail 'B utf16le_bom_result' 'result not found'; return }
    if ($r.Text -notmatch 'AUTOPILOT_RESULT:\s*DONE') { Fail 'B utf16le_bom_result' 'UTF-16LE text not decoded'; return }
    $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
    if ($c -notmatch '\| M11\.4 \| DONE \|') { Fail 'B utf16le_bom_result' 'queue not DONE on UTF-16LE input'; return }
    Pass 'B utf16le_bom_result'
  }
}

# ---------------------------------------------------------------------------
# TEST C: child exits without writing a result -> runner fails closed, never DONE.
# ---------------------------------------------------------------------------
function Test-C {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  With-StubMode 'noresult' {
    $state = @{}
    $null = Start-MissionAttempt $state (Get-MissionRows | Select -First 1)
    $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
    if ($c -match '\| M11\.4 \| DONE \|') { Fail 'C no_result_fails_closed' 'missing result classified DONE'; return }
    if ($c -notmatch '\| M11\.4 \| PARTIAL \|') { Fail 'C no_result_fails_closed' "expected PARTIAL, got: $c"; return }
    Pass 'C no_result_fails_closed'
  }
}

# ---------------------------------------------------------------------------
# TEST D: child exceeds the timeout -> runner records TIMEOUT, regains control.
# ---------------------------------------------------------------------------
function Test-D {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  $stubSlow = Join-Path $sandbox 'stub_slow.ps1'
  Set-Content -LiteralPath $stubSlow -Encoding UTF8 @'
param([string]$n, [switch]$continueFresh)
Start-Sleep -Seconds 300
'@
  $proc = $null
  try {
    SetStatus 'M11.4' 'RUNNING'
    $proc = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$stubSlow`" -n ap_M11_4"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $w = Wait-ForChildBounded $proc 4 1 'M11.4' $proc.Id
    $sw.Stop()
    if ($w.Outcome -ne 'TIMEOUT') { Fail 'D child_timeout_recorded' "expected TIMEOUT, got $($w.Outcome)"; return }
    if ($sw.Elapsed.TotalSeconds -gt 30) { Fail 'D child_timeout_recorded' "wait was not bounded: $($sw.Elapsed.TotalSeconds)s"; return }
    Pass 'D child_timeout_recorded'
  } finally {
    if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  }
}

# ---------------------------------------------------------------------------
# TEST E: runner interrupted after launch -> recoverable from durable state.
# ---------------------------------------------------------------------------
function Test-E {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  # Simulate a previous generation that launched and died mid-flight, leaving only
  # the durable record plus a completed result it never consumed.
  $active = Join-Path $sandbox 'autopilot\active.json'
  @{ mission='M11.4'; safe='ap_M11_4'; attempt=0; task_path="$sandbox\task.txt"; result_path=(Join-Path $sandbox '_claude_ap_M11_4_result.txt'); launched_at=((Get-Date).AddHours(-1).ToString('o')); runner_pid=99999; child_pid=99998; phase='LAUNCHED' } |
    ConvertTo-Json | Out-File -Encoding utf8 $active
  [IO.File]::WriteAllText((Join-Path $sandbox '_claude_ap_M11_4_result.txt'), "AUTOPILOT_RESULT: PARTIAL remains=M11.4`n", (New-Object Text.UTF8Encoding $false))

  $rec = Reconcile-ActiveState
  if (-not $rec -or $rec.Action -ne 'APPLIED') { Fail 'E interruption_recovery' "expected APPLIED, got $(if($rec){$rec.Action}else{'null'})"; return }
  if ($rec.Verdict -ne 'PARTIAL') { Fail 'E interruption_recovery' "expected PARTIAL verdict, got $($rec.Verdict)"; return }
  if (-not (Test-Consumed 'ap_M11_4')) { Fail 'E interruption_recovery' 'consumption marker not written'; return }
  Pass 'E interruption_recovery'
}

# ---------------------------------------------------------------------------
# TEST F: an already-completed result is never executed again.
# ---------------------------------------------------------------------------
function Test-F {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  $cd = Join-Path $sandbox 'autopilot\consumed'
  $null = New-Item -ItemType Directory -Force -Path $cd
  @{ mission='M11.4'; safe='ap_M11_4'; verdict='DONE'; ts=(Get-Date -Format o) } |
    ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $cd 'ap_M11_4.json')
  $state = @{}
  $ok = Start-MissionAttempt $state (Get-MissionRows | Select -First 1)
  if ($ok) { Fail 'F no_duplicate_execution' 'launch proceeded despite a consumed marker'; return }
  $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
  if ($c -notmatch '\| M11\.4 \| PENDING \|') { Fail 'F no_duplicate_execution' "a consumed result changed queue status: $c"; return }
  Pass 'F no_duplicate_execution'
}

# ---------------------------------------------------------------------------
# TEST G: NEEDS_REVIEW cannot be silently converted to accepted.
# ---------------------------------------------------------------------------
function Test-G {
  Clear-SandboxState
  New-Queue @('M11.2 | NEEDS_REVIEW | t2', 'M11.3 | PENDING | t3')
  $sel = Select-NextMission (Get-MissionRows)
  if (-not $sel.Held) { Fail 'G owner_gate_preserved' 'queue below a NEEDS_REVIEW row was allowed to launch'; return }
  if ($sel.Gate -ne 'M11.2') { Fail 'G owner_gate_preserved' "wrong gate id: $($sel.Gate)"; return }
  if ($sel.Blocked -ne 'M11.3') { Fail 'G owner_gate_preserved' "wrong blocked id: $($sel.Blocked)"; return }

  # And a direct DONE verdict aimed at a NEEDS_REVIEW row must be refused.
  Clear-SandboxState
  New-Queue @('M11.2 | NEEDS_REVIEW | t2')
  $state = @{}
  Apply-Verdict $state 'M11.2' 'ap_M11_2' 'DONE' '' @{ Outcome='EXITED'; ExitCode=0; WaitedSec=1 }
  $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
  if ($c -notmatch '\| M11\.2 \| NEEDS_REVIEW \|') { Fail 'G owner_gate_preserved' "DONE overwrote NEEDS_REVIEW: $c"; return }
  Pass 'G owner_gate_preserved'
}

# ---------------------------------------------------------------------------
# TEST H: no path can launch two copies of the same mission attempt.
# ---------------------------------------------------------------------------
function Test-H {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  $stubHang = Join-Path $sandbox 'stub_hang.ps1'
  Set-Content -LiteralPath $stubHang -Encoding UTF8 @'
param([string]$n, [switch]$continueFresh)
Start-Sleep -Seconds 120
'@
  $proc = $null
  try {
    $state = @{}
    $rows = Get-MissionRows
    SetStatus 'M11.4' 'RUNNING'
    $proc = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$stubHang`" -n ap_M11_4"
    $active = Join-Path $sandbox 'autopilot\active.json'
    @{ mission='M11.4'; safe='ap_M11_4'; attempt=0; task_path=''; result_path=''; launched_at=(Get-Date -Format o); runner_pid=$PID; child_pid=$proc.Id; phase='LAUNCHED' } |
      ConvertTo-Json | Out-File -Encoding utf8 $active

    # Second launch attempt for the SAME mission while the first child is live.
    $ok = Start-MissionAttempt $state $rows
    if ($ok) { Fail 'H no_duplicate_launch' 'second launch was permitted'; return }
    # A hidden powershell child also owns a conhost; only count real mission children.
    $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($proc.Id)" |
      ?{ $_.Name -eq 'powershell.exe' -and $_.CommandLine -like '*stub*' })
    if ($kids.Count -gt 0) { Fail 'H no_duplicate_launch' "duplicate mission child spawned: $($kids.Count)"; return }
    Pass 'H no_duplicate_launch'
  } finally {
    if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  }
}

# ---------------------------------------------------------------------------
# TEST I (runtime verification support): the full control loop wires together
# selection -> launch -> bounded wait -> decode -> verdict -> queue transition,
# with no manual intervention.
# ---------------------------------------------------------------------------
function Test-I {
  Clear-SandboxState
  New-Queue @('M11.2 | NEEDS_REVIEW | t2', 'M11.3 | PENDING | t3')
  $script:LoopBudget = 2
  Invoke-RunnerLoop
  $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
  if ($c -match '\| M11\.3 \| (RUNNING|DONE) \|') { Fail 'I loop_respects_owner_gate' "loop advanced M11.3: $c"; return }
  if ($c -notmatch '\| M11\.3 \| PENDING \|') { Fail 'I loop_respects_owner_gate' "M11.3 left PENDING: $c"; return }
  if ($c -notmatch '\| M11\.2 \| NEEDS_REVIEW \|') { Fail 'I loop_respects_owner_gate' "gate was modified: $c"; return }
  Pass 'I loop_respects_owner_gate'
}

# ---------------------------------------------------------------------------
# TEST J: a retryable verdict does not permanently block re-execution.
#         (the M11.3 deadlock: MALFORMED result, PARTIAL row, retry never ran)
# ---------------------------------------------------------------------------
function Test-J {
  # The predicate: only terminal verdicts are permanent no-re-execution guards.
  Clear-SandboxState
  $cd = Join-Path $sandbox 'autopilot\consumed'
  $null = New-Item -ItemType Directory -Force -Path $cd
  foreach ($v in 'DONE','BLOCKED_OWNER','TIMEOUT') {
    @{ mission='M11.4'; safe='ap_M11_4'; verdict=$v; ts=(Get-Date -Format o) } |
      ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $cd 'ap_M11_4.json')
    if (-not (Test-ConsumedTerminal 'ap_M11_4')) { Fail 'J retryable_after_partial' "verdict $v was not treated as terminal"; return }
  }
  foreach ($v in 'PARTIAL','MALFORMED','MISSING','LIMIT') {
    @{ mission='M11.4'; safe='ap_M11_4'; verdict=$v; ts=(Get-Date -Format o) } |
      ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $cd 'ap_M11_4.json')
    if (Test-ConsumedTerminal 'ap_M11_4') { Fail 'J retryable_after_partial' "verdict $v blocked the retry path"; return }
  }

  # End to end: a mission left at PARTIAL by a MALFORMED result is re-launched, and the
  # fresh result replaces the old marker.
  Clear-SandboxState
  New-Queue @('M11.4 | PARTIAL | t4')
  $null = New-Item -ItemType Directory -Force -Path $cd
  @{ mission='M11.4'; safe='ap_M11_4'; verdict='MALFORMED'; ts=(Get-Date -Format o) } |
    ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $cd 'ap_M11_4.json')
  # A stale result from the previous attempt must be moved aside and preserved, not
  # re-read as if the new child had produced it.
  $stale = Join-Path $sandbox '_claude_ap_M11_4_result.txt'
  [IO.File]::WriteAllText($stale, "stale`r`nAUTOPILOT_RESULT: PARTIAL remains=stale`r`n", (New-Object Text.UTF8Encoding $false))
  $state = @{ 'M11.4' = 1 }
  $ok = Start-MissionAttempt $state (Get-MissionRows | Select -First 1)
  if (-not $ok) { Fail 'J retryable_after_partial' 'a MALFORMED marker blocked the retry launch'; return }
  if (-not (Test-Path -LiteralPath ($stale + '.superseded'))) { Fail 'J retryable_after_partial' 'the stale result was not preserved as .superseded'; return }
  $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
  if ($c -notmatch '\| M11\.4 \| DONE \|') { Fail 'J retryable_after_partial' "retry did not reach DONE: $c"; return }
  $m = Get-Content -Raw -LiteralPath (Join-Path $cd 'ap_M11_4.json') | ConvertFrom-Json
  if ($m.verdict -ne 'DONE') { Fail 'J retryable_after_partial' "marker not overwritten with the new verdict: $($m.verdict)"; return }
  Pass 'J retryable_after_partial'
}

# ---------------------------------------------------------------------------
# TEST K: an out-of-band attempt-budget correction reaches a LIVE runner.
#         (the defect this session: state.json was loaded once at loop entry, so a
#          correction made while the runner was running was ignored and then
#          clobbered by the next Save-AttemptState)
# ---------------------------------------------------------------------------
function Test-K {
  Clear-SandboxState
  New-Queue @('M11.4 | PENDING | t4')
  $statePath = Join-Path $sandbox 'autopilot\state.json'
  # The loop's own save is the only internal writer, so the reload is invisible in the
  # normal flow -- the only thing that can prove it is a write from OUTSIDE the loop,
  # landing between two iterations. A background job is used rather than a threadpool
  # timer on purpose: an error in a delegate-invoked scriptblock terminates the process
  # from a threadpool thread, whereas a job is a separate process whose failure cannot
  # take the harness down. It writes at T+3s, after iteration 1's save at ~T+1.1s and
  # well before iteration 2's load at ~T+31s (the 30s post-launch sleep).
  $jb = Start-Job -ArgumentList $statePath -ScriptBlock {
    param($p) Start-Sleep -Seconds 3
    @{ 'M11.4' = 2 } | ConvertTo-Json | Out-File -Encoding utf8 $p
  }
  try {
    With-StubMode 'partial' {
      $script:LoopBudget = 2
      Invoke-RunnerLoop
    }
  } finally {
    $jb | Wait-Job -Timeout 15 | Out-Null
    Remove-Job $jb -Force -ErrorAction SilentlyContinue
  }

  # Iteration 1 loads an empty state -> PARTIAL -> counter 1 -> PARTIAL. The job then
  # writes counter 2. Iteration 2 must load THAT: 2 + 1 = 3 >= MAX_ATTEMPTS ->
  # NEEDS_REVIEW. Under the old load-once code iteration 2 would still see its
  # in-memory 1 -> 2 -> PARTIAL, and the correction would be silently ignored.
  $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
  if ($c -notmatch '\| M11\.4 \| NEEDS_REVIEW \|') { Fail 'K out_of_band_state_read' "expected NEEDS_REVIEW from the reloaded counter, got: $c"; return }
  $s = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
  if ([int]$s.'M11.4' -ne 3) { Fail 'K out_of_band_state_read' "counter should be 3 after the reloaded 2 was incremented, got $($s.'M11.4')"; return }
  Pass 'K out_of_band_state_read'
}

# ---------------------------------------------------------------------------
# TEST L: a platform/quota failure is infrastructure, not a mission failure.
#         (the M10/M12 false escalation: a dead token quota froze the whole queue)
# ---------------------------------------------------------------------------
function Test-L {
  # 1. The classifier must match the CLI's REAL wording. The old 'quota exceeded'
  #    pattern does not, which is why M12 escalated.
  $infraText = "claude.exe : [claude-code:unrecognized_model] {""model"":""Atria-Dawn-Preview""}`r`n`r`nAPI Error: Request rejected (429) . Token quota exhausted.`r`n"
  if (-not (Test-InfraFailure $infraText)) { Fail 'L infra_failure_is_not_mission_failure' 'the real CLI quota output was not classified as infrastructure'; return }

  # 2. A mission whose child died on a dead quota returns to PENDING, charges no
  #    attempt, and does NOT escalate to NEEDS_REVIEW.
  Clear-SandboxState
  New-Queue @('M12 | PENDING | agent org')
  With-StubMode 'infra' {
    $state = @{}
    $null = Start-MissionAttempt $state (Get-MissionRows | Select -First 1)
    $c = Get-Content -Raw -LiteralPath (Join-Path $sandbox 'CLAUDE_AUTOPILOT_QUEUE.md')
    if ($c -notmatch '\| M12 \| PENDING \|') { Fail 'L infra_failure_is_not_mission_failure' "infra failure did not return the row to PENDING: $c"; return }
    if ($state.Count -ne 0 -and [int]$state['M12'] -ne 0) { Fail 'L infra_failure_is_not_mission_failure' "an infra failure charged an attempt: $($state | ConvertTo-Json -Compress)"; return }
    if ($c -match '\| M12 \| NEEDS_REVIEW \|') { Fail 'L infra_failure_is_not_mission_failure' 'an infra failure escalated to an owner gate and would freeze the queue'; return }
  }

  # 3. The marker records INFRA and is NOT terminal, so the row stays launchable.
  $cd = Join-Path $sandbox 'autopilot\consumed'
  $m = Get-Content -Raw -LiteralPath (Join-Path $cd 'ap_M12.json') | ConvertFrom-Json
  if ($m.verdict -ne 'INFRA') { Fail 'L infra_failure_is_not_mission_failure' "marker verdict was $($m.verdict), expected INFRA"; return }
  if (Test-ConsumedTerminal 'ap_M12') { Fail 'L infra_failure_is_not_mission_failure' 'an INFRA marker blocked re-execution; the queue would stall on a dead quota'; return }

  # 4. The queue below an infra-affected row is NOT held -- only NEEDS_REVIEW holds.
  Clear-SandboxState
  New-Queue @('M12 | PENDING | agent org', 'M34 | PENDING | coherence audit')
  $sel = Select-NextMission (Get-MissionRows)
  if ($sel.Held) { Fail 'L infra_failure_is_not_mission_failure' 'a PENDING row held the queue (only NEEDS_REVIEW may hold)'; return }
  if ($sel.Mission.Id -ne 'M12') { Fail 'L infra_failure_is_not_mission_failure' "expected M12 to be launchable, got $($sel.Mission.Id)"; return }

  # 5. Backoff is monotonic, positive, and saturates at its declared ceiling. The
  #    ceiling is the test-overridable $LIMIT_SLEEP_SEC, so the invariants are
  #    asserted rather than any production value.
  $cap = $LIMIT_SLEEP_SEC
  $prev = 0
  foreach ($n in 1..8) {
    $got = Get-InfraBackoffSec $n
    if ($got -lt 1) { Fail 'L infra_failure_is_not_mission_failure' "backoff for n=$n was ${got}s, must be positive"; return }
    if ($got -lt $prev) { Fail 'L infra_failure_is_not_mission_failure' "backoff must be monotonic: $prev then $got"; return }
    if ($got -gt $cap) { Fail 'L infra_failure_is_not_mission_failure' "backoff ${got}s exceeded the ceiling ${cap}s"; return }
    $prev = $got
  }
  if ((Get-InfraBackoffSec 99) -ne $cap) { Fail 'L infra_failure_is_not_mission_failure' 'backoff must saturate at its ceiling'; return }

  # 6. The REAL M12 evidence file is classified as infrastructure. This is the
  #    regression pin against the exact wording that froze the queue on 2026-10-08.
  $real = Join-Path (Split-Path -Parent (Split-Path -Parent $here)) '_claude_ap_M12_result.txt'
  if (Test-Path -LiteralPath $real) {
    $rr = Read-MissionResult $real
    if ($rr.Found -and -not (Test-InfraFailure $rr.Text)) { Fail 'L infra_failure_is_not_mission_failure' 'the committed M12 result file is not recognised as an infrastructure failure'; return }
  }

  Pass 'L infra_failure_is_not_mission_failure'
}

$wanted = if ($Test -eq 'ALL') { 'A','B','C','D','E','F','G','H','I','J','K','L' } else { @($Test) }
foreach ($t in $wanted) {
  switch ($t) {
    'A' { Test-A }
    'B' { Test-B }
    'C' { Test-C }
    'D' { Test-D }
    'E' { Test-E }
    'F' { Test-F }
    'G' { Test-G }
    'H' { Test-H }
    'I' { Test-I }
    'J' { Test-J }
    'K' { Test-K }
    'L' { Test-L }
    default { Fail "TEST_$t" 'unknown test id' }
  }
}

$failed = @($results | ?{ $_ -like 'RESULT: FAIL *' })
Write-Host ("TOTAL: {0} passed, {1} failed" -f (($results.Count) - ($failed.Count)), $failed.Count)
if ($failed.Count -gt 0) { exit 1 }
