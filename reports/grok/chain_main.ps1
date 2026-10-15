$g='G:\robat\ahos\reports\grok'
powershell -ExecutionPolicy Bypass -File "$g\run_mission.ps1" -n 9_6 -continueFresh
foreach ($n in @('10','11')) { powershell -ExecutionPolicy Bypass -File "$g\run_mission.ps1" -n $n }
"CHAIN DONE (9_6,10,11) $(Get-Date)" | Out-File -Append -Encoding utf8 "$g\_chain.log"
