#!/bin/sh
set -e

# Railway injeta $PORT automaticamente
# Se não existir, usa 8000 (desenvolvimento)
PORT=${PORT:-8000}

echo "Starting MedID Data API on port $PORT..."

# Executar uvicorn com workers configuráveis
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --workers ${WORKERS:-2} \
  --log-level ${LOG_LEVEL:-info}
