import pygame
import random
from vehicle import Vehicle
from config import (
    ROAD_COLOR, ROAD_MARKING_COLOR, ROAD_BORDER_COLOR, SIDEWALK_COLOR,
    CENTER_X, CENTER_Y, ROAD_WIDTH, LANE_WIDTH, STOP_LINE_OFFSET,
    WINDOW_WIDTH, WINDOW_HEIGHT
)

class Intersection:
    def __init__(self):
        self.lanes = {
            ('N', 0): [], ('N', 1): [],
            ('S', 0): [], ('S', 1): [],
            ('E', 0): [], ('E', 1): [],
            ('W', 0): [], ('W', 1): [],
        }

        self.spawn_rate = 1.0
        self.spawn_timers = {'N': 0.0, 'S': 0.0, 'E': 0.0, 'W': 0.0}
        self.spawn_intervals = {'N': 2.8, 'S': 2.8, 'E': 3.2, 'W': 3.2}
        self.traffic_preset = "BALANCED"

        self.total_spawned = 0
        self.total_cleared = 0
        self.cleared_wait_times = []
        self.active_queues = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        self.max_wait_times = {'N': 0.0, 'S': 0.0, 'E': 0.0, 'W': 0.0}
        self.avg_wait_times = {'N': 0.0, 'S': 0.0, 'E': 0.0, 'W': 0.0}

        self.stats_by_mode = {
            'FIXED': {'cleared': 0, 'total_wait': 0.0, 'samples': []},
            'ADAPTIVE': {'cleared': 0, 'total_wait': 0.0, 'samples': []}
        }

    def set_preset(self, preset_name):
        self.traffic_preset = preset_name
        if preset_name == "BALANCED":
            self.spawn_intervals = {'N': 2.6, 'S': 2.6, 'E': 2.6, 'W': 2.6}
        elif preset_name == "HEAVY_NS":
            self.spawn_intervals = {'N': 1.4, 'S': 1.4, 'E': 5.5, 'W': 5.5}
        elif preset_name == "RUSH_HOUR":
            self.spawn_intervals = {'N': 1.5, 'S': 1.5, 'E': 1.6, 'W': 1.6}

    def adjust_spawn_rate(self, delta):
        self.spawn_rate = max(0.4, min(3.0, self.spawn_rate + delta))

    def reset_stats(self):
        self.total_spawned = 0
        self.total_cleared = 0
        self.cleared_wait_times.clear()
        self.stats_by_mode = {
            'FIXED': {'cleared': 0, 'total_wait': 0.0, 'samples': []},
            'ADAPTIVE': {'cleared': 0, 'total_wait': 0.0, 'samples': []}
        }

    def _try_spawn_vehicle(self, direction):
        lane_idx = random.choice([0, 1])
        lane_vehicles = self.lanes[(direction, lane_idx)]

        can_spawn = True
        for v in lane_vehicles:
            if v.path_pos < 60.0:
                can_spawn = False
                break

        if can_spawn:
            new_v = Vehicle(direction, lane_idx)
            lane_vehicles.append(new_v)
            self.total_spawned += 1

    def update(self, dt, traffic_controller):
        for direction in ['N', 'S', 'E', 'W']:
            self.spawn_timers[direction] += dt
            effective_interval = self.spawn_intervals[direction] / self.spawn_rate
            if self.spawn_timers[direction] >= effective_interval:
                self.spawn_timers[direction] = 0.0
                self._try_spawn_vehicle(direction)

        active_mode = traffic_controller.mode
        for (direction, lane_idx), vehicles in self.lanes.items():
            vehicles.sort(key=lambda v: v.path_pos, reverse=True)
            signal_state = traffic_controller.get_signal_state(direction)
            is_green_or_yellow = (signal_state in ['GREEN', 'YELLOW'])

            for i, v in enumerate(vehicles):
                lead_vehicle = vehicles[i - 1] if i > 0 else None
                v.update(dt, lead_vehicle, is_green_or_yellow)

            cleared_this_frame = [v for v in vehicles if v.is_cleared]
            for v in cleared_this_frame:
                self.total_cleared += 1
                self.cleared_wait_times.append(v.waiting_time)
                self.stats_by_mode[active_mode]['cleared'] += 1
                self.stats_by_mode[active_mode]['total_wait'] += v.waiting_time
                self.stats_by_mode[active_mode]['samples'].append(v.waiting_time)

            self.lanes[(direction, lane_idx)] = [v for v in vehicles if not v.is_cleared]

        for d in ['N', 'S', 'E', 'W']:
            waiting_in_d = []
            for lane_idx in [0, 1]:
                for v in self.lanes[(d, lane_idx)]:
                    if v.speed < 0.35 and not v.has_crossed_stop_line:
                        waiting_in_d.append(v.waiting_time)

            self.active_queues[d] = len(waiting_in_d)
            self.max_wait_times[d] = max(waiting_in_d) if waiting_in_d else 0.0
            self.avg_wait_times[d] = (sum(waiting_in_d) / len(waiting_in_d)) if waiting_in_d else 0.0

    def get_controller_stats(self):
        return {
            'ns_queue': self.active_queues['N'] + self.active_queues['S'],
            'ew_queue': self.active_queues['E'] + self.active_queues['W'],
            'ns_max_wait': max(self.max_wait_times['N'], self.max_wait_times['S']),
            'ew_max_wait': max(self.max_wait_times['E'], self.max_wait_times['W']),
        }

    def get_overall_stats(self):
        avg_wait = (sum(self.cleared_wait_times) / len(self.cleared_wait_times)) if self.cleared_wait_times else 0.0
        max_cleared_wait = max(self.cleared_wait_times) if self.cleared_wait_times else 0.0
        current_queued = sum(self.active_queues.values())

        fixed_samples = self.stats_by_mode['FIXED']['samples']
        adapt_samples = self.stats_by_mode['ADAPTIVE']['samples']
        fixed_avg = (sum(fixed_samples) / len(fixed_samples)) if fixed_samples else 0.0
        adapt_avg = (sum(adapt_samples) / len(adapt_samples)) if adapt_samples else 0.0

        return {
            'spawned': self.total_spawned,
            'cleared': self.total_cleared,
            'current_queued': current_queued,
            'avg_wait_time': avg_wait,
            'max_wait_time': max_cleared_wait,
            'fixed_cleared': len(fixed_samples),
            'fixed_avg_wait': fixed_avg,
            'adapt_cleared': len(adapt_samples),
            'adapt_avg_wait': adapt_avg,
            'queues': self.active_queues,
            'max_wait_per_dir': self.max_wait_times
        }

    def draw_roads(self, surface):
        half_w = ROAD_WIDTH // 2

        pygame.draw.rect(surface, SIDEWALK_COLOR, (CENTER_X - half_w - 6, 0, ROAD_WIDTH + 12, WINDOW_HEIGHT))
        pygame.draw.rect(surface, SIDEWALK_COLOR, (0, CENTER_Y - half_w - 6, WINDOW_WIDTH, ROAD_WIDTH + 12))

        pygame.draw.rect(surface, ROAD_COLOR, (CENTER_X - half_w, 0, ROAD_WIDTH, WINDOW_HEIGHT))
        pygame.draw.rect(surface, ROAD_COLOR, (0, CENTER_Y - half_w, WINDOW_WIDTH, ROAD_WIDTH))

        pygame.draw.line(surface, ROAD_BORDER_COLOR, (CENTER_X - half_w, 0), (CENTER_X - half_w, WINDOW_HEIGHT), 2)
        pygame.draw.line(surface, ROAD_BORDER_COLOR, (CENTER_X + half_w, 0), (CENTER_X + half_w, WINDOW_HEIGHT), 2)
        pygame.draw.line(surface, ROAD_BORDER_COLOR, (0, CENTER_Y - half_w), (WINDOW_WIDTH, CENTER_Y - half_w), 2)
        pygame.draw.line(surface, ROAD_BORDER_COLOR, (0, CENTER_Y + half_w), (WINDOW_WIDTH, CENTER_Y + half_w), 2)

        yellow_col = (234, 179, 8)
        pygame.draw.line(surface, yellow_col, (CENTER_X - 2, 0), (CENTER_X - 2, CENTER_Y - half_w), 2)
        pygame.draw.line(surface, yellow_col, (CENTER_X + 2, 0), (CENTER_X + 2, CENTER_Y - half_w), 2)
        pygame.draw.line(surface, yellow_col, (CENTER_X - 2, CENTER_Y + half_w), (CENTER_X - 2, WINDOW_HEIGHT), 2)
        pygame.draw.line(surface, yellow_col, (CENTER_X + 2, CENTER_Y + half_w), (CENTER_X + 2, WINDOW_HEIGHT), 2)

        pygame.draw.line(surface, yellow_col, (0, CENTER_Y - 2), (CENTER_X - half_w, CENTER_Y - 2), 2)
        pygame.draw.line(surface, yellow_col, (0, CENTER_Y + 2), (CENTER_X - half_w, CENTER_Y + 2), 2)
        pygame.draw.line(surface, yellow_col, (CENTER_X + half_w, CENTER_Y - 2), (WINDOW_WIDTH, CENTER_Y - 2), 2)
        pygame.draw.line(surface, yellow_col, (CENTER_X + half_w, CENTER_Y + 2), (WINDOW_WIDTH, CENTER_Y + 2), 2)

        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (CENTER_X + LANE_WIDTH, 0), (CENTER_X + LANE_WIDTH, CENTER_Y - half_w))
        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (CENTER_X - LANE_WIDTH, 0), (CENTER_X - LANE_WIDTH, CENTER_Y - half_w))
        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (CENTER_X + LANE_WIDTH, CENTER_Y + half_w), (CENTER_X + LANE_WIDTH, WINDOW_HEIGHT))
        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (CENTER_X - LANE_WIDTH, CENTER_Y + half_w), (CENTER_X - LANE_WIDTH, WINDOW_HEIGHT))

        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (0, CENTER_Y + LANE_WIDTH), (CENTER_X - half_w, CENTER_Y + LANE_WIDTH))
        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (0, CENTER_Y - LANE_WIDTH), (CENTER_X - half_w, CENTER_Y - LANE_WIDTH))
        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (CENTER_X + half_w, CENTER_Y + LANE_WIDTH), (WINDOW_WIDTH, CENTER_Y + LANE_WIDTH))
        self._draw_dashed_line(surface, ROAD_MARKING_COLOR, (CENTER_X + half_w, CENTER_Y - LANE_WIDTH), (WINDOW_WIDTH, CENTER_Y - LANE_WIDTH))

        stop_w = 4
        pygame.draw.line(surface, (255, 255, 255), (CENTER_X, CENTER_Y - STOP_LINE_OFFSET), (CENTER_X + half_w, CENTER_Y - STOP_LINE_OFFSET), stop_w)
        pygame.draw.line(surface, (255, 255, 255), (CENTER_X - half_w, CENTER_Y + STOP_LINE_OFFSET), (CENTER_X, CENTER_Y + STOP_LINE_OFFSET), stop_w)
        pygame.draw.line(surface, (255, 255, 255), (CENTER_X - STOP_LINE_OFFSET, CENTER_Y), (CENTER_X - STOP_LINE_OFFSET, CENTER_Y + half_w), stop_w)
        pygame.draw.line(surface, (255, 255, 255), (CENTER_X + STOP_LINE_OFFSET, CENTER_Y - half_w), (CENTER_X + STOP_LINE_OFFSET, CENTER_Y), stop_w)

        self._draw_zebra_crossing(surface, CENTER_X - half_w, CENTER_Y - half_w - 6, ROAD_WIDTH, 12, horizontal=True)
        self._draw_zebra_crossing(surface, CENTER_X - half_w, CENTER_Y + half_w - 6, ROAD_WIDTH, 12, horizontal=True)
        self._draw_zebra_crossing(surface, CENTER_X - half_w - 6, CENTER_Y - half_w, 12, ROAD_WIDTH, horizontal=False)
        self._draw_zebra_crossing(surface, CENTER_X + half_w - 6, CENTER_Y - half_w, 12, ROAD_WIDTH, horizontal=False)

    def _draw_dashed_line(self, surface, color, start_pos, end_pos, dash_len=12, gap_len=10):
        x1, y1 = start_pos
        x2, y2 = end_pos
        if x1 == x2:
            y = min(y1, y2)
            max_y = max(y1, y2)
            while y < max_y:
                next_y = min(y + dash_len, max_y)
                pygame.draw.line(surface, color, (x1, y), (x1, next_y), 2)
                y += dash_len + gap_len
        else:
            x = min(x1, x2)
            max_x = max(x1, x2)
            while x < max_x:
                next_x = min(x + dash_len, max_x)
                pygame.draw.line(surface, color, (x, y1), (next_x, y1), 2)
                x += dash_len + gap_len

    def _draw_zebra_crossing(self, surface, x, y, width, height, horizontal=True):
        stripe_color = (200, 205, 215)
        if horizontal:
            stripe_width = 8
            gap = 6
            cur_x = x + 4
            while cur_x < x + width - 4:
                pygame.draw.rect(surface, stripe_color, (cur_x, y, stripe_width, height))
                cur_x += stripe_width + gap
        else:
            stripe_height = 8
            gap = 6
            cur_y = y + 4
            while cur_y < y + height - 4:
                pygame.draw.rect(surface, stripe_color, (x, cur_y, width, stripe_height))
                cur_y += stripe_height + gap

    def draw_vehicles(self, surface):
        for vehicles in self.lanes.values():
            for v in vehicles:
                v.draw(surface)
