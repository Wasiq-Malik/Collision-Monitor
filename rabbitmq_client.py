import pika
import json

class RabbitMQClient:
    def __init__(self, rabbitmq_server, queue_name):
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_server)
            )
            self.channel = self.connection.channel()
            self.queue_name = queue_name  # Store the queue name

    def send_message(self, message):
        self.channel.queue_declare(queue=self.queue_name)  # Use the stored queue name
        self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=json.dumps(message))

    def close(self):
        self.connection.close()
