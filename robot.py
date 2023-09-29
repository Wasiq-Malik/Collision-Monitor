import time
import json

class Robot:
    def __init__(self, device_id, initial_position, path):
        self.device_id = device_id
        self.x, self.y, self.theta = initial_position
        self.battery_level = 100  # Assuming battery starts at 100%
        self.loaded = False
        self.path = path
        self.path_index = 0  # Index to keep track of robot's position in the path
        self.status = 'active'  # Possible statuses: active, paused

    def move(self):
        # Check if there are more nodes in the path and the robot is active
        if self.path_index < len(self.path) - 1 and self.status == 'active':
            self.path_index += 1
            next_node = self.path[self.path_index]
            self.x, self.y, self.theta = next_node['x'], next_node['y'], next_node['theta']
            # You might also want to decrement the battery level based on movement

    def pause(self):
        self.status = 'paused'

    def resume(self):
        self.status = 'active'

    def get_state(self):
        return {
            "device_id": self.device_id,
            "timestamp": int(time.time() * 1000),  # Current time in milliseconds
            "x": self.x,
            "y": self.y,
            "theta": self.theta,
            "battery_level": self.battery_level,
            "loaded": self.loaded,
            "path": self.path[self.path_index:]  # Remaining path
        }

# Example path
path = [
    {"x": 10.0, "y": 12.3, "theta": 1.57},
    {"x": 11.0, "y": 12.3, "theta": 1.57},
    {"x": 12.0, "y": 12.3, "theta": 1.57},
    {"x": 13.0, "y": 12.3, "theta": 1.57}
]

# Instantiate a robot
robot = Robot(device_id="Herby", initial_position=(10.0, 12.3, 1.57), path=path)

# Simulate movement
for _ in range(len(path) - 1):
    robot.move()
    print(json.dumps(robot.get_state(), indent=4))  # Print the robot's state after each move
