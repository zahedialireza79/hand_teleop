import cv2 as cv
from gesture.right_hand_tracker import RightHandTracker
#from gesture.finger_counter import FingerCounter

def main():
    cap = cv.VideoCapture(0)

    #finger_counter = FingerCounter()
    right_hand_tracker = RightHandTracker()

    print("Camera Teleop using left and right hand:")
    print("\nLeft hand  = select motor (1→M0, 2→M1, 3→M2, 4→M3)")
    print("\nRight hand = UP/DOWN (while FIST)")
    print("\nPress 'c' to calibrate")
    print("\nPress 'q' to quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv.flip(frame, 1)
        h, w, _ = frame.shape

        left_frame  = frame[:, : w//2]
        right_frame = frame[:, w//2 :]

        # -----------------------------
        # LEFT HAND → FINGER COUNT (MOTOR SELECT)
        # -----------------------------

        # -----------------------------
        # RIGHT HAND → UP/DOWN + FIST
        # Pass the FULL frame so MediaPipe gets proper dimensions
        # -----------------------------
        cy, direction, is_fist = right_hand_tracker.update(frame)

        # -----------------------------
        # MOTOR COMMAND
        # -----------------------------
        # Only move when fist
        # if is_fist and direction != "NONE":
        #     pass

        # -----------------------------
        # VISUAL CALIBRATION LINE
        # Drawn on right_frame but y is relative to full frame height (same h)
        # -----------------------------
        if right_hand_tracker.neutral_y is not None:
            cy_px = int(right_hand_tracker.neutral_y * h)
            cv.line(right_frame, (0, cy_px), (right_frame.shape[1], cy_px),
                    (255, 255, 0), 2)
            cv.putText(right_frame, "ZERO", (5, cy_px - 8),
                       cv.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)
        else:
            cv.putText(right_frame, "Press 'c' to calibrate", (10, h - 20),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 1)

        # -----------------------------
        # UI LEFT
        # -----------------------------
        # cv.putText(left_frame, f"Motor: M{selected_motor}", (10, 40),
        #            cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        # cv.putText(left_frame, f"Fingers={fingers}", (10, 80),
        #            cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # -----------------------------
        # UI RIGHT
        # -----------------------------
        cv.putText(right_frame, f"Dir : {direction}", (10, 40),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv.putText(right_frame, f"Fist: {is_fist}", (10, 80),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 200), 2)

        # -----------------------------
        # COMBINE AND SHOW
        # -----------------------------
        combined = cv.hconcat([left_frame, right_frame])
        cv.imshow("Teleoperation", combined)

        # -----------------------------
        # KEY HANDLING
        # waitKey(1) can miss keys on Mac — use 10ms for reliability
        # -----------------------------
        key = cv.waitKey(10) & 0xFF

        if key == ord('c'):
            if cy is not None:
                right_hand_tracker.calibrate(cy)
            else:
                print("[Calibration] No hand detected — show your right hand first.")

        if key == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()