FROM python:3.9-slim

WORKDIR /app

ADD . /app

RUN apt-get update && apt-get install -y netcat-openbsd && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    chmod +x wait.sh

EXPOSE 80

# Run producer.py when the container launches
CMD ["python", "producer.py"]
