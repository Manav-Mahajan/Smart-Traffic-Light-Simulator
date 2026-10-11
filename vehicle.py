import pygame
import random
from config import (
    VEHICLE_TYPES, SAFE_DISTANCE, STOP_LINE_OFFSET,
    CENTER_X, CENTER_Y, ROAD_WIDTH, LANE_WIDTH,
    WINDOW_WIDTH, WINDOW_HEIGHT
)

class Vehicle:
    _id_counter = 0

    def __init__(self, direction, lane_idx=0, vehicle_type=None):
        Vehicle._id_counter += 1
        self.id = Vehicle._id_counter
        self.direction = direction  
        self.lane_idx = lane_idx  

        if vehicle_type is None:
            vehicle_type = random.choices(['car', 'bus', 'bike'], weights=[0.75, 0.15, 0.10])[0]

        self.type_name = vehicle_type
        specs = VEHICLE_TYPES[vehicle_type]
        self.length = specs['length']
        self.width = specs['width']
        self.max_speed = specs['max_speed'] + random.uniform(-0.3, 0.3)
        self.accel = specs['accel']
        self.decel = specs['decel']
        self.color = random.choice(specs['colors'])

        self.speed = 0.0
        self.waiting_time = 0.0  
        self.travel_time = 0.0 
        self.is_cleared = False 

        self.path_pos = 0.0
        self.stop_line_dist = self._calc_stop_line_dist()
        self.has_crossed_stop_line = False

    def _calc_stop_line_dist(self):
        """Calculates distance from spawn point to stop line for this approach."""
        if self.direction == 'N':
            return (CENTER_Y - STOP_LINE_OFFSET) - (-self.length)
        elif self.direction == 'S':
            return (WINDOW_HEIGHT + self.length) - (CENTER_Y + STOP_LINE_OFFSET)
        elif self.direction == 'W':
            return (CENTER_X - STOP_LINE_OFFSET) - (-self.length)
        elif self.direction == 'E':
            return (WINDOW_WIDTH + self.length) - (CENTER_X + STOP_LINE_OFFSET)
        return 300.0

    def update(self, dt, lead_vehicle, is_green_or_yellow):
        self.travel_time += dt
        target_pos = None
      
        if lead_vehicle is not None:
            lead_bumper = lead_vehicle.path_pos - (lead_vehicle.length / 2)
            target_pos = lead_bumper - SAFE_DISTANCE - (self.length / 2)

        if not self.has_crossed_stop_line and not is_green_or_yellow:
            stop_point = self.stop_line_dist - (self.length / 2)
            if target_pos is None or stop_point < target_pos:
                target_pos = stop_point

        if target_pos is not None:
            distance_to_target = target_pos - self.path_pos
            if distance_to_target <= 1.0:
                self.speed = max(0.0, self.speed - self.decel * 2.0)
            elif distance_to_target < 60.0:
                target_speed = self.max_speed * (distance_to_target / 60.0)
                if self.speed > target_speed:
                    self.speed = max(0.0, self.speed - self.decel)
                else:
                    self.speed = min(target_speed, self.speed + self.accel)
            else:
                self.speed = min(self.max_speed, self.speed + self.accel)
        else:
            self.speed = min(self.max_speed, self.speed + self.accel)

        self.path_pos += self.speed * (dt * 60.0)

        if self.path_pos >= self.stop_line_dist:
            self.has_crossed_stop_line = True

        if self.speed < 0.35 and not self.has_crossed_stop_line:
            self.waiting_time += dt

        current_x, current_y = self.get_position()
        margin = 100
        if (current_x < -margin or current_x > WINDOW_WIDTH + margin or
            current_y < -margin or current_y > WINDOW_HEIGHT + margin):
            self.is_cleared = True

    def get_position(self):
        if self.direction == 'N':
            lane_center_x = CENTER_X + (self.lane_idx + 0.5) * LANE_WIDTH
            pos_y = -self.length + self.path_pos
            return lane_center_x, pos_y

        elif self.direction == 'S':
            lane_center_x = CENTER_X - (self.lane_idx + 0.5) * LANE_WIDTH
            pos_y = (WINDOW_HEIGHT + self.length) - self.path_pos
            return lane_center_x, pos_y

        elif self.direction == 'W':
            lane_center_y = CENTER_Y + (self.lane_idx + 0.5) * LANE_WIDTH
            pos_x = -self.length + self.path_pos
            return pos_x, lane_center_y

        elif self.direction == 'E':
            lane_center_y = CENTER_Y - (self.lane_idx + 0.5) * LANE_WIDTH
            pos_x = (WINDOW_WIDTH + self.length) - self.path_pos
            return pos_x, lane_center_y

        return 0, 0

    def draw(self, surface):
        cx, cy = self.get_position()
        is_vertical = self.direction in ['N', 'S']
        body_w = self.width if is_vertical else self.length
        body_h = self.length if is_vertical else self.width

        rect = pygame.Rect(0, 0, body_w, body_h)
        rect.center = (int(cx), int(cy))

        pygame.draw.rect(surface, self.color, rect, border_radius=4)
        pygame.draw.rect(surface, (20, 20, 25), rect, width=2, border_radius=4)

        roof_rect = rect.inflate(-4, -6) if is_vertical else rect.inflate(-6, -4)
        if roof_rect.width > 2 and roof_rect.height > 2:
            roof_color = (
                max(0, self.color[0] - 40),
                max(0, self.color[1] - 40),
                max(0, self.color[2] - 40)
            )
            pygame.draw.rect(surface, roof_color, roof_rect, border_radius=2)

        headlight_color = (254, 240, 138)
        taillight_color = (239, 68, 68) if self.speed < 0.5 else (185, 28, 28)

        if self.direction == 'N':
            pygame.draw.circle(surface, headlight_color, (rect.left + 3, rect.bottom - 2), 2)
            pygame.draw.circle(surface, headlight_color, (rect.right - 3, rect.bottom - 2), 2)
            pygame.draw.circle(surface, taillight_color, (rect.left + 3, rect.top + 2), 2)
            pygame.draw.circle(surface, taillight_color, (rect.right - 3, rect.top + 2), 2)

        elif self.direction == 'S':
            pygame.draw.circle(surface, headlight_color, (rect.left + 3, rect.top + 2), 2)
            pygame.draw.circle(surface, headlight_color, (rect.right - 3, rect.top + 2), 2)
            pygame.draw.circle(surface, taillight_color, (rect.left + 3, rect.bottom - 2), 2)
            pygame.draw.circle(surface, taillight_color, (rect.right - 3, rect.bottom - 2), 2)

        elif self.direction == 'W':
            pygame.draw.circle(surface, headlight_color, (rect.right - 2, rect.top + 3), 2)
            pygame.draw.circle(surface, headlight_color, (rect.right - 2, rect.bottom - 3), 2)
            pygame.draw.circle(surface, taillight_color, (rect.left + 2, rect.top + 3), 2)
            pygame.draw.circle(surface, taillight_color, (rect.left + 2, rect.bottom - 3), 2)

        elif self.direction == 'E':
            pygame.draw.circle(surface, headlight_color, (rect.left + 2, rect.top + 3), 2)
            pygame.draw.circle(surface, headlight_color, (rect.left + 2, rect.bottom - 3), 2)
            pygame.draw.circle(surface, taillight_color, (rect.right - 2, rect.top + 3), 2)
            pygame.draw.circle(surface, taillight_color, (rect.right - 2, rect.bottom - 3), 2)

        if self.waiting_time > 4.0 and not self.has_crossed_stop_line:
            badge_pos = (rect.centerx, rect.top - 6 if is_vertical else rect.top - 5)
            badge_color = (239, 68, 68) if self.waiting_time > 10.0 else (245, 158, 11)
            pygame.draw.circle(surface, badge_color, badge_pos, 4)
