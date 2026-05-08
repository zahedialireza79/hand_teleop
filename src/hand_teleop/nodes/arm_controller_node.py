#!/usr/bin/env python3
"""
arm_controller_node.py
----------------------
ROS 2 node that subscribes to gesture topics and drives the robot arm.

Subscribes to:
  - /gesture/selected_joint (Int32)  → which motor to control (1-4)
  - /gesture/direction     (String)  → "UP", "DOWN", or "NONE"
  - /gesture/is_fist       (Bool)    → True if right hand is fist

Flow:
  1. On startup: scan motors, calibrate each one interactively
  2. On fist + direction: step the selected motor
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String, Bool

from hand_teleop.controller.motor_bus import MotorBus
from hand_teleop.controller.motor_controller import Motor
from hand_teleop.controller.motor_id_search import MotorIDSearch


class ArmControllerNode(Node):
    def __init__(self):
        super().__init__('arm_controller_node')

        # ── State from gesture node ──
        self.selected_joint = 1       # motor ID (1-4)
        self.direction      = "NONE"
        self.is_fist        = False

        # ── Connect to motors ──
        PORT = "/dev/ttyACM0"

        self.get_logger().info(f"🔌 Connecting to motors on {PORT}...")
        self.bus = MotorBus(port=PORT)

        # Scan for motor IDs
        scanner   = MotorIDSearch(PORT)
        found_ids = scanner.scan()

        if not found_ids:
            self.get_logger().error("❌ No motors found — check USB connection")
            raise RuntimeError("No motors found")

        self.get_logger().info(f"✅ Found motors: {found_ids}")

        # Initialize one Motor per ID
        self.motors = {}
        for m_id in found_ids:
            self.motors[m_id] = Motor(bus=self.bus, motor_id=m_id, name=f"motor_{m_id}")
            self.get_logger().info(f"⚙️  Motor {m_id} initialized")

        # ── Calibrate all motors ──
        self.get_logger().info("\n🚀 Starting calibration for all motors...")
        for m_id, motor in self.motors.items():
            self.get_logger().info(f"\n▶️  Calibrating motor_{m_id}...")
            calibrated = False
            while not calibrated:
                calibrated = motor.calibrate()
                if not calibrated:
                    retry = input(f"Retry calibration for motor_{m_id}? (y/n): ").strip().lower()
                    if retry != 'y':
                        raise RuntimeError(f"Calibration aborted for motor_{m_id}")

            self.get_logger().info(f"✅ motor_{m_id} ready")

        self.get_logger().info("\n✨ All motors calibrated!")

        # ── Subscribers ──
        self.create_subscription(Int32,  '/gesture/selected_joint', self.cb_joint, 10)
        self.create_subscription(String, '/gesture/direction',      self.cb_dir,   10)
        self.create_subscription(Bool,   '/gesture/is_fist',        self.cb_fist,  10)

        self.get_logger().info("✅ Arm controller node started — listening for gestures")

    # ── Callbacks ─────────────────────────────────────────────────────────

    def cb_joint(self, msg: Int32):
        """Update selected motor ID from gesture node."""
        if msg.data in self.motors:
            self.selected_joint = msg.data

    def cb_dir(self, msg: String):
        """Update direction from gesture node."""
        self.direction = msg.data

    def cb_fist(self, msg: Bool):
        """
        Triggered when fist state changes.
        If fist is detected AND direction is set → step the selected motor.
        """
        self.is_fist = msg.data

        # Only move when fist is closed AND hand is moving
        if self.is_fist and self.direction != "NONE":
            if self.selected_joint in self.motors:
                motor = self.motors[self.selected_joint]
                motor.step(self.direction, step_deg=5.0)
                self.get_logger().info(
                    f"[motor_{self.selected_joint}] {self.direction} "
                    f"→ stepped 5°"
                )
            else:
                self.get_logger().warn(
                    f"⚠️  Motor ID {self.selected_joint} not found"
                )

    def destroy_node(self):
        """Safe shutdown — disable all motors and close bus."""
        self.get_logger().info("🛑 Shutting down arm controller...")
        for motor in self.motors.values():
            motor.close()
        self.bus.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ArmControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
