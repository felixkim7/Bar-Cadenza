import subprocess
import sys
import threading
import time

from bar_cadenza.ai.jobs import JobRequest, JobRunner


def delayed(request: JobRequest, cancel: threading.Event):
    """Fake provider scripted by payload: delay seconds, optional failure."""
    if cancel.wait(request.payload.get("delay", 0.0)):
        return None
    if request.payload.get("fail"):
        raise RuntimeError("simulated provider failure")
    return f"reply to {request.payload['text']}"


def collect(runner: JobRunner, revisions: dict, seconds: float = 2.0) -> list:
    """Poll like a frame loop until the runner has nothing in flight (or time runs out)."""
    results, end = [], time.monotonic() + seconds
    while time.monotonic() < end:
        results += runner.poll(revisions.get)
        if not runner._pending and runner._results.empty():
            break
        time.sleep(0.005)
    return results


def test_result_carries_identity_and_submit_never_blocks():
    runner = JobRunner(delayed)
    start = time.monotonic()
    request = runner.submit("enc1", 3, "dialogue", {"text": "hi", "delay": 0.3})
    assert time.monotonic() - start < 0.05
    [result] = collect(runner, {"enc1": 3})
    assert result.ok and result.value == "reply to hi"
    assert (result.request.request_id, result.request.encounter_id) == (request.request_id, "enc1")
    assert (result.request.revision, result.request.kind) == (3, "dialogue")
    assert runner.shutdown()


def test_provider_failure_becomes_error_data_not_dialogue():
    runner = JobRunner(delayed)
    runner.submit("enc1", 0, "dialogue", {"text": "hi", "fail": True})
    [result] = collect(runner, {"enc1": 0})
    assert (result.ok, result.value) == (False, None)
    assert result.error == "RuntimeError: simulated provider failure"
    assert runner.shutdown()


def test_timeout_is_reported_once_and_the_late_value_is_dropped():
    seen = threading.Event()

    def ignores_cancel(request, cancel):
        time.sleep(0.3)
        seen.set()
        return "too late"

    runner = JobRunner(ignores_cancel, timeout_s=0.05)
    runner.submit("enc1", 0, "dialogue", {})
    time.sleep(0.1)
    assert [r.error for r in runner.poll({"enc1": 0}.get)] == ["timeout"]
    seen.wait(1)
    time.sleep(0.05)
    assert runner.poll({"enc1": 0}.get) == []
    assert runner.shutdown()


def test_cancelled_request_never_delivers_and_provider_sees_cancel():
    saw_cancel = threading.Event()

    def cooperative(request, cancel):
        if cancel.wait(1.0):
            saw_cancel.set()
        return "should not arrive"

    runner = JobRunner(cooperative)
    request = runner.submit("enc1", 0, "dialogue", {})
    time.sleep(0.05)
    assert runner.cancel(request.request_id)
    assert saw_cancel.wait(1)
    assert collect(runner, {"enc1": 0}, seconds=0.2) == []
    assert runner.stats["cancelled"] == 1
    assert runner.shutdown()


def test_stale_revision_and_closed_encounter_results_are_dropped():
    runner = JobRunner(delayed)
    runner.submit("enc1", 1, "dialogue", {"text": "a", "delay": 0.05})
    runner.submit("enc2", 1, "dialogue", {"text": "b", "delay": 0.05})
    # enc1 moved on to revision 2; enc2 closed (absent -> None).
    assert collect(runner, {"enc1": 2}) == []
    assert runner.stats["stale"] == 2
    assert runner.shutdown()


def test_one_in_flight_request_per_encounter_and_kind_and_bounded_queue():
    runner = JobRunner(delayed, max_pending=2)
    assert runner.submit("enc1", 0, "dialogue", {"text": "a", "delay": 0.1})
    assert runner.submit("enc1", 0, "dialogue", {"text": "dup"}) is None
    assert runner.submit("enc2", 0, "dialogue", {"text": "b", "delay": 0.1})
    assert runner.submit("enc3", 0, "dialogue", {"text": "c"}) is None  # queue full
    assert len(collect(runner, {"enc1": 0, "enc2": 0})) == 2
    assert runner.submit("enc1", 0, "dialogue", {"text": "again"})  # free again
    assert runner.shutdown()


def test_shutdown_returns_promptly_even_with_a_hung_provider():
    runner = JobRunner(lambda request, cancel: time.sleep(60))
    runner.submit("enc1", 0, "dialogue", {})
    time.sleep(0.05)
    start = time.monotonic()
    assert runner.shutdown(wait_s=0.2) is False  # the hung worker is abandoned
    assert time.monotonic() - start < 0.5


def test_experiment_runs_headless_with_traffic_and_shuts_down(monkeypatch):
    import os

    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    from bar_cadenza.ai.latency_experiment import run

    report = run(max_seconds=1.5, auto=True)
    assert report["frames"] > 30 and report["submitted"] > 0
    assert report["clean_shutdown"] is True


def test_process_exits_while_a_provider_call_is_hung():
    script = (
        "import time; from bar_cadenza.ai.jobs import JobRunner\n"
        "r = JobRunner(lambda req, cancel: time.sleep(60))\n"
        "r.submit('enc1', 0, 'dialogue', {}); time.sleep(0.1); r.shutdown(wait_s=0.1)\n"
    )
    start = time.monotonic()
    done = subprocess.run([sys.executable, "-c", script], timeout=10)
    assert done.returncode == 0
    assert time.monotonic() - start < 5
