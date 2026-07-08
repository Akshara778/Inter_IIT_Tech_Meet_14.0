import rclpy
import serial
import struct
from math import cos, sin
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class encoder_reader(Node):
    """
    ROS2 node that reads position and orientation from ESP32 over serial (UART-USB Bridge).

    Published Topics:
    /odom : nav_msgs/Odometry containing estimated (x, y, theta).

    TF Broadcast:
    odom-base_link transform is broadcast into the TF2 tree

    """

    def __init__(self):
        # Initialize ROS publishers, serial connection, TF broadcaster, and pose state.
        super().__init__("encoder_reader")
        self.odom_publisher = self.create_publisher(Odometry, "/odom", 10)
        self.esp32 = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.05)  # 11.52Kbps baud rate of STM32
        self.timer = self.create_timer(0.05, self.publish_msg)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.start = b'\xAA'
        self.end = b'\x55'

        # init dead-reckoning
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.get_logger().info("Encoder odometry node <encoder_reader.py> initialized.")

    def publish_msg(self):
        # Reads data from ESP32 serial.
        if self.esp32.read(1) == self.start:
            data = self.esp32.read(12)
            if self.esp32.read(1) == self.end:
                self.x, self.y, self.theta = struct.unpack('<fff', data)            

        # Publish Odometry
        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_link"
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0

        msg.pose.pose.orientation.z = sin(self.theta / 2)
        msg.pose.pose.orientation.w = cos(self.theta / 2)

        self.odom_publisher.publish(msg)

        # Publish Transform
        transform = TransformStamped()
        transform.header.stamp = msg.header.stamp  # keep TF and odom time-aligned
        transform.header.frame_id = "odom"
        transform.child_frame_id = "base_link"
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0

        transform.transform.rotation.w = cos(self.theta / 2)
        transform.transform.rotation.z = sin(self.theta / 2)

        self.tf_broadcaster.sendTransform(transform)



def main():
    rclpy.init()
    node = encoder_reader()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()