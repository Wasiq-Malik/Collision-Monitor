import unittest
from unittest.mock import patch
from robot_simulator.robot import Robot  # Ensure this is the correct import


class TestRobot(unittest.TestCase):

    def setUp(self):
        self.device_id = 'Herby'
        self.initial_position = (10.0, 12.3, 1.57)
        self.path = [
            {"x": 10.0, "y": 12.3, "theta": 1.57},
            {"x": 11.0, "y": 12.3, "theta": 1.57},
            {"x": 12.0, "y": 12.3, "theta": 1.57},
            {"x": 13.0, "y": 12.3, "theta": 1.57},
        ]
        self.rabbitmq_server = 'some_server'

        with patch('robot_simulator.robot.RabbitMQConsumer', autospec=True) as self.MockConsumer, \
                patch('robot_simulator.robot.RabbitMQPublisher', autospec=True) as self.MockPublisher:
            self.robot = Robot(self.device_id, self.initial_position, self.path, self.rabbitmq_server)

    def test_move_success(self):
        self.robot.move()
        self.assertEqual(self.robot.path_index, 1)
        self.assertEqual(self.robot.battery_level, 99)
        self.assertEqual(self.robot.x, 11.0)
        self.assertEqual(self.robot.y, 12.3)
        self.assertEqual(self.robot.theta, 1.57)

    def test_pause_and_move(self):
        self.robot.pause()
        self.robot.move()
        self.assertEqual(self.robot.path_index, 0, "Robot should not move when paused")
        self.assertEqual(self.robot.status, 'paused')

    def test_resume_and_move(self):
        self.robot.pause()
        self.robot.resume()
        self.assertEqual(self.robot.status, 'active')
        self.robot.move()
        self.assertEqual(self.robot.path_index, 1, "Robot should move when active")

    def test_move_at_last_node(self):
        self.robot.path_index = len(self.path) - 1  # Set robot to the last node in its path
        self.robot.move()
        self.assertEqual(self.robot.path_index, len(self.path) - 1, "Robot should not move past the last node")

    def test_handle_command_pause(self):
        message_dict = {'command': 'pause'}
        self.robot.handle_command(message_dict)
        self.assertEqual(self.robot.status, 'paused')

    def test_handle_command_resume(self):
        message_dict = {'command': 'resume'}
        self.robot.handle_command(message_dict)
        self.assertEqual(self.robot.status, 'active')

    def test_handle_command_invalid(self):
        message_dict = {'command': 'invalid'}
        self.robot.handle_command(message_dict)
        self.assertNotEqual(self.robot.status, 'invalid', "Robot should not accept invalid status")


if __name__ == '__main__':
    unittest.main()

