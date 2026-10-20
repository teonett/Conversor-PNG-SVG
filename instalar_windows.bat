@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 goto :no_python
py -3.11 -c "import sys; print(sys.version)"
if errorlevel 1 goto :no_python
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
if errorlevel 1 goto :fail
set "APP_PYTHON=.venv\Scripts\python.exe"
"%APP_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :fail
rem CPU is the default: it works without an NVIDIA GPU.
"%APP_PYTHON%" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto :fail
if /I "%~1"=="github" (
    where git >nul 2>&1
    if errorlevel 1 goto :no_git
    "%APP_PYTHON%" -m pip install -r requirements-github.txt
) else (
    "%APP_PYTHON%" -m pip install -r requirements.txt
)
if errorlevel 1 goto :fail
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ATENCAO: FFmpeg ausente. Instale conforme README e reabra o terminal.
) else (
    echo FFmpeg encontrado.
)
echo Instalacao concluida. Execute iniciar_windows.bat
pause
exit /b 0
:no_python
echo Instale Python 3.11 x64 com o Python Launcher. Consulte o README.
goto :fail
:no_git
echo Instale Git for Windows ou execute instalar_windows.bat sem argumentos.
:fail
echo Nao foi possivel concluir. Consulte a mensagem acima e o README.
pause
exit /b 1
