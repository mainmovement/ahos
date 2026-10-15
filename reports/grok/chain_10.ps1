$g='G:\robat\ahos\reports\grok'
function WaitDone($n){ $t=0; while (-not (Select-String -Path "$g\_claude_${n}_runlog.txt" -Pattern '^DONE' -Quiet -ErrorAction SilentlyContinue) -and $t -lt 28800) { Start-Sleep 30; $t+=30 }; Start-Sleep 30 }
WaitDone 9
foreach ($n in @('9_5','9_6','10')) { powershell -ExecutionPolicy Bypass -File "$g\run_mission.ps1" -n $n }
"CHAIN DONE (9_5,9_6,10) $(Get-Date)" | Out-File -Encoding utf8 "$g\_chain.log"
