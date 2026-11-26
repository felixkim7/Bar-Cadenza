"""T004 background job and latency experiment (not the game).

Run: uv run python -m bar_cadenza.ai.latency_experiment [--seconds S] [--auto]
Keys: Enter send · C cancel · R new revision (pending reply goes stale) · N next guest
(closes the encounter; its pending reply goes stale) · Esc quit. --auto presses them on a timer.
Fake guest: replies after 0.1-1.5 s, fails 15%, hangs 15% (times out after 2 s).
"""

import argparse
import random
import threading
import time
from collections import deque

import pygame

from bar_cadenza.ai.jobs import JobRequest, JobRunner
from bar_cadenza.app.clock import NS_PER_MS, NS_PER_S, SimClock
from bar_cadenza.app.window_experiment import ACCENT, BG, FG, LOGICAL_SIZE, indicator_x

TIMEOUT_S = 2.0
KEYS = {pygame.K_RETURN: "send", pygame.K_c: "cancel", pygame.K_r: "revision", pygame.K_n: "next"}


def fake_guest(request: JobRequest, cancel: threading.Event) -> str | None:
    rng = random.Random(request.request_id)
    roll = rng.random()
    if roll < 0.15:
        cancel.wait(30)  # hang until the runner times out and cancels
        return None
    if cancel.wait(rng.uniform(0.1, 1.5)):
        return None
    if roll < 0.30:
        raise ConnectionError("simulated network failure")
    return f"reply to {request.payload!r}"


def run(max_seconds: float | None = None, auto: bool = False) -> dict:
    pygame.init()
    runner = JobRunner(fake_guest, timeout_s=TIMEOUT_S)
    report: dict = {}
    try:
        screen = pygame.display.set_mode(LOGICAL_SIZE, pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption("Bar Cadenza — T004 background job experiment")
        font = pygame.font.Font(None, 28)
        sim, limiter, rng = SimClock(), pygame.time.Clock(), random.Random(0)
        guest, revisions = 1, {"guest-1": 0}
        log: deque[str] = deque(maxlen=12)
        max_frame_ns = frame = 0
        start = last = time.perf_counter_ns()
        running = True
        while running:
            now = time.perf_counter_ns()
            dt, last = now - last, now
            sim.advance(dt)
            max_frame_ns, frame = max(max_frame_ns, dt), frame + 1
            actions = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in KEYS:
                    actions.append(KEYS[event.key])
            if auto and frame % 12 == 0:
                actions += rng.choices(["send", "revision", "cancel", "next"], [60, 15, 10, 15])

            for action in actions:
                eid = f"guest-{guest}"
                if action == "send":
                    req = runner.submit(eid, revisions[eid], "dialogue", f"hello at frame {frame}")
                    log.append(f"sent #{req.request_id} (rev {req.revision})" if req else "busy")
                elif action == "cancel":
                    for req in runner.in_flight(eid):
                        runner.cancel(req.request_id)
                        log.append(f"cancelled #{req.request_id}")
                elif action == "revision":
                    revisions[eid] += 1
                    log.append(f"{eid} now at rev {revisions[eid]}")
                elif action == "next":
                    del revisions[eid]
                    guest += 1
                    revisions[f"guest-{guest}"] = 0
                    log.append(f"{eid} left; guest-{guest} arrived")
            for result in runner.poll(revisions.get):
                outcome = result.value if result.ok else f"ERROR {result.error}"
                log.append(f"#{result.request.request_id} -> {outcome}")
            if max_seconds is not None and now - start >= max_seconds * NS_PER_S:
                running = False

            screen.fill(BG)
            pygame.draw.rect(screen, ACCENT, (40 + indicator_x(sim.sim_ns, 1160), 20, 32, 32))
            eid = f"guest-{guest}"
            in_flight = [r.request_id for r in runner.in_flight(eid)]
            lines = [
                f"sim {sim.sim_ns / NS_PER_S:7.2f} s   max frame {max_frame_ns / NS_PER_MS:5.1f} ms"
                f"   fps {limiter.get_fps():5.1f}",
                f"{eid}  rev {revisions[eid]}  in flight {in_flight}",
                "stats " + "  ".join(f"{k}={v}" for k, v in sorted(runner.stats.items())),
                "Enter send · C cancel · R new revision · N next guest · Esc quit",
                "",
                *log,
            ]
            for i, line in enumerate(lines):
                screen.blit(font.render(line, True, FG), (40, 70 + i * 32))
            pygame.display.flip()
            limiter.tick(60)
        report = {"frames": frame, "max_frame_ms": round(max_frame_ns / NS_PER_MS, 1)}
    finally:
        t0 = time.perf_counter()
        report["clean_shutdown"] = runner.shutdown()
        report["shutdown_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        report.update(runner.stats)
        pygame.quit()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=None, help="auto-quit after S seconds")
    parser.add_argument("--auto", action="store_true", help="press keys on a timer")
    args = parser.parse_args()
    print(" ".join(f"{k}={v}" for k, v in run(args.seconds, args.auto).items()))


if __name__ == "__main__":
    main()
