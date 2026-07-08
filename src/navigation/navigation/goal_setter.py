import rclpy
import os
import numpy as np
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool
from math import sin, cos, radians


'''
This node passes waypoints serially to the BT navigator of Nav2 and co-operates with the scanner node to stop for a finite time
until scanning is done. In case of emergency, this node cancels the task and halts any cmd_vel publishing, and starts from the current
task after operation resumes. 15 waypoints are passed in total with 10 being optimal waypoints for scanning.

Subscribers: /scan_flag, /move_flag

Publishers: /scan_flag (for notifying scanner node to start)


'''

class GoalSetter(Node):
    def __init__(self):
        super().__init__("goal_setter")
        #subscribe and publish to z-mechanism scan flag
        self.scan_flag_sub = self.create_subscription(Bool, "/scan_flag", self.get_flag, 10)
        #subsctibe to movement flag, for emergency stopping
        self.move = self.create_subscription(Bool, "/start_flag", self.move_bot, 10)
        self.scan_flag_pub = self.create_publisher(Bool, "/scan_flag", 10)
        #raise flag when no movement 
        self.cancelled_task = 0
        #optimal pos (x,y,theta)
        self.racks_pos = np.zeros((15, 3))
        self.rack_labels=[]
        #read from the txt file containing optimal rack positions for waypoints and also get their labels
        text_path = os.path.expanduser("~/rack_positions.txt")
        with open(text_path, "r") as file:
            for i, line in enumerate(file):
                parts = line.strip().split() 
                # "I" or "W" get the label   
                label = parts[0] 
                 # [x,y,yaw]
                coords = list(map(float, parts[1].split(','))) 

                self.rack_labels.append(label)
                self.racks_pos[i] = coords

        self.navigator = BasicNavigator()

        #updated by subscription to /start_flag
        self.move_flag = False

        #set initial pose
        self.initial_pose = self.add_waypoint([0.0, 0.0, 0.0])
        self.navigator.setInitialPose(self.initial_pose)
        self.navigator.waitUntilNav2Active()
        i = 0
        while i < 15:
            #when not moving keep cancelling task and raise the cancelled task flag
            if not self.move_flag:
                self.navigator.cancelTask()
                self.cancelled_task = 1
                self.get_logger().info("EMERGENCY STOP!!!")
            else:
                #when moving, if cancelled task flag is up, start from previous task since it wasn't reached
                if self.cancelled_task:
                    i -= 1
                    self.cancelled_task = 0
                #if not scanning, and moving, give  the next waypoint as a goal
                if not self.scan_flag:
                    waypoint = self.add_waypoint(self.racks_pos[i])
                    self.navigator.goToPose(waypoint)
                    i += 1
                #print waypoints during task execution
                while not self.navigator.isTaskComplete():
                    
                    feedback : NavigateToPose.Feedback = self.navigator.getFeedback()
                    if feedback is not None:
                        print(feedback)  

                #obtain the result of the task and log according to the result value
                #if not a waypoint dont raise scan flag
                result = self.navigator.getResult()
                if self.rack_labels[i]=="W":
                    if result == 0:
                        self.scan_flag = True
                        self.scan_flag_pub.publish(Bool(data = True))
                        self.get_logger().info("Succeeded")
                    else:
                        self.get_logger().info("Failed")

                    print(result)

    def get_flag(self, msg : Bool):
        self.scan_flag = msg.data

    def move_bot(self, msg : Bool):
        self.move_flag = msg.data
        

    #add a waypoint as a PoseStamped() message type
    def add_waypoint(self, position):
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = position[0]
        goal.pose.position.y = position[1]
        position[2] = radians(position[2])
        goal.pose.orientation.z = sin(position[2] / 2)
        goal.pose.orientation.w = cos(position[2] / 2)
        return goal
    
def main():
    rclpy.init()
    node = GoalSetter()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()