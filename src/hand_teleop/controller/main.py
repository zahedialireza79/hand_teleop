from motor_bus import MotorBus
from motor_controller import Motor
from motor_id_search import MotorIDSearch

if __name__ == "__main__":
    PORT = "/dev/ttyACM0"

    # ── Open the serial bus ONCE ──
    bus = MotorBus(port=PORT)
    
    try:
        # ── Check the number of motors ──
        scanner = MotorIDSearch(PORT)
        found_ids = scanner.scan()  # Returns a list like [1, 3, 5]
        
        motors = {}  # Dictionary to store motor objects: {id: MotorObject}

        print("\nWhich motor(s) do you want to initialize?")
        print("  - 'all' to initialize everything found")
        print("  - specific numbers separated by comma (e.g., 1, 3)")

        while True:
            cmd = input("→ ").strip().lower()
            if not cmd:
                continue
            
            target_ids = []

            if cmd == "all":
                target_ids = found_ids  # Use every ID found during the scan 
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

            # ── Dynamic initialization using the shared bus ──
            for m_id in target_ids:
                print(f"⚙️ Initializing Motor ID: {m_id}...")
                motors[m_id] = Motor(bus=bus, motor_id=m_id, name=f"motor_{m_id}")
            
            break  

        
        # ── The Calibration Loop ──
        print("\n" + "="*50)
        print("🚀 STARTING MULTI-MOTOR CALIBRATION")
        print("="*50)

        for m_id, motor_obj in motors.items():
            print(f"\n▶️ Calibrating Motor: {motor_obj.name} (ID: {m_id})")
            
            calibrated = False
            while not calibrated:
                # Calls the internal calibrate method
                calibrated = motor_obj.calibrate()
                
                if not calibrated:
                    print(f"⚠️ Calibration failed for Motor {m_id}.")
                    retry = input(f"Retry calibration for Motor {m_id}? (y/n): ").strip().lower()
                    if retry != 'y':
                        print("Terminating setup...")
                        exit(1)
            
            print(f"✅ Motor {m_id} is ready.\n")
            print("-------------------------------\n")
        print("\n✨ All motors calibrated and homed successfully!")

    
        # ── The Control Loop ──
        print("\n═══ CONTROL MODE ═══════════════════════════════════")
        available_ids = list(motors.keys())  
        print(f"  Available IDs : {available_ids}")
        print("  Instructions  : Type an ID to select it, or 'all' for all motors.")
        print("  Commands      : <degrees>, 'r', 'home', 'recal', 'q' (to exit)")
        print("════════════════════════════════════════════════════\n")

        # Start with 'all' as default
        active_ids = available_ids 

        while True:
            # Show which motors are currently being targeted
            target_label = "ALL" if len(active_ids) == len(available_ids) else f"IDs {active_ids}"
            cmd = input(f"[{target_label}] → ").strip().lower()

            if not cmd:
                continue
            
            # 1. Selection Logic: Change which motor(s) we are talking to
            if cmd == "all":
                active_ids = available_ids
                print(f"📢 Now targeting all motors: {active_ids}")
                continue
            elif cmd.isdigit() and int(cmd) in available_ids:
                active_ids = [int(cmd)]
                print(f"🎯 Now targeting Motor ID: {active_ids[0]}")
                continue
            
            # 2. Exit Logic
            if cmd == "q":
                break

            # 3. Action Logic: Loop through the currently active IDs
            for m_id in active_ids:
                m_obj = motors[m_id]  

                if cmd == "r":
                    raw, deg = m_obj.read_position()  
                    print(f"  [ID {m_id}] {m_obj.name}: raw={raw:4d}  {deg:+.1f}°")

                elif cmd == "home":
                    print(f"🏠 [ID {m_id}] Going home...")
                    m_obj.go_home()  

                elif cmd == "recal":
                    print(f"🔄 [ID {m_id}] Starting recalibration...")
                    m_obj.calibrate()  

                else:
                    try:
                        degrees = float(cmd)
                        m_obj.move_to_degrees(degrees)  
                    except ValueError:
                        if m_id == active_ids[0]:  # Only print warning once
                            print("  ⚠️ Enter degrees, ID, 'all', 'r', 'home', 'recal', or 'q'")
                        break

    finally:
        # Disable torque on all motors
        if 'motors' in locals():
            for m_id, m_obj in motors.items():  
                m_obj.close()  # just disables torque now
        
        # Close the bus ONCE at the end
        bus.close()