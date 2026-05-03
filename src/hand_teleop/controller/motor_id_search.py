import scservo_sdk as scs

class MotorIDSearch:
    ADDR_LOCK = 55
    ADDR_ID   = 5

    def __init__(self, port="/dev/tty.usbmodem5A4B0486761", baudrate=1_000_000):
        self.ph = scs.PortHandler(port)
        self.pkh = scs.PacketHandler(0)
        if not self.ph.openPort() or not self.ph.setBaudRate(baudrate):
            raise RuntimeError("❌ Connection failed.")

    def scan(self):
        print("Looking for the IDs of motors .... \n")
        found = []
        for i in range(1, 254):
            _, res, _ = self.pkh.ping(self.ph, i)
            if res == scs.COMM_SUCCESS:
                print(f"✅ Found: {i}")
                found.append(i)
        return found

    def change_id(self, old_id, new_id):
        self.pkh.write1ByteTxRx(self.ph, old_id, self.ADDR_LOCK, 0)
        self.pkh.write1ByteTxRx(self.ph, old_id, self.ADDR_ID, new_id)
        print(f"✅ ID {old_id} changed to {new_id}. Power cycle now.")

    def close(self):
        self.ph.closePort()