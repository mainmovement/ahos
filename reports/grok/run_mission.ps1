param([string]$n, [int]$maxAttempts = 14, [switch]$continueFresh)
Set-Location G:\robat\ahos
# Use the CURRENT Claude account (User env, same as interactive Claude), not env inherited from a long-lived runner.
foreach ($v in 'ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY','ANTHROPIC_MODEL') { $x = [Environment]::GetEnvironmentVariable($v,'User'); if ($x) { Set-Item env:$v $x } elseif (Test-Path env:$v) { Remove-Item env:$v } }
$env:PYTHONIOENCODING='utf-8'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)  # pipe the prompt to claude as UTF-8 (Persian names), PS5 default is ASCII
$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS='1800000'
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS='110000'
$env:API_TIMEOUT_MS='900000'
$proj = 'C:\Users\Sniper\.claude\projects\G--robat-ahos'
$out = "reports\grok\_claude_${n}_result.txt"
$log = "reports\grok\_claude_${n}_runlog.txt"
$tools = "Bash Read Edit Write Glob Grep"
$task = Get-Content "reports\grok\_claude_task_$n.txt" -Raw -Encoding UTF8
$contNote = "`n`nCONTINUATION: an earlier Claude session already worked on this exact mission and was cut off by API errors. FIRST inspect git log -15, git status and git diff (uncommitted edits are that session's unfinished work) and the latest handoff/guide sections. Do NOT redo committed work; finish or repair the uncommitted work, run targeted tests, commit, then complete whatever remains of the mission."
$resumeMsg = "Continue the same mission exactly where you stopped. If your last turn ended while you were waiting on a background task, that task was killed when the process exited -- claude -p is one-shot, so ending a turn exits the process and its completion notification never arrives. Re-run any suite you still need and POLL it inside this same turn (short sleeps reading its output file) until it finishes; never end your turn while a background task is still running. Check git status/log first, do not redo finished work, keep committing incrementally, and finish with the required FINAL OUTPUT (<=15 short lines)."
$backoff = @(0, 120, 300, 600, 600, 900)
function NewestSession($since) { (Get-ChildItem $proj -Filter *.jsonl | Where-Object { $_.LastWriteTime -ge $since } | Sort-Object LastWriteTime -Descending | Select-Object -First 1).BaseName }
function IsFail($t) { return ($t -match 'API Error|Background tasks still running|408 status|overloaded|ECONNRESET|socket hang|issue with the selected model|Reached max turns') }
"START $(Get-Date) continueFresh=$continueFresh" | Out-File -Append -Encoding utf8 $log
$mode = 'fresh'; $sess = $null; $fastFails = 0; $failCount = 0
for ($a = 0; $a -lt $maxAttempts; $a++) {
  $t0 = Get-Date
  if ($mode -eq 'fresh') {
    $prompt = $task; if ($a -gt 0 -or $continueFresh) { $prompt = $task + $contNote }
    $prompt | claude -p --permission-mode acceptEdits --allowedTools $tools --max-turns 300 --output-format text *> $out
    $sess = NewestSession $t0
  } else {
    $resumeMsg | claude -p --resume $sess --permission-mode acceptEdits --allowedTools $tools --max-turns 300 --output-format text *> $out
  }
  $dur = ((Get-Date) - $t0).TotalSeconds
  $txt = Get-Content $out -Raw -Encoding UTF8
  "attempt$a mode=$mode session=$sess dur=$([int]$dur)s end=$(Get-Date)" | Out-File -Append -Encoding utf8 $log
  $wf = "reports\grok\_claude_watchdog_kill_$n.flag"; $wf = "reports\grok\_watchdog_kill_$n.flag"; $wd = Test-Path $wf; if ($wd) { Remove-Item $wf -Force; "watchdog-kill -> resume" | Out-File -Append -Encoding utf8 $log }
  # A result without an AUTOPILOT_RESULT line is not a delivered verdict -- it is a turn
  # that ended mid-work (the M11.3 shape: the mission went idle waiting on a background
  # suite and claude -p exited at end of turn, killing it). Accepting it here would let a
  # truncated result reach the runner and be classified MALFORMED, charging an attempt
  # against output the mission never finished. Same predicate as the runner's
  # Classify-MissionResult, so both scripts agree on what a verdict looks like.
  $hasVerdict = ($txt -match 'AUTOPILOT_RESULT:\s*(DONE|PARTIAL|BLOCKED_OWNER)')
  if (-not $hasVerdict) { "no AUTOPILOT_RESULT in output -> resume" | Out-File -Append -Encoding utf8 $log }
  if (-not $wd -and $hasVerdict -and -not (IsFail $txt)) { break }
  if ($txt -match 'usage limit|quota exceeded|credit balance|invalid api key|authentication_error') { "STOP: limit/auth" | Out-File -Append -Encoding utf8 $log; break }
  $failCount++
  Copy-Item $out "reports\grok\_claude_${n}_result_fail$failCount.txt" -Force
  if ($dur -lt 180) { $fastFails++ } else { $fastFails = 0 }
  if ($fastFails -ge 2 -and $fastFails -lt 4) { $mode = 'fresh' } elseif ($fastFails -ge 4) { $mode = 'fresh'; Start-Sleep $backoff[[Math]::Min($fastFails-3, $backoff.Count-1)] } else { $mode = 'resume' }
  if ($mode -eq 'resume' -and -not $sess) { $mode = 'fresh' }
  Start-Sleep 20
}
"DONE attempts=$($a+1) END=$(Get-Date)" | Out-File -Append -Encoding utf8 $log
