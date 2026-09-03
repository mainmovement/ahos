# AHOS worktree bootstrap (Windows). Runs inside the NEW worktree.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Write-Host "==> AHOS worktree setup in $(Get-Location)"

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt

if (Test-Path package-lock.json) {
  npm ci
} else {
  npm install
}

New-Item -ItemType Directory -Force -Path .cursor-local\data, .cursor-local\reports | Out-Null
if ((Test-Path .env.example) -and -not (Test-Path .env)) {
  Copy-Item .env.example .env
  Add-Content .env "`nAHOS_PAPER_ONLY=1"
  Add-Content .env ("AHOS_DATA_DIR=" + (Join-Path (Get-Location) ".cursor-local\data"))
}

Write-Host "==> worktree setup complete (no databases initialized, no servers started)"
