import pygame
from config import (
    PANEL_BG, TEXT_WHITE, TEXT_MUTED, TEXT_ACCENT,
    TEXT_SUCCESS, TEXT_WARNING, BUTTON_BG, BUTTON_HOVER, BUTTON_ACTIVE,
    GREEN_COLOR, RED_COLOR, YELLOW_COLOR
)

class Button:
    def __init__(self, rect, text, callback, active=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.is_active = active
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface, font):
        color = BUTTON_ACTIVE if self.is_active else (BUTTON_HOVER if self.is_hovered else BUTTON_BG)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (100, 150, 255), self.rect, width=1, border_radius=6)
        txt_surf = font.render(self.text, True, TEXT_WHITE)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)


class Dashboard:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        pygame.font.init()
        self.title_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.sub_font = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.body_font = pygame.font.SysFont("Segoe UI", 12)
        self.num_font = pygame.font.SysFont("Consolas", 18, bold=True)
        self.small_num_font = pygame.font.SysFont("Consolas", 13, bold=True)
        self.buttons = []

    def setup_buttons(self, toggle_mode_cb, cycle_preset_cb, force_phase_cb, inc_spawn_cb, dec_spawn_cb, reset_cb):
        bx = self.rect.x + 16
        by = self.rect.y + 115

        self.btn_mode = Button((bx, by, 185, 30), "Mode: ADAPTIVE (M)", toggle_mode_cb, active=True)
        self.btn_preset = Button((bx + 195, by, 185, 30), "Traffic: Balanced (P)", cycle_preset_cb)

        by += 38
        self.btn_spawn_dec = Button((bx, by, 45, 26), " - ", dec_spawn_cb)
        self.btn_spawn_inc = Button((bx + 140, by, 45, 26), " + ", inc_spawn_cb)
        self.btn_force = Button((bx + 195, by, 185, 26), "Next Light Phase (T)", force_phase_cb)

        by += 34
        self.btn_reset = Button((bx, by, 380, 26), "Reset Simulation Stats (R)", reset_cb)

        self.buttons = [
            self.btn_mode, self.btn_preset,
            self.btn_spawn_dec, self.btn_spawn_inc,
            self.btn_force, self.btn_reset
        ]

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def update_button_labels(self, mode, preset, spawn_rate):
        self.btn_mode.text = f"Mode: {mode} (M)"
        self.btn_mode.is_active = (mode == "ADAPTIVE")
        preset_names = {"BALANCED": "Balanced", "HEAVY_NS": "Heavy N-S", "RUSH_HOUR": "Rush Hour"}
        self.btn_preset.text = f"Traffic: {preset_names.get(preset, preset)} (P)"

    def draw(self, surface, traffic_controller, intersection, is_paused):
        panel_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surf.fill(PANEL_BG)
        surface.blit(panel_surf, self.rect.topleft)
        pygame.draw.line(surface, (60, 75, 100), self.rect.topleft, self.rect.bottomleft, 2)

        header_y = self.rect.y + 14
        title = self.title_font.render("Smart Traffic Light Simulator", True, TEXT_WHITE)
        surface.blit(title, (self.rect.x + 16, header_y))

        status_text = "PAUSED [SPACE]" if is_paused else "RUNNING"
        status_color = TEXT_WARNING if is_paused else TEXT_SUCCESS
        surface.blit(self.sub_font.render(f"System: {status_text}", True, status_color), (self.rect.x + 16, header_y + 28))
        pygame.draw.line(surface, (50, 60, 80), (self.rect.x + 16, header_y + 52), (self.rect.right - 16, header_y + 52), 1)

        ctrl_y = header_y + 60
        mode_color = TEXT_SUCCESS if traffic_controller.mode == "ADAPTIVE" else TEXT_ACCENT
        surface.blit(self.sub_font.render(f"Active Algorithm: {traffic_controller.mode} CONTROL", True, mode_color), (self.rect.x + 16, ctrl_y))

        phase_names = {
            0: ("North - South", "GREEN", GREEN_COLOR),
            1: ("North - South", "YELLOW", YELLOW_COLOR),
            2: ("Intersection Clearance", "ALL RED", RED_COLOR),
            3: ("East - West", "GREEN", GREEN_COLOR),
            4: ("East - West", "YELLOW", YELLOW_COLOR),
            5: ("Intersection Clearance", "ALL RED", RED_COLOR),
        }
        name, color_lbl, col = phase_names.get(traffic_controller.current_phase, ("Phase", "...", TEXT_WHITE))
        rem_sec = traffic_controller.get_remaining_time()

        phase_str = f"Phase: {name} "
        p_surf = self.body_font.render(phase_str, True, TEXT_MUTED)
        surface.blit(p_surf, (self.rect.x + 16, ctrl_y + 20))
        badge_surf = self.sub_font.render(f"[{color_lbl}] {rem_sec:04.1f}s", True, col)
        surface.blit(badge_surf, (self.rect.x + 16 + p_surf.get_width(), ctrl_y + 18))

        for btn in self.buttons:
            btn.draw(surface, self.body_font)

        sp_rate_label = self.body_font.render(f"{intersection.spawn_rate:0.1f}x Rate", True, TEXT_WHITE)
        sp_rect = sp_rate_label.get_rect(center=(self.rect.x + 16 + 92, self.rect.y + 166))
        surface.blit(sp_rate_label, sp_rect)

        div_y = self.rect.y + 225
        pygame.draw.line(surface, (50, 60, 80), (self.rect.x + 16, div_y), (self.rect.right - 16, div_y), 1)

        stats = intersection.get_overall_stats()
        tele_y = div_y + 10
        surface.blit(self.sub_font.render("REAL-TIME QUEUE & DEMAND SENSORS", True, TEXT_ACCENT), (self.rect.x + 16, tele_y))

        card_y = tele_y + 22
        dirs = [('N', 'North'), ('S', 'South'), ('E', 'East'), ('W', 'West')]
        for i, (code, label) in enumerate(dirs):
            cx = self.rect.x + 16 + (i % 2) * 192
            cy = card_y + (i // 2) * 52
            card_rect = pygame.Rect(cx, cy, 185, 46)
            pygame.draw.rect(surface, (28, 36, 50), card_rect, border_radius=5)
            pygame.draw.rect(surface, (45, 55, 75), card_rect, width=1, border_radius=5)

            q_cnt = stats['queues'][code]
            max_w = stats['max_wait_per_dir'][code]

            surface.blit(self.sub_font.render(f"{label} ({code})", True, TEXT_WHITE), (cx + 8, cy + 6))
            q_color = RED_COLOR if q_cnt >= 5 else (YELLOW_COLOR if q_cnt >= 2 else TEXT_SUCCESS)
            surface.blit(self.num_font.render(f"{q_cnt} cars", True, q_color), (cx + 8, cy + 22))
            surface.blit(self.body_font.render(f"max {max_w:.1f}s", True, TEXT_MUTED), (cx + 105, cy + 25))

        perf_y = card_y + 115
        surface.blit(self.sub_font.render("FLOW & EFFICIENCY METRICS", True, TEXT_ACCENT), (self.rect.x + 16, perf_y))

        metrics = [
            ("Throughput", f"{stats['cleared']}", "vehicles cleared"),
            ("Avg Wait", f"{stats['avg_wait_time']:.1f}s", "per vehicle"),
            ("Max Wait", f"{stats['max_wait_time']:.1f}s", "peak congestion")
        ]

        m_box_y = perf_y + 22
        for i, (m_title, m_val, m_sub) in enumerate(metrics):
            mx = self.rect.x + 16 + i * 128
            m_rect = pygame.Rect(mx, m_box_y, 122, 60)
            pygame.draw.rect(surface, (28, 36, 50), m_rect, border_radius=5)
            pygame.draw.rect(surface, (45, 55, 75), m_rect, width=1, border_radius=5)
            surface.blit(self.body_font.render(m_title, True, TEXT_MUTED), (mx + 8, m_box_y + 5))
            surface.blit(self.num_font.render(m_val, True, TEXT_WHITE), (mx + 8, m_box_y + 21))
            surface.blit(self.body_font.render(m_sub, True, (130, 140, 155)), (mx + 8, m_box_y + 42))

        comp_y = m_box_y + 72
        surface.blit(self.sub_font.render("ALGORITHM COMPARISON EXPERIMENT", True, TEXT_ACCENT), (self.rect.x + 16, comp_y))

        comp_box = pygame.Rect(self.rect.x + 16, comp_y + 22, 380, 125)
        pygame.draw.rect(surface, (20, 26, 38), comp_box, border_radius=6)
        pygame.draw.rect(surface, (55, 68, 92), comp_box, width=1, border_radius=6)

        fixed_avg = stats['fixed_avg_wait']
        adapt_avg = stats['adapt_avg_wait']
        f_cleared = stats['fixed_cleared']
        a_cleared = stats['adapt_cleared']

        fy = comp_box.y + 10
        surface.blit(self.sub_font.render("1. Fixed Timer Mode:", True, TEXT_MUTED), (comp_box.x + 12, fy))
        surface.blit(self.small_num_font.render(f"{f_cleared} cars | Avg wait: {fixed_avg:.1f}s", True, TEXT_WHITE), (comp_box.x + 175, fy))

        ay = fy + 24
        surface.blit(self.sub_font.render("2. Smart Adaptive Mode:", True, TEXT_SUCCESS), (comp_box.x + 12, ay))
        surface.blit(self.small_num_font.render(f"{a_cleared} cars | Avg wait: {adapt_avg:.1f}s", True, TEXT_SUCCESS), (comp_box.x + 175, ay))

        diff_y = ay + 30
        if fixed_avg > 0 and adapt_avg > 0:
            pct_saved = ((fixed_avg - adapt_avg) / fixed_avg) * 100.0
            diff_text = f"Result: Smart mode reduced delay by {pct_saved:.1f}%!" if pct_saved > 0 else "Result: Comparable wait times under this flow"
            diff_col = TEXT_SUCCESS if pct_saved > 0 else TEXT_WARNING
        else:
            diff_text = "Run both modes (press M) to see comparative delay reduction"
            diff_col = TEXT_MUTED

        surface.blit(self.sub_font.render(diff_text, True, diff_col), (comp_box.x + 12, diff_y))

        bar_y = diff_y + 22
        max_bar_width = 350
        max_scale_wait = max(15.0, fixed_avg, adapt_avg)

        f_w = int((fixed_avg / max_scale_wait) * max_bar_width) if fixed_avg > 0 else 0
        pygame.draw.rect(surface, (70, 85, 110), (comp_box.x + 12, bar_y, max_bar_width, 6), border_radius=3)
        if f_w > 0:
            pygame.draw.rect(surface, (239, 68, 68), (comp_box.x + 12, bar_y, f_w, 6), border_radius=3)

        a_w = int((adapt_avg / max_scale_wait) * max_bar_width) if adapt_avg > 0 else 0
        pygame.draw.rect(surface, (70, 85, 110), (comp_box.x + 12, bar_y + 10, max_bar_width, 6), border_radius=3)
        if a_w > 0:
            pygame.draw.rect(surface, (16, 185, 129), (comp_box.x + 12, bar_y + 10, a_w, 6), border_radius=3)

        foot_y = self.rect.bottom - 46
        surface.blit(self.body_font.render("[M] Toggle Mode  |  [P] Change Flow  |  [T] Skip Light", True, (130, 140, 160)), (self.rect.x + 16, foot_y))
        surface.blit(self.body_font.render("[+/-] Spawn Rate  |  [Space] Pause    |  [R] Reset Stats", True, (130, 140, 160)), (self.rect.x + 16, foot_y + 18))
