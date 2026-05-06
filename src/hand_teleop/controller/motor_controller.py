import time
import threading
import scservo_sdk as scs
from motor_bus import MotorBus

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

    def __init__(self, bus: MotorBus, motor_id: int, name: str):
        self.ph       = bus.ph    
        self.pkh      = bus.pkh  
        self.motor_id = motor_id
        self.name     = name

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
    def calibrate(self) -> bool:
        """Interactive calibration: Records home, min, and max positions."""
        print(f"\n── Calibrating '{self.name}' (ID {self.motor_id}) ──")
        self.disable_torque() 

        # 1. HOME
        print(f"   👉 Move '{self.name}' to HOME (0°)")
        t, stop = self.start_live_display(reference_raw=2048) 
        input("      Press ENTER when at home position...")
        stop.set(); t.join()
        raw_home = self.read_raw() 

        # 2. MIN
        print(f"\n   👉 Move '{self.name}' to MINIMUM position")
        t, stop = self.start_live_display(reference_raw=raw_home) 
        input("      Press ENTER when at minimum position...")
        stop.set(); t.join()
        raw_min = self.read_raw() 
        deg_min = (raw_min - raw_home) / self.RAW_PER_DEGREE 

        # 3. MAX
        print(f"\n   👉 Move '{self.name}' to MAXIMUM position")
        t, stop = self.start_live_display(reference_raw=raw_home) 
        input("      Press ENTER when at maximum position...")
        stop.set(); t.join()
        raw_max = self.read_raw() 
        deg_max = (raw_max - raw_home) / self.RAW_PER_DEGREE 

        if raw_min >= raw_max:
            print("\n   ❌ Min >= Max — calibration failed.")
            return False

        self.cal = {
            "home_raw": raw_home,
            "raw_min": raw_min,
            "raw_max": raw_max,
            "deg_min": round(deg_min, 2),
            "deg_max": round(deg_max, 2),
        } 

        print("\n   ✅ Calibration complete!")
        self.go_home() 
        return True

    