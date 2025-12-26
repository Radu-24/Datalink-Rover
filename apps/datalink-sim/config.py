import math

# --- Window & Rendering ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
VIEWPORT_WIDTH = 800
VIEWPORT_HEIGHT = 700
UI_PANEL_WIDTH = SCREEN_WIDTH - VIEWPORT_WIDTH

FPS = 60
TITLE = "DataLink Rover Sim - v15.0 (Unrestricted Physics)"

# --- Colors ---
COLOR_BG = (10, 12, 16)
COLOR_GRID = (30, 35, 45)
COLOR_WALL = (60, 70, 80)
COLOR_OBSTACLE = (160, 60, 60)
COLOR_DOCK_BODY = (40, 160, 100)
COLOR_DOCK_ZONE = (40, 160, 100, 40)
COLOR_ROVER_BODY = (200, 200, 210)
COLOR_ROVER_TREADS = (40, 40, 45)
COLOR_ROVER_DETAIL = (255, 165, 0)
COLOR_UI_BG = (20, 24, 28)
COLOR_UI_BORDER = (80, 90, 100)
COLOR_TEXT_MAIN = (200, 220, 255)
COLOR_TEXT_DIM = (100, 120, 140)
COLOR_ACCENT = (0, 200, 255)
COLOR_BTN_IDLE = (60, 60, 70)
COLOR_BTN_HOVER = (80, 80, 90)
COLOR_TEXT = (220, 220, 220)
COLOR_PP_IDLE = (80, 90, 100, 40)
COLOR_PP_SAFE = (0, 255, 100, 100)
COLOR_PP_WARN = (255, 200, 0, 150)
COLOR_PP_DANGER = (255, 50, 50, 200)
COLOR_WARNING = (255, 50, 50)

# --- REAL LIFE PHYSICS SCALE ---
# Viewport is 800px. If we want that to be 10 meters:
# 800 px / 10 m = 80 px/m
METERS_TO_PIXELS = 80 
ROVER_RADIUS = 20 # 20px radius = 40px width = 0.5m wide (Large RC Car)

# Physics
DT = 1.0 / FPS
# 3.0 m/s * 80 px/m = 240 px/s
MAX_SPEED_PPS = 240.0   
ACCEL_FACTOR = 400.0    
FRICTION = 0.90         
TURN_SPEED = 180.0      

# --- SAFETY ASSIST ---
SAFETY_YELLOW_DIST_PX = 80 
SAFETY_RED_DIST_PX = 30     
SAFETY_SPEED_LIMIT = 0.3    

# --- SENSORS ---
LIDAR_FOV = 180
LIDAR_NUM_RAYS = 36
LIDAR_MAX_RANGE_PX = 300 # ~3.75m range
LIDAR_NOISE_STD_PX = 2.0 

PROX_MAX_RANGE_PX = 120  # ~1.5m range
PP_ANGLES_FRONT = [(-45, -25), (-10, 10), (25, 45)] 
PP_ANGLES_REAR = [(150, 170), (190, 210)]

UWB_MAX_RANGE_PX = 700   # ~8.75m range
UWB_NOISE_STD_PX = 15.0  

# --- FRONT IR (Approach / ILS) ---
IR_MAX_RANGE_PX = 500     
IR_FRONT_CONE = 45        
IR_TURN_DIST = 100        
IR_TURN_TOLERANCE = 15    
IR_CONE_INNER = 5   
IR_CONE_OUTER = 60  

# --- REAR DOCKING SYSTEM (Real Life Fusion) ---
REAR_IR_SPACING = 30    
REAR_IR_FOV = 60        

TOF_MAX_RANGE_PX = 200 # ~2.5m range
TOF_SPACING = 34        
TOF_NOISE_STD_PX = 0.2 # Lowered noise for stability

# --- Difficulty Settings ---
# 'dist' is pixels. 16px is ~20cm tolerance.
DIFF_EASY = { "name": "EASY", "obs": 2, "complex": 0.0, "clutter": 0.0, "dist": 24, "angle": 40 }
DIFF_MEDIUM = { "name": "MEDIUM", "obs": 6, "complex": 0.15, "clutter": 0.10, "dist": 16, "angle": 10 }
DIFF_HARD = { "name": "HARD", "obs": 10, "complex": 0.40, "clutter": 0.30, "dist": 10, "angle": 5 }
DIFF_DOCKING = { "name": "DOCKING ONLY", "obs": 0, "complex": 0.0, "clutter": 0.0, "dist": 16, "angle": 10 }

# --- World Generation ---
GRID_SIZE = 40

# --- Docking ---
DOCK_WIDTH = 60
DOCK_HEIGHT = 20
DOCK_ZONE_DEPTH = 80      
DOCK_PIN_LENGTH = 15      

# --- Gym / Modes ---
MAX_STEPS = 1200