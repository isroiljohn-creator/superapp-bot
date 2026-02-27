web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
bot: python -m bot.main
worker: python -m arq taskqueue.worker.WorkerSettings
