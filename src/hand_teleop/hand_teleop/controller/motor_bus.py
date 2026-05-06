import scservo_sdk as scs

class MotorBus:
    """Owns the single serial connection for all motors."""
    def __init__(self, port, baudrate=1_000_000, protocol=0):
        self.ph  = scs.PortHandler(port)
        self.pkh = scs.PacketHandler(protocol)

        if not self.ph.openPort():
            raise RuntimeError(f"❌ Cannot open port: {port}")
        if not self.ph.setBaudRate(baudrate):
            raise RuntimeError("❌ Cannot set baudrate")
        print(f"✅ Serial connection opened on {port}")

    def close(self):
        self.ph.closePort()
        print("🔌 Port closed.")


