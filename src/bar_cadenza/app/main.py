"""Game entry: startup checks, window, frame loop and scene routing.

Run: uv run python -m bar_cadenza [--seconds S]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pygame

from bar_cadenza.app.clock import NS_PER_S, SimClock
from bar_cadenza.app.paths import resource_root
from bar_cadenza.domain.session import LANGUAGES, Session
from bar_cadenza.scenes.shell import MainMenu

LOGICAL_SIZE = (1280, 720)  # B007
FONT = "assets/fonts/NanumGothic-Regular.ttf"
# SDL2 on Windows freezes the loop while the window is dragged or resized; these events
# arrive in the first frame after, whose gap is then dropped (D022).
STALL_EVENTS = {pygame.WINDOWMOVED, pygame.WINDOWSIZECHANGED}


class StartupError(Exception):
    """A required resource is missing or unreadable; the message names it."""


def load_strings(root: Path) -> dict[str, dict[str, str]]:
    """Check required resources and return UI strings per language."""
    if not (root / FONT).is_file():
        raise StartupError(f"Missing required font: {root / FONT}")
    strings = {}
    for lang in LANGUAGES:
        path = root / "content/locales" / f"{lang}.json"
        try:
            strings[lang] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise StartupError(f"Cannot read required file {path}: {exc}") from exc
    if mismatch := strings["ko"].keys() ^ strings["en"].keys():
        raise StartupError(f"ko.json and en.json keys differ: {sorted(mismatch)}")
    return strings


class App:
    """Owns the session, the simulation clock and the active scene (main thread only)."""

    def __init__(self, screen: pygame.Surface, strings: dict, font_path: Path) -> None:
        self.screen, self.strings = screen, strings
        self.font = pygame.font.Font(font_path, 28)
        self.title_font = pygame.font.Font(font_path, 44)
        self.small_font = pygame.font.Font(font_path, 22)
        self.sim = SimClock()
        self.session: Session | None = None
        self.running = True
        self.scene = MainMenu(self)

    def t(self, key: str, **values) -> str:
        """String in the session's language."""
        text = self.strings[self.session.language][key]
        return text.format(**values) if values else text

    def bilingual(self, key: str) -> str:
        """Both languages, for screens shown before a language is chosen."""
        ko, en = self.strings["ko"][key], self.strings["en"][key]
        return ko if ko == en else f"{ko} · {en}"

    def go(self, scene) -> None:
        self.scene = scene

    def frame(self, events: list, dt_ns: int) -> None:
        """Events first, so a pause or a drag reported this frame also keeps this frame's
        gap out of game time (D022). Typing and busy actions never stop time."""
        stalled = False
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            else:
                stalled |= event.type in STALL_EVENTS
                self.scene.handle(event)
        if not (stalled or getattr(self.scene, "paused", False)):
            self.sim.advance(dt_ns)
        if update := getattr(self.scene, "update", None):
            update()
        self.scene.draw(self.screen)


def _report_startup_error(message: str) -> None:
    if sys.stderr:
        print(message, file=sys.stderr)
    try:  # the windowed build has no console, so also show a native dialog
        pygame.display.message_box(
            "Bar Cadenza",
            f"{message}\n\n필수 파일이 없거나 읽을 수 없습니다.\nA required file is missing or unreadable.",
            message_type="error",
        )
    except pygame.error:
        pass


def run(max_seconds: float | None = None) -> int:
    root = resource_root()
    try:
        strings = load_strings(root)
    except StartupError as exc:
        _report_startup_error(str(exc))
        return 1
    os.environ.setdefault("SDL_IME_SHOW_UI", "1")  # native candidate list (e.g. Hanja)
    pygame.init()
    try:
        screen = pygame.display.set_mode(LOGICAL_SIZE, pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(strings["en"]["app.title"])
        pygame.key.set_repeat(500, 33)  # held keys repeat like Windows (D021)
        app = App(screen, strings, root / FONT)
        limiter = pygame.time.Clock()
        start = last = time.perf_counter_ns()
        while app.running:
            now = time.perf_counter_ns()
            app.frame(pygame.event.get(), now - last)
            last = now
            if max_seconds is not None and now - start >= max_seconds * NS_PER_S:
                break
            pygame.display.flip()
            limiter.tick(60)
    finally:
        pygame.quit()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Bar Cadenza")
    parser.add_argument("--seconds", type=float, default=None, help="auto-quit after S seconds")
    sys.exit(run(parser.parse_args().seconds))
