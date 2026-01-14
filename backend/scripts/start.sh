#!/usr/bin/env bash
set -e

echo "Starting Planilhex..."

echo "DATABASE_URL = ${DATABASE_URL}"
echo "JWT_SECRET   = ${JWT_SECRET}"

# Garante que as variáveis estejam no ambiente do Python
export DATABASE_URL
export JWT_SECRET
export CORS_ORIGINS
export ADMIN_EMAIL
export ADMIN_PASSWORD

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
