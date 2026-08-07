# ============================================================
# Ravena AIM - v1.0.0-beta
# Dockerfile para Oracle Cloud Infrastructure (OCI)
# ============================================================
FROM python:3.11-slim

LABEL maintainer="Ravena AI Team"
LABEL version="1.0.0-beta"
LABEL description="Ravena AIM - Sistema Cognitivo Modular de Trading"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RAVENA_ENV=production
ENV RAVENA_VERSION=1.0.0-beta

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache de camadas Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/

# Criar diretórios de runtime
RUN mkdir -p /app/logs /app/data /app/memoria

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.utils.oci_readiness_check import check_health; check_health()" || exit 1

# Usuário não-root para segurança
RUN useradd -m -r ravena && chown -R ravena:ravena /app
USER ravena

# Porta padrão (API/Dashboard)
EXPOSE 8000

# Entrypoint
CMD ["python", "-m", "src.core.omega_core_v3.2.6"]
