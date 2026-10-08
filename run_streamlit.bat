@echo off
title Product Management System - Streamlit DBMS Dashboard
echo =====================================================================
echo       PRODUCT MANAGEMENT SYSTEM - STREAMLIT DBMS DASHBOARD
echo =====================================================================
echo.
echo [1/2] Checking dependencies...
python -m pip install streamlit pandas --quiet

echo [2/2] Launching Streamlit Dashboard...
echo.
echo Application will open automatically in your browser (default: http://localhost:8501)
echo Press Ctrl+C in this terminal window to stop the server.
echo.

python -m streamlit run streamlit_app.py

pause
