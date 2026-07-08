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

    rviz_launch_file = os.path.join(
        get_package_share_directory('eternal_gazebo'),
        'launch',
        'eternal_keepoutnav2.gazebo.launch.py'
    )


    bash_file = os.path.join(
        os.environ['HOME'],
        'eternal-ros-architecture',
        'nav2lifecycle.sh'
    )

    keepout_filter = Node(
        package = "navigation",
        executable = "keepout_filter",
        parameters=[{
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

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rviz_launch_file),
        launch_arguments={
            'rviz_config_file': rviz_config_file,
        }.items()
    )

    lifecycle = TimerAction(
        period=10.0,
        actions=[
            ExecuteProcess(
                cmd = ['bash', bash_file],
                output = 'screen'
            )
        ]
    )


    return LaunchDescription([
        
        keepout_filter,

        RegisterEventHandler(
            OnProcessExit(
                target_action = keepout_filter,
                on_exit = [
                    encoder_reader,
                    motor_controller,
                    leadscrew_controller,
                    qr_scanner,
                    camera_launch,
                    goal_setter,
                    lidar,
                    nav2,
		    lidar_processor,
                    lifecycle
                ]
            )
        )
    ])



    
