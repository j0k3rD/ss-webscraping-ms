FROM python:3.10-slim-bullseye AS production

ENV PYTHONUNBUFFERED=1
ENV PATH=$PATH:/home/app/.local/bin

WORKDIR /app

# Create a new user "appuser"
RUN adduser --disabled-password --gecos '' appuser

COPY requirements_dev.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Redis
RUN apt-get update && apt-get install -y lsb-release curl gnupg && \
    curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list && \
    apt-get update && apt-get install -y redis && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

#Remove cache
RUN rm -rf /var/cache/apt/*

COPY ./app /app/app/
COPY ./install.sh /app/
COPY ./boot.sh /app/
COPY ./run.py /app/

RUN chmod +x /app/install.sh /app/boot.sh
RUN /app/./install.sh

# Change to the new user
USER appuser

EXPOSE 5000