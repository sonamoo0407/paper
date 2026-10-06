@echo off
setlocal
cd /d "%~dp0"
title 경기대 도서관 논문 수집기

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo [설치 필요] 먼저 PowerShell에서 아래를 한 번 실행하세요.
  echo py -m venv .venv
  echo .\.venv\Scripts\Activate.ps1
  echo pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

set /p QUERY=검색 키워드 입력 ^(예: ransomware detection^): 
if "%QUERY%"=="" (
  echo 검색 키워드가 비어 있어 종료합니다.
  pause
  exit /b 1
)

echo.
echo Chrome이 열리면 ID와 비밀번호를 이 창에서 입력합니다.
echo 검색 결과 목록 화면까지 간 뒤 이 창에서 Enter를 누르세요.
echo.
".venv\Scripts\python.exe" kyonggi_collector.py collect --mode browser --auto-login --query "%QUERY%" --max-records 100 --max-pages 10

echo.
echo 종료 코드: %ERRORLEVEL%
pause
