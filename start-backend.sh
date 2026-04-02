#!/bin/bash
echo "Starting XRP AI Trader Backend..."
cd "$(dirname "$0")/backend"

if [ ! -f ".env" ]; then
    if [ -f "../.env.example" ]; then
        cp "../.env.example" ".env"
        echo "Created .env from .env.example — edit it before continuing!"
    fi
fi

# Create venv if missing or broken
if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    rm -rf venv
    python3 -m venv venv
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment creation failed. Please run: sudo apt-get install python3-venv"
    exit 1
fi

source venv/bin/activate
venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "Backend starting at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
