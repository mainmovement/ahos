# AHOS Claude autopilot: runs CLAUDE_AUTOPILOT_QUEUE.md missions one by one via run_mission.ps1, independent of Grok.
$g='G:\robat\ahos\reports\grok'; $qf="$g\CLAUDE_AUTOPILOT_QUEUE.md"; $ap="$g\autopilot"; $log="$ap\autopilot_log.txt"; $sf="$ap\state.json"
function L($m){ "$(Get-Date -f s) $m" | Out-File -Append -Encoding utf8 $log }
$me=$PID; if(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ?{ $_.CommandLine -match 'claude_autopilot\.ps1' -and $_.ProcessId -ne $me }){ exit }
L "autopilot start pid=$me"
$state=@{}; if(Test-Path $sf){ (Get-Content $sf -Raw | ConvertFrom-Json).psobject.Properties | %{ $state[$_.Name]=[int]$_.Value } }
function SaveState{ $state | ConvertTo-Json | Out-File -Encoding utf8 $sf }
function SetStatus($id,$st){ $c=[IO.File]::ReadAllText($qf,[Text.Encoding]::UTF8); $e=[regex]::Escape($id); $c=[regex]::Replace($c,"(?m)^\| $e \| [A-Z_]+ \|","| $id | $st |"); [IO.File]::WriteAllText($qf,$c,(New-Object Text.UTF8Encoding $false)); L "$id -> $st" }
while($true){
  try{
    if(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ?{ $_.CommandLine -match 'run_mission\.ps1' }){ Start-Sleep 120; continue }
    $h="$ap\HOLD.flag"; if((Test-Path $h) -and ((Get-Date)-(Get-Item $h).LastWriteTime).TotalHours -lt 6){ Start-Sleep 120; continue }   # Grok review hold, auto-expires after 6h
    $rows=[regex]::Matches([IO.File]::ReadAllText($qf,[Text.Encoding]::UTF8),'(?m)^\| (M[\w.\-]+|BL) \| ([A-Z_]+) \| (.+?) \|\s*$')
    $run=$rows | ?{ $_.Groups[2].Value -eq 'RUNNING' } | Select -First 1
    if($run){ SetStatus $run.Groups[1].Value 'NEEDS_REVIEW'; continue }   # finished outside autopilot (e.g. M11.1): Grok/owner review
    $next=$rows | ?{ $_.Groups[2].Value -in 'PENDING','PARTIAL' } | Select -First 1
    if(-not $next){ L "queue empty - autopilot idle"; Start-Sleep 1800; continue }
    $id=$next.Groups[1].Value; $title=$next.Groups[3].Value; $safe='ap_'+($id -replace '[^\w]','_')
    $p=[IO.File]::ReadAllText("$ap\MISSION_PROMPT_TEMPLATE.txt",[Text.Encoding]::UTF8).Replace('{ID}',$id).Replace('{TITLE}',$title)
    if($id -eq 'M14-M33'){ $p+="`n`nSPECIAL: pick the NEXT unfinished mission in M14..M33 (plan order) and deliver it. If every one of M14..M33 is done or owner-blocked, end with AUTOPILOT_RESULT: DONE NO_REMAINING. Otherwise end with AUTOPILOT_RESULT: PARTIAL <which missions remain>." }
    [IO.File]::WriteAllText("$g\_claude_task_$safe.txt",$p,(New-Object Text.UTF8Encoding $false))
    SetStatus $id 'RUNNING'
    $cf = ''; if($state[$id] -gt 0){ $cf='-continueFresh' }
    $pr=Start-Process powershell.exe -WindowStyle Hidden -PassThru -Wait -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$g\run_mission.ps1`" -n $safe $cf"
    $res=''; if(Test-Path "$g\_claude_${safe}_result.txt"){ $res=[IO.File]::ReadAllText("$g\_claude_${safe}_result.txt",[Text.Encoding]::UTF8) }
    $m=[regex]::Match($res,'AUTOPILOT_RESULT:\s*(DONE|PARTIAL|BLOCKED_OWNER)(.*)')
    if($res -match 'usage limit|quota exceeded|credit balance'){ SetStatus $id 'PARTIAL'; L "limit hit - sleeping 30m"; Start-Sleep 1800; continue }
    if($m.Success -and $m.Groups[1].Value -eq 'DONE' -and ($id -ne 'M14-M33' -or $m.Groups[2].Value -match 'NO_REMAINING')){ SetStatus $id 'DONE'; $state[$id]=0 }
    elseif($m.Success -and $m.Groups[1].Value -eq 'BLOCKED_OWNER'){ SetStatus $id 'BLOCKED_OWNER'; L "$id owner: $($m.Groups[2].Value.Trim())" }
    elseif($id -eq 'M14-M33' -and $m.Success){ SetStatus $id 'PENDING'; $state[$id]=0 }
    else { $state[$id]=[int]$state[$id]+1; if($state[$id] -ge 3){ SetStatus $id 'NEEDS_REVIEW' } else { SetStatus $id 'PARTIAL' } }
    SaveState; Start-Sleep 30
  } catch { L "err $_"; Start-Sleep 300 }
}