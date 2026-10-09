param([string]$n, [int]$maxAttempts = 14, [switch]$continueFresh)
Set-Location G:\robat\ahos
# Use the CURRENT Claude account (User env, same as interactive Claude), not env inherited from a long-lived runner.
foreach ($v in 'ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY','ANTHROPIC_MODEL') { $x = [Environment]::GetEnvironmentVariable($v,'User'); if ($x) { Set-Item env:$v $x } elseif (Test-Path env:$v) { Remove-Item env:$v } }
$env:PYTHONIOENCODING='utf-8'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)  # pipe the prompt to claude as UTF-8 (Persian names), PS5 default is ASCII
$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS='1800000'
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS='110000'
$env:API_TIMEOUT_MS='900000'
# The model the headless runs use is DERIVED, never named here: this script
# resolves it from the exact same source the interactive Claude session on this
# machine uses (User-scoped ANTHROPIC_MODEL, or the `model` field of the User
# settings.json), and passes it to `claude -p` as an explicit --model argument.
# The Atria gateway serves a single model id which the local Claude Code
# catalog does not describe, so the CLI prints an `unrecognized_model` notice
# to stderr on every run -- a notice, not a refusal; the reply still arrives on
# stdout. Hard-coding the name anywhere in this repo led two separate
# investigations to mistake that notice for the failure, so the literal is gone
# and the resolution is fail-loud instead: if the model cannot be derived, the
# script aborts rather than letting claude -p silently fall back to a catalog
# default the gateway does not serve.
$env:CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT='1'
$model = [Environment]::GetEnvironmentVariable('ANTHROPIC_MODEL','User')
if (-not $model) {
  $s = "$env:USERPROFILE\.claude\settings.json"
  if (Test-Path $s) { try { $j = Get-Content $s -Raw -Encoding UTF8 | ConvertFrom-Json; $model = $j.model } catch { } }
}
if (-not $model) { throw "run_mission.ps1: cannot derive the model -- set the User-scoped ANTHROPIC_MODEL to the model id the interactive Claude session uses." }
"model=$model" | Out-File -Append -Encoding utf8 $log
$proj = 'C:\Users\Sniper\.claude\projects\G--robat-ahos'
$out = "reports\grok\_claude_${n}_result.txt"
$log = "reports\grok\_claude_${n}_runlog.txt"
$errFile = "reports\grok\_claude_${n}_stderr.txt"
$tools = "Bash Read Edit Write Glob Grep"
$task = Get-Content "reports\grok\_claude_task_$n.txt" -Raw -Encoding UTF8
$contNote = "`n`nCONTINUATION: an earlier Claude session already worked on this exact mission and was cut off by API errors. FIRST inspect git log -15, git status and git diff (uncommitted edits are that session's unfinished work) and the latest handoff/guide sections. Do NOT redo committed work; finish or repair the uncommitted work, run targeted tests, commit, then complete whatever remains of the mission."
$resumeMsg = "Continue the same mission exactly where you stopped. If your last turn ended while you were waiting on a background task, that task was killed when the process exited -- claude -p is one-shot, so ending a turn exits the process and its completion notification never arrives. Re-run any suite you still need and POLL it inside this same turn (short sleeps reading its output file) until it finishes; never end your turn while a background task is still running. Check git status/log first, do not redo finished work, keep committing incrementally, and finish with the required FINAL OUTPUT (<=15 short lines)."
$backoff = @(0, 120, 300, 600, 600, 900)
function NewestSession($since) { (Get-ChildItem $proj -Filter *.jsonl | Where-Object { $_.LastWriteTime -ge $since } | Sort-Object LastWriteTime -Descending | Select-Object -First 1).BaseName }
function IsFail($t) { return ($t -match 'API Error|Background tasks still running|408 status|overloaded|ECONNRESET|socket hang|issue with the selected model|Reached max turns') }
# A platform failure is not a mission failure. The CLI's real quota wording --
# "Token quota exhausted", "Request rejected (429)", "unrecognized_model" -- is what
# killed M10 and M12: the older 'quota exceeded' pattern never matched it, so this
# loop burned every retry against a dead quota and then handed the verdictless
# output to the runner, which escalated a platform outage to an owner gate.
function IsInfraFailure($t) { return ($t -match 'Token quota exhausted|quota exceeded|usage limit|credit balance|Request rejected \(429\)|unrecognized_model|invalid api key|authentication_error|rate[- ]?limited') }
"START $(Get-Date) continueFresh=$continueFresh" | Out-File -Append -Encoding utf8 $log
$mode = 'fresh'; $sess = $null; $fastFails = 0; $failCount = 0
for ($a = 0; $a -lt $maxAttempts; $a++) {
  $t0 = Get-Date
  if ($mode -eq 'fresh') {
    $prompt = $task; if ($a -gt 0 -or $continueFresh) { $prompt = $task + $contNote }
    $prompt | claude -p --model $model --permission-mode acceptEdits --allowedTools $tools --max-turns 300 --output-format text > $out 2> $errFile
    $sess = NewestSession $t0
  } else {
    $resumeMsg | claude -p --model $model --resume $sess --permission-mode acceptEdits --allowedTools $tools --max-turns 300 --output-format text > $out 2> $errFile
  }
  $dur = ((Get-Date) - $t0).TotalSeconds
  $txt = Get-Content $out -Raw -Encoding UTF8
  $err = if (Test-Path $errFile) { (Get-Content $errFile -Raw -Encoding UTF8) } else { '' }
  "attempt$a mode=$mode session=$sess dur=$([int]$dur)s end=$(Get-Date)" | Out-File -Append -Encoding utf8 $log
  $wf = "reports\grok\_claude_watchdog_kill_$n.flag"; $wf = "reports\grok\_watchdog_kill_$n.flag"; $wd = Test-Path $wf; if ($wd) { Remove-Item $wf -Force; "watchdog-kill -> resume" | Out-File -Append -Encoding utf8 $log }
  # A result without an AUTOPILOT_RESULT line is not a delivered verdict -- it is a turn
  # that ended mid-work (the M11.3 shape: the mission went idle waiting on a background
  # suite and claude -p exited at end of turn, killing it). Accepting it here would let a
  # truncated result reach the runner and be classified MALFORMED, charging an attempt
  # against output the mission never finished. Same predicate as the runner's
  # Classify-MissionResult, so both scripts agree on what a verdict looks like.
  $hasVerdict = ($txt -match 'AUTOPILOT_RESULT:\s*(DONE|PARTIAL|BLOCKED_OWNER)')
  if (-not $hasVerdict) {
    # No reply the mission authored: fold stderr into the text so IsFail /
    # IsInfraFailure can still see a real quota/auth/model failure, which prints
    # to stderr and produces no stdout verdict. A run that DID deliver a verdict
    # keeps its stderr in $errFile only -- the recognized-model notice arrives on
    # stderr even on a fully successful run, and folding it in would match
    # 'unrecognized_model' and discard real completed work (the M10/M12 shape).
    if ($err -and $err.Trim()) { $txt = $txt + "`n" + $err }
    "no AUTOPILOT_RESULT in output -> resume" | Out-File -Append -Encoding utf8 $log
  }
  if (-not $wd -and $hasVerdict -and -not (IsFail $txt)) { break }
  if (IsInfraFailure $txt) { "STOP: infra/quota failure -- the mission never ran, no attempt is chargeable" | Out-File -Append -Encoding utf8 $log; break }
  $failCount++
  Copy-Item $out "reports\grok\_claude_${n}_result_fail$failCount.txt" -Force
  if ($dur -lt 180) { $fastFails++ } else { $fastFails = 0 }
  if ($fastFails -ge 2 -and $fastFails -lt 4) { $mode = 'fresh' } elseif ($fastFails -ge 4) { $mode = 'fresh'; Start-Sleep $backoff[[Math]::Min($fastFails-3, $backoff.Count-1)] } else { $mode = 'resume' }
  if ($mode -eq 'resume' -and -not $sess) { $mode = 'fresh' }
  Start-Sleep 20
}
"DONE attempts=$($a+1) END=$(Get-Date)" | Out-File -Append -Encoding utf8 $log
