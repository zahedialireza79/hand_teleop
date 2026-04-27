import mediapipe as mp
import cv2 as cv

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import os

class RightHandTracker:
    def __init__(self):
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
        tips = [8, 12, 16, 20]  # MediaPipe identifies 21 points on the hand.
                                 # Points 8, 12, 16, 20 are fingertips (thumb=4, not included).
        folded = 0

        for tip in tips:
            if lm[tip].y > lm[tip - 2].y:  # If tip is lower than mid-joint → finger is folded.
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
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = self.detector.detect(mp_image)

        # -----------------------------------------------------
        # If no hand → ALWAYS return 3 values
        # -----------------------------------------------------
        if not results.hand_landmarks or not results.handedness:
            return None, "NONE", False

        # Find the RIGHT hand by MediaPipe label
        right_lm = None
        for lm, handedness in zip(results.hand_landmarks, results.handedness):
            if handedness[0].category_name == "Left":
                right_lm = lm
                break

        if right_lm is None:
            return None, "NONE", False

        # Extract cy landmark (palm centre)
        cy = right_lm[9].y

        # Determine if fist
        is_fist = self._is_fist(right_lm)

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