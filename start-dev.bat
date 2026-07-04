@echo off
setlocal
REM ====================================================================
REM  VulnForge dev launcher
REM  - Ensures deps, frees ports, then starts BOTH dev servers:
REM      API : FastAPI  http://localhost:8081  (uvicorn --reload)
REM      web : Next.js   http://localhost:8082  (next dev)
REM  - Prefers Windows Terminal -> ONE window with TWO tabs.
REM  - Falls back to two PowerShell windows if Windows Terminal is absent.
REM  Just double-click this file, or run it from any terminal.
REM ====================================================================

REM Repo root = this script's folder (strip trailing backslash).
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

REM Prefer PowerShell 7 (pwsh); fall back to Windows PowerShell 5.1.
set "PSEXE=powershell"
where pwsh >nul 2>nul && set "PSEXE=pwsh"

echo [VulnForge] root : %ROOT%
echo [VulnForge] shell: %PSEXE%

REM   Origins (localhost + any local hostname) are configured in api\.env and
REM   web\.env.local, which the servers read on every start. To add a hostname,
REM   edit those files and add the matching line to the Windows hosts file.

REM --- Free ports 8082/8081 (stop any stale dev servers) --------------
echo [VulnForge] freeing ports 8082/8081 if in use...
%PSEXE% -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8082,8081 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

REM --- Ensure Python deps for the API (no-op if already installed) ----
python -c "import uvicorn, fastapi" 1>nul 2>nul
if errorlevel 1 (
  echo [VulnForge] installing Python dependencies...
  python -m pip install -r "%ROOT%\api\requirements.txt" -r "%ROOT%\requirements-dev.txt"
)

REM --- Ensure web deps (first run only) -------------------------------
if not exist "%ROOT%\web\node_modules" (
  echo [VulnForge] installing web dependencies ^(first run^)...
  pushd "%ROOT%\web"
  call npm install
  popd
)

set "API_CMD=python -m uvicorn api.main:app --port 8081 --reload"
set "WEB_CMD=npm run dev"

REM --- Launch ---------------------------------------------------------
where wt >nul 2>nul
if %errorlevel%==0 (
  echo [VulnForge] launching Windows Terminal: one window, two tabs...
  wt new-tab --title "VulnForge API" -d "%ROOT%" %PSEXE% -NoExit -Command "%API_CMD%" ; new-tab --title "VulnForge Web" -d "%ROOT%\web" %PSEXE% -NoExit -Command "%WEB_CMD%"
) else (
  echo [VulnForge] Windows Terminal not found; opening two PowerShell windows...
  start "VulnForge API" %PSEXE% -NoExit -Command "Set-Location '%ROOT%'; %API_CMD%"
  start "VulnForge Web" %PSEXE% -NoExit -Command "Set-Location '%ROOT%\web'; %WEB_CMD%"
)

echo.
echo [VulnForge] API : http://localhost:8081/docs
echo [VulnForge] web : http://localhost:8082 (or your local hostname)
endlocal
