# Build stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/dev.txt requirements.txt
RUN pip install --user -r requirements.txt

# Final stage
FROM python:3.12-slim

WORKDIR /src

# Install only the essential runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxcomposite1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libnss3 \
        libcups2 \
        libxss1 \
        libxrandr2 \
        libasound2 \
        libatk1.0-0 \
        libpango-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libgtk-3-0 \
        libdbus-1-3 \
        redis-tools \
        curl \
        iputils-ping \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -ms /bin/bash appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Install and setup Playwright
ENV PATH=/home/appuser/.local/bin:$PATH
RUN pip install --no-cache-dir playwright \
    && playwright install-deps \
    && playwright install chromium --with-deps

# Set permissions
RUN chown -R appuser:appuser /src

# Switch to non-root user
USER appuser

EXPOSE 5001

CMD ["./boot.sh"]
