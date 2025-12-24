import math
import numpy as np
from config import *
from core.raycast import ray_segment_intersection

class IRSensor:
    def __init__(self, rover):
        self.rover = rover
        # Data: [Red, Green, RL_Vis, RR_Vis, AlignError, ReadyTurn]
        self.data = np.zeros(6, dtype=float) 
        
    def _is_in_beam(self, dock_rel_angle, center_offset):
        if center_offset == "RED":
            return -30 < dock_rel_angle < 5
        elif center_offset == "GREEN":
            return -5 < dock_rel_angle < 30
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
        
        # Calculate Angles
        angle_dock_to_rover = math.degrees(math.atan2(-dy, -dx))
        dock_rel_angle = (angle_dock_to_rover - dock.facing_angle + 180) % 360 - 180
        
        angle_rover_to_dock = math.degrees(math.atan2(dy, dx))
        rover_front_rel = (angle_rover_to_dock - self.rover.angle + 180) % 360 - 180

        # --- 1. FRONT SENSOR (Approach) ---
        if dist_px < IR_MAX_RANGE_PX:
            if abs(rover_front_rel) < IR_FRONT_CONE:
                 if self._check_line_of_sight((self.rover.x, self.rover.y), dock.emit_pos, obstacles):
                    in_red = self._is_in_beam(dock_rel_angle, "RED")
                    in_green = self._is_in_beam(dock_rel_angle, "GREEN")
                    if in_red: self.data[0] = 1.0
                    if in_green: self.data[1] = 1.0
                    if in_red and in_green:
                        dist_error = abs(dist_px - IR_TURN_DIST)
                        if dist_error < IR_TURN_TOLERANCE:
                            self.data[5] = 1.0 

        # --- 2. REAR GUIDANCE (Strict Dead-Ahead Only) ---
        
        # CONDITION 1: Must be within the "Dead Ahead" Cone (+/- 20 degrees)
        # If we are to the side of the dock, rear sensors see nothing.
        if abs(dock_rel_angle) > 20: 
            return

        # CONDITION 2: Distance Range
        if dist_px > IR_MAX_RANGE_PX: 
            return

        # Rover Rear Logic
        rear_angle_rad = math.radians(self.rover.angle + 180)
        port_x = self.rover.x + math.cos(rear_angle_rad) * ROVER_RADIUS
        port_y = self.rover.y + math.sin(rear_angle_rad) * ROVER_RADIUS
        
        # CONDITION 3: Is Rear pointing at dock?
        dx_rear = dock.emit_pos[0] - port_x
        dy_rear = dock.emit_pos[1] - port_y
        angle_rear_to_dock = math.degrees(math.atan2(dy_rear, dx_rear))
        rover_rear_facing = self.rover.angle + 180
        diff = (angle_rear_to_dock - rover_rear_facing + 180) % 360 - 180
        
        if abs(diff) < IR_REAR_CONE:
            # Check LOS (Skip if very close to prevent clipping)
            has_los = True
            if dist_px > 30:
                has_los = self._check_line_of_sight((port_x, port_y), dock.emit_pos, obstacles)
            
            if has_los:
                # Calculate Lateral Error
                vec_d_x = port_x - dock.emit_pos[0]
                vec_d_y = port_y - dock.emit_pos[1]
                dock_rad = math.radians(dock.facing_angle)
                norm_x = math.cos(dock_rad); norm_y = math.sin(dock_rad)
                right_x = -norm_y; right_y = norm_x 
                
                lateral_offset = (vec_d_x * right_x) + (vec_d_y * right_y)
                normalized_error = lateral_offset / 50.0
                
                self.data[2] = 1.0 
                self.data[3] = 1.0 
                self.data[4] = normalized_error

    def get_data(self):
        return self.data