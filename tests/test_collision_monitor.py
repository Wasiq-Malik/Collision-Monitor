import unittest
from unittest.mock import patch
from collision_monitor import CollisionMonitor


class TestCollisionMonitor(unittest.TestCase):

    def setUp(self):
        self.rabbitmq_server = 'some_server'
        self.input_queue_name = 'input_queue'

        # Patching the RabbitMQConsumer and RabbitMQPublisher to avoid real RabbitMQ interactions during the test.
        with patch('collision_monitor.RabbitMQConsumer', autospec=True) as self.MockConsumer, \
                patch('collision_monitor.RabbitMQPublisher', autospec=True) as self.MockPublisher:

            self.collision_monitor = CollisionMonitor(self.rabbitmq_server, self.input_queue_name)
            self.collision_monitor.consumer = self.MockConsumer

    def test_no_collision(self):
        # Define mock states simulating 3 robots with no collision.
        state1 = {"device_id": "robot1", "path": [{"x": 1, "y": 1}, {"x": 20, "y": 20}]}
        state2 = {"device_id": "robot2", "path": [{"x": 30, "y": 30}, {"x": 40, "y": 40}]}
        state3 = {"device_id": "robot3", "path": [{"x": 50, "y": 50}, {"x": 60, "y": 60}]}

        # Simulate state updates.
        self.collision_monitor.handle_state_update(state1)
        self.collision_monitor.handle_state_update(state2)
        self.collision_monitor.handle_state_update(state3)

        # Assertions
        self.assertEqual(len(self.collision_monitor.robot_states), 3, "All robots should be in robot_states")
        self.assertEqual(len(self.collision_monitor.dependencies), 0, "No robots should be paused")

    def test_all_robots_collide(self):
        with patch.object(self.collision_monitor, 'publishers',
                        robot1=self.MockPublisher,
                        robot2=self.MockPublisher,
                        robot3=self.MockPublisher):

            # Define mock states simulating 3 robots in a 3-way collision scenario.
            state1 = {"device_id": "robot1", "path": [{"x": 1, "y": 1}, {"x": 8, "y": 8}]}
            state2 = {"device_id": "robot2", "path": [{"x": 8, "y": 8}, {"x": 15, "y": 15}]}
            state3 = {"device_id": "robot3", "path": [{"x": 15, "y": 15}, {"x": 1, "y": 1}]}

            self.collision_monitor.handle_state_update(state1)
            self.collision_monitor.handle_state_update(state2)
            self.collision_monitor.handle_state_update(state3)

            dependencies = self.collision_monitor.dependencies
            self.assertEqual(len(dependencies), 1, "One robot should have dependencies")

            # The robot with dependencies should be 'robot1'
            self.assertIn('robot1', dependencies, "'robot1' should have dependencies")

            robot1_dependencies = dependencies.get('robot1', set())
            self.assertEqual(len(robot1_dependencies), 2, "'robot1' should have two dependencies")

            # 'robot1' should have dependencies on 'robot2' and 'robot3'
            self.assertIn('robot2', robot1_dependencies, "'robot2' should be in dependencies of 'robot1'")
            self.assertIn('robot3', robot1_dependencies, "'robot3' should be in dependencies of 'robot1'")

    def test_two_robots_collide(self):
        with patch.object(self.collision_monitor, 'publishers',
                        robot1=self.MockPublisher,
                        robot2=self.MockPublisher,
                        robot3=self.MockPublisher):

            # Define mock states simulating a scenario where two robots are in a collision course, and one is not.
            state1 = {"device_id": "robot1", "path": [{"x": 1, "y": 1}, {"x": 8, "y": 8}]}
            state2 = {"device_id": "robot2", "path": [{"x": 8, "y": 8}, {"x": 15, "y": 15}]}
            state3 = {"device_id": "robot3", "path": [{"x": 50, "y": 50}, {"x": 60, "y": 60}]}

            self.collision_monitor.handle_state_update(state1)
            self.collision_monitor.handle_state_update(state2)
            self.collision_monitor.handle_state_update(state3)

            dependencies = self.collision_monitor.dependencies
            self.assertEqual(len(dependencies), 1, "One robot should have dependencies")

            # Check which robot has dependencies and validate those.
            dependent_robot = next(iter(dependencies))
            dependent_robot_dependencies = dependencies[dependent_robot]

            self.assertEqual(len(dependent_robot_dependencies), 1, f"{dependent_robot} should have one dependency")
            self.assertIn('robot1' if dependent_robot == 'robot2' else 'robot2', dependent_robot_dependencies, f"Invalid dependency for {dependent_robot}")

    def test_robot_resumes_after_collision_resolution(self):
        with patch.object(self.collision_monitor, 'publishers',
                        robot1=self.MockPublisher,
                        robot2=self.MockPublisher):

            # Initial states simulating 2 robots about to collide.
            state1 = {"device_id": "robot1", "path": [{"x": 1, "y": 1}, {"x": 8, "y": 8}]}
            state2 = {"device_id": "robot2", "path": [{"x": 8, "y": 8}, {"x": 15, "y": 15}]}

            # First Iteration: Handle state updates and check the dependencies.
            self.collision_monitor.handle_state_update(state1)
            self.collision_monitor.handle_state_update(state2)
            self.assertIn('robot1', self.collision_monitor.dependencies, "'robot1' should be paused in the first iteration")

            # Second Iteration: Update the state of 'robot2' to simulate 'robot2' moving away from collision point.
            state2_moved = {"device_id": "robot2", "path": [{"x": 15, "y": 15}, {"x": 22, "y": 22}]}
            self.collision_monitor.handle_state_update(state2_moved)

            # Assert if 'robot1' resumed and there are no dependencies left.
            self.assertFalse(self.collision_monitor.dependencies, "There should be no dependencies after second iteration")

    def test_robot_reaches_destination(self):
        # Define mock states simulating a scenario where a robot has reached its destination.
        state1 = {"device_id": "robot1", "path": [{"x": 1, "y": 1}]}

        self.collision_monitor.handle_state_update(state1)

        # Assertions
        self.assertEqual(len(self.collision_monitor.robot_states), 0, "No robots should be in robot_states")

if __name__ == '__main__':
    unittest.main()

