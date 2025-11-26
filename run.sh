#!/bin/bash

# Kill existing
pkill -f "bot_runner.py"
pkill -f "uvicorn"
pkill -f "cloudflared"

# Start Tunnel
echo "🌐 Starting Tunnel..."
nohup cloudflared tunnel --url http://127.0.0.1:8000 > tunnel.log 2>&1 &

echo "⏳ Waiting for Tunnel URL..."
sleep 10

# Extract URL
WEBAPP_URL=$(grep -a -o 'https://[a-z0-9-]\+\.trycloudflare\.com' tunnel.log | head -n 1)

if [ -z "$WEBAPP_URL" ]; then
    echo "❌ Could not extract WEBAPP_URL. Check tunnel.log"
    exit 1
fi

echo "✅ Tunnel URL: $WEBAPP_URL"
export WEBAPP_URL=$WEBAPP_URL

# Start Backend
echo "🚀 Starting YASHA v2.0 Backend..."
nohup uvicorn backend.main:app --reload --port 8000 > backend.log 2>&1 &

# Start Bot
echo "🤖 Starting Bot..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
nohup python3 -u bot_runner.py > bot.log 2>&1 &

echo "✅ YASHA v2.0 Started!"
echo "📋 Logs: backend.log, bot.log, tunnel.log"

