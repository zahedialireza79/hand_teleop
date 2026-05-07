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

    def process_frame(self):
        """"Called every 0.033 S = 30 FPS"""
        ret, frame = self.cap.read()
        if not ret:
            return
        
        frame = cv.flip(frame, 1) # Miror
        h, w, _ = frame.shape
        
        left_frame  = frame[:, : w//2]
        right_frame = frame[:, w//2 :]

        # ── LEFT HAND → finger count → motor selection ──
        fingers = self.finger_counter.count_fingers(frame)

        if fingers == 1:
            self.selected_motor = 1
        if fingers == 2:
            self.selected_motor = 2
        if fingers == 3:
            self.selected_motor = 3
        if fingers == 4:
            self.selected_motor = 4
        else:
            self.selected_motor = 0

        # ── RIGHT HAND → direction + fist ──
        cy, direction, is_fist = self.right_hand_tracker.update(frame)
        
        # ── VISUAL CALIBRATION LINE ──
        if self.right_hand_tracker.neutral_y is not None:
            cy_px = int(self.right_hand_tracker.neutral_y * h)
            cv.line(right_frame, (0, cy_px), (right_frame.shape[1], cy_px),
                    (255, 255, 0), 2)
            cv.putText(right_frame, "ZERO", (5, cy_px - 8),
                       cv.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)
        else:
            cv.putText(right_frame, "Press 'c' to calibrate", (10, h - 20),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 1)
        
        # ── UI LEFT ──
        cv.putText(left_frame, f"Motor : M{self.selected_motor}", (10, 40),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv.putText(left_frame, f"Fingers: {fingers}", (10, 80),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # ── UI RIGHT ──
        cv.putText(right_frame, f"Dir : {direction}", (10, 40),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv.putText(right_frame, f"Fist: {is_fist}", (10, 80),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 200), 2)
        
        # ── COMBINE AND SHOW ──
        combined = cv.hconcat([left_frame, right_frame])
        cv.imshow("Gesture Teleoperation", combined)
        
        # ── KEY HANDLING ──
        key = cv.waitKey(1) & 0xFF
        
        if key == ord('c'):
            if cy is not None:
                self.right_hand_tracker.calibrate(cy)
                self.get_logger().info(f"✅ Calibrated at cy={cy:.3f}")
            else:
                self.get_logger().warn("⚠️  No hand detected — show right hand first")
        
        if key == ord('q'):
            self.get_logger().info("🛑 'q' pressed — shutting down node")
            rclpy.shutdown()  


        msg_joint = Int32()
        msg_joint.data = self.selected_motor
        self.pub_joint.publish(msg_joint)

        msg_dir = String()
        msg_dir.data = direction
        self.pub_dir.publish(msg_dir)
        
        msg_fist = Bool()
        msg_fist.data = is_fist
        self.pub_fist.publish(msg_fist)

    def destroy_node(self):
        """Clean up camera on shutdown."""
        self.cap.release()
        cv.destroyAllWindows()
        self.get_logger().info("🔌 Camera released")
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = GestureNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
 
 
if __name__ == '__main__':
    main()