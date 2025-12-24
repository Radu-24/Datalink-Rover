import numpy as np
import math
from config import *
from core.raycast import get_ray_intersection_dist

class ProximitySensor:
    def __init__(self, rover):
        self.rover = rover
        # 5 Sensors: [FrontLeft, FrontCenter, FrontRight, RearLeft, RearRight]
        self.readings = np.array([1.0]*5, dtype=float)
        
    def update(self, obstacles):
        # Scan 3 Front Zones
        self.readings[0] = self._scan_arc(PP_ANGLES_FRONT[0][0], PP_ANGLES_FRONT[0][1], obstacles)
        self.readings[1] = self._scan_arc(PP_ANGLES_FRONT[1][0], PP_ANGLES_FRONT[1][1], obstacles)
        self.readings[2] = self._scan_arc(PP_ANGLES_FRONT[2][0], PP_ANGLES_FRONT[2][1], obstacles)
        
        # Scan 2 Rear Zones
        self.readings[3] = self._scan_arc(PP_ANGLES_REAR[0][0], PP_ANGLES_REAR[0][1], obstacles)
        self.readings[4] = self._scan_arc(PP_ANGLES_REAR[1][0], PP_ANGLES_REAR[1][1], obstacles)
        
    def _scan_arc(self, start_deg, end_deg, obstacles):
        # We raycast in Pixels
        min_d_px = PROX_MAX_RANGE_PX
        steps = 5 
        
        for angle in np.linspace(start_deg, end_deg, steps):
            global_angle = (self.rover.angle + angle) % 360
            d_px = get_ray_intersection_dist(
                (self.rover.x, self.rover.y),
                global_angle,
                obstacles,
                PROX_MAX_RANGE_PX
            )
            if d_px < min_d_px:
                min_d_px = d_px
                
        # Return normalized distance (0.0 = touching, 1.0 = max range)
        return min_d_px / PROX_MAX_RANGE_PX

    def get_data(self):
        return self.readings