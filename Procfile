# Railway uses this file to determine how to run your app
web: if [ ! -d 'frontend/dist' ]; then echo '⚠️ frontend/dist missing, building now...'; cd frontend && npm install && npm run build && cd ..; fi && alembic upgrade head && .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port $PORT
worker: .venv/bin/python bot_runner.py
