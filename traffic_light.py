import pygame
from config import (
    RED_COLOR, YELLOW_COLOR, GREEN_COLOR, LIGHT_HOUSING_COLOR, LIGHT_OFF_COLOR,
    CENTER_X, CENTER_Y, ROAD_WIDTH,
    FIXED_GREEN_TIME, FIXED_YELLOW_TIME, ALL_RED_CLEARANCE,
    MIN_SMART_GREEN, MAX_SMART_GREEN, SMART_QUEUE_WEIGHT
)

PHASE_NS_GREEN = 0
PHASE_NS_YELLOW = 1
PHASE_ALL_RED_1 = 2
PHASE_EW_GREEN = 3
PHASE_EW_YELLOW = 4
PHASE_ALL_RED_2 = 5

class TrafficController:
    def __init__(self, mode="ADAPTIVE"):
        self.mode = mode
        self.current_phase = PHASE_NS_GREEN
        self.phase_timer = 0.0
        self.target_green_duration = FIXED_GREEN_TIME if mode == "FIXED" else 8.0
        self.phase_switches = 0
        self.time_in_mode = 0.0

    def set_mode(self, new_mode):
        if new_mode in ["FIXED", "ADAPTIVE"]:
            self.mode = new_mode
            self.phase_timer = 0.0
            self.target_green_duration = FIXED_GREEN_TIME if self.mode == "FIXED" else 6.0

    def toggle_mode(self):
        new_mode = "ADAPTIVE" if self.mode == "FIXED" else "FIXED"
        self.set_mode(new_mode)
        return self.mode

    def force_next_phase(self):
        self._advance_phase(forced=True)

    def _advance_phase(self, forced=False, ns_queue=0, ew_queue=0):
        self.current_phase = (self.current_phase + 1) % 6
        self.phase_timer = 0.0
        self.phase_switches += 1

        if self.mode == "ADAPTIVE":
            if self.current_phase == PHASE_NS_GREEN:
                allocated = MIN_SMART_GREEN + (ns_queue * SMART_QUEUE_WEIGHT)
                self.target_green_duration = max(MIN_SMART_GREEN, min(MAX_SMART_GREEN, allocated))
            elif self.current_phase == PHASE_EW_GREEN:
                allocated = MIN_SMART_GREEN + (ew_queue * SMART_QUEUE_WEIGHT)
                self.target_green_duration = max(MIN_SMART_GREEN, min(MAX_SMART_GREEN, allocated))
        else:
            self.target_green_duration = FIXED_GREEN_TIME

    def update(self, dt, intersection_stats):
        self.phase_timer += dt
        self.time_in_mode += dt

        ns_queue = intersection_stats.get('ns_queue', 0)
        ew_queue = intersection_stats.get('ew_queue', 0)
        ns_max_wait = intersection_stats.get('ns_max_wait', 0.0)
        ew_max_wait = intersection_stats.get('ew_max_wait', 0.0)

        if self.mode == "FIXED":
            if self.current_phase in [PHASE_NS_GREEN, PHASE_EW_GREEN]:
                if self.phase_timer >= FIXED_GREEN_TIME:
                    self._advance_phase()
            elif self.current_phase in [PHASE_NS_YELLOW, PHASE_EW_YELLOW]:
                if self.phase_timer >= FIXED_YELLOW_TIME:
                    self._advance_phase()
            elif self.current_phase in [PHASE_ALL_RED_1, PHASE_ALL_RED_2]:
                if self.phase_timer >= ALL_RED_CLEARANCE:
                    self._advance_phase()

        else:
            if self.current_phase == PHASE_NS_GREEN:
                should_cut_early = (self.phase_timer >= MIN_SMART_GREEN and ns_queue == 0 and ew_queue > 0)
                high_cross_pressure = (self.phase_timer >= MIN_SMART_GREEN and ew_max_wait > 10.0 and ns_queue < ew_queue)
                time_up = (self.phase_timer >= self.target_green_duration)
                if should_cut_early or high_cross_pressure or time_up:
                    self._advance_phase(ns_queue=ns_queue, ew_queue=ew_queue)

            elif self.current_phase == PHASE_NS_YELLOW:
                if self.phase_timer >= FIXED_YELLOW_TIME:
                    self._advance_phase(ns_queue=ns_queue, ew_queue=ew_queue)

            elif self.current_phase == PHASE_ALL_RED_1:
                if self.phase_timer >= ALL_RED_CLEARANCE:
                    self._advance_phase(ns_queue=ns_queue, ew_queue=ew_queue)

            elif self.current_phase == PHASE_EW_GREEN:
                should_cut_early = (self.phase_timer >= MIN_SMART_GREEN and ew_queue == 0 and ns_queue > 0)
                high_cross_pressure = (self.phase_timer >= MIN_SMART_GREEN and ns_max_wait > 10.0 and ew_queue < ns_queue)
                time_up = (self.phase_timer >= self.target_green_duration)
                if should_cut_early or high_cross_pressure or time_up:
                    self._advance_phase(ns_queue=ns_queue, ew_queue=ew_queue)

            elif self.current_phase == PHASE_EW_YELLOW:
                if self.phase_timer >= FIXED_YELLOW_TIME:
                    self._advance_phase(ns_queue=ns_queue, ew_queue=ew_queue)

            elif self.current_phase == PHASE_ALL_RED_2:
                if self.phase_timer >= ALL_RED_CLEARANCE:
                    self._advance_phase(ns_queue=ns_queue, ew_queue=ew_queue)

    def get_signal_state(self, direction):
        if direction in ['N', 'S']:
            if self.current_phase == PHASE_NS_GREEN:
                return 'GREEN'
            elif self.current_phase == PHASE_NS_YELLOW:
                return 'YELLOW'
            return 'RED'
        else:
            if self.current_phase == PHASE_EW_GREEN:
                return 'GREEN'
            elif self.current_phase == PHASE_EW_YELLOW:
                return 'YELLOW'
            return 'RED'

    def get_remaining_time(self):
        if self.current_phase in [PHASE_NS_GREEN, PHASE_EW_GREEN]:
            return max(0.0, self.target_green_duration - self.phase_timer)
        elif self.current_phase in [PHASE_NS_YELLOW, PHASE_EW_YELLOW]:
            return max(0.0, FIXED_YELLOW_TIME - self.phase_timer)
        return max(0.0, ALL_RED_CLEARANCE - self.phase_timer)

    def draw(self, surface):
        half_w = ROAD_WIDTH // 2
        signals = [
            ('N', CENTER_X + half_w + 14, CENTER_Y - half_w - 30, 'vertical'),
            ('S', CENTER_X - half_w - 28, CENTER_Y + half_w + 5, 'vertical'),
            ('W', CENTER_X - half_w - 30, CENTER_Y - half_w - 28, 'horizontal'),
            ('E', CENTER_X + half_w + 5,  CENTER_Y + half_w + 14, 'horizontal'),
        ]

        for dir_code, x, y, orientation in signals:
            state = self.get_signal_state(dir_code)
            self._draw_traffic_box(surface, x, y, state, orientation)

    def _draw_traffic_box(self, surface, x, y, state, orientation):
        box_w, box_h = (16, 44) if orientation == 'vertical' else (44, 16)
        housing_rect = pygame.Rect(x, y, box_w, box_h)

        pygame.draw.rect(surface, LIGHT_HOUSING_COLOR, housing_rect, border_radius=4)
        pygame.draw.rect(surface, (70, 80, 95), housing_rect, width=1, border_radius=4)

        bulb_radius = 4
        if orientation == 'vertical':
            red_center = (x + box_w // 2, y + 8)
            yel_center = (x + box_w // 2, y + 22)
            grn_center = (x + box_w // 2, y + 36)
        else:
            red_center = (x + 8, y + box_h // 2)
            yel_center = (x + 22, y + box_h // 2)
            grn_center = (x + 36, y + box_h // 2)

        c_red = RED_COLOR if state == 'RED' else LIGHT_OFF_COLOR
        c_yel = YELLOW_COLOR if state == 'YELLOW' else LIGHT_OFF_COLOR
        c_grn = GREEN_COLOR if state == 'GREEN' else LIGHT_OFF_COLOR

        if state == 'RED':
            self._draw_glow(surface, red_center, RED_COLOR, 8)
        elif state == 'YELLOW':
            self._draw_glow(surface, yel_center, YELLOW_COLOR, 8)
        elif state == 'GREEN':
            self._draw_glow(surface, grn_center, GREEN_COLOR, 8)

        pygame.draw.circle(surface, c_red, red_center, bulb_radius)
        pygame.draw.circle(surface, c_yel, yel_center, bulb_radius)
        pygame.draw.circle(surface, c_grn, grn_center, bulb_radius)

    def _draw_glow(self, surface, center, color, radius):
        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        glow_color = (color[0], color[1], color[2], 70)
        pygame.draw.circle(glow_surf, glow_color, (radius, radius), radius)
        surface.blit(glow_surf, (center[0] - radius, center[1] - radius))
