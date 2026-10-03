# AHOS Claude watchdog: restarts a stalled headless Claude mission. Never touches PID 4708 or interactive claude.
$proj='C:\Users\Sniper\.claude\projects\G--robat-ahos'; $g='G:\robat\ahos\reports\grok'; $log="$g\_watchdog_log.txt"; $stallMin=20
function L($m){ "$(Get-Date -f s) $m" | Out-File -Append -Encoding utf8 $log }
if(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ?{ $_.CommandLine -match 'claude_watchdog\.ps1' -and $_.ProcessId -ne $PID }){ exit } # single-instance
L "watchdog start pid=$PID"
while($true){
  try{
    $runners=Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ?{ $_.CommandLine -match 'run_mission\.ps1' -and $_.ProcessId -ne $PID }
    foreach($r in $runners){
      $n=[regex]::Match($r.CommandLine,'-n\s+(\S+)').Groups[1].Value
      $kids=Get-CimInstance Win32_Process -Filter "ParentProcessId=$($r.ProcessId)"
      $cl=@(); foreach($k in $kids){ if($k.Name -eq 'claude.exe'){$cl+=$k}; $cl+=Get-CimInstance Win32_Process -Filter "ParentProcessId=$($k.ProcessId) AND Name='claude.exe'" }
      $cl=$cl | ?{ $_.ProcessId -ne 4708 -and $_.CommandLine -match ' -p ' }
      if(-not $cl){ continue }
      $last=(Get-ChildItem $proj -Filter *.jsonl | Sort LastWriteTime -Desc | Select -First 1).LastWriteTime
      $idle=((Get-Date)-$last).TotalMinutes
      if($idle -gt $stallMin){
        L "STALL mission=$n idle=$([int]$idle)m -> kill claude $($cl.ProcessId -join ',')"
        New-Item "$g\_watchdog_kill_$n.flag" -ItemType File -Force | Out-Null
        foreach($c in $cl){ Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep 90
        if($n -notlike 'ap_*' -and -not (Get-Process -Id $r.ProcessId -ErrorAction SilentlyContinue)){  # autopilot missions are retried by claude_autopilot.ps1 itself
          L "runner exited -> relaunch mission $n continueFresh"
          Start-Process powershell.exe -WindowStyle Hidden -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$g\run_mission.ps1`" -n $n -continueFresh"
        }
      }
    }
  } catch { L "err $_" }
  Start-Sleep 60
}