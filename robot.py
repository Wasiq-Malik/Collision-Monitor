import time

class Robot:
    def __init__(self, device_id, initial_position, path, rabbitmq_client):
        self.device_id = device_id
        self.x, self.y, self.theta = initial_position
        self.battery_level = 100  # Assuming battery starts at 100%
        self.loaded = False
        self.path = path
        self.path_index = 0  # Index to keep track of robot's position in the path
        self.status = 'active'  # Possible statuses: active, paused
        self.rabbitmq_client = rabbitmq_client  # Composition


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

    def send_state(self):
        state_message = self.get_state()
        self.rabbitmq_client.send_message(state_message)
