# Railway uses this file to determine how to run your app
web: echo 'Building main frontend...' && (cd frontend && npm install && npm run build) && echo 'Building admin insights...' && (cd yasha-insights && npm install && npm run build) && alembic upgrade head && .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port $PORT
worker: .venv/bin/python bot_runner.py
