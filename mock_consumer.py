import json
import logging
from rabbitmq_consumer import RabbitMQConsumer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def on_message_received(message_dict):
    pretty_message = json.dumps(message_dict, indent=4)
    logger.info(f"Received message:\n{pretty_message}")

def main():
    rabbitmq_server = 'localhost'
    shared_queue_name = 'robot_states'

    consumer = RabbitMQConsumer(rabbitmq_server, shared_queue_name, on_message_received)

    logger.info(f"Starting consumer on queue: {shared_queue_name}")
    consumer.start_consuming()

if __name__ == "__main__":
    main()