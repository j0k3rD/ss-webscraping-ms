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

# Install system dependencies for Playwright and utilities
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
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
    libgtk-3-0 \
    libasound2 \
    libfreetype6 \
    libfontconfig1 \
    libdbus-1-3 \
    redis-tools \
    curl \
    iputils-ping \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/dev.txt /src/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install --no-cache-dir playwright
RUN playwright install-deps
RUN playwright install chromium

# Copy application code
COPY . .

# Set permissions for the non-root user
RUN chown -R appuser:appuser /src

# Switch to non-root user
USER appuser

EXPOSE 5000

CMD ["./boot.sh"]
