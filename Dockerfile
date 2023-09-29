FROM python:3.9-slim

WORKDIR /app

ADD . /app

RUN apt-get update && apt-get install -y netcat-openbsd && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    chmod +x wait-for-it.sh

ENTRYPOINT ["./wait-for-it.sh", "rabbitmq:5672", "--"]

