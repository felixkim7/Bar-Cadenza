"""Application shell scenes (T006). Pre-shift and results are labelled placeholders; the bar
is composed from the asset manifest with dialogue and recipe panels (T009).

A scene has handle(event) and draw(screen); it switches scenes with app.go(...).
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from bar_cadenza.app.clock import NS_PER_S
from bar_cadenza.domain.encounter import DrinkState, Encounter, Phase, Talk
from bar_cadenza.ui.buttons import ButtonList
from bar_cadenza.ui.input_router import InputRouter
from bar_cadenza.ui.palette import BALSAMICO, BURNT_COFFEE, CHAMPAGNE, HONEY_GARLIC, WHISKEY_SOUR
from bar_cadenza.ui.text_input import TextField, draw_field, wrap_spans

if TYPE_CHECKING:
    from bar_cadenza.app.main import App

CENTER_X = 640
REPLY_DELAY_NS = 3 * NS_PER_S // 2
PAUSE_EVENTS = {pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED}  # D022: unseen → paused

# Bar layout (T009, UI_DESIGN baseline): guest in the middle, tools on the work surface,
# conversation on the left, recipe and actions on the right, typing over the cabinets.
SCENE = "bar"  # assets/manifest.json
SHAKER = "prop_shaker_idle"
TOOLS = {  # interactable props and their name keys; only these get hover feedback
    "prop_bottle_gin_idle": "bar.prop_gin",
    "prop_jigger_idle": "bar.prop_jigger",
    SHAKER: "bar.prop_shaker",
}
PAD = 14
TRANSCRIPT_RECT = pygame.Rect(16, 44, 340, 548)
RECIPE_RECT = pygame.Rect(924, 44, 340, 352)
FIELD_RECT = pygame.Rect(16, 604, 1248, 108)
ROOM_DIM = (200, 200, 200)  # multiply the room by ~78% so the guest and tools read first
SHAKE_STEP_NS = 60_000_000  # a held shaker hops every 60 ms (code-drawn active state)


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


def _draw_notice(app: App, screen, key: str | None) -> None:
    if key:
        text = app.small_font.render(app.t(key), True, CHAMPAGNE)
        screen.blit(text, text.get_rect(midtop=(CENTER_X, 560)))


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
            if (notice := self.app.continue_game()) is None:
                self.app.go(PreShift(self.app))
            self.notice = notice
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
            self.app.go(PreShift(self.app, notice=self.app.new_game(action)))
        elif action == "back":
            self.app.go(MainMenu(self.app))

    def draw(self, screen) -> None:
        s = self.app.strings
        _draw_frame(self.app, screen, s["ko"]["language.choose"], s["en"]["language.choose"])
        self.buttons.draw(screen, self.app.font)


class PreShift:
    def __init__(self, app: App, notice: str | None = None) -> None:
        self.app, self.notice = app, notice
        self.buttons = ButtonList([("open", app.t("preshift.open"))], CENTER_X, 330)

    def handle(self, event) -> None:
        if self.buttons.handle(event) == "open":
            self.app.go(Bar(self.app))

    def draw(self, screen) -> None:
        app = self.app
        subtitle = app.t("shift.number", n=app.session.shift)
        _draw_frame(app, screen, app.t("preshift.title"), subtitle, placeholder=True)
        self.buttons.draw(screen, app.font)
        _draw_notice(app, screen, self.notice)


class Bar:
    """The bar, composed from the manifest's "bar" scene (T009) around the T007 test bench:
    one guest, chat, a hold-the-shaker mixing action and serving, each on its own state
    track, plus the D022 pause menu. F3 shows the state readout."""

    def __init__(self, app: App) -> None:
        self.app = app
        t = app.t
        self.opened_ns = app.sim.sim_ns
        self.encounter = Encounter(f"shift{app.session.shift}-guest1")
        self.encounter.move(Phase.ORDERING)
        self.field = TextField()
        placed = app.assets.placed(SCENE)
        self.stir_rect = next(
            pygame.Rect(a.hit).move(r.topleft) for a, r in placed if a.asset_id == SHAKER
        )
        items = [("add", t("bar.add")), ("serve", t("bar.serve")), ("close", t("bar.close"))]
        top = RECIPE_RECT.bottom + 16
        self.buttons = ButtonList(items, RECIPE_RECT.centerx, top, RECIPE_RECT.width, 48, 10)
        pause_items = [("resume", t("bar.resume")), ("menu", t("results.main_menu"))]
        self.pause_buttons = ButtonList(pause_items, CENTER_X, 300)
        self.router = InputRouter(self.field, FIELD_RECT, self.buttons, {"stir": self.stir_rect})
        self.stirred_ns = 0
        self.stir_from: int | None = None
        self.notice: str | None = None
        self.you = self.guest = ""
        self.log: list[tuple[str, str]] = []  # (speaker key, text), oldest first
        self.reply_due: tuple[int, int] | None = None  # (sim_ns, revision)
        self.show_state = False
        self._ime_rect = None
        self._transcript_bg = pygame.Surface(TRANSCRIPT_RECT.size, pygame.SRCALPHA)
        pygame.draw.rect(
            self._transcript_bg,
            (*BURNT_COFFEE, 225),
            ((0, 0), TRANSCRIPT_RECT.size),
            border_radius=8,
        )

    @property
    def paused(self) -> bool:
        return self.router.modal is not None

    def handle(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.show_state = not self.show_state
            return
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
            self.log.append(("bar.you", value))
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
        if action == "add":
            if drink in (None, DrinkState.SERVED, DrinkState.DISCARDED):
                self.stirred_ns = 0  # a new glass
            if drink is not DrinkState.ASSEMBLING:
                enc.move_drink(DrinkState.ASSEMBLING)
            self.notice = "bar.added"
        elif action == "serve":
            if drink not in (DrinkState.ASSEMBLING, DrinkState.READY):
                self.notice = "bar.need_ingredient"
                return
            if drink is DrinkState.ASSEMBLING:
                enc.move_drink(DrinkState.READY)
            enc.move_drink(DrinkState.SERVED)
            self.notice = "bar.served"
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
                self.log.append(("bar.guest", self.guest))
                self.encounter.read_reply()
            self.reply_due = None
            self.field.send_blocked = not self.encounter.can_send
        self.field.end_frame()

    def draw(self, screen) -> None:
        app, router = self.app, self.router
        now, small = app.sim.sim_ns, app.small_font
        held = router.captured == "stir"
        for asset, rect in app.assets.placed(SCENE):
            if held and asset.asset_id == SHAKER and now // SHAKE_STEP_NS % 2:
                rect = rect.move(0, -5)
            screen.blit(app.assets.image(asset.asset_id), rect)
            if asset.layer == "room":
                screen.fill(ROOM_DIM, special_flags=pygame.BLEND_RGB_MULT)
        self._draw_transcript(screen)
        self._draw_recipe(screen)
        self.buttons.draw(screen, small, active=not (router.text_focus or self.paused))
        self._draw_tool_feedback(screen, held, now)  # labels above the panels
        self._draw_status(screen, now)

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

    def _draw_tool_feedback(self, screen, held: bool, now: int) -> None:
        """Outline and name the tool under the pointer (or the one being held)."""
        app = self.app
        hit = app.assets.hit_test(SCENE, pygame.mouse.get_pos())
        target = (SHAKER, self.stir_rect) if held else (hit[0].asset_id, hit[1]) if hit else None
        if target is None or target[0] not in TOOLS:
            return
        asset_id, rect = target
        pygame.draw.rect(screen, WHISKEY_SOUR, rect.inflate(8, 8), 4 if held else 2, 6)
        label = app.t(TOOLS[asset_id])
        if asset_id == SHAKER:
            stirred = self.stirred_ns + (now - self.stir_from if self.stir_from is not None else 0)
            seconds = f"{stirred / NS_PER_S:.1f}"
            label = f"{label} · {app.t('bar.stir')} · {app.t('bar.stirred', seconds=seconds)}"
        _tag(screen, app.small_font, label, (rect.centerx, rect.top - 8))

    def _draw_status(self, screen, now: int) -> None:
        app, enc = self.app, self.encounter
        minutes, seconds = divmod((now - self.opened_ns) // NS_PER_S, 60)
        lines = [app.t("bar.shift_time", time=f"{minutes:02d}:{seconds:02d}")]
        if self.show_state:
            drink = self._drink() or DrinkState.EMPTY
            context = self.router.context
            lines.append(
                app.t("bar.state", phase=enc.phase, drink=drink, talk=enc.talk, input=context)
            )
        if self.notice:
            lines.append(app.t(self.notice))
        for i, line in enumerate(lines):
            _tag(screen, app.small_font, line, (CENTER_X, 38 + i * 36))

    def _draw_transcript(self, screen) -> None:
        """Newest lines at the bottom; older ones scroll off the top."""
        app, small, rect = self.app, self.app.small_font, TRANSCRIPT_RECT
        screen.blit(self._transcript_bg, rect)
        pygame.draw.rect(screen, HONEY_GARLIC, rect, 2, border_radius=8)
        title = app.font.render(app.t("bar.transcript"), True, WHISKEY_SOUR)
        screen.blit(title, (rect.x + PAD, rect.y + PAD))
        entries = [
            (app.t(key, text=text), WHISKEY_SOUR if key == "bar.you" else CHAMPAGNE)
            for key, text in self.log
        ]
        if self.encounter.talk is Talk.REQUEST_PENDING:
            entries.append((app.t("bar.ai_pending"), CHAMPAGNE))
        width = rect.width - 2 * PAD
        rows = [(row, color) for text, color in entries for row in _wrapped(small, text, width)]
        top, y = rect.y + PAD + title.get_height() + 8, rect.bottom - PAD - small.get_linesize()
        for row, color in reversed(rows):
            if y < top:
                break
            screen.blit(small.render(row, True, color), (rect.x + PAD, y))
            y -= small.get_linesize()

    def _draw_recipe(self, screen) -> None:
        """Recipe card on Champagne paper (palette role). The sample text is a layout fixture
        until the recipe book (T018)."""
        rect = RECIPE_RECT
        pygame.draw.rect(screen, CHAMPAGNE, rect, border_radius=8)
        pygame.draw.rect(screen, HONEY_GARLIC, rect, 2, border_radius=8)
        y = rect.y + PAD
        for font, color, text in recipe_lines(self.app):
            for row in _wrapped(font, text, rect.width - 2 * PAD):
                screen.blit(font.render(row, True, color), (rect.x + PAD, y))
                y += font.get_linesize()


def recipe_lines(app: App) -> list[tuple[pygame.font.Font, tuple[int, int, int], str]]:
    t = app.t
    lines = [(app.small_font, HONEY_GARLIC, t("bar.recipe_book"))]
    lines.append((app.font, BALSAMICO, t("bar.recipe_sample_title")))
    lines += [(app.small_font, BALSAMICO, line) for line in t("bar.recipe_sample").split("\n")]
    return lines


@lru_cache(maxsize=1024)
def _wrapped(font: pygame.font.Font, text: str, width: int) -> tuple[str, ...]:
    """Wrapped rows of `text`, cached so a long transcript is not re-measured every frame."""
    return tuple(text[a:b] for a, b in wrap_spans(text, width, lambda s: font.size(s)[0]))


def _tag(screen, font, text: str, midbottom: tuple[int, int]) -> None:
    """A small label on a dark plate, kept on screen."""
    label = font.render(text, True, CHAMPAGNE)
    box = label.get_rect(midbottom=midbottom).inflate(16, 8).clamp(screen.get_rect())
    pygame.draw.rect(screen, BURNT_COFFEE, box, border_radius=6)
    pygame.draw.rect(screen, HONEY_GARLIC, box, 1, border_radius=6)
    screen.blit(label, label.get_rect(center=box.center))


class Results:
    def __init__(self, app: App) -> None:
        self.app = app
        items = [("next", app.t("results.next_shift")), ("menu", app.t("results.main_menu"))]
        self.buttons = ButtonList(items, CENTER_X, 330)
        # The shift is over, so a reload starts the next one, even after "Main menu".
        self.notice = app.save_game(replace(app.session, shift=app.session.shift + 1))

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
        _draw_notice(app, screen, self.notice)
