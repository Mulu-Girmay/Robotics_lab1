import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math


class LidarSubscriber(Node):

    def __init__(self):
        super().__init__('lidar_subscriber')

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.lidar_callback,
            10
        )

        self.get_logger().info('LiDAR Subscriber Started!')

    def lidar_callback(self, msg):

        valid_ranges = [
            distance for distance in msg.ranges
            if math.isfinite(distance)
        ]

        if valid_ranges:
            closest = min(valid_ranges)
            farthest = max(valid_ranges)

            self.get_logger().info(
                f'Measurements: {len(msg.ranges)}, '
                f'Closest: {closest:.2f} m, '
                f'Farthest: {farthest:.2f} m'
            )


def main(args=None):
    rclpy.init(args=args)

    node = LidarSubscriber()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
