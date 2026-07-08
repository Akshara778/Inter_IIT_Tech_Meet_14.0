============================================================
TEAM89 ETERNAL PS – FINAL SUBMISSION README
============================================================
LEADSCREW DRIVEN OMNIDIRECTIONAL WAREHOUSE BOT
============================================================
1. PROJECT OVERVIEW
============================================================

This repository contains the complete technical, software, and hardware 
documentation for the autonomous warehouse robot developed by Team 89.

============================================================
2. DIRECTORY STRUCTURE
============================================================

Team89_WarehouseRobot_Submission/
|
|__ 01_TECHNICAL_DOCUMENTATION/
|     - Complete system design
|     - Software & control architecture
|     - Algorithms used for navigation and scanning
|     - User Manual Details and Maintenance 
|
|__ 02_CODE_REPOSITORY/
|     |__ README.md
|     |__ navigation/
|     |__ scanning/
|     |__ hmi/
|     |__ utils/
|     |__ teleop_controller.py
|
|__ 03_HARDWARE/
|     |__ BOM_Itemized.csv / Table
|     |__ Videos/
|     |__ Electrical_Schematics/
|     |__ PCB_Gerbers/ (If fabricated)
|     |__ CAD_Models/ (3D parts + assembly drawings)
|
|__ README_SUBMISSION.txt   (This file)

============================================================
3. SOFTWARE STACK SUMMARY
============================================================

Operating System   : Ubuntu 24.04 Raspi5
Middleware         : ROS 2 Jazzy
Programming Lang   : Python
Simulation         : Gazebo / RViz2
Version Control    : Git
Build System       : colcon + CMake (ament_cmake)

Key ROS 2 Packages:
- rclpy
- nav2
- slam_toolbox
- geometry_msgs, sensor_msgs, nav_msgs
- tf2_ros
- lifecycle nodes
- joy

Other Packages:
- matplotlib
- opencv cv2
- pyzbar
- pyserial
============================================================
4. FUNCTIONAL MODULE DESCRIPTION
============================================================

----------------------------------------
4.1 NAVIGATION MODULE
----------------------------------------
Location:
02_CODE_REPOSITORY/navigation/

Features:
- Autonomous waypoint navigation
- Obstacle-aware motion planning
- Integration with SLAM & localization using goal_setter.py and keepout_filter.py
- Holonomic/mecanum drive support

Uses:
- /cmd_vel        (geometry_msgs/Twist)
- /odom           (nav_msgs/Odometry)
- /map            (nav_msgs/OccupancyGrid)
- /scan           (sensor_msgs/LaserScan)
- /scan_flag      (Bool)-->This is for z-mechanism
- /start_flag     (Bool)-->From watchdog.

----------------------------------------
4.2 SCANNING MODULE
----------------------------------------

Location:
02_CODE_REPOSITORY/scanning/

Features:
- Real-time sensor scanning
- Height and clearance mapping
- Obstacle contour detection
- Rack edge extraction

Key Topics:
- /scan_flag      (Int32)
- /cam            (Image)

----------------------------------------
4.3 HMI MODULE
----------------------------------------
Location:
02_CODE_REPOSITORY/hmi/

Features:
- Rviz config files
teleop/
-teleop_controller.py
rviz/
- rviz_for_nav.rviz
- rviz_for_slam.rviz

----------------------------------------
4.4 UTILS MODULE
----------------------------------------
Location:
02_CODE_REPOSITORY/utils/

Features:
- encoder_reader.py
- leadscrew_controller.py
- motor_controller.py

----------------------------------------
4.5 LAUNCH MODULE
----------------------------------------
Location:
02_CODE_REPOSITORY/navigation/launch/

-navigation.launch.py
-slam.launch.py





============================================================
5. HARDWARE DOCUMENTATION CONTENTS
============================================================

----------------------------------------
5.1 BILL OF MATERIAL (BOM)
----------------------------------------
Location:
03_HARDWARE/BOM_Itemized.csv

Includes:
- Motor specifications
- Motor drivers
- Batteries
- Sensors
- Controllers
- PCBs
- Mechanical components

----------------------------------------
5.2 ELECTRICAL SCHEMATICS
----------------------------------------
Location:
03_HARDWARE/Electrical_Schematics/

Includes:
- Power distribution diagram
- Motor driver wiring
- Sensor wiring
- MCU pin mappings

----------------------------------------
5.3 PCB GERBER FILES
----------------------------------------
Location:
03_HARDWARE/PCB_Gerbers/

Includes:
- Fabrication-ready Gerber files
- Drill files
- Pick-and-place data

----------------------------------------
5.4 CAD MODELS
----------------------------------------
Location:
03_HARDWARE/CAD_Models/

Includes:
- Individual part models
- Full robot assembly
- Manufacturing drawings
- Exploded assembly views

----------------------------------------
5.5 VIDEOS
----------------------------------------
Location:
03_HARDWARE/Videos/

Includes:
- Simulation demos
- Hardware testing
- Navigation trials
- System integration tests


============================================================
6. BUILD & RUN INSTRUCTIONS
============================================================

1. Clone Repository:
   git clone <repo_url>
   cd 02_CODE_REPOSITORY

2. Build:
   colcon build

3. Source:
   source install/setup.bash

4. Launch Full System:
   ros2 launch navigation navigation.launch.py

5. Simulation:
   ros2 launch navigation slam.launch.py

============================================================
7. SYSTEM SAFETY FEATURES
============================================================

- Emergency stop through HMI
- Velocity saturation in controller
- Obstacle proximity stop

============================================================
8. PERFORMANCE CAPABILITIES
============================================================

- Autonomous navigation in narrow aisles
- Keepout zone navigation
- Real-time obstacle detection
- Modular expandability
- Simulation-to-hardware transfer readiness


