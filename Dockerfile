FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src

# Configure apt and update package lists
RUN echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/10no-check-valid-until \
    && echo 'APT::Get::Assume-Yes "true";' > /etc/apt/apt.conf.d/90assumeyes \
    && echo 'APT::Install-Suggests "0";' > /etc/apt/apt.conf.d/90no-suggests \
    && echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/90no-recommends

# Update package list and install essential build dependencies
RUN set -ex \
    && apt-get update \
    && apt-get install -y build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies
RUN set -ex \
    && apt-get update \
    && apt-get install -y \
        curl \
        iputils-ping \
        redis-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install browser dependencies
RUN set -ex \
    && apt-get update \
    && apt-get install -y \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libpango-1.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -ms /bin/bash appuser

# Copy and install Python dependencies
COPY requirements/dev.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

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
