#!/usr/bin/python3

import rclpy
import serial
import struct
from math import cos, sin
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
# 🟢 NEW: Import LaserScan message
from sensor_msgs.msg import LaserScan
import numpy as np


class odompub(Node):
    """
    ROS2 node that reads position and orientation from ESP32 over serial (UART-USB Bridge).
    Now also publishes fake Lidar data to /scan.

    Published Topics:
    /odom : nav_msgs/Odometry containing estimated (x, y, theta).
    /scan : sensor_msgs/LaserScan (fake data)

    TF Broadcast:
    odom-base_link transform is broadcast into the TF2 tree

    """

    def __init__(self):
        # Initialize ROS publishers, serial connection, TF broadcaster, and pose state.
        super().__init__("odom_pub")
        
        # 🟢 MODIFIED: Publisher for fake LaserScan data
        self.lidar_publisher = self.create_publisher(LaserScan, "/scan", 10)
        
        self.odom_publisher = self.create_publisher(Odometry, "/odom", 10) # Added Odom pub for completeness
        
        self.timer = self.create_timer(0.05, self.publish_msg)
        self.tf_broadcaster = TransformBroadcaster(self)

        # 🟢 Lidar Parameters (Define constants for the fake scan)
        self.SCAN_RADIUS = 0.5  # Fixed range in meters
        self.NUM_SAMPLES = 360  # Number of beams/samples
        self.ANGLE_MIN = 0.0    # Start angle (rad)
        self.ANGLE_MAX = 2 * np.pi # End angle (rad)
        self.ANGLE_INCREMENT = (self.ANGLE_MAX - self.ANGLE_MIN) / self.NUM_SAMPLES
        self.RANGE_MIN = 0.0
        self.RANGE_MAX = 10.0


    def publish_msg(self):

        current_time = self.get_clock().now().to_msg()
        
        # --- 1. Publish Odometry (Unmodified from your code, ensuring it runs) ---
        
        msg = Odometry()
        msg.header.stamp = current_time
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_footprint"
        msg.pose.pose.position.x = 0.0
        msg.pose.pose.position.y = 0.0
        msg.pose.pose.position.z = 0.0

        msg.pose.pose.orientation.z = 0.0
        msg.pose.pose.orientation.w = 1.0

        self.odom_publisher.publish(msg)

        # --- 2. Publish Transform ---
        
        transform = TransformStamped()
        transform.header.stamp = current_time  # keep TF and odom time-aligned
        transform.header.frame_id = "odom"
        transform.child_frame_id = "base_footprint"
        transform.transform.translation.x = 0.0
        transform.transform.translation.y = 0.0
        transform.transform.translation.z = 0.0

        transform.transform.rotation.w = 1.0 # Fixed typo: should be 1.0, not 0.0/1.0
        transform.transform.rotation.z = 0.0 # Fixed typo: should be 0.0, not 1.0

        self.tf_broadcaster.sendTransform(transform)
        
        # --- 3. Publish Fake LaserScan Data ---
        
        scan_msg = LaserScan()
        scan_msg.header.stamp = current_time
        # Lidar is typically mounted relative to base_link
        scan_msg.header.frame_id = "base_link" 
        
        # Set Lidar properties
        scan_msg.angle_min = self.ANGLE_MIN
        scan_msg.angle_max = self.ANGLE_MAX
        scan_msg.angle_increment = self.ANGLE_INCREMENT
        scan_msg.time_increment = 0.0 # Assuming instantaneous scan
        scan_msg.scan_time = 0.1 # Example: Scan takes 0.1s to complete
        scan_msg.range_min = self.RANGE_MIN
        scan_msg.range_max = self.RANGE_MAX
        
        # Set the fake data: all ranges are the fixed radius (0.5m)
        # This simulates a robot in an empty circular room of radius 0.5m 
        # or a sensor that always returns 0.5m.
        scan_msg.ranges = [self.SCAN_RADIUS] * self.NUM_SAMPLES
        
        # Optional: Set intensity array to 0.0
        scan_msg.intensities = [0.0] * self.NUM_SAMPLES
        
        #self.lidar_publisher.publish(scan_msg)


def main():
    rclpy.init()
    node = odompub()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
