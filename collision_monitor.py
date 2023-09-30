import json
import random
import logging
from rabbitmq_client import RabbitMQConsumer, RabbitMQPublisher


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

publishers_dict = {}

def on_message_received(message_dict):
    pretty_message = json.dumps(message_dict, indent=4)
    logger.info(f"Received message:\n{pretty_message}")

    device_id = message_dict.get('device_id')
    if not device_id:
        logger.error("device_id not found in the received message")
        return

    command = random.choice(['pause', 'resume'])
    command_queue_name = f"{device_id}_commands"
    command_message = {"command": command}

    # Check if there is already a publisher for this device_id
    if device_id not in publishers_dict:
        publishers_dict[device_id] = RabbitMQPublisher(rabbitmq_server='localhost', queue_name=command_queue_name)

    publishers_dict[device_id].send_message(command_message)

def main():
    rabbitmq_server = 'localhost'
    shared_queue_name = 'robot_states'

    consumer = RabbitMQConsumer(rabbitmq_server, shared_queue_name, on_message_received)

    logger.info(f"Starting consumer on queue: {shared_queue_name}")
    consumer.start_consuming()

if __name__ == "__main__":
    main()