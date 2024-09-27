ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /src

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid ${UID} \
    appuser

# Instalando redis-cli (redis-tools)
RUN apt-get update && apt-get install -y redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Instalando dependencias
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=/requirements/dev.txt,target=/src/requirements.txt \
    python -m pip install -r requirements.txt

# Copiando el código de la aplicación
COPY . .

# Copiando el script de espera
COPY wait-for-redis.sh /usr/local/bin/wait-for-redis.sh
RUN chmod +x /usr/local/bin/wait-for-redis.sh

EXPOSE 5000

# Usando el script de espera antes de iniciar la aplicación
CMD ["wait-for-redis.sh", "redis", "./boot.sh"]
