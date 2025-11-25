#!/bin/bash

# Kill existing
pkill -f "python3"
pkill -f "uvicorn"
pkill -f "cloudflared"

# Start Backend
echo "🚀 Starting YASHA v2.0 Backend..."
nohup uvicorn backend.main:app --reload --port 8000 > backend.log 2>&1 &

# Start Bot
echo "🤖 Starting Bot..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
nohup python3 bot_runner.py > bot.log 2>&1 &

# Start Tunnel
echo "🌐 Starting Tunnel..."
nohup cloudflared tunnel --url http://localhost:8000 > tunnel.log 2>&1 &

sleep 3

echo "✅ YASHA v2.0 Started!"
echo "📋 Logs: backend.log, bot.log, tunnel.log"
echo ""
echo "🔍 Extracting Tunnel URL..."
sleep 2
grep -o 'https://[a-z0-9-]\+\.trycloudflare\.com' tunnel.log | head -n 1
