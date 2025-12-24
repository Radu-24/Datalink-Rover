import numpy as np
import math
import random
from config import *
from core.raycast import get_ray_intersection_dist

class Lidar:
    def __init__(self, rover):
        self.rover = rover
        self.distances = np.zeros(LIDAR_NUM_RAYS)
        
        # Create rays covering ONLY the front FOV (e.g., -90 to +90)
        half_fov = LIDAR_FOV / 2.0
        self.ray_angles = np.linspace(-half_fov, half_fov, LIDAR_NUM_RAYS)
        
    def update(self, obstacles):
        for i, angle_offset in enumerate(self.ray_angles):
            # Calculate global angle
            global_angle = (self.rover.angle + angle_offset) % 360
            
            # True distance
            true_dist_px = get_ray_intersection_dist(
                (self.rover.x, self.rover.y), 
                global_angle, 
                obstacles, 
                LIDAR_MAX_RANGE_PX
            )
            
            # Add Gaussian Noise
            noise = random.gauss(0, LIDAR_NOISE_STD_PX)
            dist_px = true_dist_px + noise
            
            # Clamp
            dist_px = max(0.0, min(dist_px, LIDAR_MAX_RANGE_PX))
            
            # Store normalized (0..1)
            self.distances[i] = dist_px / LIDAR_MAX_RANGE_PX
            
    def get_data(self):
        return self.distances