#!/usr/bin/env bash
# Start the ARQ background worker in the background
python run_worker.py &

# Start Uvicorn in the foreground
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
