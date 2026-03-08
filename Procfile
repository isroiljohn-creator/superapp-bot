web: echo 'Building Admin Panel...' && (cd miniapp/admin-dashboard && npm install && npm run build) && mkdir -p api/static/admin && cp -r miniapp/admin-dashboard/dist/* api/static/admin/ && alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT
worker: python -m bot.main
