import pika

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

# Declare a queue named 'hello'
channel.queue_declare(queue='hello')

# Publish a message to the 'hello' queue
channel.basic_publish(exchange='', routing_key='hello', body='Hello, RabbitMQ!')

print(" [x] Sent 'Hello, RabbitMQ!'")

import time
time.sleep(5)

channel.basic_publish(exchange='', routing_key='hello', body='Hello, RabbitMQ! (2)')

print(" [x] Sent Another 'Hello, RabbitMQ!'")
# Close the connection
connection.close()
