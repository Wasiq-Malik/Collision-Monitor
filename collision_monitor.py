import math
import logging
from rabbitmq_client import RabbitMQConsumer, RabbitMQPublisher
from collections import defaultdict


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CollisionMonitor:
    def __init__(self, rabbitmq_server, input_queue_name):
        self.rabbitmq_server = rabbitmq_server
        self.robot_states = {}  # To store the latest state of each robot
        self.paused_robots = set()  # To keep track of which robots are paused each iteration
        self.dependencies = defaultdict(set)  # Maintain a set of dependencies for each paused robot
        self.consumer = RabbitMQConsumer(self.rabbitmq_server, input_queue_name, self.handle_state_update)
        self.publishers = {}  # To store RabbitMQPublisher instances for each robot


    def handle_state_update(self, message_dict):
        logger.info(f"Received state update: {message_dict}")
        device_id = message_dict.get('device_id')
        if not device_id:
            logger.warning(f"device_id not found in the received message: {message_dict}")
            return

        # Check if the robot has reached the end of its path
        if len(message_dict.get('path', [])) <= 1:  # If there is only one node left in the path, it means the robot has reached its destination.
            # Remove the robot from the global state and return
            self.robot_states.pop(device_id, None)
            logger.info(f"Robot {device_id} has reached its destination and is removed from the global state.")
            return

        # Update the stored state for the robot
        self.robot_states[device_id] = message_dict

        # Detect all potential collisions between all pairs of robots
        potential_collisions = self.detect_all_collisions()

        # Resolve all potential collisions in a coordinated manner
        self.resolve_collisions(potential_collisions)

        # Check if any paused robot can be resumed by the movement of the current robot
        self.resume_robots(device_id)

        # Clear the set of paused robots at the end of the iteration
        self.paused_robots.clear()


    def resolve_collisions(self, potential_collisions):
        collision_map = defaultdict(list)

        # Create a collision map
        for robot1, robot2 in potential_collisions:
            collision_map[robot1].append(robot2)
            collision_map[robot2].append(robot1)

        # Iteratively resolve collisions globally
        while collision_map:
            logger.info(f"Remaining collisions to resolve: {len(collision_map)}")

            # Find the robot with the most potential collisions
            robot_to_pause = max(collision_map, key=lambda robot: len(collision_map[robot]))

            # Pause the robot and send the command
            self.send_command(robot_to_pause, 'pause')
            self.dependencies[robot_to_pause].update(collision_map[robot_to_pause])  # Add dependencies
            self.paused_robots.add(robot_to_pause)  # Mark the robot as paused in the current iteration

            logger.info(f"Paused {robot_to_pause} to resolve collisions")

            # Remove all related collision pairs
            for robot in collision_map[robot_to_pause]:
                collision_map[robot].remove(robot_to_pause)
                if not collision_map[robot]:
                    del collision_map[robot]
            del collision_map[robot_to_pause]

    def detect_all_collisions(self):
        logger.info("Detecting all potential collisions between robots")
        potential_collisions = []
        robot_states_items = list(self.robot_states.items())

        # runtime O(n^2)
        for i, (robot_id1, state1) in enumerate(robot_states_items):
            for j in range(i + 1, len(robot_states_items)):
                robot_id2, state2 = robot_states_items[j]

                if self.detect_collision(state1, state2):
                    potential_collisions.append((robot_id1, robot_id2))

        return potential_collisions


    def detect_collision(self, state1, state2):
        logger.info(f"Detecting collisions between  {state1['device_id']} and {state2['device_id']}")
        # Get the next nodes in the paths of the robots
        next_node1 = state1['path'][1] if len(state1['path']) > 1 else state1['path'][0]  # Use current node if no next node
        next_node2 = state2['path'][1] if len(state2['path']) > 1 else state2['path'][0]  # Use current node if no next node

        # Get the positions of the next nodes
        x1, y1 = next_node1['x'], next_node1['y']
        x2, y2 = next_node2['x'], next_node2['y']

        # Calculate the distance between the next nodes
        distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        # Calculate the diagonal of a robot
        width, length = 6.3, 14.3  # Adjusted to the unit of the Cartesian plane (1 unit = 100 mm)
        diagonal = math.sqrt(width ** 2 + length ** 2)

        # Calculate the threshold for collision
        threshold = diagonal  # Since both robots are of the same size

        # Check if the distance between the next nodes is less than the threshold
        if distance < threshold:
            logger.info(f"Collision detected between {state1['device_id']} and {state2['device_id']}")
            return True

        return False

    def resume_robots(self, moved_robot_id):
        for paused_robot, dependencies in list(self.dependencies.items()):
            if paused_robot in self.paused_robots:  # Skip robots that were paused in the current iteration
                continue
            dependencies.discard(moved_robot_id)  # Remove the moved robot from the dependencies of paused robots

            # using graphs can reduce the complexity of dependency resolution
            def is_in_dependency_list(robot_id):
                return any(robot_id in deps for deps in self.dependencies.values())

            # Check for potential deadlock
            if all(is_in_dependency_list(dep) for dep in dependencies):
                logger.info(f"Potential deadlock detected involving {paused_robot} and {', '.join(dependencies)}")

                # Resolve deadlock by choosing one robot to resume
                robot_to_resume = self.resolve_deadlock([paused_robot] + list(dependencies))
                self.resume_robot(robot_to_resume)

            # If a paused robot no longer has any dependencies, resume it
            if not dependencies:
                self.resume_robot(paused_robot)

    def resume_robot(self, device_id):
        # Send the 'resume' command to the specified robot
        self.send_command(device_id, 'resume')

        # Delete the robot's dependencies
        if device_id in self.dependencies:
            del self.dependencies[device_id]

        logger.info(f"Resumed {device_id} as it no longer has any dependencies")

    def resolve_deadlock(self, robots_in_deadlock):
        # choose the robot with the smallest ID to move incase of deadlock
        robot_to_resume = min(robots_in_deadlock)
        logger.info(f"Resolving deadlock by resuming {robot_to_resume}")
        return robot_to_resume

    def send_command(self, robot_id, command):
        # Get the existing publisher for the robot or create a new one if it doesn't exist
        publisher = self.publishers.get(robot_id)
        if not publisher:
            queue_name = f"{robot_id}_commands"  # Assume each robot has a unique queue named "{device_id}_commands"
            publisher = RabbitMQPublisher(self.rabbitmq_server, queue_name)
            self.publishers[robot_id] = publisher  # Store the publisher in the dictionary

        # Send the command to the specified robot via RabbitMQ
        publisher.send_message({'command': command})
        logger.info(f"Sent {command} command to {robot_id}")

    def start(self):
        self.consumer.start_consuming()

    def close(self):
        # Close all RabbitMQPublisher instances when closing the CollisionMonitor
        for publisher in self.publishers.values():
            publisher.close()
        self.consumer.close()
