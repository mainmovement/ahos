
# Ensure local LLM bridge is up (Node cannot reach OpenRouter/Groq directly from this network).
$bridge = Join-Path $PSScriptRoot 'ahos_llm_bridge.ps1'
$bridgeUp = $false
try { $h = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8787/health' -TimeoutSec 2; if ($h.StatusCode -eq 200) { $bridgeUp = $true } } catch {}
if (-not $bridgeUp -and (Test-Path $bridge)) { Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',$bridge -WindowStyle Hidden; Start-Sleep 2 }
# claude_keepalive.ps1 - local, token-free keepalive. Every 3 min: if NO claude.exe is running, start claude_fresh.ps1.
# Ensures exactly one Claude (never starts a second). Portable: paths from script location.
$here = $PSScriptRoot; $root = Split-Path (Split-Path $here -Parent) -Parent
$log = Join-Path $here '_keepalive_log.txt'
$mutex = New-Object System.Threading.Mutex($false, 'Global\AHOS_Claude_Keepalive')
if (-not $mutex.WaitOne(0)) { exit }   # only one keepalive instance
while ($true) {
  Start-Sleep -Seconds 180
  if (-not (Get-Process claude -ErrorAction SilentlyContinue)) {
    Start-Sleep -Seconds 60
    if (-not (Get-Process claude -ErrorAction SilentlyContinue)) {
      "$(Get-Date -Format s) no claude running -> starting claude_fresh.ps1" | Out-File -Append -Encoding utf8 $log
      Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $here 'claude_fresh.ps1')
      Start-Sleep -Seconds 120
    }
  }
}

