import pygame
import numpy as np
from config import *

class HUD:
    def __init__(self):
        self.font_sm = pygame.font.SysFont("Consolas", 12)
        self.font_md = pygame.font.SysFont("Consolas", 14, bold=True)
        self.font_lg = pygame.font.SysFont("Arial", 20, bold=True)
        
        # --- SMOOTHING VARIABLES ---
        self.smooth_center = 0.0
        self.smooth_angle = 0.0
        
        # Memory variables
        self.last_center_status = "OFF"
        self.last_angle_status = "OFF"
        self.last_valid_center = 0.0
        self.last_valid_angle = 0.0
        self.last_active_time = 0

    def draw_status_panel(self, surface, flags):
        x, y = 20, 20
        w, h = 200, 140
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((20, 24, 28, 200)) 
        surface.blit(s, (x, y))
        pygame.draw.rect(surface, COLOR_UI_BORDER, (x, y, w, h), 2)
        title = self.font_md.render("SYSTEM MODES", True, COLOR_ACCENT)
        surface.blit(title, (x + 10, y + 10))
        labels = ["MANUAL MODE", "PATHFINDING", "RTH (AI)"]
        curr_y = y + 40
        for i, is_active in enumerate(flags):
            lbl = self.font_sm.render(labels[i], True, COLOR_TEXT_MAIN)
            surface.blit(lbl, (x + 10, curr_y + 5))
            switch_w, switch_h = 40, 20
            switch_x = x + w - 50
            switch_y = curr_y + 2
            pill_col = (50, 200, 50) if is_active else (80, 80, 80)
            pygame.draw.rect(surface, pill_col, (switch_x, switch_y, switch_w, switch_h), border_radius=10)
            knob_x = switch_x + switch_w - 10 if is_active else switch_x + 10
            pygame.draw.circle(surface, (255,255,255), (knob_x, switch_y + 10), 8)
            curr_y += 35

    def draw(self, surface, env, return_mode_name, debug_mode):
        panel_rect = pygame.Rect(VIEWPORT_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, COLOR_UI_BG, panel_rect)
        pygame.draw.line(surface, COLOR_ACCENT, (VIEWPORT_WIDTH, 0), (VIEWPORT_WIDTH, SCREEN_HEIGHT), 2)
        
        x_pad = VIEWPORT_WIDTH + 20
        y = 20
        
        # Header
        title = self.font_lg.render("DATALINK OS", True, COLOR_ACCENT)
        surface.blit(title, (x_pad, y))
        y += 40
        lbl = self.font_sm.render("ACTIVE MODE:", True, COLOR_TEXT_DIM)
        surface.blit(lbl, (x_pad, y))
        mode_txt = self.font_md.render(return_mode_name, True, (255, 200, 50))
        surface.blit(mode_txt, (x_pad + 90, y))
        y += 40
        
        status_color = (100, 255, 100) if not env.collided else (255, 50, 50)
        status_txt = "ONLINE" if not env.collided else "CRITICAL FAIL"
        if env.success: status_txt = "DOCKED"; status_color = COLOR_ACCENT
        pygame.draw.rect(surface, (30, 35, 40), (x_pad, y, 160, 30), border_radius=4)
        pygame.draw.rect(surface, status_color, (x_pad + 5, y + 5, 20, 20), border_radius=2)
        lbl = self.font_md.render(status_txt, True, COLOR_TEXT_MAIN)
        surface.blit(lbl, (x_pad + 35, y + 7))
        y += 50
        
        # Telemetry
        def draw_label_value(label, value, unit=""):
            nonlocal y
            l_surf = self.font_sm.render(label, True, COLOR_TEXT_DIM)
            v_surf = self.font_md.render(f"{value}{unit}", True, COLOR_TEXT_MAIN)
            surface.blit(l_surf, (x_pad, y))
            surface.blit(v_surf, (x_pad + 80, y))
            y += 20
        draw_label_value("SPEED", f"{env.rover.vx:.2f}", " m/s")
        draw_label_value("PWM L/R", f"{int(env.rover.pwm_l)} | {int(env.rover.pwm_r)}")
        draw_label_value("HEADING", f"{int(env.rover.angle)}", "°")
        y += 20
        lbl = self.font_sm.render(f"DIST: {env.last_dist:.1f}m", True, COLOR_TEXT_DIM)
        surface.blit(lbl, (x_pad, y))
        y += 30

        # --- ILS DISPLAY ---
        ir_data = env.sensors.ir.get_data()
        pygame.draw.rect(surface, (20, 20, 20), (x_pad, y, 160, 30), border_radius=4)
        r_col = (255, 50, 50) if ir_data[0] > 0 else (50, 20, 20)
        pygame.draw.rect(surface, r_col, (x_pad + 10, y + 5, 20, 20), border_radius=10)
        g_col = (50, 255, 50) if ir_data[1] > 0 else (20, 50, 20)
        pygame.draw.rect(surface, g_col, (x_pad + 130, y + 5, 20, 20), border_radius=10)
        
        msg = "NO SIGNAL"
        msg_col = (100, 100, 100)
        if ir_data[5] > 0:
            msg = "EXECUTE TURN"
            msg_col = (255, 0, 255)
        elif ir_data[0] > 0 and ir_data[1] > 0:
            msg = "DEAD AHEAD"
            msg_col = (50, 200, 255)
        elif ir_data[0] > 0:
            msg = "FLY RIGHT >>"
            msg_col = (255, 100, 100)
        elif ir_data[1] > 0:
            msg = "<< FLY LEFT"
            msg_col = (100, 255, 100)
        txt = self.font_md.render(msg, True, msg_col)
        rect = txt.get_rect(center=(x_pad + 80, y + 15))
        surface.blit(txt, rect)
        y += 40
        
        # --- DOCKING GUIDANCE (Rear) ---
        rear_data = env.sensors.rear.get_data()
        ir_left, ir_right = rear_data[2], rear_data[3]
        las_left, las_right = rear_data[0], rear_data[1]
        
        is_active = (ir_left > 0 or ir_right > 0 or las_left > 0 or las_right > 0)
        
        target_center = self.smooth_center 
        target_angle = self.smooth_angle   
        
        center_status = "OFF"
        angle_status = "OFF"
        center_col = (80, 80, 80)
        angle_col = (80, 80, 80)
        
        if is_active:
            self.last_active_time = pygame.time.get_ticks()
            
            # --- 1. CENTER LOGIC ---
            diff = ir_left - ir_right
            # Use a threshold so tiny jitter doesn't flash the text
            if abs(diff) < 0.15: 
                center_status = "LOCKED"
                center_col = (50, 255, 50)
                target_center = 0.0
            elif diff > 0:
                center_status = "TOO LEFT"
                center_col = (255, 200, 0)
                target_center = -1.0 * (diff * 2.0)
            else:
                center_status = "TOO RIGHT"
                center_col = (255, 200, 0)
                target_center = -1.0 * (diff * 2.0)

            # --- 2. ANGLE LOGIC ---
            raw_angle = (las_left - las_right) * 6.0 # Lower multiplier to reduce jitter
            target_angle = raw_angle
            
            if abs(target_angle) < 0.2:
                angle_status = "STRAIGHT"
                angle_col = (50, 255, 50)
            else:
                angle_status = "ANGLED"
                angle_col = (255, 50, 50)
                
            self.last_center_status = center_status
            self.last_angle_status = angle_status
            self.last_valid_center = target_center
            self.last_valid_angle = target_angle
            
        else:
            if pygame.time.get_ticks() - self.last_active_time < 1000:
                center_status = self.last_center_status
                angle_status = self.last_angle_status
                center_col = (100, 100, 100)
                angle_col = (100, 100, 100)
                target_center = self.last_valid_center
                target_angle = self.last_valid_angle
            else:
                center_status = "OFF"
                angle_status = "OFF"
                target_center = 0.0
                target_angle = 0.0

        # --- HEAVY SMOOTHING (0.05 factor) ---
        self.smooth_center += (target_center - self.smooth_center) * 0.05
        self.smooth_angle += (target_angle - self.smooth_angle) * 0.05

        y += 10
        lbl = self.font_sm.render("REAR GUIDANCE", True, COLOR_TEXT_DIM)
        surface.blit(lbl, (x_pad, y))
        y += 20
        
        def draw_guidance_bar(label, val, status_txt, color, active):
            bar_w = 160
            bar_center = x_pad + bar_w // 2
            
            bg_col = (40, 44, 50) 
            pygame.draw.rect(surface, bg_col, (x_pad, y, bar_w, 15))
            pygame.draw.line(surface, (100, 100, 100), (bar_center, y), (bar_center, y+15), 1)
            
            clamped = max(-1.0, min(1.0, val))
            cursor_x = bar_center + (clamped * (bar_w/2 - 5))
            
            if color != (80, 80, 80): 
                pygame.draw.rect(surface, color, (cursor_x - 3, y, 6, 15))
            
            lbl_surf = self.font_sm.render(label, True, (180, 180, 180))
            stat_surf = self.font_sm.render(status_txt, True, color)
            
            surface.blit(lbl_surf, (x_pad, y - 12))
            # Fixed text position to align right
            txt_w = stat_surf.get_width()
            surface.blit(stat_surf, (x_pad + bar_w - txt_w, y - 12))

        draw_guidance_bar("CENTER", self.smooth_center, center_status, center_col, is_active)
        y += 35
        draw_guidance_bar("ANGLE", self.smooth_angle, angle_status, angle_col, is_active)
        y += 30

        # Warning
        prox_data = env.sensors.prox.get_data()
        if np.any(prox_data < 0.3):
            if (pygame.time.get_ticks() // 250) % 2 == 0:
                warn_rect = pygame.Rect(VIEWPORT_WIDTH - 160, 20, 140, 40)
                pygame.draw.rect(surface, (255, 50, 50, 100), warn_rect, border_radius=4)
                pygame.draw.rect(surface, (255, 255, 255), warn_rect, 2, border_radius=4)
                w_txt = self.font_md.render("PROXIMITY ALERT", True, (255, 255, 255))
                surface.blit(w_txt, (warn_rect.x + 10, warn_rect.y + 12))