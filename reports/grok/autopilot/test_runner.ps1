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
#   noresult -> exit without writing anything
$stub = Join-Path $env:TEMP ('ahos_stub_' + [IO.Path]::GetRandomFileName().Replace('.','') + '.ps1')
Set-Content -LiteralPath $stub -Encoding UTF8 @'
param([string]$n, [switch]$continueFresh)
$out = Join-Path $env:AHOS_RUNNER_TEST_ROOT ("_claude_${n}_result.txt")
Start-Sleep -Seconds 1
$mode = $env:STUB_MODE; if (-not $mode) { $mode = 'default' }
switch ($mode) {
  'noresult' { }
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
  foreach ($f in @('active.json','heartbeat.json','state.json','startup_reconciliation.json')) {
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

$wanted = if ($Test -eq 'ALL') { 'A','B','C','D','E','F','G','H','I' } else { @($Test) }
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
    default { Fail "TEST_$t" 'unknown test id' }
  }
}

$failed = @($results | ?{ $_ -like 'RESULT: FAIL *' })
Write-Host ("TOTAL: {0} passed, {1} failed" -f (($results.Count) - ($failed.Count)), $failed.Count)
if ($failed.Count -gt 0) { exit 1 }
