import numpy as np
import pygame
from core.world_gen import generate_world
from core.physics import check_collision, circle_rect_collision
from entities.rover import Rover
from entities.dock import DockingStation
from entities.obstacles import Obstacle
from sensors.sensor_suite import SensorSuite
from config import *

class RoverEnv:
    def __init__(self):
        self.obstacles = []
        self.dock = None
        self.rover = None
        self.sensors = None
        self.step_count = 0
        self.max_steps = MAX_STEPS
        self.last_dist = 0
        self.success = False
        self.collided = False
        self.spawn_on_dock_setting = False
        self.current_difficulty = DIFF_MEDIUM 

    def reset(self, force_spawn_dock=False):
        self.step_count = 0
        self.success = False
        self.collided = False
        
        should_spawn_dock = self.spawn_on_dock_setting or force_spawn_dock
        obs_rects, dock_rect, dock_side, start_pos, start_angle = generate_world(
            should_spawn_dock, 
            self.current_difficulty
        )
        
        self.obstacles = obs_rects 
        self.dock = DockingStation(dock_rect, dock_side)
        self.rover = Rover(start_pos[0], start_pos[1], start_angle)
        
        self.sensors = SensorSuite(self.rover)
        obs = self._get_observation()
        self.last_dist = self.sensors.uwb.get_ground_truth_dist(self.dock)
        return obs

    def step(self, action):
        self.step_count += 1
        prev_pos = (self.rover.x, self.rover.y)
        self.rover.update(action)
        
        collision = False
        for obs in self.obstacles:
            if circle_rect_collision((self.rover.x, self.rover.y), ROVER_RADIUS, obs):
                collision = True; break
        if circle_rect_collision((self.rover.x, self.rover.y), ROVER_RADIUS, self.dock.rect):
             collision = True

        if collision:
            self.collided = True
            self.rover.x, self.rover.y = prev_pos
            self.rover.vx = 0.0
            self.rover.omega = 0.0

        self.sensors.update(self.obstacles + [self.dock.rect], self.dock)

        curr_dist = self.sensors.uwb.get_ground_truth_dist(self.dock)
        
        # --- DYNAMIC DOCKING ---
        tol_dist = self.current_difficulty["dist"]
        tol_angle = self.current_difficulty["angle"]
        
        # Check docking (speed is ignored inside function now)
        is_touching, is_parallel, _ = self.dock.check_docking(self.rover, tol_dist, tol_angle)
        
        # INSTANT SUCCESS Logic
        if is_touching and is_parallel:
            self.success = True
            # KILL SWITCH: Stop rover immediately
            self.rover.vx = 0.0
            self.rover.omega = 0.0
        else:
            self.success = False
        
        reward = 0.0
        reward -= 0.01 
        reward += (self.last_dist - curr_dist) * 0.1
        if self.collided: reward -= 10.0
        if self.success: reward += 100.0
        
        self.last_dist = curr_dist
        done = self.success or self.collided or (self.step_count >= self.max_steps)
        info = { "success": self.success, "collided": self.collided, "dist": curr_dist }
        
        return self._get_observation(), reward, done, info

    def _get_observation(self):
        return self.sensors.get_normalized_array()