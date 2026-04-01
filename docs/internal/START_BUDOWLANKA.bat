@echo off
title Synapsa Budowlanka v5 — Professional Launcher
color 0A
echo.
echo ============================================================
echo    SYNAPSA BUDOWLANKA EDITION v5
echo    Profesjonalne AI dla branzy budowlanej
echo ============================================================
echo.

REM --- Wykrywanie Python (3.10, 3.11, 3.12, 3.13) ---
set PYTHON_CMD=
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :check_python_ver
)
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3
    goto :check_python_ver
)
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :check_python_ver
)
goto :NoPython

:check_python_ver
for /f "tokens=2" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do set PY_VER=%%v
echo [INFO] Znaleziono Python %PY_VER%

REM --- Wirtualne środowisko ---
if not exist "venv" goto :CreateVenv
goto :ActivateVenv

:CreateVenv
echo [INFO] Tworzenie wirtualnego srodowiska (pierwszy raz)...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 goto :VenvError
echo [OK] Srodowisko stworzone.

:ActivateVenv
call venv\Scripts\activate
if %errorlevel% neq 0 goto :VenvError

REM --- Sprawdzenie podstawowych zależności ---
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 goto :RunSetup

REM --- Sprawdzenie czy konfiguracja jest aktualna ---
if not exist "synapsa_config.json" goto :RunSetup
goto :Launch

:RunSetup
echo.
echo [INFO] Instalowanie zaleznosci i konfiguracja (pierwsze uruchomienie)...
echo [INFO] To moze zajac kilka minut...
echo.
python synapsa\install_helper.py
if %errorlevel% neq 0 (
    echo [WARN] Setup zakonczyl sie z ostrzezeniami. Kontynuuje...
)

:Launch
echo.
echo ============================================================
echo [OK] Uruchamiam Synapsa Budowlanka...
echo [OK] Otworz przegladarke na: http://localhost:8501
echo ============================================================
echo.

REM Otwieramy przeglądarkę po 4 sekundach
start /b cmd /c "timeout /t 4 >nul && start http://localhost:8501"

REM Uruchamiamy aplikację Streamlit
python -m streamlit run app_budowlanka.py --server.headless false --server.port 8501 --theme.base dark --theme.primaryColor "#FF9800" --theme.backgroundColor "#0E1117" --theme.secondaryBackgroundColor "#1A1A2E"
goto :End

:NoPython
echo.
echo [BLAD] Python nie znaleziony!
echo Zainstaluj Python 3.10+ ze strony: https://python.org/downloads/
echo Pamietaj o zaznaczeniu: "Add Python to PATH"
echo.
pause
goto :End

:VenvError
echo [BLAD] Nie mozna uruchomic srodowiska wirtualnego.
echo Sprobuj usunac folder 'venv' i uruchomic ponownie.
pause
goto :End

:End
pause
