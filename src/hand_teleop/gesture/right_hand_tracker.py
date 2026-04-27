import mediapipe as mp
import cv2 as cv

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import os

class RightHandTracker:
    def __init__(self, model_path="hand_landmarker.task"):
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

        # Calibration
        self.neutral_y = None
        self.th = 0.05

    # ---------------------------------------------------------
    # Fist Detector
    # ---------------------------------------------------------
    def _is_fist(self, lm):
        tips = [8, 12, 16, 20]  # MediaPipe identifies 21 points on the hand. Points 8, 12, 16, and 20 are the fingertips(thumb is 4 but not included.)
        folded = 0

        for tip in tips:
            if lm[tip].y > lm[tip - 2].y:  # Compare using the landmark on the middle of the finger. if the tip is lower, it is folded.
                folded += 1

        return folded >= 3

    # ---------------------------------------------------------
    # Calibrate
    # ---------------------------------------------------------
    def calibrate(self, cy):
        self.neutral_y = cy
        print(f"[Right Hand Calibrated] neutral_y = {cy:.3f}")

    # ---------------------------------------------------------
    # SAFELY return 3 values ALWAYS
    # ---------------------------------------------------------
    def update(self, frame):
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        # -----------------------------------------------------
        # If no hand → ALWAYS return 3 values
        # -----------------------------------------------------
        if not results.multi_hand_landmarks:
            return None, "NONE", False

        lm = results.multi_hand_landmarks[0].landmark

        # Extract cy landmark
        cy = lm[9].y

        # Determine if fist
        is_fist = self._is_fist(lm)

        # If not calibrated yet → return 3 values
        if self.neutral_y is None:
            return cy, "NONE", is_fist

        # Motion direction
        if cy < self.neutral_y - self.th:
            direction = "UP"
        elif cy > self.neutral_y + self.th:
            direction = "DOWN"
        else:
            direction = "NONE"

        # ALWAYS return 3 values
        return cy, direction, is_fist