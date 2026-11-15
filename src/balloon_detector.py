import cv2 as cv
import numpy as np

class DetectorConfig:
    def __init__(self,
                 red_low_1=(0, 100, 100), red_high_1=(10, 255, 255),
                 red_low_2=(170, 100, 100), red_high_2=(180, 255, 255),
                 min_area=500, kernel_size=5):
        # Red is in the limiar of HSV representation
        # Forcing us to use two different thresholds to fully represent its spectrum

        self.red_low_1 = red_low_1
        self.red_high_1 = red_high_1
        self.red_low_2 = red_low_2
        self.red_high_2 = red_high_2
        self.min_area = min_area
        self.kernel_size = kernel_size


class Detection:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

class BalloonDetector:
    def __init__(self, config=None):
        self.config = config or DetectorConfig()
        k = self.config.kernel_size
        self._kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (k, k))
    
    def _red_mask(self, frame):
        c = self.config
        # Converts BGR system to HSV
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        
        # Creates the raw red mask uniting the two red tresholds
        mask1 = cv.inRange(hsv, np.array(c.red_low_1), np.array(c.red_high_1))
        mask2 = cv.inRange(hsv, np.array(c.red_low_2), np.array(c.red_high_2))
        mask = cv.bitwise_or(mask1, mask2)
        
        # Cleans up noise white pixels, and brings back bits cleaned in the first operation
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, self._kernel)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, self._kernel)
        return mask

    def _find_contours(self, mask):
            # Identify all red objects contours, considers only 'external' contours
            contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            return list(contours)

    def _filter_candidates(self, contours):
        # Logic to choose wich objects are considered valid 
        candidates = []
        for contour in contours:
            if cv.contourArea(contour) >= self.config.min_area:
                candidates.append(contour)
        return candidates

    def _select_target(self, candidates):
        # Logic to choose between all possible targets, wich one will be followed
        if not candidates:
            return None
        return max(candidates, key=cv.contourArea)

    def _to_detection(self, contour):
        (x, y), radius = cv.minEnclosingCircle(contour)
        return Detection((x, y), radius)

    def detect(self, frame):
        mask = self._red_mask(frame)
        contours = self._find_contours(mask)
        candidates = self._filter_candidates(contours)
        target = self._select_target(candidates)
        if target is None:
            return None
        return self._to_detection(target)