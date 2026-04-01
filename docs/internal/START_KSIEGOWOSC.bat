@echo off
chcp 65001 >nul
title Synapsa — Audyt Faktur
color 0A
cls

echo ╔══════════════════════════════════════════════════╗
echo ║          SYNAPSA — Audyt Faktur                       ║
echo ║          Uruchamianie programu...                     ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo Program otwiera sie w przegladarce internetowej.
echo Prosze chwile poczekac...
echo.
echo (Tego okna nie zamykac podczas pracy z programem!)
echo.

timeout /t 2 >nul
start "" "http://localhost:8502"
timeout /t 1 >nul
streamlit run app_ksiegowosc.py --server.port 8502 --server.headless true

pause
