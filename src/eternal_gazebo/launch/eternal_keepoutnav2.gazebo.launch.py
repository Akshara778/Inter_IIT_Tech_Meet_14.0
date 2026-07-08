#!/usr/bin/env python3

import os
import numpy as np
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


def generate_launch_description():

    package_name_gazebo = 'eternal_gazebo'
    package_name_description = 'eternal_description'
    package_name_bringup = 'eternal_bringup'
    package_name_navigation = 'navigation'

    default_robot_name = 'rosmaster_x3'
    gazebo_models_path = 'models'
    default_world_file = 'arena_obs.world'
    gazebo_worlds_path = 'worlds'
    rviz_config_filename = 'rviz_for_nav.rviz'

    pkg_share_gazebo = FindPackageShare(package=package_name_gazebo).find(package_name_gazebo)
    pkg_share_description = FindPackageShare(package=package_name_description).find(package_name_description)
    pkg_share_bringup = FindPackageShare(package=package_name_bringup).find(package_name_bringup)
    pkg_share_navigation = FindPackageShare(package=package_name_navigation).find(package_name_navigation)

    default_rviz_config_path = PathJoinSubstitution([pkg_share_gazebo, 'rviz', rviz_config_filename])
    gazebo_models_path = os.path.join(pkg_share_gazebo, gazebo_models_path)

    # Launch configs
    autostart = LaunchConfiguration('autostart')
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
    use_composition = LaunchConfiguration('use_composition')

    # args

    declare_autostart_cmd = DeclareLaunchArgument(
        name='autostart',
        default_value='true',
        description='Automatically startup the Nav2 stack')
    declare_enable_odom_tf_cmd = DeclareLaunchArgument(
        name='enable_odom_tf', default_value='true',
        choices=['true', 'false'],
        description='Whether to enable odometry transform broadcasting')

    declare_headless_cmd = DeclareLaunchArgument(
        name='headless', default_value='true',
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
        name='use_gazebo', default_value='false')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time', default_value='false')

    declare_world_cmd = DeclareLaunchArgument(
        name='world_file', default_value=default_world_file)
    
    declare_composition = DeclareLaunchArgument(
        name='use_composition', default_value='True')


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
    #load_controllers_cmd = IncludeLaunchDescription(
    #    PythonLaunchDescriptionSource([
    #        os.path.join(pkg_share_bringup, 'launch', 'load_ros2_controllers.launch.py')
    #    ]),
    #    condition=IfCondition(load_controllers),
    #    launch_arguments={'use_sim_time': use_sim_time}.items()
    #)



    pkg_nav2 = FindPackageShare(package='nav2_bringup').find('nav2_bringup')
    pkg_slam = FindPackageShare(package='slam_toolbox').find('slam_toolbox')

    # Launch Nav2
    nav2_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [pkg_nav2, '/launch/bringup_launch.py']
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map': os.path.join(pkg_share_bringup, os.path.expanduser('/home/team89/eternal-ros-architecture/src/navigation/navigation/arena.yaml')),
            'params_file': os.path.join(pkg_share_navigation, 'config/nav2_params.yaml'),
            'use_composition': use_composition,
            'autostart': autostart
        }.items()
    )


    start_lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_costmap_filters',
        output='screen',
        emulate_tty=True,
        parameters=[{'use_sim_time': use_sim_time},
                    {'autostart': True},
                    {'node_names': ['filter_mask_server', 'costmap_filter_info_server']}])
    
    params_file = os.path.join(pkg_share_navigation, 'config/nav2_params.yaml')

    start_map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        name='filter_mask_server',
        output='screen',
        emulate_tty=True,
        parameters=[params_file])

    start_costmap_filter_info_server_cmd = Node(
        package='nav2_map_server',
        executable='costmap_filter_info_server',
        name='costmap_filter_info_server',
        output='screen',
        emulate_tty=True,
        parameters=[params_file])


    #ld launching
    ld = LaunchDescription()
    ld.add_action(declare_autostart_cmd)
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
    ld.add_action(declare_composition)


    ld.add_action(robot_state_publisher_cmd)
    #ld.add_action(load_controllers_cmd)

    ld.add_action(nav2_launch_cmd)
    ld.add_action(start_lifecycle_manager_cmd)
    ld.add_action(start_map_server_cmd)
    ld.add_action(start_costmap_filter_info_server_cmd)  


    return ld
