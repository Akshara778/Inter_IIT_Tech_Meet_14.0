import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, ExecuteProcess, TimerAction
from launch.event_handlers import OnProcessExit
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
    # --- 1. Define Launch Arguments and Package Shares ---
    
    # Arguments for Nav2
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    autostart = LaunchConfiguration('autostart', default='true')
    use_composition = LaunchConfiguration('use_composition', default='True')
    enable_odom_tf = LaunchConfiguration('enable_odom_tf', default = 'true')
    jsp_gui =LaunchConfiguration('jsp_gui', default = 'false')
    
    # Package directories
    pkg_nav2 = get_package_share_directory('nav2_bringup')
    pkg_share_bringup = get_package_share_directory('eternal_gazebo') # Assuming this package holds the map file
    pkg_share_navigation = get_package_share_directory('navigation') # Assuming this package holds nav2_params.yaml
    pkg_share_description = get_package_share_directory('eternal_description')

    # --- 2. Define Existing Components ---

    lidar_launch_file = os.path.join(
        get_package_share_directory('ldlidar_node'),
        'launch',
        'ldlidar_with_mgr.launch.py'
    )

    rviz_config_file = os.path.join(
        get_package_share_directory('hmi'),
        'rviz',
        'rviz_for_nav.rviz'
    )

    camera_pkg = get_package_share_directory('camera_ros')


    bash_file = os.path.join(
        os.environ['HOME'],
        'eternal-ros-architecture',
        'nav2lifecycle.sh'
    )

    keepout_filter = Node(
        package = "navigation",
        executable = "keepout_filter",
        parameters=[{
        # NOTE: The path for arena_file should be checked against the path in nav2_launch_cmd's map argument.
        'arena_file': os.path.expanduser('/home/team89/eternal-ros-architecture/src/navigation/navigation/arena.yaml') 
    }]
    )

    encoder_reader = Node(
        package = "utils",
        executable = "encoder_reader"
    )

    motor_controller = Node(
        package = "utils",
        executable = "motor_controller"
    )

    leadscrew_controller = Node(
        package = "utils",
        executable = "leadscrew_controller"
    )

    qr_scanner = Node(
        package = "scanning",
        executable = "qr_scanner"  
    )

    goal_setter = Node(
        package = "navigation",
        executable = "goal_setter"
    )

    lidar_processor = Node(
    package = "utils",
    executable = "lidar_processor"
    )

    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_file)
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(camera_pkg, 'launch', 'camera.launch.py')
        )
    )

    lifecycle_bash = TimerAction(
        period=10.0,
        actions=[
            ExecuteProcess(
                cmd = ['bash', bash_file],
                output = 'screen'
            )
        ]
    )

    # --- 3. Define New Nav2 Components ---

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_share_description, 'launch', 'robot_state_publisher.launch.py')
        ]),
        launch_arguments={
            'enable_odom_tf': enable_odom_tf,
            'jsp_gui': jsp_gui,
            'use_sim_time': use_sim_time
        }.items()
    )
    
    # Launch Nav2 (main navigation stack)
    nav2_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [pkg_nav2, '/launch/bringup_launch.py']
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            # NOTE: Assuming map is in the bringup package share, but the path is an absolute path
            'map': os.path.join(pkg_share_bringup, os.path.expanduser('/home/team89/eternal-ros-architecture/src/navigation/navigation/arena.yaml')), 
            'params_file': os.path.join(pkg_share_navigation, 'config/nav2_params.yaml'),
            'use_composition': use_composition,
            'autostart': autostart
        }.items()
    )

    params_file = os.path.join(pkg_share_navigation, 'config/nav2_params.yaml')

    # Map Server for Keepout Mask
    start_map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        name='filter_mask_server',
        output='screen',
        emulate_tty=True,
        parameters=[params_file]
    )

    # Costmap Filter Info Server
    start_costmap_filter_info_server_cmd = Node(
        package='nav2_map_server',
        executable='costmap_filter_info_server',
        name='costmap_filter_info_server',
        output='screen',
        emulate_tty=True,
        parameters=[params_file]
    )

    # Lifecycle Manager for Keepout Components
    start_lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_costmap_filters',
        output='screen',
        emulate_tty=True,
        parameters=[{'use_sim_time': use_sim_time},
                    {'autostart': True},
                    {'node_names': ['filter_mask_server', 'costmap_filter_info_server']}]
    )

    # --- 4. Return Launch Description ---

    return LaunchDescription([
        # 1. Declare Launch Arguments
        DeclareLaunchArgument('use_sim_time', default_value='false', description='Use simulation (Gazebo) clock if true'),
        DeclareLaunchArgument('autostart', default_value='true', description='Automatically start the navigation stack'),
        DeclareLaunchArgument('use_composition', default_value='False', description='Use component manager to compose nodes'),
        DeclareLaunchArgument('jsp_gui', default_value = 'false'),
        DeclareLaunchArgument('enable_odom_tf', default_value = 'true'),
        # 2. Add New Nav2 Components (Need to start before keepout_filter to ensure map server is ready)
        # Note: Nav2 nodes are started by nav2_launch_cmd, but map filter-related nodes are started separately here.
        robot_state_publisher_cmd,
        lidar,
        lidar_processor,
        nav2_launch_cmd,
        start_lifecycle_manager_cmd,
        start_map_server_cmd,
        start_costmap_filter_info_server_cmd,
        
        # 3. Existing Keepout Filter Node
        keepout_filter,

        # 4. Existing Event Handler for dependent nodes
        RegisterEventHandler(
            OnProcessExit(
                target_action = keepout_filter,
                on_exit = [
                    #encoder_reader,
                    #motor_controller,
                    #leadscrew_controller,
                    #qr_scanner,
                    #camera_launch,
                    #goal_setter,

                    lifecycle_bash
                ]
            )
        )
    ])
