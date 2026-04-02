#!/bin/bash
echo "Starting XRP AI Trader Backend..."
cd "$(dirname "$0")/backend"

if [ ! -f ".env" ]; then
    if [ -f "../.env.example" ]; then
        cp "../.env.example" ".env"
        echo "Created .env from .env.example — edit it before continuing!"
    fi
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "Backend starting at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
