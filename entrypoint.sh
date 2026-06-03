#!/bin/bash
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-mediddata}"

echo "Aguardando banco de dados em $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
    sleep 1
done
echo "Banco disponível."

echo "Aplicando migrations..."
alembic upgrade head
echo "Migrations aplicadas."

echo "Iniciando MedID Data..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WORKERS:-1}" \
    --access-log
