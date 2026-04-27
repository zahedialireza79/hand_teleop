import mediapipe as mp
import cv2 as cv

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import os

class FingerCounter:
    """
    Counts how many fingers are extended.
    Only meant for LEFT HAND in this project.
    """
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
        self.detector = vision.HandLandmarker.create_from_options(options)  # was missing!

        self.finger_tips = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

    def count_fingers(self, frame):
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = self.detector.detect(mp_image)

        if not results.hand_landmarks or not results.handedness:
            return 0  # no hand detected

        # NOTE: frame is flipped in main.py for natural mirror view,
        # so MediaPipe labels are swapped — user's left hand = "Right" label
        left_lm = None
        for lm, handedness in zip(results.hand_landmarks, results.handedness):
            if handedness[0].category_name == "Right":
                left_lm = lm
                break

        if left_lm is None:
            return 0  # left hand not found

        # ---------------------------------------------------------
        # Count extended fingers based on y-coordinates
        # Tip is extended if it is higher (lower y) than its mid-joint
        # ---------------------------------------------------------
        count = 0
        for tip_id in self.finger_tips[1:]:  # skip thumb (index 4)
            if left_lm[tip_id].y < left_lm[tip_id - 2].y:
                count += 1

        # Thumb: extended if tip is to the right of its knuckle (mirrored frame)
        if left_lm[4].x > left_lm[3].x:
            count += 1

        return count