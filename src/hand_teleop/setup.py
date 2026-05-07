from setuptools import find_packages, setup

package_name = 'hand_teleop'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    # include the mediapipe model file
    (f'lib/python3.12/site-packages/{package_name}/gesture',
        ['hand_teleop/gesture/hand_landmarker.task']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your@email.com',
    description='Hand gesture teleoperation for robot arm control',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gesture_node = nodes.gesture_node:main',
            'arm_controller_node = nodes.arm_controller_node:main',
        ],
    },
)