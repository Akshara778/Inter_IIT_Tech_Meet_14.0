#!/usr/bin/python3

import rclpy
import serial
import numpy as np
from rclpy.node import Node
from std_msgs.msg import Float32
import time


class LeadScrewController(Node):
    def __init__(self):
        super().__init__("leadscrew_controller")

        self.create_subscription(Float32, "/scan_vel", self.vel_callback, 10)

        self.ser = serial.Serial(
            port="/dev/ttyUSB0",
            baudrate=115200,
            timeout=0.1
        )

        self.current_vel = 0.0
        self.last_update = time.time()

        self.timer = self.create_timer(0.05, self.timer_callback)


    def vel_callback(self, msg):
        self.current_vel = msg.data
        self.last_update = time.time()

    def timer_callback(self):
        if time.time() - self.last_update > 0.5:
            cmd = "0.0\n"
        else:
            cmd = f"{self.current_vel:.3f}\n"

        try:
            self.ser.write(cmd.encode())
        except serial.SerialException:
            self.get_logger().error("Serial write failed")

    def destroy_node(self):
        if self.ser.is_open:
            self.ser.close()

        super().destroy_node()


def main(args=Node):
    rclpy.init()
    node = LeadScrewController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

