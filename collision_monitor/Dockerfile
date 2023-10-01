FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ./collision_monitor/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy collision_detector and rabbitmq_client
COPY ./collision_monitor/ ./collision_monitor/
COPY ./rabbitmq_client/ ./rabbitmq_client/
COPY ./wait-for-it.sh wait-for-it.sh

# Run the application
CMD ["python", "./collision_monitor/main.py"]

