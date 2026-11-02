import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuSubscriber(Node):

    def __init__(self):
        super().__init__('imu_subscriber')

        self.subscription = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )

        self.get_logger().info('IMU Subscriber Started!')

    def imu_callback(self, msg):
        self.get_logger().info(
            f'Angular velocity: '
            f'x={msg.angular_velocity.x:.2f}, '
            f'y={msg.angular_velocity.y:.2f}, '
            f'z={msg.angular_velocity.z:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = ImuSubscriber()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
