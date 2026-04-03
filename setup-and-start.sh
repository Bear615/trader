#!/bin/bash
set -e

echo "=========================================="
echo "XRP AI Trader — Setup & Start"
echo "=========================================="

# Check if running on Linux
if [[ ! "$OSTYPE" =~ ^linux ]]; then
    echo "This script is for Linux only."
    exit 1
fi

# Install system dependencies
echo ""
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip nodejs npm git
elif command -v yum &> /dev/null; then
    sudo yum install -y python3 python3-devel nodejs npm git
else
    echo "Unsupported package manager. Please install: python3, nodejs, npm, git"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")"

# Setup backend
echo ""
echo "Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
echo ""
echo "Setting up frontend..."
cd ../frontend
npm install
cd ..

# Install PM2 globally
echo ""
echo "Installing PM2..."
sudo npm install -g pm2

# Start both services with PM2
echo ""
echo "Starting backend and frontend with PM2..."
pm2 start ecosystem.config.cjs

# Save PM2 state and enable startup hook
echo ""
echo "Enabling auto-start on boot..."
pm2 save
sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp $HOME
echo "Add this line to your crontab to auto-start: @reboot pm2 start ecosystem.config.cjs"

echo ""
echo "=========================================="
echo "✓ All set!"
echo "=========================================="
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Monitor logs:"
echo "  pm2 logs"
echo "  pm2 logs xrp-backend"
echo "  pm2 logs xrp-frontend"
echo ""
echo "View status:"
echo "  pm2 status"
echo ""
echo "Stop:"
echo "  pm2 stop ecosystem.config.cjs"
echo ""
