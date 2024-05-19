# synctax = docker/dockerfile:1

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

# Instalando dependencias
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=/requirements/dev.txt,target=/src/requirements.txt \
    python -m pip install -r requirements.txt

COPY . .

EXPOSE 5001

CMD uvicorn main:app --host 0.0.0.0 --port 5001 --reload
