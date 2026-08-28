@echo off
REM AHOS -- pull Windows ops unlock files from PR #45 tip (working tree only)
REM Falls back to PR #43 branch if #45 ref missing.
REM STATE B: does NOT db:migrate / db:push
REM Does NOT invent PRE_SOAK / OPERATOR_READY
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS pull ops unlock (PR #45 -^> working tree)
echo   STATE B: no migrate / no READY claim
echo ==========================================================

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

set "UNLOCK_REF=origin/cursor/windows-g2-empty-gateway-default-4bde"
set "FALLBACK_REF=origin/cursor/windows-reconcile-ops-artifacts-4bde"

echo ==^> git fetch origin main + unlock branches
git fetch origin main cursor/windows-g2-empty-gateway-default-4bde cursor/windows-reconcile-ops-artifacts-4bde
if errorlevel 1 (
  echo WARNING: fetch failed - check network / remotes
)

git rev-parse --verify "%UNLOCK_REF%" >nul 2>&1
if errorlevel 1 (
  set "UNLOCK_REF=%FALLBACK_REF%"
  git rev-parse --verify "%UNLOCK_REF%" >nul 2>&1
  if errorlevel 1 (
    echo ERROR: missing unlock refs after fetch
    echo Merge PR #45 on GitHub, or: git pull origin main
    pause
    exit /b 2
  )
  echo WARNING: using fallback %UNLOCK_REF%
)

echo ==^> checkout unlock ops files onto working tree ^(not a merge^)
git checkout "%UNLOCK_REF%" -- AHOS_WINDOWS_OPS.bat AHOS_PRE_SOAK_NOW.bat AHOS_PULL_OPS_UNLOCK.bat WINDOWS_RUN_THIS_FIRST.txt .env.example .gitignore "scripts/windows_*.ps1" scripts/operator_validation_gate.py tests/validate_n8n.py
if errorlevel 1 (
  echo ERROR: git checkout unlock files failed
  pause
  exit /b 2
)

echo.
echo OK -- unlock files are in the working tree ^(from %UNLOCK_REF%^).
echo NEXT:
echo   1^) Start Docker Desktop, wait GREEN, confirm: docker ps
echo   2^) Double-click AHOS_PRE_SOAK_NOW.bat  ^(preferred^)
echo      or AHOS_WINDOWS_OPS.bat
echo   3^) Paste reports\OWNER_PASTE_WINDOWS_GATE.txt into Cursor
echo.
echo PRE_SOAK only if paste shows pre_soak_entry_ok=true. Never invent READY.
echo STATE B: never db:migrate / db:push
echo.
pause
endlocal
exit /b 0
