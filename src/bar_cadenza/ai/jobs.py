"""Background request runner: daemon worker threads, a result queue polled by the main thread.

No pygame and no provider SDK here. The main thread owns all state; workers only call the
provider and hand back plain data. Every request ends in at most one delivered result
(value, error or timeout); cancelled, timed-out-then-late and stale results are dropped.
"""

import itertools
import queue
import threading
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

# provider(request, cancel_event) -> value. Should return early when cancel_event is set.
Provider = Callable[["JobRequest", threading.Event], object]


@dataclass(frozen=True)
class JobRequest:
    request_id: int
    encounter_id: str
    revision: int  # conversation revision the request was built from
    kind: str
    payload: object  # immutable snapshot prepared by the caller


@dataclass(frozen=True)
class JobResult:
    request: JobRequest
    value: object | None
    error: str | None  # "timeout" or "<Exception>: <message>"; never mixed into value

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class _Pending:
    request: JobRequest
    cancel: threading.Event
    deadline: float


class JobRunner:
    def __init__(
        self,
        provider: Provider,
        workers: int = 2,
        max_pending: int = 8,
        timeout_s: float = 20.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._provider = provider
        self._max_pending = max_pending
        self._timeout_s = timeout_s
        self._clock = clock
        self._ids = itertools.count(1)
        self._pending: dict[int, _Pending] = {}  # main thread only
        self._jobs: queue.Queue = queue.Queue()
        self._results: queue.Queue = queue.Queue()
        self.stats: Counter[str] = Counter()
        # Daemon threads: a provider call that never returns cannot keep the process alive.
        self._threads = [
            threading.Thread(target=self._work, name=f"ai-worker-{i}", daemon=True)
            for i in range(workers)
        ]
        for t in self._threads:
            t.start()

    def submit(
        self, encounter_id: str, revision: int, kind: str, payload: object
    ) -> JobRequest | None:
        """Queue a request; None if the queue is full or this encounter already has one
        of this kind in flight (one dialogue turn per encounter)."""
        busy = any(
            p.request.encounter_id == encounter_id and p.request.kind == kind
            for p in self._pending.values()
        )
        if busy or len(self._pending) >= self._max_pending:
            self.stats["rejected"] += 1
            return None
        request = JobRequest(next(self._ids), encounter_id, revision, kind, payload)
        cancel = threading.Event()
        self._pending[request.request_id] = _Pending(
            request, cancel, self._clock() + self._timeout_s
        )
        self._jobs.put((request, cancel))
        self.stats["submitted"] += 1
        return request

    def in_flight(self, encounter_id: str) -> list[JobRequest]:
        return [p.request for p in self._pending.values() if p.request.encounter_id == encounter_id]

    def cancel(self, request_id: int) -> bool:
        pending = self._pending.pop(request_id, None)
        if pending is None:
            return False
        pending.cancel.set()
        self.stats["cancelled"] += 1
        return True

    def cancel_encounter(self, encounter_id: str) -> None:
        for request in self.in_flight(encounter_id):
            self.cancel(request.request_id)

    def poll(
        self, current_revision: Callable[[str], int | None], max_results: int = 8
    ) -> list[JobResult]:
        """Main thread, once per frame. current_revision(encounter_id) returns the live
        revision, or None when the encounter is closed; mismatches are dropped as stale."""
        results = []
        now = self._clock()
        for request_id, pending in list(self._pending.items()):
            if now >= pending.deadline:
                del self._pending[request_id]
                pending.cancel.set()
                self.stats["timeout"] += 1
                results.append(JobResult(pending.request, None, "timeout"))
        for _ in range(max_results):
            try:
                request_id, value, error = self._results.get_nowait()
            except queue.Empty:
                break
            pending = self._pending.pop(request_id, None)
            if pending is None:
                self.stats["late"] += 1  # cancelled or already timed out
                continue
            self.stats["error" if error else "ok"] += 1
            results.append(JobResult(pending.request, value, error))
        fresh = []
        for result in results:
            if current_revision(result.request.encounter_id) != result.request.revision:
                self.stats["stale"] += 1
            else:
                fresh.append(result)
        return fresh

    def shutdown(self, wait_s: float = 1.0) -> bool:
        """Cancel everything and stop workers; True if all exited within wait_s."""
        for pending in self._pending.values():
            pending.cancel.set()
        self._pending.clear()
        for _ in self._threads:
            self._jobs.put(None)
        deadline = time.monotonic() + wait_s
        for t in self._threads:
            t.join(max(0.0, deadline - time.monotonic()))
        return not any(t.is_alive() for t in self._threads)

    def _work(self) -> None:
        while (job := self._jobs.get()) is not None:
            request, cancel = job
            if cancel.is_set():
                continue
            try:
                value, error = self._provider(request, cancel), None
            except Exception as exc:  # provider failures become data, never crash the game
                value, error = None, f"{type(exc).__name__}: {exc}"
            if not cancel.is_set():
                self._results.put((request.request_id, value, error))
