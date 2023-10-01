import time
import logging
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rabbitmq_client.rabbitmq_client import RabbitMQConsumer, RabbitMQPublisher

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Robot:
    def __init__(self, device_id, initial_position, path, rabbitmq_server):
        self.device_id = device_id
        self.x, self.y, self.theta = initial_position
        self.battery_level = 100  # Assuming battery starts at 100%
        self.loaded = False
        self.path = path
        self.path_index = 0  # Index to keep track of robot's position in the path
        self.status = "active"  # Possible statuses: active, paused
        self.publisher = RabbitMQPublisher(
            rabbitmq_server, os.getenv("RABBITMQ_QUEUE", "robot_states")
        )
        self.consumer = RabbitMQConsumer(
            rabbitmq_server, f"{self.device_id}_commands", self.handle_command
        )
        self.command_listener_thread = threading.Thread(
            target=self.listen_commands, daemon=True
        )
        self.command_listener_thread.start()

    def handle_command(self, message_dict):
        command = message_dict.get("command")
        if not command:
            logging.error(f"Command not found in the received message: {message_dict}")
            return

        if command == "pause":
            self.pause()
            logging.info(f"{self.device_id} has been paused")
        elif command == "resume":
            self.resume()
            logging.info(f"{self.device_id} has resumed")
        else:
            logging.warning(f"Invalid command received: {command}")

    def move(self):
        # Check if the robot is paused
        if self.status == "paused":
            logging.info(f"{self.device_id} is paused and cannot move")
            return

        # Check if the robot is at the last node in its path
        if self.path_index >= len(self.path) - 1:
            logging.info(
                f"{self.device_id} has reached the last node in its path and cannot move"
            )
            return

        # Check if the battery level is sufficient to move
        if self.battery_level <= 0:
            logging.warning(f"{self.device_id} has insufficient battery level to move")
            return

        # Move to the next node in the path
        self.path_index += 1
        next_node = self.path[self.path_index]
        self.x, self.y, self.theta = next_node["x"], next_node["y"], next_node["theta"]
        self.battery_level -= (
            1  # Assume moving to the next node consumes 1% of the battery
        )
        logging.info(f"{self.device_id} moved to node {next_node}")

    def pause(self):
        self.status = "paused"
        logging.info(
            f"{self.device_id} paused at position {self.x}, {self.y}, {self.theta} with remaining path {self.path[self.path_index:]}"
        )

    def resume(self):
        self.status = "active"
        logging.info(
            f"{self.device_id} resumed at position {self.x}, {self.y}, {self.theta} with remaining path {self.path[self.path_index:]}"
        )

    def get_state(self):
        return {
            "device_id": self.device_id,
            "timestamp": int(time.time() * 1000),  # Current time in milliseconds
            "x": self.x,
            "y": self.y,
            "theta": self.theta,
            "battery_level": self.battery_level,
            "loaded": self.loaded,
            "path": self.path[self.path_index :],  # Remaining path
        }

    def send_state(self):
        try:
            state_message = self.get_state()
            self.publisher.send_message(state_message)
            logging.info(f"Sent state message for {self.device_id}")
        except Exception as e:
            logging.error(f"Failed to send state message for {self.device_id}: {e}")

    def listen_commands(self):
        self.consumer.start_consuming()

    def close(self):
        self.consumer.close()
        self.publisher.close()
