import math
import numpy as np

def ray_segment_intersection(ray_origin, ray_dir, seg_p1, seg_p2):
    """
    Calculates intersection between a ray (origin, dir) and a line segment (p1, p2).
    Returns distance to intersection or None.
    ray_dir must be normalized.
    """
    v1 = ray_origin - seg_p1
    v2 = seg_p2 - seg_p1
    v3 = np.array([-ray_dir[1], ray_dir[0]]) # perpendicular to ray

    dot_v2_v3 = np.dot(v2, v3)
    
    if abs(dot_v2_v3) < 1e-6:
        return None

    t1 = np.cross(v2, v1) / dot_v2_v3
    t2 = np.dot(v1, v3) / dot_v2_v3

    if t1 >= 0.0 and 0.0 <= t2 <= 1.0:
        return t1
    return None

def get_ray_intersection_dist(origin, angle, obstacles, max_range):
    """
    Casts a single ray against a list of rectangular obstacles.
    obstacles: list of pygame.Rect
    """
    # Create direction vector
    rad = math.radians(angle)
    direction = np.array([math.cos(rad), math.sin(rad)])
    origin_np = np.array(origin, dtype=float)
    
    min_dist = max_range

    for rect in obstacles:
        # Define segments of the rect
        tl = np.array(rect.topleft)
        tr = np.array(rect.topright)
        bl = np.array(rect.bottomleft)
        br = np.array(rect.bottomright)

        segments = [(tl, tr), (tr, br), (br, bl), (bl, tl)]
        
        for p1, p2 in segments:
            dist = ray_segment_intersection(origin_np, direction, p1, p2)
            if dist is not None and dist < min_dist:
                min_dist = dist
                
    return min_dist