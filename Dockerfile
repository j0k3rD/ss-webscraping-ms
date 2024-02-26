FROM python:3.10-slim-bullseye AS production

ENV PYTHONUNBUFFERED=1
ENV PATH=$PATH:/home/app/.local/bin

WORKDIR /app

COPY requirements_dev.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app/
COPY ./install.sh /app/
COPY ./boot.sh /app/
COPY ./run.py /app/

RUN chmod +x /app/install.sh /app/boot.sh
RUN /app/./install.sh

EXPOSE 5000