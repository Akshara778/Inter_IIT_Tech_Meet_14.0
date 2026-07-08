import rclpy
from rclpy.node import Node 
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
from sensor_msgs.msg import Joy
from nav2_msgs.srv import SaveMap
import os
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import Bool


class TeleopController(Node):

    '''
    This node is used for controlling the bot through a joystick during the mapping phase of SLAM.
    Publishers: /cmd_vel, /scan_vel
    Subscribers: /joy
    Clients: /map_saver/save_map
    The node is lauched with the joy node.
    It reads the axes and button data from the /joy topic and converts it into required velocities.
    Also, a button is configured such that on pressing it for 5 seconds, it saves the map
    '''

    def __init__(self):
        super().__init__("teleop_controller")
        #declaring the required publishers and clients
        self.controller_sub = self.create_subscription(Joy, "/joy", self.publish_vel, 10)
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.vel_z = self.create_publisher(Float32, "/scan_vel", 10)
        self.map_saver = self.create_client(SaveMap,"/map_saver/save_map")
        self.stop_bot_pub = self.create_publisher(Bool,"/start_flag",10)
        #initializing variables used
        self.max_val = 1
        self.max_speed_linear = 0.05
        self.max_speed_angular = 0.025
        self.max_speed_z = 0.001
        self.save_start_time = 0
        self.save_end_time = 0
        self.button_prev_state = 0      

    
    def publish_vel(self, msg : Joy):
        #publishing the linear and angular velocites of the bot
        vel = Twist()
        vel.linear.x = (msg.axes[1] / self.max_val) * self.max_speed_linear
        vel.linear.y = -(msg.axes[0] / self.max_val) * self.max_speed_linear
        vel.angular.z = -(msg.axes[2] / self.max_val) * self.max_speed_angular

        #publishing the velocity for the z mechanism
        z_vel = Float32()
        z_vel.data = (msg.axes[7] / self.max_val) * self.max_speed_z

        #checking the button state for the saving of map generated
        if msg.buttons[4] == 1 and self.button_prev_state == 0:
            self.save_start_time = self.get_clock().now().to_msg().sec
        elif msg.buttons[4] == 1 and self.button_prev_state == 1:
            self.save_end_time = self.get_clock().now().to_msg().sec
        elif msg.buttons[4] == 0 and self.button_prev_state == 1:
            #map is saved if button was pressed for longer than 5 seconds
            if (self.save_end_time - self.save_start_time) > 5.0:
                req = SaveMap().Request()
                req.map_topic = "/map"
                req.map_url = os.path.join(get_package_share_directory("navigation3"), "navigation", "arena")
                req.image_format = "pgm"
                req.map_mode = "trinary"
                self.map_saver.call_async(request = req)
                self.get_logger().info("Map Saved to {}".format(req.map_url))
                self.destroy_node()
                rclpy.shutdown()

        #update the previous state for button 4
        self.button_prev_state = msg.buttons[4]

        #button 3 for emergency stop, destroys node.
        if(msg.buttons[3]==1):
            vel.linear.x = 0.0
            vel.linear.y = 0.0
            vel.angular.z = 0.0
            z_vel.data = 0.0
            msg=Bool()
            msg.data=False
            self.stop_bot_pub.publish(msg)
            self.destroy_node()
            rclpy.shutdown()
        #regular motion, bot movement flag is true
        msg=Bool()
        msg.data=True
        self.stop_bot_pub.publish(msg)

        self.vel_pub.publish(vel)
        self.vel_z.publish(z_vel)

def main():
    rclpy.init()
    node = TeleopController()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()