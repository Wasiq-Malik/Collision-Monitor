import logging
from robot import Robot
import time
import json
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_robot_details(robot_details):
    required_keys = ["device_id", "x", "y", "theta", "path"]
    for key in required_keys:
        if key not in robot_details:
            raise ValueError(f"Missing required key: {key}")

    path = robot_details.get("path", [])
    if not isinstance(path, list) or not all(
        isinstance(node, dict) and "x" in node and "y" in node and "theta" in node
        for node in path
    ):
        raise ValueError("Invalid path format")


def main():
    logger.info("Starting application")
    filename = os.getenv("ROBOT_CONFIG_FILE")

    # Validate filename
    if not filename:
        logger.error("Missing environment variable: ROBOT_CONFIG_FILE")
        sys.exit(1)

    # Load robot details from the specified JSON file
    with open(filename, "r") as file:
        robot_details = json.load(file)

    # Validate robot details
    try:
        validate_robot_details(robot_details)
    except ValueError as e:
        logger.error(f"Invalid robot details in {filename}: {e}")
        sys.exit(1)

    # Define the RabbitMQ server and queue name
    rabbitmq_server = os.getenv("RABBITMQ_HOST", "localhost")

    # Create an instance of the Robot
    robot = Robot(
        device_id=robot_details["device_id"],
        initial_position=(
            robot_details["x"],
            robot_details["y"],
            robot_details["theta"],
        ),
        path=robot_details["path"],
        rabbitmq_server=rabbitmq_server,
    )
    # Simulate the robot's movement and send its state to RabbitMQ
    while robot.path_index < len(robot.path) - 1:
        logger.info("Moving robot and sending state to RabbitMQ")
        robot.move()
        robot.send_state()
        time.sleep(1)  # Wait for 1 second to simulate real-time state updates at 1Hz

    # Close the RabbitMQ connection when done
    logger.info("Closing RabbitMQ connection")
    robot.close()


if __name__ == "__main__":
    time.sleep(1)  # wait for collision monitor to start in docker-compose setup
    main()
