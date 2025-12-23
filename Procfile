# Railway uses this file to determine how to run your app
web: if [ ! -d 'frontend/dist' ]; then echo '⚠️ frontend/dist missing, building now...'; cd frontend && npm install && npm run build && cd ..; fi && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
worker: python bot_runner.py
