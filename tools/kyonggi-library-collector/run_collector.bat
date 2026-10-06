@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Kyonggi Library Collector

if not exist ".venv\Scripts\python.exe" goto :missing_venv

set /p "QUERY=Research keyword (example: ransomware detection): "
if "%QUERY%"=="" goto :missing_query

echo.
echo The program will query Kyonggi Library EDS metadata directly.
echo No browser, login, password, cookie, PDF, or download is used in this mode.
echo.
".venv\Scripts\python.exe" "kyonggi_collector.py" collect --mode direct --query "%QUERY%" --max-records 100 --max-pages 10
echo.
echo Program exit code: %ERRORLEVEL%
pause
exit /b %ERRORLEVEL%

:missing_venv
echo.
echo INSTALLATION REQUIRED. Run these commands once in PowerShell:
echo py -m venv .venv
echo .\.venv\Scripts\Activate.ps1
echo pip install -r requirements.txt
echo.
pause
exit /b 1

:missing_query
echo.
echo No keyword entered.
pause
exit /b 1
