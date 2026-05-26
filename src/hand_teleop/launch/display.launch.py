import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # Path to the URDF file
    urdf_path = os.path.join(
        get_package_share_directory('hand_teleop'),
        'urdf',
        'arm.urdf'
    )

    # Read the URDF file content
    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([

        # robot_state_publisher — reads URDF and publishes TF frames
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),

        # joint_state_publisher_gui — slider GUI to move joints manually
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
        ),

        # rviz2 — visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
        ),
    ])
