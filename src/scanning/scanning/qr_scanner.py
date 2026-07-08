import rclpy
from rclpy.node import Node
import os
from sensor_msgs.msg import Image
from std_msgs.msg import Int32, Float32
from cv_bridge import CvBridge
import cv2 as cv
from pyzbar.pyzbar import decode

class QRScanner(Node):
    def __init__(self):
        super().__init__('qr_scanner')

        self.bridge = CvBridge()

        # Subscriptions
        self.create_subscription(Image, "/camera/image_raw", self.cam_callback, 10)
        self.create_subscription(Int32, "/scan_flag", self.flag_callback, 10)

        # Publishers
        self.vel_pub = self.create_publisher(Float32, "/scan_vel", 10)
        self.flag_pub = self.create_publisher(Int32, "/scan_status", 10)

        self.scan_flag = 1
        self.current_frame = None

        # Ensure qr_decode.txt is created inside your package
        self.file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "qr_decode.txt"
        )

        self.get_logger().info(f"Saving QR results to: {self.file_path}")

        self.timer = self.create_timer(0.03, self.timer_callback)

    def cam_callback(self, msg):
        self.current_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def flag_callback(self, msg):
        self.scan_flag = msg.data

    def timer_callback(self):
        if self.scan_flag != 1:
            return

        if self.current_frame is None:
            return

        # Try normal decode
        result = decode(self.current_frame)

        # Try grayscale if not found
        if not result:
            gray = cv.cvtColor(self.current_frame, cv.COLOR_BGR2GRAY)
            result = decode(gray)

        # Try adaptive threshold if still not found
        if not result:
            thresh = cv.adaptiveThreshold(
                gray, 255,
                cv.ADAPTIVE_THRESH_MEAN_C,
                cv.THRESH_BINARY,
                11, 2
            )
            result = decode(thresh)

        # Publish velocity always during scanning
        vel_msg = Float32()
        vel_msg.data = 0.02
        self.vel_pub.publish(vel_msg)
        if result:
            qr_data = result[0].data.decode("utf-8")
            self.get_logger().info(f"QR Detected: {qr_data}")
            #print("RESULT:", result)

            # Write to file
            with open(self.file_path, "a") as file:
                file.write(qr_data + "\n")

            # Publish done flag
            done = Int32()
            done.data = 2
            self.flag_pub.publish(done)

            self.scan_flag = 2  # stop scanning

def main():
    rclpy.init()
    node = QRScanner()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
