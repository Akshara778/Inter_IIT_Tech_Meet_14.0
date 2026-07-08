# mask_server_launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node




def generate_launch_description():
    yaml_filename = LaunchConfiguration('yaml_filename')
    use_sim_time = LaunchConfiguration('use_sim_time')


    declare_yaml_arg = DeclareLaunchArgument(
    'yaml_filename',
    description='Full path to keepout mask YAML file'
    )


    declare_sim_arg = DeclareLaunchArgument(
    'use_sim_time',
    default_value='true'
    )


    mask_server = Node(
    package='nav2_map_server',
    executable='map_server',
    name='keepout_filter_mask_server',
    output='screen',
    parameters=[
    yaml_filename,
    {'use_sim_time': use_sim_time}
    ]
    )


    return LaunchDescription([
    declare_yaml_arg,
    declare_sim_arg,
    mask_server
    ])