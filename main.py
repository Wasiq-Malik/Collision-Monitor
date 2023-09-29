import logging
from robot import Robot
from rabbitmq_client import RabbitMQClient
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def main():
    logger.info('Starting application')

    # Define the RabbitMQ server and queue name
    rabbitmq_server = 'localhost'
    shared_queue_name = 'robot_states'

    # Create an instance of the RabbitMQClient
    rabbitmq_client = RabbitMQClient(rabbitmq_server=rabbitmq_server, queue_name=shared_queue_name)

    # Define the initial position, path, and device ID for the robot
    initial_position = (10.0, 12.3, 1.57)
    path = [
        {"x": 10.0, "y": 12.3, "theta": 1.57},
        {"x": 11.0, "y": 12.3, "theta": 1.57},
        {"x": 12.0, "y": 12.3, "theta": 1.57},
        {"x": 13.0, "y": 12.3, "theta": 1.57}
    ]
    device_id = 'Herby'

    # Create an instance of the Robot
    robot = Robot(device_id=device_id, initial_position=initial_position, path=path, rabbitmq_client=rabbitmq_client)

    # Simulate the robot's movement and send its state to RabbitMQ
    for _ in range(len(path) - 1):
        logger.info('Moving robot and sending state to RabbitMQ')
        robot.move()
        robot.send_state()
        time.sleep(1)  # Wait for 1 second to simulate real-time state updates at 1Hz

    # Close the RabbitMQ connection when done
    logger.info('Closing RabbitMQ connection')
    rabbitmq_client.close()

if __name__ == "__main__":
    main()
