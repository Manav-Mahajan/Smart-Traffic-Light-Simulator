import sys
import os
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, BG_COLOR
from intersection import Intersection
from traffic_light import TrafficController
from ui import Dashboard

def main():
    test_mode = "--test" in sys.argv
    max_frames = 180 if test_mode else None

    if test_mode or os.environ.get("SDL_VIDEODRIVER") == "dummy":
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    pygame.init()
    pygame.display.set_caption("Smart Traffic Light Simulator")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    intersection = Intersection()
    traffic_controller = TrafficController(mode="ADAPTIVE")
    dashboard = Dashboard(x=780, y=0, width=420, height=WINDOW_HEIGHT)

    is_paused = False
    presets = ["BALANCED", "HEAVY_NS", "RUSH_HOUR"]
    preset_idx = 0

    def toggle_mode():
        new_mode = traffic_controller.toggle_mode()
        dashboard.update_button_labels(new_mode, intersection.traffic_preset, intersection.spawn_rate)

    def cycle_preset():
        nonlocal preset_idx
        preset_idx = (preset_idx + 1) % len(presets)
        intersection.set_preset(presets[preset_idx])
        dashboard.update_button_labels(traffic_controller.mode, presets[preset_idx], intersection.spawn_rate)

    def force_phase():
        traffic_controller.force_next_phase()

    def inc_spawn():
        intersection.adjust_spawn_rate(0.2)
        dashboard.update_button_labels(traffic_controller.mode, intersection.traffic_preset, intersection.spawn_rate)

    def dec_spawn():
        intersection.adjust_spawn_rate(-0.2)
        dashboard.update_button_labels(traffic_controller.mode, intersection.traffic_preset, intersection.spawn_rate)

    def reset_stats():
        intersection.reset_stats()

    dashboard.setup_buttons(
        toggle_mode_cb=toggle_mode,
        cycle_preset_cb=cycle_preset,
        force_phase_cb=force_phase,
        inc_spawn_cb=inc_spawn,
        dec_spawn_cb=dec_spawn,
        reset_cb=reset_stats
    )
    dashboard.update_button_labels(traffic_controller.mode, intersection.traffic_preset, intersection.spawn_rate)

    for _ in range(4):
        intersection._try_spawn_vehicle('N')
        intersection._try_spawn_vehicle('S')
        intersection._try_spawn_vehicle('E')
        intersection._try_spawn_vehicle('W')

    running = True
    frame_count = 0

    print("Smart Traffic Light Simulator running...")

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        frame_count += 1

        if max_frames and frame_count >= max_frames:
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if dashboard.handle_event(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    is_paused = not is_paused
                elif event.key == pygame.K_m:
                    toggle_mode()
                elif event.key == pygame.K_p:
                    cycle_preset()
                elif event.key == pygame.K_t:
                    force_phase()
                elif event.key in [pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS]:
                    inc_spawn()
                elif event.key in [pygame.K_MINUS, pygame.K_KP_MINUS]:
                    dec_spawn()
                elif event.key == pygame.K_r:
                    reset_stats()

        if not is_paused:
            ctrl_stats = intersection.get_controller_stats()
            traffic_controller.update(dt, ctrl_stats)
            intersection.update(dt, traffic_controller)

        screen.fill(BG_COLOR)
        intersection.draw_roads(screen)
        traffic_controller.draw(screen)
        intersection.draw_vehicles(screen)
        dashboard.draw(screen, traffic_controller, intersection, is_paused)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
