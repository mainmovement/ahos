@echo off
REM AHOS -- pull Windows ops unlock files from PR #43 branch (working tree only)
REM STATE B: does NOT db:migrate / db:push
REM Does NOT invent PRE_SOAK / OPERATOR_READY
REM Does NOT merge or change branch -- only refreshes ops scripts from unlock tip
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS pull ops unlock (PR #43 branch -^> working tree)
echo   STATE B: no migrate / no READY claim
echo ==========================================================

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

set "UNLOCK_REF=origin/cursor/windows-reconcile-ops-artifacts-4bde"

echo ==^> git fetch origin main + unlock branch
git fetch origin main cursor/windows-reconcile-ops-artifacts-4bde
if errorlevel 1 (
  echo WARNING: fetch failed - check network / remotes
)

git rev-parse --verify "%UNLOCK_REF%" >nul 2>&1
if errorlevel 1 (
  echo ERROR: missing %UNLOCK_REF% after fetch
  echo Try: git fetch origin pull/43/head:refs/remotes/origin/pr-43
  echo Then: set UNLOCK_REF=origin/pr-43 and re-run, or merge PR #43 on GitHub.
  pause
  exit /b 2
)

echo ==^> checkout unlock ops files onto working tree ^(not a merge^)
git checkout "%UNLOCK_REF%" -- AHOS_WINDOWS_OPS.bat AHOS_PULL_OPS_UNLOCK.bat WINDOWS_RUN_THIS_FIRST.txt .env.example .gitignore "scripts/windows_*.ps1" scripts/operator_validation_gate.py tests/validate_n8n.py
if errorlevel 1 (
  echo ERROR: git checkout unlock files failed
  pause
  exit /b 2
)

echo.
echo OK -- unlock files are in the working tree.
echo NEXT:
echo   1^) Start Docker Desktop, wait GREEN, confirm: docker ps
echo   2^) Double-click AHOS_WINDOWS_OPS.bat
echo   3^) Paste reports\OWNER_PASTE_WINDOWS_GATE.txt into Cursor
echo.
echo PRE_SOAK only if paste shows pre_soak_entry_ok=true. Never invent READY.
echo STATE B: never db:migrate / db:push
echo.
pause
endlocal
exit /b 0
