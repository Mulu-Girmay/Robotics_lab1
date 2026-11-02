
#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor, ExternalShutdownException

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

from my_robot_interfaces.action import Rotate


def yaw_from_quaternion(q):
    """Extract yaw angle from an orientation quaternion."""
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    )


def angle_difference(target, current):
    """Return wrapped target-current difference in [-pi, pi]."""
    return math.atan2(
        math.sin(target - current),
        math.cos(target - current)
    )


class RotateServer(Node):

    def __init__(self):
        super().__init__('rotate_server')

        self.declare_parameter('turn_speed', 0.5)

        self.yaw = None

        # Allows odometry callbacks while the action is executing.
        self.callback_group = ReentrantCallbackGroup()

        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.on_odom,
            10,
            callback_group=self.callback_group
        )

        self.action_server = ActionServer(
            self,
            Rotate,
            '/rotate',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info('Rotate action server started')

    def on_odom(self, msg):
        self.yaw = yaw_from_quaternion(
            msg.pose.pose.orientation
        )

    def goal_callback(self, goal_request):
        if goal_request.angle == 0.0:
            self.get_logger().warning('Rejecting zero-angle goal')
            return GoalResponse.REJECT

        if self.yaw is None:
            self.get_logger().warning('Waiting for odometry')
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Rotation cancellation requested')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        target_angle = goal_handle.request.angle

        previous_yaw = self.yaw
        turned = 0.0

        direction = 1.0 if target_angle > 0.0 else -1.0

        turn_speed = self.get_parameter('turn_speed').value

        twist = Twist()
        twist.angular.z = direction * turn_speed

        feedback = Rotate.Feedback()
        result = Rotate.Result()

        self.get_logger().info(
            f'Rotating through {target_angle:.2f} radians'
        )

        while rclpy.ok():

            if goal_handle.is_cancel_requested:
                self.cmd_vel_pub.publish(Twist())

                result.turned = turned
                goal_handle.canceled()

                self.get_logger().info(
                    f'Rotation canceled at {turned:.2f} radians'
                )

                return result

            current_yaw = self.yaw

            if current_yaw is not None:
                # Add each small wrapped yaw change.
                yaw_change = angle_difference(
                    current_yaw, previous_yaw
                )

                turned += yaw_change
                previous_yaw = current_yaw

            feedback.turned = turned
            goal_handle.publish_feedback(feedback)

            if abs(turned) >= abs(target_angle):
                break

            self.cmd_vel_pub.publish(twist)

            time.sleep(0.05)

        # Stop after reaching the target.
        self.cmd_vel_pub.publish(Twist())

        result.turned = turned
        goal_handle.succeed()

        self.get_logger().info(
            f'Rotation completed: {turned:.2f} radians'
        )

        return result


def main(args=None):
    rclpy.init(args=args)

    node = RotateServer()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()

    except (KeyboardInterrupt, ExternalShutdownException):
        pass

    finally:
        node.cmd_vel_pub.publish(Twist())
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

