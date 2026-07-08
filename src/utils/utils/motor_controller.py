import rclpy
import serial
import numpy as np
import struct
from math import sqrt
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32


class motor_controller(Node):
    def __init__(self):
        super().__init__("motor_controller")
        self.wheel_vel = self.create_subscription(Twist, '/cmd_vel', self.callback_wheel_vel, 10)
        self.w = 0.4
        self.l = 0.6
        self.wheel_speeds = np.array([0.0, 0.0, 0.0, 0.0])
        self.z_height = 0.0
        self.start = b'\xAA'
        self.end = b'\x55'


        self.esp32 = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.05)
        self.timer = self.create_timer(0.05, self.send_msg)
        
    def callback_wheel_vel(self, msg: Twist):

        self.wheel_speeds = (msg.linear.x * (sqrt(2) / 4) * np.array([-1.0, -1.0, 1.0, 1.0])) - (msg.linear.y * (sqrt(2) / 4) * np.array([1.0, -1.0, -1.0, 1.0])) + (msg.angular.z * (1 / (4 * sqrt(2) * ((1 / self.w) - (1 / self.l)))) * np.array([-1.0, 1.0, -1.0, 1.0]))
        self.wheel_speeds = 10000*self.wheel_speeds * 50 / 255

    def send_msg(self):
        #message = self.start + struct.pack('<ffff', 1, 356, 87, 67.967) + self.end
        message = self.start + struct.pack('<ffff', self.wheel_speeds[0], self.wheel_speeds[1], self.wheel_speeds[2], self.wheel_speeds[3]) + self.end
        self.get_logger().info(f"Message: {message}. Speeds = {self.wheel_speeds}")
        self.esp32.write(message)


def main():
    rclpy.init()
    node = motor_controller()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()