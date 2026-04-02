@echo off
echo Starting XRP AI Trader Backend...
cd /d "%~dp0backend"

if not exist ".env" (
    copy "..\\.env.example" ".env"
    echo Created .env from .env.example — edit it before continuing!
)

:: Create venv if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo.
echo Backend starting at http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
uvicorn main:app --reload --host 0.0.0.0 --port 8000
