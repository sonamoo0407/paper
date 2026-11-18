@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "RECORDS=%~1"
if not defined RECORDS set /p "RECORDS=Path to records.jsonl: "
set "RECORDS=%RECORDS:"=%"
if not defined RECORDS exit /b 1
for %%I in ("%RECORDS%") do set "RUN_FOLDER=%%~dpI"
set "LIMIT="
set /p "LIMIT=How many records should be processed? [100]: "
if "%LIMIT%"=="" set "LIMIT=100"

echo(%LIMIT%| findstr /r "^[1-9][0-9]*$" >nul
if errorlevel 1 (
  echo Please enter a positive whole number.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo INSTALLATION REQUIRED. Run run_collector.bat first.
  pause
  exit /b 1
)

if not exist "%RECORDS%" (
  echo Records file not found: "%RECORDS%"
  pause
  exit /b 1
)

echo Chrome will open. Log in to Kyonggi Library or libproxy, then return here and press Enter.
".venv\Scripts\python.exe" ".\kyonggi_collector.py" auto-downloads ^
  --records "%RECORDS%" ^
  --output-dir "%RUN_FOLDER%institution-auto-downloads" ^
  --max-records %LIMIT% ^
  --priority top-tier

echo.
echo Finished. See "%RUN_FOLDER%institution-auto-downloads"
pause
