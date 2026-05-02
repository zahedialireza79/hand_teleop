import time
import threading
import scservo_sdk as scs

class Motor:
    # ── Register addresses (STS3215) ──
    ADDR_TORQUE_ENABLE  = 40
    ADDR_GOAL_POSITION  = 42
    ADDR_GOAL_VELOCITY  = 46
    ADDR_LOCK           = 55
    ADDR_PRESENT_POS    = 56

    # ── Conversion constants ──
    RAW_PER_DEGREE  = 1000 / 90
    SIGN_BIT        = 15

    def __init__(self, port, baudrate=1_000_000, motor_id=1, name="base", protocol=0):
        self.port = port
        self.baudrate = baudrate
        self.motor_id = motor_id
        self.name = name
        
        self.ph = scs.PortHandler(port)
        self.pkh = scs.PacketHandler(protocol)
        
        self.cal = {} # Stores home_raw, raw_min, raw_max, etc.

        if not self.ph.openPort():
            raise RuntimeError(f"❌ Cannot open port: {self.port}")
        if not self.ph.setBaudRate(self.baudrate):
            raise RuntimeError("❌ Cannot set baudrate")
        
        print(f"✅ Connected to '{self.name}' on {self.port}")

    def close(self):
        """Safely shut down the motor."""
        self.disable_torque()
        self.ph.closePort()
        print("🔌 Port closed.")

    # ── Conversion Methods ──
    def _encode_sign_magnitude(self, value: int) -> int:
        if value < 0:
            return abs(value) | (1 << self.SIGN_BIT)
        return value

    def _decode_sign_magnitude(self, value: int) -> int:
        if value & (1 << self.SIGN_BIT):
            return -(value & ~(1 << self.SIGN_BIT))
        return value

    def degrees_to_raw(self, degrees: float) -> int:
        if not self.cal:
            raise ValueError("Motor not calibrated. Unknown home.")
        return int(self.cal["home_raw"] + degrees * self.RAW_PER_DEGREE)

    def raw_to_degrees(self, raw: int) -> float:
        if not self.cal:
            raise ValueError("Motor not calibrated. Unknown home.")
        return (raw - self.cal["home_raw"]) / self.RAW_PER_DEGREE

    # ── Hardware Control ──
    def enable_torque(self):
        self.pkh.write1ByteTxRx(self.ph, self.motor_id, self.ADDR_TORQUE_ENABLE, 1)
        self.pkh.write1ByteTxRx(self.ph, self.motor_id, self.ADDR_LOCK, 1)
        print(f"⚡ Torque ON  → {self.name}")

    def disable_torque(self):
        self.pkh.write1ByteTxRx(self.ph, self.motor_id, self.ADDR_TORQUE_ENABLE, 0)
        self.pkh.write1ByteTxRx(self.ph, self.motor_id, self.ADDR_LOCK, 0)
        print(f"💤 Torque OFF → {self.name} (motor is free to move)")

    def read_raw(self) -> int:
        val, result, _ = self.pkh.read2ByteTxRx(self.ph, self.motor_id, self.ADDR_PRESENT_POS)
        if result != scs.COMM_SUCCESS:
            return -1
        return self._decode_sign_magnitude(val)

    def read_position(self) -> tuple[int, float]:
        raw = self.read_raw()
        if raw == -1:
            print("❌ Read error")
            return -1, 0.0
        deg = self.raw_to_degrees(raw) if self.cal else 0.0
        return raw, deg

    def move_to_raw(self, raw: int, velocity: int = 300):
        """Move directly to a raw value (ignores calibration constraints)."""
        encoded = self._encode_sign_magnitude(raw)
        self.pkh.write2ByteTxRx(self.ph, self.motor_id, self.ADDR_GOAL_VELOCITY, velocity)
        self.pkh.write2ByteTxRx(self.ph, self.motor_id, self.ADDR_GOAL_POSITION, encoded)

    def move_to_degrees(self, degrees: float, velocity: int = 300):
        """Move to a specific angle safely clamped within calibrated bounds."""
        if not self.cal:
            print("⚠️ Cannot move to degrees: Motor not calibrated!")
            return

        # Clamp to bounds
        degrees = max(self.cal["deg_min"], min(self.cal["deg_max"], degrees))
        raw = self.degrees_to_raw(degrees)
        raw = max(self.cal["raw_min"], min(self.cal["raw_max"], raw))
        
        print(f"  → {self.name}: {degrees:+.1f}° (raw {raw})")
        self.move_to_raw(raw, velocity)

    def go_home(self, velocity: int = 200):
        """Explicitly handles the homing logic to the recorded center point."""
        if not self.cal:
            print("⚠️ Cannot go home: Calibration missing.")
            return
        
        print(f"\n   🏠 Returning to home...")
        self.enable_torque()
        self.move_to_raw(self.cal["home_raw"], velocity)
        time.sleep(2) # Give motor time to travel
        
        raw_now, deg_now = self.read_position()
        print(f"      Position now: raw={raw_now}  ({deg_now:+.1f}°)")

    # ── Live Display Helper ──
    def start_live_display(self, reference_raw: int) -> tuple[threading.Thread, threading.Event]:
        stop_event = threading.Event()
        
        def _display():
            while not stop_event.is_set():
                raw = self.read_raw()
                if raw != -1:
                    # Temporary conversion for live view
                    deg = (raw - reference_raw) / self.RAW_PER_DEGREE
                    print(f"\r  📍 raw={raw:4d}  {deg:+7.1f}°    ", end="", flush=True)
                time.sleep(0.3)
            print() 

        t = threading.Thread(target=_display, daemon=True)
        t.start()
        return t, stop_event


