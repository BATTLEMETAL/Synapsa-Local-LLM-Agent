@echo off
REM Synapsa Professional Launcher
title Synapsa Professional Server

echo ========================================================
echo   Synapsa Professional - AI Engineering Platform
echo ========================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 goto NoPython

REM 2. Check Venv
if not exist "venv" goto CreateVenv
goto VenvExists

:CreateVenv
echo [INFO] Creating virtual environment (First Run)...
python -m venv venv
echo [INFO] Virtual environment created.
goto ActivateVenv

:VenvExists
goto ActivateVenv

:ActivateVenv
call venv\Scripts\activate
if %errorlevel% neq 0 goto VenvError

REM 3. Check Dependencies
if exist "venv\Lib\site-packages\fastapi" goto Launch

echo [INFO] Installing dependencies - this may take a while...
pip install -r requirements.txt

echo [INFO] Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:Launch
echo.
echo [INFO] Launching Synapsa Server...
echo [INFO] Access the Dashboard at: http://localhost:8000
echo.

REM Start Browser (wait 5s)
timeout /t 5
start http://localhost:8000

REM Run Server
python main.py
goto End

:NoPython
echo [ERROR] Python not found! Please install Python 3.10+ and add to PATH.
pause
goto End

:VenvError
echo [ERROR] Failed to activate venv.
pause
goto End

:End
pause
