import pygame
import sys
import math
import numpy as np
from config import *
from core.environment import RoverEnv
from core.raycast import ray_segment_intersection
from ui.parkpilot import draw_park_pilot
from ui.hud import HUD
from ui.buttons import Button

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    
    env = RoverEnv()
    hud = HUD()
    
    STATE_RUNNING = 0
    STATE_MENU = 1
    STATE_DIFF_MENU = 2
    current_state = STATE_RUNNING
    
    MODE_MANUAL = "Manual"
    MODE_PATH = "Pathfinding"
    MODE_RTH = "RTH (AI)"
    current_mode = MODE_MANUAL
    
    setting_spawn_on_dock = False
    show_sensors = False 
    dock_timer = 0
    has_left_dock = False
    
    # MASTER SWITCH FOR AI TRAINING
    ai_train_active = False
    
    env.reset()
    font_menu = pygame.font.SysFont("Arial", 24)
    
    # State Switchers
    def toggle_menu():
        nonlocal current_state
        if current_state == STATE_RUNNING: current_state = STATE_MENU
        else: current_state = STATE_RUNNING
        
    def open_diff_menu():
        nonlocal current_state
        current_state = STATE_DIFF_MENU

    def set_difficulty(diff_preset):
        nonlocal current_state
        env.current_difficulty = diff_preset
        env.reset()
        current_state = STATE_RUNNING
        
    def close_diff_menu():
        nonlocal current_state
        current_state = STATE_RUNNING

    def set_mode(mode):
        nonlocal current_mode, has_left_dock
        current_mode = mode
        if mode == MODE_PATH: env.spawn_on_dock_setting = True
        else: env.spawn_on_dock_setting = setting_spawn_on_dock
        env.reset()
        has_left_dock = False
        if current_state == STATE_MENU: toggle_menu()

    def toggle_spawn_setting():
        nonlocal setting_spawn_on_dock
        setting_spawn_on_dock = not setting_spawn_on_dock
        env.spawn_on_dock_setting = setting_spawn_on_dock
        
    def toggle_sensor_view():
        nonlocal show_sensors
        show_sensors = not show_sensors

    def toggle_ai_train():
        nonlocal ai_train_active, current_mode
        ai_train_active = not ai_train_active
        
        if ai_train_active:
            # LOCKDOWN: Force RTH, Close Menus
            current_mode = MODE_RTH
            current_state = STATE_RUNNING # Force close menu if open

    def reset_sim():
        nonlocal has_left_dock
        env.reset()
        has_left_dock = False

    def draw_blocked_beam(surface, start_pos, start_angle, end_angle, color, obstacles):
        points = [start_pos]
        steps = 15
        max_dist = 400
        angles = np.linspace(start_angle, end_angle, steps)
        for ang_rad in angles:
            ray_dir = np.array([math.cos(ang_rad), math.sin(ang_rad)])
            ray_origin = np.array(start_pos)
            closest_dist = max_dist
            for rect in obstacles:
                tl = np.array(rect.topleft); tr = np.array(rect.topright)
                bl = np.array(rect.bottomleft); br = np.array(rect.bottomright)
                segments = [(tl, tr), (tr, br), (br, bl), (bl, tl)]
                for p1, p2 in segments:
                    hit = ray_segment_intersection(ray_origin, ray_dir, p1, p2)
                    if hit is not None and hit < closest_dist:
                        closest_dist = hit
            end_x = start_pos[0] + ray_dir[0] * closest_dist
            end_y = start_pos[1] + ray_dir[1] * closest_dist
            points.append((end_x, end_y))
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points)

    # --- BUTTONS ---
    btn_ai        = Button(VIEWPORT_WIDTH + 20, SCREEN_HEIGHT - 220, 160, 50, "AI TRAIN: OFF", toggle_ai_train)
    btn_diff      = Button(VIEWPORT_WIDTH + 20, SCREEN_HEIGHT - 150, 160, 40, "DIFFICULTY", open_diff_menu)
    btn_settings  = Button(VIEWPORT_WIDTH + 20, SCREEN_HEIGHT - 100, 160, 40, "MENU / MODES", toggle_menu)
    btn_toggle_view = Button(VIEWPORT_WIDTH + 20, SCREEN_HEIGHT - 50, 160, 40, "TOGGLE SENSORS", toggle_sensor_view)
    
    menu_btns = [
        Button(SCREEN_WIDTH//2 - 100, 150, 200, 40, "Mode: MANUAL", lambda: set_mode(MODE_MANUAL)),
        Button(SCREEN_WIDTH//2 - 100, 200, 200, 40, "Mode: PATHFINDING", lambda: set_mode(MODE_PATH)),
        Button(SCREEN_WIDTH//2 - 100, 250, 200, 40, "Mode: RTH (AI)", lambda: set_mode(MODE_RTH)),
        Button(SCREEN_WIDTH//2 - 100, 320, 200, 40, "Toggle Spawn Dock", toggle_spawn_setting),
        Button(SCREEN_WIDTH//2 - 100, 450, 200, 40, "CLOSE MENU", toggle_menu)
    ]

    diff_btns = [
        Button(SCREEN_WIDTH//2 - 100, 200, 200, 40, "EASY (Forgiving)", lambda: set_difficulty(DIFF_EASY)),
        Button(SCREEN_WIDTH//2 - 100, 250, 200, 40, "MEDIUM (Standard)", lambda: set_difficulty(DIFF_MEDIUM)),
        Button(SCREEN_WIDTH//2 - 100, 300, 200, 40, "HARD (Strict)", lambda: set_difficulty(DIFF_HARD)),
        Button(SCREEN_WIDTH//2 - 100, 350, 200, 40, "DOCKING ONLY", lambda: set_difficulty(DIFF_DOCKING)),
        Button(SCREEN_WIDTH//2 - 100, 450, 200, 40, "BACK", close_diff_menu)
    ]

    while True:
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: reset_sim()

            if current_state == STATE_RUNNING:
                btn_ai.handle_event(event)
                if not ai_train_active:
                    btn_diff.handle_event(event)
                    btn_settings.handle_event(event)
                    btn_toggle_view.handle_event(event)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: toggle_menu()
            
            elif current_state == STATE_MENU:
                for b in menu_btns: b.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: toggle_menu()
                
            elif current_state == STATE_DIFF_MENU:
                for b in diff_btns: b.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: close_diff_menu()

        if current_state == STATE_RUNNING:
            keys = pygame.key.get_pressed()
            pwm_l, pwm_r = 0, 0
            PWM_POWER = 220 
            
            # Check for docking mode to slow down
            rear_data = env.sensors.rear.get_data()
            # If any rear sensor is picking up signal, slow down
            is_docking_mode = (rear_data[2] > 0.1 or rear_data[3] > 0.1)
            turn_power = PWM_POWER
            if is_docking_mode: turn_power *= 0.3 

            # ==========================================
            #           CONTROL LOGIC BLOCK
            # ==========================================
            
            if ai_train_active:
                # LOCKED
                pwm_l, pwm_r = 0, 0 
                
            else:
                # MANUAL
                if keys[pygame.K_w]: pwm_l += PWM_POWER; pwm_r += PWM_POWER
                if keys[pygame.K_s]: pwm_l -= PWM_POWER; pwm_r -= PWM_POWER
                if keys[pygame.K_a]: pwm_l -= turn_power; pwm_r += turn_power
                if keys[pygame.K_d]: pwm_l += turn_power; pwm_r -= turn_power
                if keys[pygame.K_SPACE]: pwm_l, pwm_r = 0, 0; env.rover.vx = 0

                # --- SAFETY ASSIST ---
                if current_mode == MODE_MANUAL:
                    readings = env.sensors.prox.get_data()
                    min_front = np.min(readings[0:3])
                    min_rear = np.min(readings[3:5])
                    
                    THRESH_YELLOW = 0.75
                    THRESH_RED = 0.50
                    THRESH_CRITICAL = 0.30
                    FACTOR_YELLOW = 0.5 
                    FACTOR_RED = 0.2    

                    if pwm_l > 0 or pwm_r > 0:
                        if min_front < THRESH_CRITICAL:
                            if pwm_l > 0: pwm_l = 0
                            if pwm_r > 0: pwm_r = 0
                        elif min_front < THRESH_RED:
                            if pwm_l > 0: pwm_l *= FACTOR_RED
                            if pwm_r > 0: pwm_r *= FACTOR_RED
                        elif min_front < THRESH_YELLOW:
                            if pwm_l > 0: pwm_l *= FACTOR_YELLOW
                            if pwm_r > 0: pwm_r *= FACTOR_YELLOW

                    if pwm_l < 0 or pwm_r < 0:
                        if min_rear < THRESH_CRITICAL:
                            if pwm_l < 0: pwm_l = 0
                            if pwm_r < 0: pwm_r = 0
                        elif min_rear < THRESH_RED:
                            if pwm_l < 0: pwm_l *= FACTOR_RED
                            if pwm_r < 0: pwm_r *= FACTOR_RED
                        elif min_rear < THRESH_YELLOW:
                            if pwm_l < 0: pwm_l *= FACTOR_YELLOW
                            if pwm_r < 0: pwm_r *= FACTOR_YELLOW
            
            action = [pwm_l, pwm_r]
            obs, reward, done, info = env.step(action)
            
            if env.collided:
                if current_mode == MODE_RTH: reset_sim()
                else: reset_sim()
            
            if not env.success: has_left_dock = True
            
            if env.success and has_left_dock:
                dock_timer += 1
                if dock_timer > FPS * 1: 
                    reset_sim()
                    dock_timer = 0
            else: dock_timer = 0

        # Drawing
        screen.fill(COLOR_BG)
        for x in range(0, VIEWPORT_WIDTH, 50): pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, VIEWPORT_HEIGHT))
        for y in range(0, VIEWPORT_HEIGHT, 50): pygame.draw.line(screen, COLOR_GRID, (0, y), (VIEWPORT_WIDTH, y))
        
        pygame.draw.rect(screen, COLOR_WALL, (0,0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT), 10)
        for obs in env.obstacles: pygame.draw.rect(screen, COLOR_OBSTACLE, obs)
        env.dock.draw(screen)
        env.rover.draw(screen)
        draw_park_pilot(screen, env.rover, env.sensors.prox, show_sensors)
        
        if show_sensors:
            rx, ry = env.rover.x, env.rover.y
            emit_pos = env.dock.emit_pos
            face_ang = env.dock.facing_angle
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # --- CONE VISUALIZATION (Front ILS) ---
            # Using new WIDE cone constants
            r_start = math.radians(face_ang - IR_CONE_OUTER)
            r_end = math.radians(face_ang + IR_CONE_INNER)
            draw_blocked_beam(s, emit_pos, r_start, r_end, (255, 0, 0, 30), env.obstacles)
            
            g_start = math.radians(face_ang - IR_CONE_INNER)
            g_end = math.radians(face_ang + IR_CONE_OUTER)
            draw_blocked_beam(s, emit_pos, g_start, g_end, (0, 255, 0, 30), env.obstacles)
            
            screen.blit(s, (0,0))
            
            pygame.draw.line(screen, (0, 255, 255, 80), (rx, ry), env.dock.emit_pos, 2)
            
            # Draw LIDAR
            lidar_data = env.sensors.lidar.get_data()
            for i, dist_norm in enumerate(lidar_data):
                dist_px = dist_norm * LIDAR_MAX_RANGE_PX
                angle = math.radians(env.rover.angle + env.sensors.lidar.ray_angles[i])
                ex = rx + math.cos(angle) * dist_px; ey = ry + math.sin(angle) * dist_px
                color = (int(255*(1.0-dist_norm)), 50, 50) if dist_norm < 1.0 else (30, 30, 30)
                pygame.draw.line(screen, color, (rx, ry), (ex, ey), 1)

            # Draw Front IR Hits
            ir_data = env.sensors.ir.get_data()
            if ir_data[0] > 0 or ir_data[1] > 0:
                f_angle = math.radians(env.rover.angle)
                fx = rx + math.cos(f_angle) * IR_MAX_RANGE_PX
                fy = ry + math.sin(f_angle) * IR_MAX_RANGE_PX
                col = (0,255,255) if (ir_data[0] > 0 and ir_data[1] > 0) else (255,0,0) if ir_data[0]>0 else (0,255,0)
                pygame.draw.line(screen, col, (rx, ry), (fx, fy), 2)

            # Draw "Ready to Turn"
            if ir_data[5] > 0:
                pygame.draw.circle(screen, (255, 0, 255), (int(rx), int(ry)), ROVER_RADIUS + 10, 2)

            # --- Draw Rear Docking Sensors ---
            # Lasers (Cyan)
            l_ray, r_ray = env.sensors.rear.get_visualization_data()
            pygame.draw.line(screen, (0, 255, 255), l_ray[0], l_ray[1], 2)
            pygame.draw.line(screen, (0, 255, 255), r_ray[0], r_ray[1], 2)
            
            # Rear IR Indicators (Dots)
            rear_data = env.sensors.rear.get_data()
            if rear_data[2] > 0.5: # Left Active
                pygame.draw.circle(screen, (0, 255, 0), (int(rx - 10), int(ry)), 4)
            if rear_data[3] > 0.5: # Right Active
                pygame.draw.circle(screen, (0, 255, 0), (int(rx + 10), int(ry)), 4)

        hud.draw(screen, env, current_mode, ai_train_active)
        
        diff_txt = hud.font_sm.render(f"DIFF: {env.current_difficulty['name']}", True, (255, 200, 50))
        screen.blit(diff_txt, (VIEWPORT_WIDTH + 20, SCREEN_HEIGHT - 250))
        
        flags = [current_mode == MODE_MANUAL, current_mode == MODE_PATH, current_mode == MODE_RTH]
        hud.draw_status_panel(screen, flags)
        
        if ai_train_active:
            btn_ai.text = "AI TRAIN: ON"
            btn_ai.bg_color = (40, 200, 40)
            btn_ai.hover_color = (60, 220, 60)
            btn_diff.bg_color = (40, 40, 40); btn_diff.text_color = (100, 100, 100)
            btn_settings.bg_color = (40, 40, 40); btn_settings.text_color = (100, 100, 100)
            btn_toggle_view.bg_color = (40, 40, 40); btn_toggle_view.text_color = (100, 100, 100)
        else:
            btn_ai.text = "AI TRAIN: OFF"
            btn_ai.bg_color = (200, 40, 40)
            btn_ai.hover_color = (220, 60, 60)
            btn_diff.bg_color = COLOR_BTN_IDLE; btn_diff.text_color = COLOR_TEXT
            btn_settings.bg_color = COLOR_BTN_IDLE; btn_settings.text_color = COLOR_TEXT
            btn_toggle_view.bg_color = COLOR_BTN_IDLE; btn_toggle_view.text_color = COLOR_TEXT

        btn_ai.draw(screen)
        btn_diff.draw(screen)
        btn_settings.draw(screen)
        btn_toggle_view.draw(screen)
        
        if current_state == STATE_MENU:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, (0,0))
            menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 100, 300, 400)
            pygame.draw.rect(screen, COLOR_UI_BG, menu_rect, border_radius=10)
            pygame.draw.rect(screen, COLOR_ACCENT, menu_rect, 2, border_radius=10)
            title = font_menu.render("SYSTEM MENU", True, COLOR_ACCENT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 120))
            menu_btns[3].text = f"Spawn Dock: {'ON' if setting_spawn_on_dock else 'OFF'}"
            for b in menu_btns: b.draw(screen)
            
        elif current_state == STATE_DIFF_MENU:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, (0,0))
            menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 100, 300, 400)
            pygame.draw.rect(screen, COLOR_UI_BG, menu_rect, border_radius=10)
            pygame.draw.rect(screen, COLOR_ACCENT, menu_rect, 2, border_radius=10)
            title = font_menu.render("SELECT DIFFICULTY", True, COLOR_ACCENT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 120))
            for b in diff_btns: b.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()