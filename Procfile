web: PYTHONPATH=/app alembic upgrade head || echo "⚠️ Migration skipped or failed" ; PYTHONPATH=/app python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
worker: PYTHONPATH=/app python -m bot.main
