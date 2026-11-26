"""Application shell scenes (T006). Pre-shift, bar and results are labelled placeholders.

A scene has handle(event) and draw(screen); it switches scenes with app.go(...).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from bar_cadenza.app.clock import NS_PER_S
from bar_cadenza.domain.encounter import DrinkState, Encounter, Phase, Talk
from bar_cadenza.domain.session import Session
from bar_cadenza.ui.buttons import ButtonList
from bar_cadenza.ui.input_router import InputRouter
from bar_cadenza.ui.palette import BALSAMICO, BURNT_COFFEE, CHAMPAGNE, HONEY_GARLIC, WHISKEY_SOUR
from bar_cadenza.ui.text_input import TextField, draw_field, wrap_spans

if TYPE_CHECKING:
    from bar_cadenza.app.main import App

CENTER_X = 640
FIELD_RECT = pygame.Rect(100, 528, 1080, 118)
REPLY_DELAY_NS = 3 * NS_PER_S // 2
PAUSE_EVENTS = {pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED}  # D022: unseen → paused


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
    """Placeholder bar (T007 test bench): one guest, a chat field, a hold-to-stir tool and
    serving, each on its own state track, plus the D022 pause menu."""

    def __init__(self, app: App) -> None:
        self.app = app
        t = app.t
        self.opened_ns = app.sim.sim_ns
        self.encounter = Encounter(f"shift{app.session.shift}-guest1")
        self.encounter.move(Phase.ORDERING)
        self.field = TextField()
        self.stir_rect = pygame.Rect(100, 245, 440, 196)
        items = [("add", t("bar.add")), ("serve", t("bar.serve")), ("close", t("bar.close"))]
        self.buttons = ButtonList(items, 900, 245, width=440)
        pause_items = [("resume", t("bar.resume")), ("menu", t("results.main_menu"))]
        self.pause_buttons = ButtonList(pause_items, CENTER_X, 300)
        self.router = InputRouter(self.field, FIELD_RECT, self.buttons, {"stir": self.stir_rect})
        self.stirred_ns = 0
        self.stir_from: int | None = None
        self.notice: str | None = None
        self.you = self.guest = ""
        self.reply_due: tuple[int, int] | None = None  # (sim_ns, revision)
        self._ime_rect = None

    @property
    def paused(self) -> bool:
        return self.router.modal is not None

    def handle(self, event) -> None:
        esc = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        if event.type in PAUSE_EVENTS or (esc and not self.paused):
            if not self.paused:
                self._apply(self.router.open_modal(self.pause_buttons))
        elif esc:
            self.router.close_modal()
        else:
            self._apply(self.router.handle(event))

    def _drink(self) -> DrinkState | None:
        return self.encounter.drinks[-1].state if self.encounter.drinks else None

    def _apply(self, routed) -> None:
        if routed is None:
            return
        kind, value = routed
        enc, now = self.encounter, self.app.sim.sim_ns
        if kind == "send":
            self.you, self.guest = value, ""
            self.reply_due = (now + REPLY_DELAY_NS, enc.send_player_turn())
            self.field.send_blocked = not enc.can_send
        elif kind == "hold":
            self.notice = None
            if self._drink() in (DrinkState.ASSEMBLING, DrinkState.MIXING, DrinkState.READY):
                enc.move_drink(DrinkState.MIXING)
                self.stir_from = now
            else:
                self.notice = "bar.need_ingredient"
        elif kind == "release" and self.stir_from is not None:
            self.stirred_ns += now - self.stir_from
            self.stir_from = None
            enc.move_drink(DrinkState.READY)
        elif kind == "button":
            self._button(value)
        elif kind == "modal" and value == "resume":
            self.router.close_modal()
        elif kind == "modal":
            self.app.session = None
            self.app.go(MainMenu(self.app))

    def _button(self, action: str) -> None:
        enc, drink = self.encounter, self._drink()
        self.notice = None
        if action == "add" and drink is not DrinkState.ASSEMBLING:
            if drink in (None, DrinkState.SERVED, DrinkState.DISCARDED):
                self.stirred_ns = 0  # a new glass
            enc.move_drink(DrinkState.ASSEMBLING)
        elif action == "serve":
            if drink not in (DrinkState.ASSEMBLING, DrinkState.READY):
                self.notice = "bar.need_ingredient"
                return
            if drink is DrinkState.ASSEMBLING:
                enc.move_drink(DrinkState.READY)
            enc.move_drink(DrinkState.SERVED)
            if enc.phase is Phase.ORDERING:
                enc.move(Phase.VISITING)
        elif action == "close":
            enc.move(Phase.DEPARTING)
            enc.move(Phase.CLOSED)
            self.app.go(Results(self.app))

    def update(self) -> None:
        # ponytail: a timer stands in for the offline guest's reply until T012/T013.
        if self.reply_due and self.app.sim.sim_ns >= self.reply_due[0]:
            if self.encounter.receive_reply(self.reply_due[1]):
                self.guest = self.app.t("bar.placeholder_reply")
                self.encounter.read_reply()
            self.reply_due = None
            self.field.send_blocked = not self.encounter.can_send
        self.field.end_frame()

    def draw(self, screen) -> None:
        app, enc, router = self.app, self.encounter, self.router
        now = app.sim.sim_ns
        minutes, seconds = divmod((now - self.opened_ns) // NS_PER_S, 60)
        subtitle = app.t("bar.shift_time", time=f"{minutes:02d}:{seconds:02d}")
        _draw_frame(app, screen, app.t("bar.title"), subtitle, placeholder=True)
        small = app.small_font
        drink = self._drink() or DrinkState.EMPTY
        state = app.t(
            "bar.state", phase=enc.phase, drink=drink, talk=enc.talk, input=router.context
        )
        text = small.render(state, True, CHAMPAGNE)
        screen.blit(text, text.get_rect(midtop=(CENTER_X, 208)))

        held = router.captured == "stir"
        rect = self.stir_rect
        pygame.draw.rect(screen, HONEY_GARLIC if held else BURNT_COFFEE, rect, border_radius=6)
        pygame.draw.rect(screen, WHISKEY_SOUR, rect, 4 if held else 2, border_radius=6)
        stirred = self.stirred_ns + (now - self.stir_from if self.stir_from is not None else 0)
        lines = [
            (app.font, app.t("bar.stir")),
            (small, app.t("bar.stirred", seconds=f"{stirred / NS_PER_S:.1f}")),
            (small, app.t(self.notice) if self.notice else ""),
        ]
        for i, (font, line) in enumerate(lines):
            text = font.render(line, True, CHAMPAGNE)
            screen.blit(text, text.get_rect(center=(rect.centerx, rect.y + 50 + i * 48)))
        self.buttons.draw(screen, app.font, active=not (router.text_focus or self.paused))

        guest = self.guest and app.t("bar.guest", text=self.guest)
        if enc.talk is Talk.REQUEST_PENDING:
            guest = app.t("bar.ai_pending")
        for i, line in enumerate((self.you and app.t("bar.you", text=self.you), guest)):
            text = small.render(_fit(small, line or "", FIELD_RECT.width), True, CHAMPAGNE)
            screen.blit(text, (FIELD_RECT.x, 455 + i * 30))

        focused = router.text_focus
        pygame.draw.rect(screen, BURNT_COFFEE, FIELD_RECT, border_radius=6)
        border = WHISKEY_SOUR if focused else HONEY_GARLIC
        pygame.draw.rect(screen, border, FIELD_RECT, 4 if focused else 2, border_radius=6)
        if not (self.field.text or self.field.composition):
            hint = small.render(app.t("bar.chat_hint"), True, WHISKEY_SOUR)
            screen.blit(hint, (FIELD_RECT.x + 16, FIELD_RECT.y + 12))
        caret = draw_field(screen, small, self.field, FIELD_RECT, CHAMPAGNE)
        if focused and caret != self._ime_rect:  # keep the IME candidate window at the caret
            pygame.key.set_text_input_rect(caret)
            self._ime_rect = caret

        if self.paused:
            veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            veil.fill((*BALSAMICO, 242))
            screen.blit(veil, (0, 0))
            text = app.title_font.render(app.t("bar.paused"), True, CHAMPAGNE)
            screen.blit(text, text.get_rect(midtop=(CENTER_X, 200)))
            self.pause_buttons.draw(screen, app.font)


def _fit(font, text: str, width: int) -> str:
    """First line of `text` within `width`, with an ellipsis if anything was cut."""
    text = text.replace("\n", " ")
    end = wrap_spans(text, width, lambda s: font.size(s)[0])[0][1]
    return text if end == len(text) else text[:end].rstrip() + "…"


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
