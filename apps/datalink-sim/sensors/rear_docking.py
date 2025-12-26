import numpy as np
import math
import random
from config import *
from core.raycast import ray_segment_intersection

class RearDockingSystem:
    def __init__(self, rover):
        self.rover = rover
        # Data: [Laser_L, Laser_R, IR_L, IR_R]
        self.data = np.zeros(4, dtype=float)

    def update(self, obstacles, dock):
        # Default: All Zero (System Off)
        self.data.fill(0.0)
        
        # --- 1. ACTIVATION CHECK ---
        if not self._check_activation_conditions(dock):
            return

        # --- PRE-CALCULATIONS ---
        rear_angle = math.radians(self.rover.angle + 180)
        dir_vec = np.array([math.cos(rear_angle), math.sin(rear_angle)])
        perp_angle = rear_angle + (math.pi / 2.0)
        perp_vec = np.array([math.cos(perp_angle), math.sin(perp_angle)])
        
        cx = self.rover.x + dir_vec[0] * ROVER_RADIUS
        cy = self.rover.y + dir_vec[1] * ROVER_RADIUS
        center_rear = np.array([cx, cy])

        # --- 2. LASER (ToF) UPDATE ---
        l_offset = TOF_SPACING / 2.0
        tof_l_origin = center_rear + (perp_vec * l_offset)
        tof_r_origin = center_rear - (perp_vec * l_offset)
        
        targets = obstacles + [dock.rect]
        self.data[0] = self._cast_laser(tof_l_origin, dir_vec, targets)
        self.data[1] = self._cast_laser(tof_r_origin, dir_vec, targets)

        # --- 3. IR RECEIVER UPDATE ---
        ir_offset = REAR_IR_SPACING / 2.0
        ir_l_origin = center_rear + (perp_vec * ir_offset)
        ir_r_origin = center_rear - (perp_vec * ir_offset)
        
        self.data[2] = self._check_ir_beacon(ir_l_origin, rear_angle, dock, obstacles)
        self.data[3] = self._check_ir_beacon(ir_r_origin, rear_angle, dock, obstacles)

    def _check_activation_conditions(self, dock):
        # 1. Position Check 
        dx = self.rover.x - dock.emit_pos[0]
        dy = self.rover.y - dock.emit_pos[1]
        
        dock_rad = math.radians(dock.facing_angle)
        fwd_x = math.cos(dock_rad); fwd_y = math.sin(dock_rad)
        right_x = -fwd_y; right_y = fwd_x
        
        # Distance forward from dock face
        longitudinal = (dx * fwd_x) + (dy * fwd_y)
        # Distance sideways from center line
        lateral = abs((dx * right_x) + (dy * right_y))
        
        # Must be in front (0 to 400px) and roughly centered (150px)
        if not (0 < longitudinal < 400 and lateral < 150):
            return False

        # 2. Angle Check (CRITICAL FIX)
        # Dock Face points OUT. Rover Rear points BACK.
        # For docking, these vectors should oppose each other (180 deg diff).
        rear_facing_angle = (self.rover.angle + 180) % 360
        angle_diff = (rear_facing_angle - dock.facing_angle + 180) % 360 - 180
        
        # If angle_diff is near 0, we are facing the same way (driving away).
        # If angle_diff is near 180, we are facing opposite (backing in).
        # We want to REJECT if we are facing the same way.
        if abs(angle_diff) < 90:
            return False
            
        return True

    def _cast_laser(self, origin, direction, targets):
        min_dist = TOF_MAX_RANGE_PX
        for rect in targets:
            tl = np.array(rect.topleft); tr = np.array(rect.topright)
            bl = np.array(rect.bottomleft); br = np.array(rect.bottomright)
            segments = [(tl, tr), (tr, br), (br, bl), (bl, tl)]
            for p1, p2 in segments:
                dist = ray_segment_intersection(origin, direction, p1, p2)
                if dist is not None and dist < min_dist:
                    min_dist = dist
        
        if min_dist < TOF_MAX_RANGE_PX:
            min_dist += random.gauss(0, TOF_NOISE_STD_PX)
        
        return max(0.0, min(1.0, min_dist / TOF_MAX_RANGE_PX))

    def _check_ir_beacon(self, sensor_pos, rear_facing_rad, dock, obstacles):
        dx = dock.emit_pos[0] - sensor_pos[0]
        dy = dock.emit_pos[1] - sensor_pos[1]
        dist = math.hypot(dx, dy)
        
        if dist > IR_MAX_RANGE_PX: return 0.0
        
        angle_to_dock = math.atan2(dy, dx)
        angle_diff = (math.degrees(angle_to_dock - rear_facing_rad) + 180) % 360 - 180
        
        if abs(angle_diff) > (REAR_IR_FOV / 2.0): return 0.0
            
        ray_vec = np.array([dx, dy]) / dist
        if dist > 30:
            for rect in obstacles:
                 tl = np.array(rect.topleft); tr = np.array(rect.topright)
                 bl = np.array(rect.bottomleft); br = np.array(rect.bottomright)
                 segments = [(tl, tr), (tr, br), (br, bl), (bl, tl)]
                 for p1, p2 in segments:
                     hit = ray_segment_intersection(sensor_pos, ray_vec, p1, p2)
                     if hit is not None and hit < dist:
                         return 0.0 
                         
        strength = 1.0 - (abs(angle_diff) / (REAR_IR_FOV))
        return max(0.0, strength)

    def get_data(self):
        return self.data
    
    def get_visualization_data(self):
        rear_angle = math.radians(self.rover.angle + 180)
        dir_vec = np.array([math.cos(rear_angle), math.sin(rear_angle)])
        perp_angle = rear_angle + (math.pi / 2.0)
        perp_vec = np.array([math.cos(perp_angle), math.sin(perp_angle)])
        
        cx = self.rover.x + dir_vec[0] * ROVER_RADIUS
        cy = self.rover.y + dir_vec[1] * ROVER_RADIUS
        center_rear = np.array([cx, cy])
        
        l_off = TOF_SPACING / 2.0
        tof_l_start = center_rear + (perp_vec * l_off)
        tof_r_start = center_rear - (perp_vec * l_off)
        
        tof_l_end = tof_l_start + (dir_vec * (self.data[0] * TOF_MAX_RANGE_PX))
        tof_r_end = tof_r_start + (dir_vec * (self.data[1] * TOF_MAX_RANGE_PX))
        
        return (tof_l_start, tof_l_end), (tof_r_start, tof_r_end)