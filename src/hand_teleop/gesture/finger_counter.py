import mediapipe as mp
import cv2 as cv

class FingerCounter:
    """
    Counts how many fingers are extended.
    Only meant for LEFT HAND in this project.
    """
    def __init__(self):
        self.mp_hands = mp.solutions.hands  # type: ignore
        self.hands = self.mp_hands.Hands(   # type: ignore
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.finger_tips = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

    def count_fingers(self, frame):
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if not results.multi_hand_landmarks:
            return 0  # no hand

        lm = results.multi_hand_landmarks[0].landmark

        # Simple extended finger check based on y-coordinates
        count = 0
        for tip_id in self.finger_tips[1:]:  # ignore thumb for stability
            if lm[tip_id].y < lm[tip_id - 2].y:
                count += 1

        # thumb check (optional)
        if lm[4].x < lm[3].x:  # thumb extended sideways
            count += 1

        return count