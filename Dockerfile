FROM python:3.10-slim-bullseye AS production

ENV PYTHONUNBUFFERED=1
ENV PATH=$PATH:/home/app/.local/bin

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./main /app/main
COPY ./config.py /app/
COPY ./run.py /app/
COPY ./tasks.py /app/

EXPOSE 5000

CMD [ "python3", "run.py" ]