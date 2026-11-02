
#!/usr/bin/env python3

import rclpy

from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Twist

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):

    def __init__(self):
        super().__init__('square_driver')

        self.declare_parameter('side_length', 0.5)
        self.side_length = self.get_parameter('side_length').value

        self.drive_client = ActionClient(
            self, DriveDistance, '/drive_distance'
        )

        self.rotate_client = ActionClient(
            self, Rotate, '/rotate'
        )

        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.get_logger().info(
            f'Square driver started. Side length: {self.side_length} m'
        )

    def stop_robot(self):
        self.cmd_vel_pub.publish(Twist())

    def feedback_callback(self, msg):
        feedback = msg.feedback
    
        if hasattr(feedback, 'travelled'):
            self.get_logger().info(
                f'Driving progress: {feedback.travelled:.2f} m'
            )
    
        elif hasattr(feedback, 'turned'):
            self.get_logger().info(
                f'Rotation progress: {feedback.turned:.2f} rad'
            )
    

    def send_goal_and_wait(self, client, goal, action_name):

        client.wait_for_server()

        send_future = client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )

        rclpy.spin_until_future_complete(self, send_future)

        goal_handle = send_future.result()

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f'{action_name} goal rejected')
            return False, None

        self.get_logger().info(f'{action_name} goal accepted')

        result_future = goal_handle.get_result_async()

        rclpy.spin_until_future_complete(self, result_future)

        if result_future.result() is None:
            self.get_logger().error(f'{action_name} returned no result')
            return False, None

        response = result_future.result()

        if response.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(f'{action_name} failed')
            return False, response.result

        return True, response.result

    def drive_one_side(self, side):

        self.get_logger().info(
            f'Side {side}/4: Driving {self.side_length} meters'
        )

        goal = DriveDistance.Goal()
        goal.distance = float(self.side_length)

        success, result = self.send_goal_and_wait(
            self.drive_client,
            goal,
            'DriveDistance'
        )

        if not success or not result.reached:
            self.stop_robot()
            self.get_logger().error(
                f'Square failed while driving side {side}/4'
            )
            return False

        self.get_logger().info(
            f'Side {side}/4 completed: {result.travelled:.2f} m'
        )

        return True

    def rotate_left(self, side):

        self.get_logger().info(
            f'Side {side}/4: Turning left 90 degrees'
        )

        goal = Rotate.Goal()
        goal.angle = 1.57079632679

        success, result = self.send_goal_and_wait(
            self.rotate_client,
            goal,
            'Rotate'
        )

        if not success:
            self.stop_robot()
            self.get_logger().error(
                f'Square failed while turning after side {side}/4'
            )
            return False

        self.get_logger().info(
            f'Turn after side {side}/4 completed: '
            f'{result.turned:.2f} radians'
        )

        return True

    def run_square(self):

        for side in range(1, 5):

            if not self.drive_one_side(side):
                return

            if not self.rotate_left(side):
                return

        self.stop_robot()

        self.get_logger().info(
            'SUCCESS: Robot completed all four sides of the square!'
        )


def main(args=None):

    rclpy.init(args=args)
    node = SquareDriver()

    try:
        node.run_square()

    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().warning('Square driver interrupted')
        node.stop_robot()

    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

