import pygame
import math
import numpy as np
from config import *

def draw_park_pilot(surface, rover, prox_sensor, show_all_sensors):
    """
    Draws 5 digital-style arcs.
    show_all_sensors: Boolean (Toggle View button status)
    """
    center = (rover.x, rover.y)
    readings = prox_sensor.get_data() # Normalized 0..1

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def draw_digital_arc(start_angle_rel, end_angle_rel, reading, num_segments=4):
        # Thresholds: 
        # > 0.6 : Safe (Green)
        # 0.3 - 0.6 : Warning (Yellow)
        # < 0.3 : Danger (Red)
        
        base_color = None
        
        if show_all_sensors:
            # Toggle ON: Show everything
            # If reading is very high (nothing detected), show IDLE color
            if reading > 0.95:
                base_color = COLOR_PP_IDLE
            elif reading > 0.6:
                base_color = COLOR_PP_SAFE
            elif reading > 0.3:
                base_color = COLOR_PP_WARN
            else:
                base_color = COLOR_PP_DANGER
        else:
            # Toggle OFF: Show only if close
            if reading < 0.3: base_color = COLOR_PP_DANGER
            elif reading < 0.6: base_color = COLOR_PP_WARN
            elif reading < 0.8: base_color = COLOR_PP_SAFE
            else: return # Don't draw if safe/far
            
        # Draw Geometry
        outer_r = ROVER_RADIUS + 40
        inner_r = ROVER_RADIUS + 10
        
        total_span = end_angle_rel - start_angle_rel
        seg_span = total_span / num_segments
        gap = 2
        
        for i in range(num_segments):
            seg_start = start_angle_rel + (i * seg_span) + gap/2
            seg_end = start_angle_rel + ((i+1) * seg_span) - gap/2
            
            points = []
            steps = 4 
            
            # Outer Arc
            for s in range(steps + 1):
                t = s / steps
                ang = math.radians(rover.angle + seg_start + (seg_end - seg_start) * t)
                points.append((center[0] + math.cos(ang) * outer_r, 
                               center[1] + math.sin(ang) * outer_r))
            
            # Inner Arc
            for s in range(steps + 1):
                t = 1.0 - (s / steps)
                ang = math.radians(rover.angle + seg_start + (seg_end - seg_start) * t)
                points.append((center[0] + math.cos(ang) * inner_r, 
                               center[1] + math.sin(ang) * inner_r))
            
            pygame.draw.polygon(overlay, base_color, points)
            pygame.draw.polygon(overlay, (255, 255, 255, 30), points, 1)

    # Draw 3 Front Sensors
    draw_digital_arc(*PP_ANGLES_FRONT[0], readings[0], 3) # FL
    draw_digital_arc(*PP_ANGLES_FRONT[1], readings[1], 3) # FC
    draw_digital_arc(*PP_ANGLES_FRONT[2], readings[2], 3) # FR
    
    # Draw 2 Rear Sensors
    draw_digital_arc(*PP_ANGLES_REAR[0], readings[3], 3)  # RL
    draw_digital_arc(*PP_ANGLES_REAR[1], readings[4], 3)  # RR
    
    surface.blit(overlay, (0,0))