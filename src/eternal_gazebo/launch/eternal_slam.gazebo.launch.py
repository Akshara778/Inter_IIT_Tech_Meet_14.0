#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import numpy as np


def generate_launch_description():

    package_name_gazebo = 'eternal_gazebo'
    package_name_description = 'eternal_description'
    package_name_bringup = 'eternal_bringup'
    package_name_localization = 'eternal_localization'

    default_robot_name = 'rosmaster_x3'
    gazebo_models_path = 'models'
    default_world_file = 'arena_obs.world'
    gazebo_worlds_path = 'worlds'
    ros_gz_bridge_config_file_path = 'config/ros_gz_bridge.yaml'
    rviz_config_filename = 'rviz_for_slam.rviz'

    pkg_ros_gz_sim = FindPackageShare(package='ros_gz_sim').find('ros_gz_sim')
    pkg_share_gazebo = FindPackageShare(package=package_name_gazebo).find(package_name_gazebo)
    pkg_share_description = FindPackageShare(package=package_name_description).find(package_name_description)
    pkg_share_bringup = FindPackageShare(package=package_name_bringup).find(package_name_bringup)
    pkg_share_localization = FindPackageShare(package=package_name_localization).find(package_name_localization)

    default_ros_gz_bridge_config_file_path = os.path.join(pkg_share_gazebo, ros_gz_bridge_config_file_path)
    default_rviz_config_path = PathJoinSubstitution([pkg_share_gazebo, 'rviz', rviz_config_filename])
    gazebo_models_path = os.path.join(pkg_share_gazebo, gazebo_models_path)

    # Launch configs
    enable_odom_tf = LaunchConfiguration('enable_odom_tf')
    headless = LaunchConfiguration('headless')
    jsp_gui = LaunchConfiguration('jsp_gui')
    load_controllers = LaunchConfiguration('load_controllers')
    robot_name = LaunchConfiguration('robot_name')
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    use_rviz = LaunchConfiguration('use_rviz')
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_file = LaunchConfiguration('world_file')

    world_path = PathJoinSubstitution([pkg_share_gazebo, gazebo_worlds_path, world_file])

    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    # args
    declare_enable_odom_tf_cmd = DeclareLaunchArgument(
        name='enable_odom_tf', default_value='true',
        choices=['true', 'false'],
        description='Whether to enable odometry transform broadcasting')

    declare_headless_cmd = DeclareLaunchArgument(
        name='headless', default_value='False',
        description='Whether to execute gzclient')

    declare_robot_name_cmd = DeclareLaunchArgument(
        name='robot_name', default_value=default_robot_name)

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        name='rviz_config_file', default_value=default_rviz_config_path)

    declare_load_controllers_cmd = DeclareLaunchArgument(
        name='load_controllers', default_value='true')

    declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
        name='use_robot_state_pub', default_value='true')

    declare_jsp_gui_cmd = DeclareLaunchArgument(
        name='jsp_gui', default_value='false')

    declare_use_rviz_cmd = DeclareLaunchArgument(
        name='use_rviz', default_value='true')

    declare_use_gazebo_cmd = DeclareLaunchArgument(
        name='use_gazebo', default_value='true')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time', default_value='true')

    declare_world_cmd = DeclareLaunchArgument(
        name='world_file', default_value=default_world_file)

    declare_x_cmd = DeclareLaunchArgument('x', default_value='0.0')
    declare_y_cmd = DeclareLaunchArgument('y', default_value='0.0')
    declare_z_cmd = DeclareLaunchArgument('z', default_value='0.40')
    declare_roll_cmd = DeclareLaunchArgument('roll', default_value='0.0')
    declare_pitch_cmd = DeclareLaunchArgument('pitch', default_value='0.0')
    declare_yaw_cmd = DeclareLaunchArgument('yaw', default_value='3.14')

    #rsp
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_share_description, 'launch', 'robot_state_publisher.launch.py')
        ]),
        condition=IfCondition(use_robot_state_pub),
        launch_arguments={
            'enable_odom_tf': enable_odom_tf,
            'jsp_gui': jsp_gui,
            'rviz_config_file': rviz_config_file,
            'use_rviz': use_rviz,
            'use_gazebo': use_gazebo,
            'use_sim_time': use_sim_time
        }.items()
    )
    #ros2 controllers - mecanum and js drive
    load_controllers_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_share_bringup, 'launch', 'load_ros2_controllers.launch.py')
        ]),
        condition=IfCondition(load_controllers),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    #gz sim
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', gazebo_models_path)
    
    ekf_launch_file = os.path.join(pkg_share_localization, 'launch/ekf_gazebo.launch.py')
    ekf_config_file = os.path.join(pkg_share_localization, 'config/ekf.yaml')
    start_ekf_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ekf_launch_file]),
        launch_arguments={
            'ekf_config_file': ekf_config_file,
            'use_sim_time': use_sim_time
        }.items()
    )

    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments=[('gz_args', [' -r -s -v 4 ', world_path])]
    )

    start_gazebo_client_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        condition=IfCondition(PythonExpression(['not ', headless])),
        launch_arguments={'gz_args': ['-g ']}.items()
    )

    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': default_ros_gz_bridge_config_file_path}],
        output='screen'
    )

    start_gazebo_ros_image_bridge_cmd = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/cam_1/image'],
        remappings=[('/cam_1/image', '/cam_1/color/image_raw')]
    )

    start_gazebo_ros_spawner_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/robot_description',
            '-name', robot_name,
            '-allow_renaming', 'true',
            '-x', x, '-y', y, '-z', z,
            '-R', roll, '-P', pitch, '-Y', yaw
        ]
    )

    pkg_nav2 = FindPackageShare(package='nav2_bringup').find('nav2_bringup')
    pkg_slam = FindPackageShare(package='slam_toolbox').find('slam_toolbox')
    slam_param_file=os.path.join(pkg_share_gazebo,'params/slam_params.yaml')
    # Launch Nav2
    nav2_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [pkg_nav2, '/launch/navigation_launch.py']
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items()
    )

    # Launch SLAM Toolbox
    slam_toolbox_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [pkg_slam, '/launch/online_async_launch.py']
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam_params_file': slam_param_file,
        }.items()
    )

    #ld launching
    ld = LaunchDescription()
    ld.add_action(declare_enable_odom_tf_cmd)
    ld.add_action(declare_headless_cmd)
    ld.add_action(declare_robot_name_cmd)
    ld.add_action(declare_rviz_config_file_cmd)
    ld.add_action(declare_jsp_gui_cmd)
    ld.add_action(declare_load_controllers_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_use_gazebo_cmd)
    ld.add_action(declare_use_robot_state_pub_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_world_cmd)

    ld.add_action(declare_x_cmd)
    ld.add_action(declare_y_cmd)
    ld.add_action(declare_z_cmd)
    ld.add_action(declare_roll_cmd)
    ld.add_action(declare_pitch_cmd)
    ld.add_action(declare_yaw_cmd)

    ld.add_action(set_env_vars_resources)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(load_controllers_cmd)
    #ld.add_action(start_ekf_cmd)
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(start_gazebo_client_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(start_gazebo_ros_image_bridge_cmd)
    ld.add_action(start_gazebo_ros_spawner_cmd)
    #ld.add_action(nav2_launch_cmd)
    ld.add_action(slam_toolbox_launch_cmd)
    #ld.add_action(pub_cmd_vel)

    return ld
