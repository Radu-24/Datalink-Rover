import pygame
import random
import math
import numpy as np
from config import *
from entities.obstacles import Obstacle
from collections import deque

def generate_world(spawn_on_dock=False, difficulty=DIFF_MEDIUM):
    # Walls
    walls = []
    walls.append(pygame.Rect(0, 0, VIEWPORT_WIDTH, 10)) 
    walls.append(pygame.Rect(0, VIEWPORT_HEIGHT - 10, VIEWPORT_WIDTH, 10))
    walls.append(pygame.Rect(0, 0, 10, VIEWPORT_HEIGHT))
    walls.append(pygame.Rect(VIEWPORT_WIDTH - 10, 0, 10, VIEWPORT_HEIGHT))

    max_attempts = 100
    for attempt in range(max_attempts):
        obstacles = list(walls)
        
        # --- Dock Placement ---
        side = random.randint(0, 3)
        dock_rect = None
        dock_front_pos = None
        dock_facing_angle = 0
        
        # Safe Zone Parameters (The "Runway")
        safe_dist = 250  # Length of clear area in front of dock
        safe_width = 140 # Width of clear area
        safe_zone = None
        
        spawn_buffer = 40 
        
        if side == 0: # Top (Faces Down)
            x = random.randint(50, VIEWPORT_WIDTH - 50 - DOCK_WIDTH)
            dock_rect = pygame.Rect(x, 10, DOCK_WIDTH, DOCK_HEIGHT)
            dock_front_pos = (x + DOCK_WIDTH//2, 10 + DOCK_HEIGHT + spawn_buffer)
            dock_facing_angle = 90
            # Safe Zone extends DOWN
            safe_zone = pygame.Rect(dock_rect.centerx - safe_width//2, dock_rect.bottom, safe_width, safe_dist)
            
        elif side == 1: # Right (Faces Left)
            y = random.randint(50, VIEWPORT_HEIGHT - 50 - DOCK_WIDTH)
            dock_rect = pygame.Rect(VIEWPORT_WIDTH - 10 - DOCK_HEIGHT, y, DOCK_HEIGHT, DOCK_WIDTH)
            dock_front_pos = (VIEWPORT_WIDTH - 10 - DOCK_HEIGHT - spawn_buffer, y + DOCK_WIDTH//2)
            dock_facing_angle = 180
            # Safe Zone extends LEFT
            safe_zone = pygame.Rect(dock_rect.left - safe_dist, dock_rect.centery - safe_width//2, safe_dist, safe_width)
            
        elif side == 2: # Bottom (Faces Up)
            x = random.randint(50, VIEWPORT_WIDTH - 50 - DOCK_WIDTH)
            dock_rect = pygame.Rect(x, VIEWPORT_HEIGHT - 10 - DOCK_HEIGHT, DOCK_WIDTH, DOCK_HEIGHT)
            dock_front_pos = (x + DOCK_WIDTH//2, VIEWPORT_HEIGHT - 10 - DOCK_HEIGHT - spawn_buffer)
            dock_facing_angle = 270
            # Safe Zone extends UP
            safe_zone = pygame.Rect(dock_rect.centerx - safe_width//2, dock_rect.top - safe_dist, safe_width, safe_dist)
            
        else: # Left (Faces Right)
            y = random.randint(50, VIEWPORT_HEIGHT - 50 - DOCK_WIDTH)
            dock_rect = pygame.Rect(10, y, DOCK_HEIGHT, DOCK_WIDTH)
            dock_front_pos = (10 + DOCK_HEIGHT + spawn_buffer, y + DOCK_WIDTH//2)
            dock_facing_angle = 0
            # Safe Zone extends RIGHT
            safe_zone = pygame.Rect(dock_rect.right, dock_rect.centery - safe_width//2, safe_dist, safe_width)

        # --- Map Generation ---
        num_obs = difficulty["obs"]
        chance_complex = difficulty["complex"]
        chance_clutter = difficulty["clutter"]
        
        generated_obs = []
        rand_val = random.random()
        
        if rand_val < chance_complex:
            # Complex
            mid_x = VIEWPORT_WIDTH // 2
            mid_y = VIEWPORT_HEIGHT // 2
            if random.choice([True, False]):
                generated_obs.append(pygame.Rect(mid_x - 10, 100, 20, VIEWPORT_HEIGHT - 200)) 
            else:
                generated_obs.append(pygame.Rect(100, mid_y - 10, VIEWPORT_WIDTH - 200, 20)) 
        
        elif rand_val < (chance_complex + chance_clutter):
            # Cluttered
            for _ in range(num_obs + 4):
                w = random.randint(20, 50)
                h = random.randint(20, 50)
                x = random.randint(50, VIEWPORT_WIDTH - 50 - w)
                y = random.randint(50, VIEWPORT_HEIGHT - 50 - h)
                generated_obs.append(pygame.Rect(x, y, w, h))
        else:
            # Standard
            for _ in range(num_obs):
                w = random.randint(40, 120)
                h = random.randint(40, 120)
                x = random.randint(50, VIEWPORT_WIDTH - 50 - w)
                y = random.randint(50, VIEWPORT_HEIGHT - 50 - h)
                generated_obs.append(pygame.Rect(x, y, w, h))

        # --- STRICT FILTERING ---
        final_obs = []
        
        # Buffer around the dock body itself (prevents touching)
        immediate_buffer = dock_rect.inflate(40, 40)
        
        for r in generated_obs:
            # 1. Must not hit the "Runway" (Safe Zone)
            # 2. Must not hit the dock itself
            if not r.colliderect(safe_zone) and not r.colliderect(immediate_buffer):
                final_obs.append(r)

        all_blockers = obstacles + final_obs + [dock_rect]

        # --- Rover Spawn ---
        start_pos = (0,0)
        start_angle = 0
        
        if spawn_on_dock:
            start_pos = dock_front_pos
            start_angle = dock_facing_angle
        else:
            found = False
            for _ in range(50):
                rx = random.randint(50, VIEWPORT_WIDTH - 50)
                ry = random.randint(50, VIEWPORT_HEIGHT - 50)
                r_rect = pygame.Rect(rx - ROVER_RADIUS, ry - ROVER_RADIUS, ROVER_RADIUS*2, ROVER_RADIUS*2)
                
                # Ensure rover doesn't spawn INSIDE the safe zone either (unless on dock)
                # This prevents spawning instantly in front of the dock facing the wrong way
                in_safe_zone = r_rect.colliderect(safe_zone)
                
                dist_to_dock = math.hypot(rx - dock_front_pos[0], ry - dock_front_pos[1])
                
                # FIXED: Reduced distance check from 300 to 200 to allow spawning in Hard mode
                if r_rect.collidelist(all_blockers) == -1 and dist_to_dock > 200 and not in_safe_zone:
                    start_pos = (rx, ry)
                    start_angle = random.randint(0, 360)
                    found = True
                    break
            if not found: continue

        if is_feasible(start_pos, dock_front_pos, all_blockers):
            return final_obs + obstacles, dock_rect, side, start_pos, start_angle

    # Fallback
    return walls, pygame.Rect(400, 0, 60, 20), 0, (400, 400), 0

def is_feasible(start, end, obstacles):
    rows = VIEWPORT_HEIGHT // GRID_SIZE
    cols = VIEWPORT_WIDTH // GRID_SIZE
    grid = np.zeros((cols, rows), dtype=int)
    for obs in obstacles:
        c1 = max(0, obs.left // GRID_SIZE)
        c2 = min(cols, (obs.right // GRID_SIZE) + 1)
        r1 = max(0, obs.top // GRID_SIZE)
        r2 = min(rows, (obs.bottom // GRID_SIZE) + 1)
        grid[c1:c2, r1:r2] = 1
    
    start_c, start_r = int(start[0] // GRID_SIZE), int(start[1] // GRID_SIZE)
    end_c, end_r = int(end[0] // GRID_SIZE), int(end[1] // GRID_SIZE)
    
    if not (0 <= start_c < cols and 0 <= start_r < rows): return False
    
    queue = deque([(start_c, start_r)])
    visited = set([(start_c, start_r)])
    while queue:
        c, r = queue.popleft()
        if c == end_c and r == end_r: return True
        for dc, dr in [(0,1), (0,-1), (1,0), (-1,0)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < cols and 0 <= nr < rows and grid[nc,nr] == 0 and (nc,nr) not in visited:
                visited.add((nc,nr))
                queue.append((nc,nr))
    return False