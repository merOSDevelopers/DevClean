@echo off
chcp 65001 >nul
title DevClean
cd /d "%~dp0"
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] DevClean baslatilirken bir sorun olustu. PyQt6 paketinin kurulu oldugundan emin olun:
    echo        pip install -r requirements.txt
    pause
)
