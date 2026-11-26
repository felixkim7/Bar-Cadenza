"""Simulation clock driven by real elapsed time, never by frame count. No pygame import."""

from dataclasses import dataclass

NS_PER_MS = 1_000_000
NS_PER_S = 1_000_000_000

# ponytail: one fixed cap for unexplained gaps; pause/focus/drag stalls are handled by D022.
MAX_STEP_NS = 1 * NS_PER_S


@dataclass
class SimClock:
    """Integer nanoseconds so per-frame steps never lose remainders."""

    sim_ns: int = 0
    dropped_ns: int = 0
    max_step_ns: int = MAX_STEP_NS

    def advance(self, real_dt_ns: int) -> int:
        """Advance by real elapsed time; return the simulated step."""
        real_dt_ns = max(real_dt_ns, 0)
        step = min(real_dt_ns, self.max_step_ns)
        self.dropped_ns += real_dt_ns - step
        self.sim_ns += step
        return step

    @property
    def sim_ms(self) -> int:
        return self.sim_ns // NS_PER_MS
