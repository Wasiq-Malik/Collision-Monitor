FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ./robot_simulator/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy robot_simulator and rabbitmq_client
COPY ./robot_simulator/ ./robot_simulator/
COPY ./rabbitmq_client/ ./rabbitmq_client/
COPY ./wait-for-it.sh wait-for-it.sh

# Run the application
CMD ["python", "./robot_simulator/robot_simulator.py"]
