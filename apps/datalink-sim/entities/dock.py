import pygame
import math
from config import *

class DockingStation:
    def __init__(self, rect, side_index):
        self.rect = rect
        self.side_index = side_index 
        
        if side_index == 0: 
            self.facing_angle = 90
            self.base_pos = (rect.centerx, rect.bottom)
            self.pin_tip = (rect.centerx, rect.bottom + DOCK_PIN_LENGTH)
            self.emit_pos = self.base_pos
            self.line_start = self.base_pos
            self.line_end = (rect.centerx, rect.bottom + 100)
        elif side_index == 1: 
            self.facing_angle = 180
            self.base_pos = (rect.left, rect.centery)
            self.pin_tip = (rect.left - DOCK_PIN_LENGTH, rect.centery)
            self.emit_pos = self.base_pos
            self.line_start = self.base_pos
            self.line_end = (rect.left - 100, rect.centery)
        elif side_index == 2: 
            self.facing_angle = 270
            self.base_pos = (rect.centerx, rect.top)
            self.pin_tip = (rect.centerx, rect.top - DOCK_PIN_LENGTH)
            self.emit_pos = self.base_pos
            self.line_start = self.base_pos
            self.line_end = (rect.centerx, rect.top - 100)
        else: 
            self.facing_angle = 0
            self.base_pos = (rect.right, rect.centery)
            self.pin_tip = (rect.right + DOCK_PIN_LENGTH, rect.centery)
            self.emit_pos = self.base_pos
            self.line_start = self.base_pos
            self.line_end = (rect.right + 100, rect.centery)
            
        self.zone_rect = self._create_zone_rect()

    def _create_zone_rect(self):
        r = self.rect
        depth = DOCK_ZONE_DEPTH
        if self.side_index == 0: return pygame.Rect(r.left, r.bottom, r.width, depth)
        elif self.side_index == 1: return pygame.Rect(r.left - depth, r.top, depth, r.height)
        elif self.side_index == 2: return pygame.Rect(r.left, r.top - depth, r.width, depth)
        else: return pygame.Rect(r.right, r.top, depth, r.height)

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_DOCK_BODY, self.rect)
        s = pygame.Surface((self.zone_rect.width, self.zone_rect.height), pygame.SRCALPHA)
        s.fill(COLOR_DOCK_ZONE)
        surface.blit(s, self.zone_rect.topleft)
        pygame.draw.line(surface, (255, 200, 0, 100), self.line_start, self.line_end, 1)
        pygame.draw.line(surface, (255, 255, 0), self.base_pos, self.pin_tip, 4)
        pygame.draw.circle(surface, (255, 255, 0), (int(self.pin_tip[0]), int(self.pin_tip[1])), 3)

    def check_docking(self, rover, tol_dist, tol_angle):
        # 1. Rover Charging Port
        rear_angle = math.radians(rover.angle + 180)
        port_x = rover.x + math.cos(rear_angle) * ROVER_RADIUS
        port_y = rover.y + math.sin(rear_angle) * ROVER_RADIUS
        
        # 2. Distance to Base
        dx = self.base_pos[0] - port_x
        dy = self.base_pos[1] - port_y
        dist = math.hypot(dx, dy)
        
        # 3. Check Contact
        is_touching = dist < tol_dist 
        
        # 4. Alignment Check
        diff = (rover.angle - self.facing_angle + 180) % 360 - 180
        is_parallel = abs(diff) < tol_angle
        
        # SPEED IGNORED for Success trigger (Instant Docking)
        speed_ok = True 
        
        return is_touching, is_parallel, speed_ok