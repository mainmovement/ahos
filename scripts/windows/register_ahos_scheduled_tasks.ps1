# Register AHOS Windows Task Scheduler jobs (G: paths, LIMITED / low priority).
$ErrorActionPreference = "Stop"
$Repo = "G:\robat\ahos"
$Py = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    $Py = "G:\robat\ahos_runtime\python\python.exe"
}
if (-not (Test-Path $Py)) {
    throw "No AHOS python at .venv or ahos_runtime"
}

function Register-AhosTask {
    param(
        [string]$Name,
        [string]$ScriptRel,
        [string]$ScheduleType,
        [string]$StartTime = "",
        [string]$Modifier = "",
        [string]$Days = ""
    )
    $Script = Join-Path $Repo $ScriptRel
    $Tr = "`"$Py`" `"$Script`""
    $sch = Join-Path $env:SystemRoot "System32\schtasks.exe"
    cmd /c "`"$sch`" /Delete /TN `"$Name`" /F >nul 2>&1"
    $args = @("/Create", "/TN", $Name, "/TR", $Tr, "/SC", $ScheduleType, "/RL", "LIMITED", "/F")
    if ($StartTime) { $args += @("/ST", $StartTime) }
    if ($Modifier) { $args += @("/MO", $Modifier) }
    if ($Days) { $args += @("/D", $Days) }
    & $sch @args
    if ($LASTEXITCODE -ne 0) { throw "schtasks create failed for $Name" }
}

Register-AhosTask -Name "AHOS_arxiv_scout_daily" -ScriptRel "scripts\scheduled\run_arxiv_scout_daily.py" -ScheduleType "DAILY" -StartTime "04:00"
Register-AhosTask -Name "AHOS_pipeline_6h" -ScriptRel "scripts\scheduled\run_pipeline_6h.py" -ScheduleType "HOURLY" -Modifier "6"
Register-AhosTask -Name "AHOS_university_exam_sat" -ScriptRel "scripts\scheduled\run_university_exam_sat.py" -ScheduleType "WEEKLY" -Days "SAT" -StartTime "09:00"
Register-AhosTask -Name "AHOS_negahban_daily" -ScriptRel "scripts\scheduled\run_negahban_daily.py" -ScheduleType "DAILY" -StartTime "05:30"

Write-Host "Registered AHOS_* tasks using $Py"
