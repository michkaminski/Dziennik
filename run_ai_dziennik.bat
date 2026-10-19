@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "ROOT=%CD%"
set "VENV=%ROOT%\.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"
set "REQ=%ROOT%\requirements.txt"
set "MARKER=%VENV%\.requirements.sha256"
set "ICO=%ROOT%\assets\ai_dziennik.ico"
set "LNK=%ROOT%\SPORTOMATYKA AI Dziennik.lnk"

title SPORTOMATYKA AI Dziennik

where python >nul 2>&1
if errorlevel 1 (
  echo [BLAD] Brak Python w PATH.
  pause
  exit /b 1
)

if not exist "%PY%" (
  echo [1/3] Tworzenie .venv ...
  python -m venv "%VENV%"
  if errorlevel 1 ( pause & exit /b 1 )
)

"%PY%" -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path(r'%REQ%').read_bytes()).hexdigest())" > "%TEMP%\ai_dziennik_req.hash"
set /p REQ_HASH=<"%TEMP%\ai_dziennik_req.hash"
del "%TEMP%\ai_dziennik_req.hash" >nul 2>&1

set "NEED_INSTALL=1"
if exist "%MARKER%" (
  set /p OLD_HASH=<"%MARKER%"
  if /I "%OLD_HASH%"=="%REQ_HASH%" set "NEED_INSTALL=0"
)

if "%NEED_INSTALL%"=="1" (
  echo [2/3] Instalacja requirements ...
  "%PY%" -m pip install --upgrade pip
  "%PIP%" install -r "%REQ%"
  if errorlevel 1 ( pause & exit /b 1 )
  >"%MARKER%" echo %REQ_HASH%
) else (
  echo [2/3] Zaleznosci aktualne.
)

if exist "%ICO%" if exist "%ROOT%\scripts\create_shortcut.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\create_shortcut.ps1" -TargetBat "%ROOT%\run_ai_dziennik.bat" -ShortcutPath "%LNK%" -IconPath "%ICO%" -WorkingDirectory "%ROOT%" >nul 2>&1
)

echo [3/3] Start ...
"%PY%" "%ROOT%\run.py"
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" pause
exit /b %EC%
