@echo off
echo Starting MTGA Swapper Web UI...
cd /d "%~dp0"
.venv\Scripts\python.exe run_web.py
pause
