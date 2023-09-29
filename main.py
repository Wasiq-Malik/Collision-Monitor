import logging
from robot import Robot
from rabbitmq_client import RabbitMQClient
import time
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def main():
    logger.info('Starting application')
    # Get filename from command line arguments
    filename = sys.argv[1]

    # Load robot details from the specified JSON file
    with open(filename, 'r') as file:
        robot_details = json.load(file)

    # Define the RabbitMQ server and queue name
    rabbitmq_server = 'localhost'
    shared_queue_name = 'robot_states'

    # Create an instance of the RabbitMQClient
    rabbitmq_client = RabbitMQClient(rabbitmq_server=rabbitmq_server, queue_name=shared_queue_name)

    # Create an instance of the Robot
    robot = Robot(
        device_id=robot_details['device_id'],
        initial_position=(robot_details['x'], robot_details['y'], robot_details['theta']),
        path=robot_details['path'],
        rabbitmq_client=rabbitmq_client
    )
    # Simulate the robot's movement and send its state to RabbitMQ
    for _ in range(len(robot.path) - 1):
        logger.info('Moving robot and sending state to RabbitMQ')
        robot.move()
        robot.send_state()
        time.sleep(1)  # Wait for 1 second to simulate real-time state updates at 1Hz

    # Close the RabbitMQ connection when done
    logger.info('Closing RabbitMQ connection')
    rabbitmq_client.close()

if __name__ == "__main__":
    main()
