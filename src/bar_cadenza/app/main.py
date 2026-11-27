"""Game entry: startup checks, window, frame loop and scene routing.

Run: uv run python -m bar_cadenza [--seconds S]
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import pygame

from bar_cadenza.app.assets import AssetError, AssetStore, Manifest, load_manifest
from bar_cadenza.app.clock import NS_PER_S, SimClock
from bar_cadenza.app.paths import resource_root, user_data_dir
from bar_cadenza.domain.session import LANGUAGES, Language, Session
from bar_cadenza.persistence.saves import (
    SaveError,
    create_save,
    latest_save,
    load_save,
    write_save,
)
from bar_cadenza.scenes.shell import MainMenu

log = logging.getLogger(__name__)

LOGICAL_SIZE = (1280, 720)  # B007: every scene draws in these logical pixels
FONT = "assets/fonts/NanumGothic-Regular.ttf"
MANIFEST = "assets/manifest.json"
# O007 (T009): SDL settings read at pygame.init()/set_mode(), measured by window capture.
DISPLAY_HINTS = {
    "SDL_IME_SHOW_UI": "1",  # native candidate list (e.g. Hanja)
    "SDL_WINDOWS_DPI_AWARENESS": "permonitorv2",  # SDL scales once; Windows does not stretch again
    # ponytail: pygame-ce reads this literal hint name to scale SCALED windows fractionally
    # (fill the window) instead of in whole steps; re-measure after a pygame-ce upgrade.
    "SDL_HINT_RENDER_SCALE_QUALITY": "1",
    "PYGAME_FORCE_SCALE": "photo",  # smooth filtering for that scale
}
WINDOW_SHARE = 0.8  # opening window: 80% of the desktop, keeping 16:9
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


def open_window(title: str) -> pygame.Surface:
    """Logical 1280×720 canvas scaled to fill a resizable window, with bars only on the
    axis whose ratio differs (O007). Call after setting DISPLAY_HINTS and pygame.init()."""
    screen = pygame.display.set_mode(LOGICAL_SIZE, pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption(title)
    (dw, dh), (lw, lh) = pygame.display.get_desktop_sizes()[0], LOGICAL_SIZE
    scale = WINDOW_SHARE * min(dw / lw, dh / lh)
    window = pygame.Window.from_display_module()
    window.size = (round(lw * scale), round(lh * scale))
    window.position = pygame.WINDOWPOS_CENTERED
    return screen


class App:
    """Owns the session and its save file, the simulation clock, the assets and the active
    scene (main thread only). Assets load on first use; run() preloads them so the bar opens
    without a stall."""

    def __init__(
        self, screen: pygame.Surface, strings: dict, root: Path, manifest: Manifest, saves: Path
    ):
        self.screen, self.strings = screen, strings
        self.font = pygame.font.Font(root / FONT, 28)
        self.title_font = pygame.font.Font(root / FONT, 44)
        self.small_font = pygame.font.Font(root / FONT, 22)
        self.assets = AssetStore(root / "assets", manifest, self.small_font)
        self.sim = SimClock()
        self.session: Session | None = None
        self.saves, self.save_path = saves, None
        self.running = True
        self.scene = MainMenu(self)

    # Saves happen at shift boundaries (DATA_MODELS): when a game starts and when a shift ends.
    # Each returns the locale key of the notice to show.
    def new_game(self, language: Language) -> str:
        self.session, self.save_path = Session(language=language), None
        return self.save_game(self.session)

    def continue_game(self) -> str | None:
        """Load the newest save; None on success."""
        if (path := latest_save(self.saves)) is None:
            return "menu.no_save"
        try:
            self.session = load_save(path)
        except SaveError as exc:
            log.warning("cannot load save: %s", exc)
            return f"save.{exc.reason}"
        self.save_path = path
        return None

    def save_game(self, snapshot: Session) -> str:
        """On failure the game goes on with its progress in memory; it never claims a save."""
        try:
            if self.save_path is None:
                self.save_path = create_save(self.saves, snapshot)
            else:
                write_save(self.save_path, snapshot)
        except SaveError as exc:
            log.warning("cannot save: %s", exc)
            return f"save.{exc.reason}"
        return "save.done"

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
        manifest = load_manifest(root / MANIFEST)
    except (StartupError, AssetError) as exc:
        _report_startup_error(str(exc))
        return 1
    for name, value in DISPLAY_HINTS.items():
        os.environ.setdefault(name, value)
    pygame.init()
    try:
        screen = open_window(strings["en"]["app.title"])
        pygame.key.set_repeat(500, 33)  # held keys repeat like Windows (D021)
        app = App(screen, strings, root, manifest, user_data_dir() / "saves")
        for asset in manifest.assets:  # load and scale once, before the clock starts
            app.assets.image(asset.asset_id)
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
