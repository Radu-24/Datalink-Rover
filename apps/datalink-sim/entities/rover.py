import pygame
import math
from config import *

class Rover:
    def __init__(self, x, y, angle_deg):
        self.x = x
        self.y = y
        self.angle = angle_deg 
        
        # Physics State
        self.vx = 0.0 
        self.omega = 0.0
        
        # PWM State (Store for UI)
        self.pwm_l = 0
        self.pwm_r = 0

        self.original_image = self._create_rover_surface()

    def update(self, pwm_action):
        """
        pwm_action: [pwm_left, pwm_right] values from -255 to 255
        """
        self.pwm_l, self.pwm_r = pwm_action
        
        # Normalize PWM to -1.0 to 1.0
        tl = max(-1.0, min(1.0, self.pwm_l / 255.0))
        tr = max(-1.0, min(1.0, self.pwm_r / 255.0))
        
        # Differential Drive Logic (Game Feel)
        # Forward command (avg of tracks)
        cmd_fwd = (tl + tr) / 2.0
        # Turn command (diff of tracks)
        cmd_turn = (tl - tr)
        
        # Apply Acceleration
        target_vx = cmd_fwd * MAX_SPEED_PPS
        target_omega = cmd_turn * TURN_SPEED
        
        # Linear Physics (Smooth lerp)
        self.vx += (target_vx - self.vx) * (DT * 5.0)
        
        # Angular Physics (Snappy turn)
        self.omega += (target_omega - self.omega) * (DT * 8.0)
        
        # Friction/Drag (when no input)
        if abs(cmd_fwd) < 0.1:
            self.vx *= FRICTION
        if abs(cmd_turn) < 0.1:
            self.omega *= FRICTION

        # Integration
        self.angle += self.omega * DT
        self.angle %= 360
        
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.vx * DT
        self.y += math.sin(rad) * self.vx * DT

    def _create_rover_surface(self):
        w_px = ROVER_RADIUS * 2.4
        h_px = ROVER_RADIUS * 2
        surf = pygame.Surface((int(w_px), int(h_px)), pygame.SRCALPHA)
        
        cx, cy = w_px/2, h_px/2
        
        # Treads
        pygame.draw.rect(surf, COLOR_ROVER_TREADS, (0, 0, w_px, h_px*0.25), border_radius=4)
        pygame.draw.rect(surf, COLOR_ROVER_TREADS, (0, h_px*0.75, w_px, h_px*0.25), border_radius=4)
        
        # Body
        body_w, body_h = w_px*0.8, h_px*0.5
        pygame.draw.rect(surf, COLOR_ROVER_BODY, (cx-body_w/2, cy-body_h/2, body_w, body_h), border_radius=2)
        
        # Orange Detail
        pygame.draw.rect(surf, COLOR_ROVER_DETAIL, (cx-body_w/4, cy-5, 10, 10))
        
        # Sensor Head
        pygame.draw.circle(surf, (50, 50, 60), (cx + body_w/4, cy), 6)
        pygame.draw.circle(surf, COLOR_ACCENT, (cx + body_w/4, cy), 3)

        return surf

    def get_rect(self):
        return pygame.Rect(self.x - ROVER_RADIUS, self.y - ROVER_RADIUS, 
                           ROVER_RADIUS*2, ROVER_RADIUS*2)

    def draw(self, surface):
        rotated_image = pygame.transform.rotate(self.original_image, -self.angle)
        new_rect = rotated_image.get_rect(center=(self.x, self.y))
        surface.blit(rotated_image, new_rect)