import math
import numpy as np
from config import *
from core.raycast import ray_segment_intersection

class IRSensor:
    def __init__(self, rover):
        self.rover = rover
        # Data: [Red, Green, unused, unused, unused, ReadyTurn]
        self.data = np.zeros(6, dtype=float) 
        
    def _is_in_beam(self, dock_rel_angle, center_offset):
        if center_offset == "RED":
            return -IR_CONE_OUTER < dock_rel_angle < IR_CONE_INNER
        elif center_offset == "GREEN":
            return -IR_CONE_INNER < dock_rel_angle < IR_CONE_OUTER
        return False

    def _check_line_of_sight(self, start_pos, end_pos, obstacles):
        ray_origin = np.array(start_pos)
        ray_vec = np.array(end_pos) - ray_origin
        dist = np.linalg.norm(ray_vec)
        if dist == 0: return True
        ray_dir = ray_vec / dist
        
        for rect in obstacles:
            tl = np.array(rect.topleft); tr = np.array(rect.topright)
            bl = np.array(rect.bottomleft); br = np.array(rect.bottomright)
            segments = [(tl, tr), (tr, br), (br, bl), (bl, tl)]
            for p1, p2 in segments:
                hit_dist = ray_segment_intersection(ray_origin, ray_dir, p1, p2)
                if hit_dist is not None and 0 < hit_dist < dist:
                    return False
        return True

    def update(self, dock, obstacles):
        self.data.fill(0.0)
        
        dx = dock.emit_pos[0] - self.rover.x
        dy = dock.emit_pos[1] - self.rover.y
        dist_px = math.hypot(dx, dy)
        
        angle_dock_to_rover = math.degrees(math.atan2(-dy, -dx))
        dock_rel_angle = (angle_dock_to_rover - dock.facing_angle + 180) % 360 - 180
        
        angle_rover_to_dock = math.degrees(math.atan2(dy, dx))
        rover_front_rel = (angle_rover_to_dock - self.rover.angle + 180) % 360 - 180

        # --- FRONT SENSOR (Approach) ---
        if dist_px < IR_MAX_RANGE_PX:
            if abs(rover_front_rel) < IR_FRONT_CONE:
                 if self._check_line_of_sight((self.rover.x, self.rover.y), dock.emit_pos, obstacles):
                    in_red = self._is_in_beam(dock_rel_angle, "RED")
                    in_green = self._is_in_beam(dock_rel_angle, "GREEN")
                    if in_red: self.data[0] = 1.0
                    if in_green: self.data[1] = 1.0
                    
                    # Ready to Turn Signal
                    if in_red and in_green:
                        dist_error = abs(dist_px - IR_TURN_DIST)
                        if dist_error < IR_TURN_TOLERANCE:
                            self.data[5] = 1.0 

    def get_data(self):
        return self.data