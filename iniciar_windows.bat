@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Execute instalar_windows.bat primeiro.
    pause
    exit /b 1
)
echo Abra http://127.0.0.1:8501 no navegador. Para encerrar, use Ctrl+C.
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 pause
