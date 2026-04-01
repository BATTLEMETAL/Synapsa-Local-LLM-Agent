@echo off
chcp 65001 >nul
title Synapsa — Pelna Automatyczna Instalacja
color 0A
cls

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║   SYNAPSA — AUDYT FAKTUR                             ║
echo  ║   Automatyczna Instalacja                            ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  Ten program zainstaluje sie automatycznie.
echo  Prosze czekac i nie zamykac tego okna.
echo.
echo ─────────────────────────────────────────────────────────
echo  KROK 1/3: Sprawdzanie czy Python jest zainstalowany...
echo ─────────────────────────────────────────────────────────
echo.

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo  [!] Python nie jest zainstalowany na tym komputerze.
    echo.
    echo  Prosze wykonac ponizsze kroki:
    echo.
    echo  1. Otworzyc strone: https://www.python.org/downloads/
    echo  2. Kliknac zolty przycisk "Download Python"
    echo  3. Uruchomic pobrany plik instalatora
    echo  4. Na PIERWSZYM EKRANIE zaznaczyc pole:
    echo     [x] "Add Python to PATH"
    echo  5. Kliknac "Install Now"
    echo  6. Po instalacji ponownie uruchomic ten plik
    echo.
    echo  Otwieram strone pobierania Pythona w przegladarce...
    start https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

FOR /F "tokens=2 delims= " %%V IN ('python --version 2^>^&1') DO SET PY_VER=%%V
echo  [OK] Python %PY_VER% zainstalowany.
echo.

echo ─────────────────────────────────────────────────────────
echo  KROK 2/3: Instalowanie bibliotek programu...
echo  (moze to potrwac kilka minut przy pierwszej instalacji)
echo ─────────────────────────────────────────────────────────
echo.

pip install streamlit pymupdf --quiet --upgrade 2>&1

IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo  [!] Blad instalacji bibliotek.
    echo  Prosze sprawdzic polaczenie z internetem i sprobowac ponownie.
    echo.
    pause
    exit /b 1
)

echo  [OK] Biblioteki zainstalowane.
echo.

echo ─────────────────────────────────────────────────────────
echo  KROK 3/3: Tworzenie skrotu na Pulpicie...
echo ─────────────────────────────────────────────────────────
echo.

:: Tworzenie skrótu na pulpicie
SET DESKTOP=%USERPROFILE%\Desktop
SET BAT_PATH=%~dp0START_KSIEGOWOSC.bat

powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%DESKTOP%\Synapsa Audyt Faktur.lnk'); ^
   $sc.TargetPath = '%BAT_PATH%'; ^
   $sc.Description = 'Synapsa - Audyt Faktur VAT'; ^
   $sc.IconLocation = 'shell32.dll,70'; ^
   $sc.Save()" >nul 2>&1

IF EXIST "%DESKTOP%\Synapsa Audyt Faktur.lnk" (
    echo  [OK] Skrot "Synapsa Audyt Faktur" dodany na Pulpicie.
) ELSE (
    echo  [OK] Instalacja gotowa. Uzyj pliku START_KSIEGOWOSC.bat
)

echo.
echo ═════════════════════════════════════════════════════════
echo.
echo  INSTALACJA ZAKONCZONA POMYSLNIE!
echo.
echo  Od teraz wystarczy kliknac dwukrotnie:
echo  [Pulpit] -> "Synapsa Audyt Faktur"
echo.
echo  Program uruchomi sie automatycznie w przegladarce.
echo.
echo ═════════════════════════════════════════════════════════
echo.
echo  Czy uruchomic program teraz? (T/N)
set /p URUCHOM=
IF /I "%URUCHOM%"=="T" (
    echo.
    echo  Uruchamiam program...
    timeout /t 1 >nul
    start "" "http://localhost:8502"
    timeout /t 2 >nul
    streamlit run "%~dp0app_ksiegowosc.py" --server.port 8502
)

pause
