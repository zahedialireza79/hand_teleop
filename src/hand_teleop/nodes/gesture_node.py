"""
Made by: Alireza Zahedi
--------------------------
ROS 2 node that reads camera, detects hand gestures, and publishes:
  - /gesture/selected_joint (Int32)  → which motor to control (0-3)
  - /gesture/direction     (String)  → "UP", "DOWN", or "NONE"
  - /gesture/is_fist       (Bool)    → True if right hand is fist
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String, Bool

import cv2 as cv

from hand_teleop.gesture.finger_counter import FingerCounter
from hand_teleop.gesture.right_hand_tracker import RightHandTracker


class GestureNode(Node):
    def __init__(self):
        super().__init__("gesture_node")

        # Publishers declration
        self.pub_joint = self.create_publisher(Int32, '/gesture/selected_joint', 10)
        self.pub_fist = self.create_publisher(Bool, '/gesture/is_fist', 10)
        self.pub_dir   = self.create_publisher(String, '/gesture/direction', 10)

        # Main classes for the logic
        self.finger_counter     = FingerCounter()
        self.right_hand_tracker = RightHandTracker()
        
        # Open camera
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error("❌ Cannot open camera")
            raise RuntimeError("Camera failed to open")
        
        self.get_logger().info("📷 Camera opened successfully")
        
        # Selected motor state
        self.selected_motor = 0
        
        # Timer — process camera at ~30fps (33ms)
        self.create_timer(0.033, self.process_frame)
        
        self.get_logger().info("✅ Gesture node started")
        self.get_logger().info("   Publishing to:")
        self.get_logger().info("     /gesture/selected_joint")
        self.get_logger().info("     /gesture/direction")
        self.get_logger().info("     /gesture/is_fist")
