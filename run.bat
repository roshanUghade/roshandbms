@echo off
title Product Management System - DBMS
echo =====================================================================
echo       PRODUCT MANAGEMENT SYSTEM - DATABASE MANAGEMENT SYSTEM (DBMS)
echo =====================================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH. Please install Python 3.8+.
    pause
    exit /b 1
)

echo [2/3] Checking and installing dependencies...
python -m pip install -r requirements.txt --quiet

echo [3/3] Initializing Database & Starting Web Server...
echo.
echo Application will be live at: http://127.0.0.1:5000
echo Press Ctrl+C in this window to stop the server.
echo.

start "" http://127.0.0.1:5000
python app.py

pause
