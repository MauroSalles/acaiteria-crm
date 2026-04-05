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
COPY Procfile .

# Criar usuário não-root para segurança
RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# Porta padrão (Render/Railway injetam via $PORT)
EXPOSE 5000

# Healthcheck para orquestradores
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Comando de produção via gunicorn
CMD gunicorn backend.app:app \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
