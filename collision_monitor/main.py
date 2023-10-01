import os
import logging
from collision_monitor import CollisionMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Collision Monitoring Service")

    # Define the RabbitMQ server and the queue name for robot states
    rabbitmq_server = os.getenv("RABBITMQ_HOST", "localhost")
    shared_queue_name = os.getenv("RABBITMQ_QUEUE", "robot_states")

    # Initialize the collision monitor
    collision_monitor = CollisionMonitor(rabbitmq_server, shared_queue_name)

    # Start the message consumption loop
    try:
        logger.info("Starting message consumption loop")
        collision_monitor.start()
    except KeyboardInterrupt:
        logger.info("Stopping Collision Monitoring Service")
    finally:
        # Perform any necessary cleanup
        collision_monitor.close()


if __name__ == "__main__":
    main()
