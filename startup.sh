#!/bin/sh
# =============================================================================
# startup.sh — Entrypoint de produção para AcaiteriaCRM
# Inicializa o banco (se necessário) e sobe o gunicorn na porta $PORT
# =============================================================================

set -e

PORT="${PORT:-5000}"

echo "=============================================="
echo "  ACAITERIA CRM — INICIANDO (porta $PORT)"
echo "=============================================="

# Free tier = 512 MB RAM → 1 worker + --preload para economizar memória
exec gunicorn backend.app:app \
    --bind "0.0.0.0:${PORT}" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -
