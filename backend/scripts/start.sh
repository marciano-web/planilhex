#!/usr/bin/env bash
set -e

echo "Starting Planilhex..."

export PYTHONPATH=/app

echo "DATABASE_URL = $DATABASE_URL"
echo "JWT_SECRET   = $JWT_SECRET"

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}



