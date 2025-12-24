import pygame
import math
import numpy as np
from config import *

def check_collision(rect, obstacles, bounds_rect):
    """
    Simple AABB collision check.
    Returns True if rect intersects any obstacle or leaves bounds.
    """
    # 1. Check Bounds
    if not bounds_rect.contains(rect):
        return True

    # 2. Check Obstacles
    idx = rect.collidelist(obstacles)
    if idx != -1:
        return True
    
    return False

def circle_rect_collision(circle_center, circle_radius, rect):
    """
    Collision between a circle and a rectangle.
    """
    cx, cy = circle_center
    rx, ry = rect.left, rect.top
    rw, rh = rect.width, rect.height

    # Closest point in rect to circle center
    test_x = cx
    test_y = cy

    if cx < rx:      test_x = rx
    elif cx > rx+rw: test_x = rx+rw
    
    if cy < ry:      test_y = ry
    elif cy > ry+rh: test_y = ry+rh

    dist_x = cx - test_x
    dist_y = cy - test_y
    distance = math.sqrt((dist_x*dist_x) + (dist_y*dist_y))

    return distance <= circle_radius