
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool

from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed


class TurnAway(Node):

    def __init__(self):
        super().__init__('turn_away')

        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)
        self.declare_parameter('max_turn_speed', 1.5)

        self.enabled = False
        self.last_obstacle_distance = 0.0

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

        self.enable_service = self.create_service(
            SetBool,
            '/turn_away_enable',
            self.on_enable
        )

        self.speed_service = self.create_service(
            SetTurnSpeed,
            '/set_turn_speed',
            self.on_set_turn_speed
        )

        self.get_logger().info('Turn away node started (disabled)')

    def on_obstacle(self, msg):
        self.last_obstacle_distance = msg.distance

        status = RobotStatus()
        status.obstacle_distance = msg.distance

        if not self.enabled:
            status.state = 'stopped'
            self.status_pub.publish(status)
            return

        twist = Twist()

        forward_speed = self.get_parameter('forward_speed').value
        turn_speed = self.get_parameter('turn_speed').value

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

    def on_enable(self, request, response):
        if request.data:
            self.enabled = True
            response.success = True
            response.message = 'Turn away enabled'

        else:
            if self.enabled:
                self.enabled = False
                self.stop()

            self.publish_status('stopped')

            response.success = True
            response.message = 'Turn away disabled'

        self.get_logger().info(response.message)
        return response

    def on_set_turn_speed(self, request, response):
        turn_speed = request.turn_speed
        max_speed = self.get_parameter('max_turn_speed').value

        if turn_speed <= 0.0 or turn_speed > max_speed:
            response.success = False
            response.message = (
                f'Turn speed must be above 0 and at most {max_speed} rad/s'
            )
        else:
            self.set_parameters([
                rclpy.parameter.Parameter(
                    'turn_speed',
                    value=float(turn_speed)
                )
            ])

            response.success = True
            response.message = f'Turn speed set to {turn_speed} rad/s'

        self.get_logger().info(response.message)
        return response

    def publish_status(self, state):
        status = RobotStatus()
        status.state = state
        status.obstacle_distance = self.last_obstacle_distance
        self.status_pub.publish(status)

    def stop(self):
        self.cmd_vel_pub.publish(Twist())


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
