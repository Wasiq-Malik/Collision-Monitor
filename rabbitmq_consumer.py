import pika
import json

class RabbitMQConsumer:
    def __init__(self, rabbitmq_server, queue_name, callback):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_server))
        self.channel = self.connection.channel()
        self.queue_name = queue_name
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.on_message, auto_ack=True)
        self.callback = callback

    def on_message(self, ch, method, properties, body):
        message_dict = json.loads(body)
        self.callback(message_dict)

    def start_consuming(self):
        self.channel.start_consuming()

    def close(self):
        self.connection.close()
