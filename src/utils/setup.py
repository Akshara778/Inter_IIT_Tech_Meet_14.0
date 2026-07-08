from setuptools import setup
import os
from glob import glob

package_name = 'utils'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name] if os.path.isdir(package_name) else [],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maintainer',
    maintainer_email='you@todo.com',
    description='Auto-fixed ROS2 package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'encoder_reader = utils.encoder_reader:main',
            'motor_controller = utils.motor_controller:main',
            'leadscrew_controller = utils.leadscrew_controller:main',
            'lidar_processor = utils.lidar_processor:main',
	    'odom_pub = utils.odom_pub:main'
        ],
    },
)
