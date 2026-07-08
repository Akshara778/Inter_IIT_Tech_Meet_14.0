import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription
)
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression


def generate_launch_description():

    lidar_launch_file = os.path.join(
        get_package_share_directory('ldlidar_node'),
        'launch',
        'ldlidar_with_mgr.launch.py'
    )

    slam_launch_file = os.path.join(
        get_package_share_directory('slam_toolbox'),
        'launch',
        'online_async_launch.py'
    )

    slam_param_file = os.path.join(
        get_package_share_directory('navigation'),
        'config',
        'slam_params.yaml'
    )

    rviz_config_file = os.path.join(
        get_package_share_directory('hmi'),
        'rviz',
        'rviz_for_slam.rviz'
    )


    rviz_launch_file = os.path.join(
        get_package_share_directory('eternal_gazebo'),
        'launch',
        'eternal.gazebo.launch.py'
    )


    return LaunchDescription([
        Node(
            package = "utils",
            executable = "encoder_reader"
        ),

        Node(
            package = "utils",
            executable = "motor_controller"
        ),

        Node(
            package = "utils",
            executable = "leadscrew_controller"
        ),

        Node(
            package = "navigation",
            executable = "teleop_controller"
        ),

        Node(
            package = "joy",
            executable = "joy_node"
        ),

        Node(
            package = "utils",
            executable = "lidar_processor"
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar_launch_file)
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_file),
            launch_arguments={
                'params_file': slam_param_file,
            }.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(rviz_launch_file),
            launch_arguments={
                'rviz_config_file': rviz_config_file,
            }.items()
        )


    ])