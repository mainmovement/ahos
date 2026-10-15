$t=0
while (-not (Select-String -Path G:\robat\ahos\reports\grok\_claude_8_runlog.txt -Pattern '^DONE' -Quiet) -and $t -lt 14400) { Start-Sleep 30; $t+=30 }
if ($t -ge 14400) { "TIMEOUT waiting M8" | Out-File G:\robat\ahos\reports\grok\_chain_9.log; exit }
powershell -ExecutionPolicy Bypass -File G:\robat\ahos\reports\grok\run_mission.ps1 -n 9
