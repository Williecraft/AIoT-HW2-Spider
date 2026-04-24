@echo off
cd /d "%~dp0"
start "Weather App" cmd /k "streamlit run app.py"
ping -n 3 127.0.0.1 > nul
@REM start http://localhost:8501
