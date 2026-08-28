@echo off
REM AHOS -- pull Windows ops unlock files onto working tree (not a merge)
REM Prefers evidence-lease tip (#46), then #45 tip, then reconcile tip.
REM STATE B: does NOT db:migrate / db:push
REM Does NOT invent PRE_SOAK / OPERATOR_READY
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS pull ops unlock (working tree only)
echo   STATE B: no migrate / no READY claim
echo ==========================================================

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

echo ==^> git fetch origin main + unlock branches
git fetch origin main cursor/windows-presoak-followup-4bde cursor/windows-chat-500-rootcause-4bde cursor/windows-g2-evidence-autopush-4bde cursor/windows-evidence-push-lease-4bde cursor/windows-g2-empty-gateway-default-4bde cursor/windows-reconcile-ops-artifacts-4bde
if errorlevel 1 (
  echo WARNING: fetch failed - check network / remotes
)

set "UNLOCK_REF="
for %%R in (
  origin/cursor/windows-dburl-probe-first-4bde
  origin/cursor/windows-presoak-followup-4bde
  origin/cursor/windows-evidence-push-lease-4bde
  origin/cursor/windows-chat-500-rootcause-4bde
  origin/cursor/windows-g2-evidence-autopush-4bde
  origin/cursor/windows-g2-empty-gateway-default-4bde
  origin/cursor/windows-reconcile-ops-artifacts-4bde
) do (
  if not defined UNLOCK_REF (
    git rev-parse --verify %%R >nul 2>&1
    if not errorlevel 1 (
      git merge-base --is-ancestor %%R origin/main >nul 2>&1
      if errorlevel 1 set "UNLOCK_REF=%%R"
    )
  )
)

if not defined UNLOCK_REF (
  echo OK -- unlock tips already contained in origin/main
  echo NEXT: AHOS_VALIDATE_G2_NOW.bat then AHOS_PRE_SOAK_NOW.bat
  pause
  exit /b 0
)

echo ==^> checkout unlock ops files from !UNLOCK_REF! ^(not a merge^)
git checkout "!UNLOCK_REF!" -- AHOS_WINDOWS_OPS.bat AHOS_PRE_SOAK_NOW.bat AHOS_VALIDATE_G2_NOW.bat AHOS_PULL_OPS_UNLOCK.bat WINDOWS_RUN_THIS_FIRST.txt .env.example .gitignore "scripts/windows_*.ps1" scripts/ahos_pg_probe.mjs scripts/windows_g2_probe.py scripts/operator_validation_gate.py app/api/chat/route.ts db/index.ts snapshot.ts tests/validate_n8n.py deployment/docker-compose.windows.yml
if errorlevel 1 (
  echo ERROR: git checkout unlock files failed
  pause
  exit /b 2
)

echo.
echo OK -- unlock files are in the working tree ^(from !UNLOCK_REF!^).
echo NEXT:
echo   1^) Docker Desktop GREEN + docker ps
echo   2^) Double-click AHOS_VALIDATE_G2_NOW.bat  ^(health + G2^)
echo   3^) If G2 PASS: AHOS_PRE_SOAK_NOW.bat  ^(full G1-G10^)
echo   4^) Paste OWNER_PASTE into Cursor
echo.
echo PRE_SOAK only if paste shows pre_soak_entry_ok=true. Never invent READY.
echo STATE B: never db:migrate / db:push
pause
exit /b 0
