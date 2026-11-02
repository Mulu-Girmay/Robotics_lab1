#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo


class TurnAway(Node):

    def __init__(self):
        super().__init__('turn_away')

        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.obstacle_sub = self.create_subscription(
            ObstacleInfo,
            '/obstacle',
            self.on_obstacle,
            10
        )

        self.get_logger().info('Turn away node started')

    def on_obstacle(self, msg):
        twist = Twist()

        if not msg.too_close:
            twist.linear.x = 0.2
            twist.angular.z = 0.0

        elif msg.angle > 0:
            twist.linear.x = 0.0
            twist.angular.z = -0.5

        else:
            twist.linear.x = 0.0
            twist.angular.z = 0.5

        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TurnAway()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()