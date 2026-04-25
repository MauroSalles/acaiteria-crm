# =============================================================================
# Dockerfile — AcaiteriaCRM (Grupo 22 - UNIVESP 2026)
# Build otimizado com multi-stage para produção
# =============================================================================

FROM python:3.13-slim AS base

# Variáveis de ambiente para Python em container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependências do sistema para psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python primeiro (cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY backend/ backend/
COPY frontend/ frontend/
COPY run.py .

# Criar usuário não-root para segurança
RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# Porta padrão (Render/Railway injetam via $PORT)
EXPOSE 5000

# Render usa healthCheckPath do render.yaml (não precisa de Docker HEALTHCHECK)
# Free tier = 512 MB RAM → 1 worker + --preload para economizar memória
CMD gunicorn backend.app:app \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -
