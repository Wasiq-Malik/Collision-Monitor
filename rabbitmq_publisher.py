import pika
import json

class RabbitMQPublisher:
    def __init__(self, rabbitmq_server, queue_name):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_server))
        self.channel = self.connection.channel()
        self.queue_name = queue_name
        self.channel.queue_declare(queue=self.queue_name)

    def send_message(self, message):
        self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=json.dumps(message))

    def close(self):
        self.connection.close()