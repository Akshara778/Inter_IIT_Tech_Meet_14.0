import rclpy
from rclpy.node import Node
import cv2 as cv
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.cam_pub = self.create_publisher(Image, "/camera/image_raw", 10)

        self.bridge = CvBridge()

        self.cap = cv.VideoCapture(0)

        if not self.cap.isOpened():
            self.get_logger().error("Could not open camera")
            rclpy.shutdown()
            return
        
        self.timer = self.create_timer(1 / 30.0, self.timer_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warning("Failed to read frame")
            return
        
        img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")

        self.cam_pub.publish(img_msg)

    def destroy_node(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()



