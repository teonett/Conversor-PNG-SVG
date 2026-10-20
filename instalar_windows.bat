@echo off
setlocal
cd /d "%~dp0"
py -3.11 --version >nul 2>&1
if errorlevel 1 goto python312
py -3.11 -m venv .venv
goto dependencies
:python312
py -3.12 --version >nul 2>&1
if errorlevel 1 goto missing
py -3.12 -m venv .venv
:dependencies
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Instalacao concluida. Execute iniciar_windows.bat.
pause
exit /b 0
:missing
echo Instale o Python 3.11 ou 3.12 com o Python Launcher e o suporte Tcl/Tk.
pause
exit /b 1
:failed
echo A instalacao falhou. Confira a mensagem acima.
pause
exit /b 1
