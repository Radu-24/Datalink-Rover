import math
import random
import numpy as np
from config import *

class UWBBeacon:
    def __init__(self, rover):
        self.rover = rover
        self.range = 0.0
        self.bearing = 0.0
        self.confidence = 1.0
        
    def update(self, obstacles, dock):
        # 1. Ground Truth (Pixels)
        dx = dock.emit_pos[0] - self.rover.x
        dy = dock.emit_pos[1] - self.rover.y
        true_dist_px = math.hypot(dx, dy)
        
        # 2. Add Noise (Pixels)
        noise = random.gauss(0, UWB_NOISE_STD_PX)
        measured_dist_px = true_dist_px + noise
        
        # Clamp
        self.range = max(0.0, min(measured_dist_px, UWB_MAX_RANGE_PX))
        
        # 3. Calculate Bearing
        abs_angle = math.degrees(math.atan2(dy, dx))
        rel_angle = (abs_angle - self.rover.angle + 180) % 360 - 180
        self.bearing = rel_angle
        
        # 4. Confidence (Simple LOS approximation based on distance)
        dist_factor = 1.0 - (self.range / UWB_MAX_RANGE_PX)
        self.confidence = max(0.0, min(1.0, dist_factor))

    def get_ground_truth_dist(self, dock):
        # Return in PIXELS for rewards/HUD
        dx = dock.emit_pos[0] - self.rover.x
        dy = dock.emit_pos[1] - self.rover.y
        return math.hypot(dx, dy)

    def get_data(self):
        # Return [range_norm, bearing_sin, bearing_cos, confidence]
        range_norm = self.range / UWB_MAX_RANGE_PX
        rad = math.radians(self.bearing)
        
        return np.array([
            range_norm,
            math.sin(rad),
            math.cos(rad),
            self.confidence
        ])