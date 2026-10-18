# M39 monthly fault report (owner schedule)

Paper-only. Does not inject live faults or clear HOLD.

## Run once manually
```
.venv\Scripts\python.exe scripts\m39_monthly_fault_report.py
```
Output: `reports/grok/M39/monthly_fault_suite.json`

## Optional Windows Task Scheduler (owner)
Create a monthly task pointing at the script above. Do not bind to the live soak PID.
Logon trigger is acceptable; reboot proof is separate from this report.
