"""T002 window and frame-loop experiment (not the game).

Run: uv run python -m bar_cadenza.app.window_experiment [--fps N] [--seconds S] [--stress]
"""

import argparse
import ctypes
import sys
import time
from dataclasses import dataclass

import pygame

from bar_cadenza.app.clock import NS_PER_MS, NS_PER_S, SimClock

LOGICAL_SIZE = (1280, 720)  # B007 logical layout; SCALED maps window/mouse to it.
# Outer sizes; below-minimum requests are clamped to LOGICAL_SIZE by SCALED.
STRESS_SIZES = [(1600, 950), (960, 540), (1800, 1080), (1350, 800)]
BG, FG, ACCENT = (21, 12, 12), (234, 206, 170), (211, 152, 88)  # Balsamico/Champagne/Whiskey Sour


@dataclass
class RunStats:
    frames: int = 0
    real_ns: int = 0
    sim_ns: int = 0
    dropped_ns: int = 0
    max_frame_ns: int = 0
    events: int = 0
    resizes: int = 0
    window_size: tuple[int, int] = (0, 0)


def indicator_x(sim_ns: int, travel_px: int, speed_px_s: int = 400) -> int:
    """Back-and-forth position as a pure function of simulation time."""
    pos = sim_ns * speed_px_s // NS_PER_S % (2 * travel_px)
    return pos if pos < travel_px else 2 * travel_px - pos


def _post_stress(hwnd: int | None, frame: int) -> None:
    """Synthetic sustained input plus periodic OS-level resizes (same path as a user drag)."""
    for i in range(50):
        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=(i, i), rel=(1, 1)))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=0))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_a, mod=0))
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text="가"))
    if hwnd and frame % 30 == 0:
        w, h = STRESS_SIZES[frame // 30 % len(STRESS_SIZES)]
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0002 | 0x0004)  # NOMOVE|NOZORDER


def run(fps: int = 60, max_seconds: float | None = None, stress: bool = False) -> RunStats:
    pygame.init()
    try:
        screen = pygame.display.set_mode(LOGICAL_SIZE, pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption("Bar Cadenza — T002 frame-loop experiment")
        # pygame-ce ignores Window.size under SCALED; resize via Win32 instead (stress only).
        on_win = stress and sys.platform == "win32"
        hwnd = pygame.display.get_wm_info().get("window") if on_win else None
        font = pygame.font.Font(None, 30)
        sim, stats, limiter = SimClock(), RunStats(), pygame.time.Clock()
        start = last = time.perf_counter_ns()
        running = True
        while running:
            now = time.perf_counter_ns()
            dt, last = now - last, now
            sim.advance(dt)
            stats.frames += 1
            stats.max_frame_ns = max(stats.max_frame_ns, dt)
            if stress:
                _post_stress(hwnd, stats.frames)
            for event in pygame.event.get():
                stats.events += 1
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.WINDOWSIZECHANGED:
                    stats.resizes += 1
            if max_seconds is not None and now - start >= max_seconds * NS_PER_S:
                running = False

            screen.fill(BG)
            x = 40 + indicator_x(sim.sim_ns, LOGICAL_SIZE[0] - 120)
            pygame.draw.rect(screen, ACCENT, (x, 300, 40, 40))
            lines = [
                f"sim {sim.sim_ns / NS_PER_S:8.2f} s   real {(now - start) / NS_PER_S:8.2f} s",
                f"fps {limiter.get_fps():5.1f}   max frame {stats.max_frame_ns / NS_PER_MS:6.1f} ms"
                f"   dropped {sim.dropped_ns / NS_PER_MS:.0f} ms",
                f"window {pygame.display.get_window_size()}   resizes {stats.resizes}   events {stats.events}",
                "Resize, type, move the mouse: the square must keep moving. Esc or close to quit.",
            ]
            for i, line in enumerate(lines):
                screen.blit(font.render(line, True, FG), (40, 40 + i * 36))
            pygame.display.flip()
            limiter.tick(fps)

        stats.real_ns = time.perf_counter_ns() - start
        stats.sim_ns, stats.dropped_ns = sim.sim_ns, sim.dropped_ns
        stats.window_size = pygame.display.get_window_size()
        return stats
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--seconds", type=float, default=None, help="auto-quit after S seconds")
    parser.add_argument("--stress", action="store_true", help="synthetic input + resizes")
    args = parser.parse_args()
    stats = run(args.fps, args.seconds, args.stress)
    print(
        f"frames={stats.frames} real_s={stats.real_ns / NS_PER_S:.3f} "
        f"sim_s={stats.sim_ns / NS_PER_S:.3f} dropped_ms={stats.dropped_ns / NS_PER_MS:.1f} "
        f"max_frame_ms={stats.max_frame_ns / NS_PER_MS:.1f} events={stats.events} "
        f"resizes={stats.resizes} final_window={stats.window_size}"
    )


if __name__ == "__main__":
    main()