# ── MAIN CALIBRATION & CONTROL LOOP ──────────────────────────────────
def calibrate_motor(motor: Motor) -> bool:
    """Handles the interactive calibration steps."""
    print(f"\n── Calibrating '{motor.name}' (ID {motor.motor_id}) ──")
    print("   Scale : 1000 raw = 90°")
    print("   Tip   : watch the live values while moving\n")

    motor.disable_torque()

    # 1. HOME
    print(f"   👉 Move '{motor.name}' to HOME (0°)")
    t, stop = motor.start_live_display(reference_raw=2048)
    input("      Press ENTER when at home position...")
    stop.set(); t.join()
    
    raw_home = motor.read_raw()
    print(f"      ✅ Home recorded: raw={raw_home}")

    # 2. MIN
    print(f"\n   👉 Move '{motor.name}' to MINIMUM position")
    t, stop = motor.start_live_display(reference_raw=raw_home)
    input("      Press ENTER when at minimum position...")
    stop.set(); t.join()
    
    raw_min = motor.read_raw()
    deg_min = (raw_min - raw_home) / motor.RAW_PER_DEGREE
    print(f"      ✅ Min recorded: raw={raw_min}  ({deg_min:+.1f}°)")

    # 3. MAX
    print(f"\n   👉 Move '{motor.name}' to MAXIMUM position")
    t, stop = motor.start_live_display(reference_raw=raw_home)
    input("      Press ENTER when at maximum position...")
    stop.set(); t.join()
    
    raw_max = motor.read_raw()
    deg_max = (raw_max - raw_home) / motor.RAW_PER_DEGREE
    print(f"      ✅ Max recorded: raw={raw_max}  ({deg_max:+.1f}°)")

    # Validate
    if raw_min >= raw_max:
        print("\n   ❌ Min >= Max — calibration failed.")
        print("      Make sure min and max are on opposite sides of home.")
        return False

    # Save to motor instance
    motor.cal = {
        "home_raw": raw_home,
        "raw_min": raw_min,
        "raw_max": raw_max,
        "deg_min": round(deg_min, 2),
        "deg_max": round(deg_max, 2),
    }

    print("\n   ✅ Calibration complete!")
    print(f"      Range: {motor.cal['deg_min']:+.1f}° to {motor.cal['deg_max']:+.1f}°")
    
    # Home the motor using the verified logic
    motor.go_home()
    return True


if __name__ == "__main__":
    PORT = "/dev/tty.usbmodem5A4B0486761"
    
    print("\n=== Single Motor Setup ===")
    
    try:
        # Initialize the motor
        motor = Motor(port=PORT, motor_id=1, name="base")
        
        # ── The Calibration Loop ──
        # Forces the user to get a successful calibration before proceeding
        calibrated = False
        while not calibrated:
            calibrated = calibrate_motor(motor)
            if not calibrated:
                retry = input("Do you want to try again? (y/n): ").strip().lower()
                if retry != 'y':
                    print("Exiting...")
                    exit(1)

        # ── The Control Loop ──
        print("\n═══ CONTROL MODE ═══════════════════════════════════")
        print("  Commands:")
        print("    <degrees>     move to angle  e.g. '45' or '-30'")
        print("    r             read current position")
        print("    home          move to 0°")
        print("    recal         redo calibration")
        print("    q             quit")
        print("════════════════════════════════════════════════════\n")

        while True:
            cmd = input("→ ").strip().lower()

            if not cmd:
                continue
            elif cmd == "q":
                break
            elif cmd == "r":
                raw, deg = motor.read_position()
                print(f"  {motor.name}: raw={raw}  {deg:+.1f}°")
            elif cmd == "home":
                motor.go_home()
            elif cmd == "recal":
                print("\n🔄 Starting recalibration...")
                calibrate_motor(motor) # Homing is baked into this function now
            else:
                try:
                    degrees = float(cmd)
                    motor.move_to_degrees(degrees)
                except ValueError:
                    print("  ⚠️  Enter a number (degrees), 'r', 'home', 'recal', or 'q'")

    finally:
        if 'motor' in locals():
            motor.close()