FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src

# Install system dependencies in a single RUN command
RUN set -eux \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        iputils-ping \
        redis-tools \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        gcc \
        python3-dev \
        libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -ms /bin/bash appuser

# Install Python dependencies with verbose output
COPY requirements/dev.txt requirements.txt
RUN pip install --no-cache-dir -v -r requirements.txt

# Install Playwright
RUN pip install --no-cache-dir playwright && \
    playwright install --with-deps chromium

# Copy application code
COPY . .

# Set permissions
RUN chown -R appuser:appuser /src

# Switch to non-root user
USER appuser

EXPOSE 5001

CMD ["./boot.sh"]
