#!/usr/bin/env bash
set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🏗️ Building Admin Panel..."
npm run build:admin

echo "📂 Organizing static assets..."
mkdir -p api/static/admin
cp -r miniapp/admin-dashboard/dist/* api/static/admin/

echo "🔄 Running database migrations..."
alembic upgrade head || echo "⚠️ Migration failed or skipped"

echo "✅ Build completed successfully!"
