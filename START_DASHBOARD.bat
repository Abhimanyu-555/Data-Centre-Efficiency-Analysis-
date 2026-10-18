@echo off
cd /d "%~dp0"
echo Starting the dashboard from this folder...
python -m streamlit run app.py --server.port 8503
pause
