
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus


class TurnAway(Node):

    def __init__(self):
        super().__init__('turn_away')

        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)

        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.status_pub = self.create_publisher(
            RobotStatus, '/robot_status', 10
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
        status = RobotStatus()

        forward_speed = self.get_parameter('forward_speed').value
        turn_speed = self.get_parameter('turn_speed').value

        status.obstacle_distance = msg.distance

        if not msg.too_close:
            twist.linear.x = forward_speed
            status.state = 'forward'

        elif msg.angle > 0:
            twist.angular.z = -turn_speed
            status.state = 'turning'

        else:
            twist.angular.z = turn_speed
            status.state = 'turning'

        self.cmd_vel_pub.publish(twist)
        self.status_pub.publish(status)


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
