import pika
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def on_message(ch, method, properties, body):
    message_dict = json.loads(body)
    pretty_message = json.dumps(message_dict, indent=4)
    logger.info(f"Received message:\n{pretty_message}")


def main():
    rabbitmq_server = 'localhost'
    shared_queue_name = 'robot_states'

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_server))
    channel = connection.channel()

    channel.queue_declare(queue=shared_queue_name)
    channel.basic_consume(queue=shared_queue_name, on_message_callback=on_message, auto_ack=True)

    logger.info(f"Starting consumer on queue: {shared_queue_name}")
    channel.start_consuming()

if __name__ == "__main__":
    main()
