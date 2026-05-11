# =============================================================================
# Dockerfile — AcaiteriaCRM (Grupo 22 - UNIVESP 2026)
# Build otimizado com multi-stage para produção
# =============================================================================

FROM python:3.13-slim AS base

# Variáveis de ambiente para Python em container
# PORT padrão 5000; sobrescrito por render.yaml / docker-compose / Render
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=5000

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
COPY startup.sh .

# Criar usuário não-root para segurança
RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/startup.sh
USER appuser

# Porta padrão 5000; sobrescrita em runtime pelo $PORT injetado pelo Render/Railway
EXPOSE 5000

# Usar startup.sh para inicializar o banco e iniciar gunicorn
CMD ["/app/startup.sh"]
