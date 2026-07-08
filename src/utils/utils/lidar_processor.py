import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class LidarProcessor(Node):
    def __init__(self):
        super().__init__("lidar_processor")
        self.lidar_publisher = self.create_publisher(LaserScan, "/scan", 10)
        self.data_receiver = self.create_subscription(LaserScan, "/ldlidar_node/scan", self.publish_data, 10)
    
    def publish_data(self, msg : LaserScan):
        self.lidar_publisher.publish(msg)


def main():
    rclpy.init()
    node = LidarProcessor()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()