@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "RUN_FOLDER=outputs\20260930T055304Z_ransomware"
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

if not exist "%RUN_FOLDER%\records.jsonl" (
  echo Records file not found: %RUN_FOLDER%\records.jsonl
  pause
  exit /b 1
)

echo Chrome will open. Log in to Kyonggi Library or libproxy, then return here and press Enter.
".venv\Scripts\python.exe" ".\kyonggi_collector.py" auto-downloads ^
  --records "%RUN_FOLDER%\records.jsonl" ^
  --output-dir "%RUN_FOLDER%\institution-auto-downloads" ^
  --max-records %LIMIT% ^
  --priority top-tier

echo.
echo Finished. See %RUN_FOLDER%\institution-auto-downloads
pause
