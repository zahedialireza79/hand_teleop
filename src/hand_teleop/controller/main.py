from motor_controller import Motor
from motor_id_search import MotorIDSearch
if __name__ == "__main__":
    PORT = "/dev/tty.usbmodem5A4B0486761"

    
    try:
        #Check the number of motors
        scanner = MotorIDSearch(PORT)
        found_ids = scanner.scan() # Returns a list like [1, 3, 5]
        
        motors = {} # Dictionary to store motor objects: {id: MotorObject}

        print("\nWhich motor(s) do you want to initialize?")
        print("  - 'all' to initialize everything found")
        print("  - specific numbers separated by comma (e.g., 1, 3)")

        while True:
            cmd = input("→ ").strip().lower()
            if not cmd:
                continue
            
            target_ids = []

            if cmd == "all":
                target_ids = found_ids # Use every ID found during the scan 
            else:
                try:
                    # Convert "1, 3" string into a list of integers [1, 3] 
                    input_ids = [int(x.strip()) for x in cmd.split(',')]
                    
                    # Validate that the requested IDs were actually found on the bus 
                    target_ids = [i for i in input_ids if i in found_ids]
                    
                    if not target_ids:
                        print(f"⚠️ None of the IDs {input_ids} were found in the scan.")
                        continue
                except ValueError:
                    print("⚠️ Invalid format. Please use numbers separated by commas.")
                    continue

            # Perform the dynamic initialization 
            for m_id in target_ids:
                print(f"⚙️ Initializing Motor ID: {m_id}...")
                motors[m_id] = Motor(port=PORT, motor_id=m_id, name=f"motor_{m_id}")
            
            break  

        
        # ── The Calibration Loop ──
        # Forces the user to get a successful calibration before proceeding
        calibrated = False
        while not calibrated:
            calibrated = motor1.calibrate()
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
                motor1.calibrate() # Homing is baked into this function now
            else:
                try:
                    degrees = float(cmd)
                    motor1.move_to_degrees(degrees)
                except ValueError:
                    print("  ⚠️  Enter a number (degrees), 'r', 'home', 'recal', or 'q'")

    finally:
        if 'motor' in locals():
            motor1.close()