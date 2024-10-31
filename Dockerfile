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

# Instalar las dependencias del sistema necesarias para Playwright y otras utilidades
RUN apt-get update && apt-get install -y \
    libxcb-shm0 \
    libx11-xcb1 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrandr2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libatk1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libglib2.0-0 \
    libgtk-3-dev \
    libasound2 \
    libfreetype6 \
    libfontconfig1 \
    libdbus-1-3 \
    redis-tools \
    curl \
    iputils-ping \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requirements e instalar las dependencias de Python
COPY requirements/dev.txt /src/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r requirements.txt

# Instalar Playwright en Python
RUN python -m pip install playwright

# Instalar las dependencias del sistema necesarias para Playwright
RUN python -m playwright install-deps

# Instalar los navegadores de Playwright
RUN python -m playwright install

# Copiar el código de la aplicación
COPY . .

# Copiar el script de espera
COPY wait-for-redis.sh /usr/local/bin/wait-for-redis.sh
RUN chmod +x /usr/local/bin/wait-for-redis.sh

EXPOSE 5000

# Usar el script de espera antes de iniciar la aplicación
CMD ["wait-for-redis.sh", "redis", "./boot.sh"]
