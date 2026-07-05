@echo off
setlocal
REM ====================================================================
REM  VulnForge CHALLENGE launcher - the hard target (no answer-key signal).
REM  Same code as start-dev.bat, but VF_LAB=0 so:
REM    - every vuln fires by DEFAULT (it IS the target), and
REM    - the X-VF-Harden override is IGNORED (a tester cannot flip to the
REM      secure twin), and the /secure/* pages are hidden.
REM  Use start-dev.bat for the LAB face (manual verification + `make verify`).
REM  Verify there is no leak first:  python tools\challenge_check.py
REM ====================================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PSEXE=powershell"
where pwsh >nul 2>nul && set "PSEXE=pwsh"

REM --- The challenge face: vulnerable by default, override OFF -----------
set "VF_HARDENED=0"
set "VF_LAB=0"

echo [VulnForge] CHALLENGE FACE (VF_LAB=0) - vulns live, no answer-key signal
echo [VulnForge] root : %ROOT%

REM   Origins (localhost + any local hostname) are configured in api\.env and
REM   web\.env.local, which the servers read on every start. To add a hostname,
REM   edit those files and add the matching line to the Windows hosts file.

REM --- Free ports 8082/8081 --------------------------------------------
%PSEXE% -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8082,8081 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

REM --- Ensure deps -----------------------------------------------------
python -c "import uvicorn, fastapi" 1>nul 2>nul
if errorlevel 1 python -m pip install -r "%ROOT%\api\requirements.txt"
if not exist "%ROOT%\web\node_modules" ( pushd "%ROOT%\web" & call npm install & popd )

REM --- Build the web once so /secure/* gating runs in production ---------
echo [VulnForge] building web (challenge face)...
pushd "%ROOT%\web" & call npm run build & popd

set "API_CMD=python -m uvicorn api.main:app --port 8081"
set "WEB_CMD=npm run start -- -p 8082"

REM Set the env per-tab with cmd's `&` (NOT PowerShell `;`, which wt would
REM mis-read as a tab separator). cmd /k keeps each window open after launch.
where wt >nul 2>nul
if %errorlevel%==0 (
  wt new-tab --title "VulnForge API [challenge]" -d "%ROOT%" cmd /k "set VF_HARDENED=0&set VF_LAB=0&%API_CMD%" ; new-tab --title "VulnForge Web [challenge]" -d "%ROOT%\web" cmd /k "set VF_LAB=0&%WEB_CMD%"
) else (
  start "VulnForge API [challenge]" /d "%ROOT%" cmd /k "set VF_HARDENED=0&set VF_LAB=0&%API_CMD%"
  start "VulnForge Web [challenge]" /d "%ROOT%\web" cmd /k "set VF_LAB=0&%WEB_CMD%"
)

echo.
echo [VulnForge] CHALLENGE up - open http://localhost:8082 (or your local hostname)
endlocal
