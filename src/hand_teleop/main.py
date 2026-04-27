import cv2 as cv
from gesture.right_hand_tracker import RightHandTracker
#from finger_counter import FingerCounter

def main():
    cap = cv.VideoCapture(0)

    #finger_counter = FingerCounter()
    right_hand_tracker = RightHandTracker()

    print("Camera Teleop using left and right hand:")
    print("\nLeft hand = select motor (1→M0, 2→M1, 3→M2, 4→M3)")
    print("\nRight hand = UP/DOWN (while FIST)")
    print("\nPress 'c' to calibrate")
    print("\nPress 'q' to quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv.flip(frame, 1)
        h, w, _ = frame.shape

        left_frame = frame[:, : w//2]
        right_frame = frame[:, w//2 :]

        # -----------------------------
        # LEFT HAND → FINGER COUNT (MOTOR SELECT)
        # -----------------------------

        # -----------------------------
        # RIGHT HAND → UP/DOWN + FIST
        # -----------------------------
        cy, direction, is_fist = right_hand_tracker.update(right_frame)

        # -----------------------------
        # MOTOR COMMAND
        # -----------------------------
        # Only move when fist
        #if is_fist and direction != "NONE":           
            
        # -----------------------------
        # VISUAL CALIBRATION
        # -----------------------------
        if right_hand_tracker.neutral_y is not None:
            cy_px = int(right_hand_tracker.neutral_y * right_frame.shape[0])
            cv.line(right_frame, (0, cy_px), (right_frame.shape[1], cy_px),
                    (255, 255, 0), 2)

        # UI left
        #cv.putText(left_frame, f"Motor: M{selected_motor}", (10, 40),
        #           cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        #cv.putText(left_frame, f"Fingers={fingers}", (10, 80),
        #           cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

        # UI right
        cv.putText(right_frame, f"Dir: {direction}", (10, 40),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
        cv.putText(right_frame, f"Fist: {is_fist}", (10, 80),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0,200,200), 2)

        # Combine
        combined = cv.hconcat([left_frame, right_frame])
        cv.imshow("Teleoperation", combined)

        key = cv.waitKey(1) & 0xFF

        if key == ord('c') and cy is not None:
            right_hand_tracker.calibrate(cy)

        if key == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()



if __name__ == "__main__":
    main()