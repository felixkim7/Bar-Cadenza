"""Application shell scenes (T006). Pre-shift, bar and results are labelled placeholders.

A scene has handle(event) and draw(screen); it switches scenes with app.go(...).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from bar_cadenza.app.clock import NS_PER_S
from bar_cadenza.domain.session import Session
from bar_cadenza.ui.buttons import ButtonList
from bar_cadenza.ui.palette import BALSAMICO, CHAMPAGNE, HONEY_GARLIC, WHISKEY_SOUR

if TYPE_CHECKING:
    from bar_cadenza.app.main import App

CENTER_X = 640


def _draw_frame(app: App, screen, title: str, subtitle: str = "", placeholder=False) -> None:
    screen.fill(BALSAMICO)
    text = app.title_font.render(title, True, CHAMPAGNE)
    screen.blit(text, text.get_rect(midtop=(CENTER_X, 90)))
    if subtitle:
        text = app.font.render(subtitle, True, WHISKEY_SOUR)
        screen.blit(text, text.get_rect(midtop=(CENTER_X, 160)))
    if placeholder:
        banner = pygame.Rect(0, 660, 1280, 44)
        pygame.draw.rect(screen, HONEY_GARLIC, banner)
        text = app.small_font.render(app.t("scene.placeholder"), True, CHAMPAGNE)
        screen.blit(text, text.get_rect(center=banner.center))


class MainMenu:
    """Shown before any language is chosen, so labels are bilingual."""

    def __init__(self, app: App) -> None:
        self.app = app
        self.notice: str | None = None
        actions = ("new_game", "continue", "settings", "quit")
        self.buttons = ButtonList([(a, app.bilingual(f"menu.{a}")) for a in actions], CENTER_X, 250)

    def handle(self, event) -> None:
        action = self.buttons.handle(event)
        if action == "new_game":
            self.app.go(LanguageSelect(self.app))
        elif action == "continue":
            self.notice = "menu.no_save"  # ponytail: no saves until T011
        elif action == "settings":
            self.notice = "menu.settings_unavailable"
        elif action == "quit":
            self.app.running = False

    def draw(self, screen) -> None:
        _draw_frame(self.app, screen, self.app.strings["en"]["app.title"])
        self.buttons.draw(screen, self.app.font)
        if self.notice:
            for i, lang in enumerate(("ko", "en")):
                text = self.app.small_font.render(
                    self.app.strings[lang][self.notice], True, CHAMPAGNE
                )
                screen.blit(text, text.get_rect(midtop=(CENTER_X, 560 + i * 32)))


class LanguageSelect:
    def __init__(self, app: App) -> None:
        self.app = app
        items = [("ko", app.strings["ko"]["language.ko"]), ("en", app.strings["en"]["language.en"])]
        self.buttons = ButtonList([*items, ("back", app.bilingual("common.back"))], CENTER_X, 270)

    def handle(self, event) -> None:
        action = self.buttons.handle(event)
        if action in ("ko", "en"):
            self.app.session = Session(language=action)
            self.app.go(PreShift(self.app))
        elif action == "back":
            self.app.go(MainMenu(self.app))

    def draw(self, screen) -> None:
        s = self.app.strings
        _draw_frame(self.app, screen, s["ko"]["language.choose"], s["en"]["language.choose"])
        self.buttons.draw(screen, self.app.font)


class PreShift:
    def __init__(self, app: App) -> None:
        self.app = app
        self.buttons = ButtonList([("open", app.t("preshift.open"))], CENTER_X, 330)

    def handle(self, event) -> None:
        if self.buttons.handle(event) == "open":
            self.app.go(Bar(self.app))

    def draw(self, screen) -> None:
        app = self.app
        subtitle = app.t("shift.number", n=app.session.shift)
        _draw_frame(app, screen, app.t("preshift.title"), subtitle, placeholder=True)
        self.buttons.draw(screen, app.font)


class Bar:
    def __init__(self, app: App) -> None:
        self.app = app
        self.opened_ns = app.sim.sim_ns
        self.buttons = ButtonList([("close", app.t("bar.close"))], CENTER_X, 330)

    def handle(self, event) -> None:
        if self.buttons.handle(event) == "close":
            self.app.go(Results(self.app))

    def draw(self, screen) -> None:
        app = self.app
        minutes, seconds = divmod((app.sim.sim_ns - self.opened_ns) // NS_PER_S, 60)
        subtitle = app.t("bar.shift_time", time=f"{minutes:02d}:{seconds:02d}")
        _draw_frame(app, screen, app.t("bar.title"), subtitle, placeholder=True)
        self.buttons.draw(screen, app.font)


class Results:
    def __init__(self, app: App) -> None:
        self.app = app
        items = [("next", app.t("results.next_shift")), ("menu", app.t("results.main_menu"))]
        self.buttons = ButtonList(items, CENTER_X, 330)

    def handle(self, event) -> None:
        action = self.buttons.handle(event)
        if action == "next":
            self.app.session.shift += 1
            self.app.go(PreShift(self.app))
        elif action == "menu":
            self.app.session = None
            self.app.go(MainMenu(self.app))

    def draw(self, screen) -> None:
        app = self.app
        subtitle = app.t("shift.number", n=app.session.shift)
        _draw_frame(app, screen, app.t("results.title"), subtitle, placeholder=True)
        self.buttons.draw(screen, app.font)
