import os

from bar_cadenza.app.clock import NS_PER_S, SimClock


def _frame_steps(total_ns: int, frames: int) -> list[int]:
    """Real per-frame deltas from evenly spaced timestamps (sums exactly to total_ns)."""
    stamps = [round(i * total_ns / frames) for i in range(frames + 1)]
    return [b - a for a, b in zip(stamps, stamps[1:])]


def _run(steps: list[int]) -> SimClock:
    clock = SimClock()
    for step in steps:
        clock.advance(step)
    return clock


def test_sim_time_identical_across_frame_rates():
    total = 2 * NS_PER_S
    irregular = [3_000_000, 41_000_000, 16_000_000] * 33
    irregular.append(total - sum(irregular))
    results = {_run(_frame_steps(total, n)).sim_ns for n in (30, 60, 144, 7)}
    results.add(_run(irregular).sim_ns)
    assert results == {total}


def test_extreme_gap_is_capped_and_reported():
    clock = SimClock()
    clock.advance(5 * NS_PER_S)
    assert clock.sim_ns == clock.max_step_ns
    assert clock.dropped_ns == 5 * NS_PER_S - clock.max_step_ns


def test_negative_step_does_not_rewind():
    clock = SimClock()
    clock.advance(10_000_000)
    clock.advance(-5_000_000)
    assert clock.sim_ms == 10


def test_window_loop_advances_time_and_shuts_down_headless(monkeypatch):
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    import pygame

    from bar_cadenza.app.window_experiment import run

    stats = run(fps=60, max_seconds=0.3, stress=True)
    assert stats.frames > 5
    assert stats.events > 0
    # Sim time tracks real time (only the final, uncounted frame delay differs).
    assert 0 <= stats.real_ns - stats.sim_ns < 0.1 * NS_PER_S
    assert not pygame.display.get_init()
