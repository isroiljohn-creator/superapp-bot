FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

WORKDIR /srv
RUN useradd --system --uid 10001 --create-home hirely \
    && mkdir -p /data/media && chown hirely /data/media

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=hirely . .
USER hirely
EXPOSE 8081

# Migrations are idempotent; two workers share Redis for rate limits and Postgres for everything else.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8081 --workers 2 --no-server-header --no-access-log"]
