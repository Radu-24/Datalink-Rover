import pygame
import math
import numpy as np
from config import *

def draw_park_pilot(surface, rover, prox_sensor, show_all_sensors):
    # SAFETY CHECK 1: If the rover itself is "broken" (NaN position), stop immediately.
    if not math.isfinite(rover.x) or not math.isfinite(rover.y) or not math.isfinite(rover.angle):
        return

    center = (rover.x, rover.y)
    readings = prox_sensor.get_data() 

    # Create a temporary surface for transparency
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def draw_digital_arc(start_angle_rel, end_angle_rel, reading, num_segments=4):
        # SAFETY CHECK 2: If sensor reading is invalid, skip this arc
        if not math.isfinite(reading):
            return

        base_color = None
        
        # Color Logic
        if show_all_sensors:
            if reading > 0.95: base_color = COLOR_PP_IDLE
            elif reading > 0.6: base_color = COLOR_PP_SAFE
            elif reading > 0.3: base_color = COLOR_PP_WARN
            else: base_color = COLOR_PP_DANGER
        else:
            # Auto-hide mode
            if reading < 0.3: base_color = COLOR_PP_DANGER
            elif reading < 0.6: base_color = COLOR_PP_WARN
            elif reading < 0.8: base_color = COLOR_PP_SAFE
            else: return # Don't draw
            
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
            
            try:
                # Outer Arc
                for s in range(steps + 1):
                    t = s / steps
                    # Calculate angle
                    ang = math.radians(rover.angle + seg_start + (seg_end - seg_start) * t)
                    
                    # Calculate points
                    px = center[0] + math.cos(ang) * outer_r
                    py = center[1] + math.sin(ang) * outer_r
                    
                    # SAFETY CHECK 3: Check every single point
                    if not (math.isfinite(px) and math.isfinite(py)):
                        return 
                    points.append((px, py))
                
                # Inner Arc
                for s in range(steps + 1):
                    t = 1.0 - (s / steps)
                    ang = math.radians(rover.angle + seg_start + (seg_end - seg_start) * t)
                    
                    px = center[0] + math.cos(ang) * inner_r
                    py = center[1] + math.sin(ang) * inner_r
                    
                    if not (math.isfinite(px) and math.isfinite(py)):
                        return
                    points.append((px, py))
                
                if len(points) > 2:
                    pygame.draw.polygon(overlay, base_color, points)
                    pygame.draw.polygon(overlay, (255, 255, 255, 30), points, 1)
                    
            except TypeError:
                # Catch any remaining "points must be number pairs" errors silently
                return

    # Draw Front Sensors
    draw_digital_arc(*PP_ANGLES_FRONT[0], readings[0], 3) 
    draw_digital_arc(*PP_ANGLES_FRONT[1], readings[1], 3) 
    draw_digital_arc(*PP_ANGLES_FRONT[2], readings[2], 3) 
    
    # Draw Rear Sensors
    draw_digital_arc(*PP_ANGLES_REAR[0], readings[3], 3) 
    draw_digital_arc(*PP_ANGLES_REAR[1], readings[4], 3) 
    
    surface.blit(overlay, (0,0))