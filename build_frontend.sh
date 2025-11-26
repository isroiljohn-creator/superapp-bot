#!/bin/bash
set -e

echo "🔨 Building Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Frontend build complete!"
echo "📂 Checking dist folder..."
ls -la frontend/dist || echo "❌ dist folder not found"
