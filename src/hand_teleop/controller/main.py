from motor_controller import Motor
if __name__ == "__main__":
    PORT = "/dev/tty.usbmodem5A4B0486761"
    
    print("\n=== Single Motor Setup ===")
    
    try:
        # Initialize the motor
        motor1 = Motor(port=PORT, motor_id=1, name="base")
        
        # ── The Calibration Loop ──
        # Forces the user to get a successful calibration before proceeding
        calibrated = False
        while not calibrated:
            calibrated = motor1.calibrate_motor(motor1)
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
                raw, deg = motor1.read_position()
                print(f"  {motor1.name}: raw={raw}  {deg:+.1f}°")
            elif cmd == "home":
                motor1.go_home()
            elif cmd == "recal":
                print("\n🔄 Starting recalibration...")
                Motor.calibrate_motor(motor1) # Homing is baked into this function now
            else:
                try:
                    degrees = float(cmd)
                    motor1.move_to_degrees(degrees)
                except ValueError:
                    print("  ⚠️  Enter a number (degrees), 'r', 'home', 'recal', or 'q'")

    finally:
        if 'motor' in locals():
            motor1.close()