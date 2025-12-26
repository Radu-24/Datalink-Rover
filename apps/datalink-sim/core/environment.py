import numpy as np
import math
import gymnasium as gym
from gymnasium import spaces
from core.world_gen import generate_world
from core.physics import circle_rect_collision
from entities.rover import Rover
from entities.dock import DockingStation
from sensors.sensor_suite import SensorSuite
from config import *

# --- STAGE DEFINITIONS ---
STAGE_SEARCH = 0    
STAGE_APPROACH = 1  
STAGE_ROTATE = 2    
STAGE_DOCKING = 3   

class RoverEnv(gym.Env):
    def __init__(self):
        super(RoverEnv, self).__init__()
        
        self.obstacles = []
        self.dock = None
        self.rover = None
        self.sensors = None
        
        # Action: [PWM_Left, PWM_Right]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        
        # Observation: 56 inputs
        # We ensure the inputs are normalized to help the AI learn faster
        self.observation_space = spaces.Box(low=-1.0, high=2.0, shape=(56,), dtype=np.float32)

        self.step_count = 0
        self.max_steps = MAX_STEPS
        self.last_dist = 0
        self.success = False
        self.collided = False
        self.spawn_on_dock_setting = False 
        self.current_difficulty = DIFF_MEDIUM 
        self.current_stage = STAGE_SEARCH
        
        self.milestones = set()
        self.approach_start_dist = None 
        self.approach_record = None     

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0
        self.success = False
        self.collided = False
        self.current_stage = STAGE_SEARCH
        
        self.milestones = set() 
        self.approach_start_dist = None
        self.approach_record = None
        
        should_spawn_dock = self.spawn_on_dock_setting 
            
        obs_rects, dock_rect, dock_side, start_pos, start_angle = generate_world(
            should_spawn_dock, 
            self.current_difficulty
        )
        
        self.obstacles = obs_rects 
        self.dock = DockingStation(dock_rect, dock_side)
        self.rover = Rover(start_pos[0], start_pos[1], start_angle)
        
        self.sensors = SensorSuite(self.rover)
        self.sensors.update(self.obstacles + [self.dock.rect], self.dock)
        
        obs = self._get_observation()
        
        self.last_dist = self.sensors.uwb.get_ground_truth_dist(self.dock)
        return obs, {}

    def step(self, action):
        self.step_count += 1
        
        # Convert -1..1 action to PWM
        pwm_l = action[0] * 255.0
        pwm_r = action[1] * 255.0
        
        prev_pos = (self.rover.x, self.rover.y)
        self.rover.update([pwm_l, pwm_r])
        
        # --- COLLISION CHECKS ---
        collision = False
        if not (0 < self.rover.x < VIEWPORT_WIDTH and 0 < self.rover.y < VIEWPORT_HEIGHT):
            collision = True
        for obs in self.obstacles:
            if circle_rect_collision((self.rover.x, self.rover.y), ROVER_RADIUS, obs):
                collision = True; break
        if circle_rect_collision((self.rover.x, self.rover.y), ROVER_RADIUS, self.dock.rect):
             collision = True

        if collision:
            self.collided = True
            self.rover.x, self.rover.y = prev_pos
            self.rover.vx = 0.0; self.rover.omega = 0.0

        # --- SENSOR UPDATES ---
        self.sensors.update(self.obstacles + [self.dock.rect], self.dock)
        curr_dist = self.sensors.uwb.get_ground_truth_dist(self.dock)
        
        reward = 0.0
        done = False
        info = { "stage": self.current_stage, "is_success": False }
        
        # Base Time Penalty (encourage speed, but small enough to allow patience)
        reward -= 0.005 
        
        if self.collided:
            # Big penalty for crashing
            return self._get_observation(), -50.0, True, False, info

        # ===================================================================
        # STAGE 0: SEARCH (The "Compass & Orbit" Phase)
        # ===================================================================
        if self.current_stage == STAGE_SEARCH:
            
            # 1. Navigation Logic (Compass)
            dock_x, dock_y = self.dock.emit_pos 
            target_angle = math.degrees(math.atan2(dock_y - self.rover.y, dock_x - self.rover.x))
            # Calculate angle difference (-180 to 180)
            angle_diff = (target_angle - self.rover.angle + 180) % 360 - 180
            
            # Reward facing the target
            reward += (1.0 - abs(angle_diff) / 180.0) * 0.1

            # 2. "Wrong Side" Logic (Orbiting)
            # If we are CLOSE (within 300px) but DO NOT see the beam (ILS)
            ir_data = self.sensors.ir.get_data()
            seeing_ils = (ir_data[0] > 0 or ir_data[1] > 0)
            
            dist_improvement = (self.last_dist - curr_dist)

            if curr_dist < 300 and not seeing_ils:
                # We are likely behind the dock or to the side.
                # PUNISH moving closer. We want it to circle.
                if dist_improvement > 0:
                    reward -= dist_improvement * 2.0  # Harsh penalty for approaching blind
                else:
                    reward += 0.05 # Slight reward for keeping distance/orbiting
            else:
                # Standard Gravity: Reward getting closer
                if dist_improvement > 0: 
                    reward += dist_improvement * 0.5 

            # 3. Transition to Approach
            if seeing_ils:
                if "found_beam" not in self.milestones:
                    reward += 10.0
                    self.milestones.add("found_beam")
                self.current_stage = STAGE_APPROACH

        # ===================================================================
        # STAGE 1: APPROACH (The "Precision Funnel")
        # ===================================================================
        elif self.current_stage == STAGE_APPROACH:
            ir_data = self.sensors.ir.get_data()
            
            # Check if we lost the beam
            if ir_data[0] == 0 and ir_data[1] == 0:
                reward -= 2.0
                self.current_stage = STAGE_SEARCH # Fallback to search
            
            else:
                # 1. Centering Reward (Dead Ahead)
                # Calculate balance between left (0) and right (1) sensors
                # If both are strong and equal, that is perfect.
                balance = abs(ir_data[0] - ir_data[1])
                reward += (1.0 - balance) * 0.2  # Reward for keeping beam centered
                
                # 2. Speed Control (Slow down to react)
                # Average throttle (0 to 1)
                throttle_avg = (abs(action[0]) + abs(action[1])) / 2.0
                
                if throttle_avg > 0.5:
                    reward -= 0.1  # Penalty for rushing
                else:
                    reward += 0.05 # Reward for cautious approach

                # 3. Ratchet Progress
                if self.approach_start_dist is None:
                    self.approach_start_dist = curr_dist
                    self.approach_record = curr_dist
                
                diff_record = self.approach_record - curr_dist
                if diff_record > 0:
                    reward += diff_record * 3.0 # Strong reward for new distance record
                    self.approach_record = curr_dist
                
                # Transition to Rotate
                if ir_data[5] > 0: # Assuming index 5 is the "Close Range" or "Docked" sensor
                    if "reached_turn" not in self.milestones:
                        reward += 20.0 
                        self.milestones.add("reached_turn")
                    self.current_stage = STAGE_ROTATE
                    self.rover.vx = 0 

        # ===================================================================
        # STAGE 2: ROTATE (Aligning to dock face)
        # ===================================================================
        elif self.current_stage == STAGE_ROTATE:
            # Penalize moving, only rotation allowed
            if abs(self.rover.vx) > 2.0: reward -= 0.5
            
            rear_angle = (self.rover.angle + 180) % 360
            angle_diff = (rear_angle - self.dock.facing_angle + 180) % 360 - 180
            
            # Smooth reward for alignment
            reward += (1.0 - abs(angle_diff)/180.0) * 0.5
            
            if abs(angle_diff) < 10: # Strict alignment
                if "aligned" not in self.milestones:
                    reward += 20.0
                    self.milestones.add("aligned")
                self.current_stage = STAGE_DOCKING

        # ===================================================================
        # STAGE 3: DOCKING (Final Connection)
        # ===================================================================
        elif self.current_stage == STAGE_DOCKING:
            # Move backwards slowly
            if pwm_l > 0 or pwm_r > 0: reward -= 0.1  # Don't go forward
            else: reward += 0.1 
            
            # Rear Laser Alignment
            rear_data = self.sensors.rear.get_data() 
            las_diff = abs(rear_data[0] - rear_data[1])
            
            if las_diff > 0.1: reward -= 0.2 
            else: reward += 0.2 
            
            tol_dist = self.current_difficulty["dist"]
            tol_angle = self.current_difficulty["angle"]
            is_touching, is_parallel, speed_ok = self.dock.check_docking(self.rover, tol_dist, tol_angle)
            
            if is_touching:
                if is_parallel and speed_ok:
                    reward += 100.0 
                    self.success = True
                    info["is_success"] = True
                    done = True
                else:
                    reward -= 50.0 # Crashing into dock or bad angle
                    done = True 

        self.last_dist = curr_dist
        if self.step_count >= self.max_steps: 
            done = True
        
        return self._get_observation(), reward, done, False, info

    def _get_observation(self):
        sensor_data = self.sensors.get_normalized_array()
        # Add stage info to help the AI know which "mode" it should be in
        stage_norm = [self.current_stage / 3.0] 
        return np.concatenate([sensor_data, stage_norm], dtype=np.float32)