@echo off
title BRK Analytics - Nstech Group
echo.
echo  ============================================
echo   BRK Analytics Platform - Nstech Group
echo  ============================================
echo.
echo  Iniciando servidor...
cd /d "%~dp0"
start "" http://localhost:8050
python app.py
pause
