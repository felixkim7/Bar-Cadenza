"""T007: input routing, pointer capture, pause (D022) and continuous time in the bar."""

import pygame
import pytest

from bar_cadenza.app.clock import NS_PER_S
from bar_cadenza.domain.encounter import DrinkState, InputContext, Talk
from bar_cadenza.domain.session import Session
from bar_cadenza.scenes.shell import Bar, MainMenu
from bar_cadenza.ui.buttons import ButtonList
from bar_cadenza.ui.input_router import InputRouter
from bar_cadenza.ui.text_input import TextField

E = pygame.event.Event
FIELD = pygame.Rect(0, 600, 1280, 100)
STIR = pygame.Rect(0, 0, 200, 200)
MS = 1_000_000


def key(k, mod=0):
    return E(pygame.KEYDOWN, key=k, mod=mod)


def text(s):
    return E(pygame.TEXTINPUT, text=s)


def down(pos):
    return E(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)


def up(pos):
    return E(pygame.MOUSEBUTTONUP, pos=pos, button=1)


@pytest.fixture
def router():
    buttons = ButtonList([("serve", "Serve"), ("close", "Close")], 900, 100)
    return InputRouter(TextField(), FIELD, buttons, {"stir": STIR})


def test_text_keys_never_activate_controls_while_typing(router):
    events = [key(pygame.K_SPACE), text(" "), key(pygame.K_s), text("s"), key(pygame.K_DOWN)]
    events += [key(pygame.K_RETURN, pygame.KMOD_SHIFT), key(pygame.K_1), text("1")]
    assert [router.handle(e) for e in events] == [None] * len(events)
    assert router.field.text == " s\n1" and router.context is InputContext.TEXT_ENTRY
    assert router.handle(key(pygame.K_RETURN)) == ("send", "s\n1")  # never ("button", ...)


def test_tab_moves_keyboard_focus_to_buttons_and_back(router):
    router.handle(key(pygame.K_TAB))
    assert router.context is InputContext.GAMEPLAY
    assert router.handle(text("x")) is None and router.field.text == ""
    assert router.handle(key(pygame.K_RETURN)) == ("button", "serve")
    router.handle(key(pygame.K_TAB))
    router.handle(text("x"))
    assert router.field.text == "x"


def test_mouse_buttons_work_while_the_field_keeps_keyboard_focus(router):
    pos = router.buttons.rects()[1].center
    assert router.handle(down(pos)) is None
    assert router.handle(up(pos)) == ("button", "close")
    assert router.text_focus


def test_release_outside_the_control_ends_the_captured_action(router):
    assert router.handle(down(STIR.center)) == ("hold", "stir")
    assert router.context is InputContext.HANDS_BUSY
    outside = router.buttons.rects()[0].center
    assert router.handle(E(pygame.MOUSEMOTION, pos=outside, rel=(1, 1), buttons=(1, 0, 0))) is None
    router.handle(text("hi"))  # typing continues while hands are busy
    assert router.handle(up(outside)) == ("release", "stir")  # not a click on "serve"
    assert router.captured is None and router.field.text == "hi"


@pytest.mark.parametrize("kind", [pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED])
def test_losing_the_window_ends_the_captured_action(router, kind):
    router.handle(down(STIR.center))
    assert router.handle(E(kind)) == ("release", "stir")


def test_modal_takes_keys_but_keeps_ime_commits_in_the_draft(router):
    router.handle(down(STIR.center))
    modal = ButtonList([("resume", "Resume"), ("menu", "Menu")], 640, 300)
    assert router.open_modal(modal) == ("release", "stir")
    assert router.context is InputContext.MODAL
    router.handle(text("한"))
    assert router.handle(key(pygame.K_DOWN)) is None
    assert router.handle(key(pygame.K_RETURN)) == ("modal", "menu")
    assert router.field.text == "한"


def test_leaving_the_field_keeps_the_composition_in_the_draft(router):
    router.handle(E(pygame.TEXTEDITING, text="하", start=1, length=1))
    router.handle(key(pygame.K_TAB))
    assert (router.field.text, router.field.composition) == ("하", "")


# --- the bar scene inside the app loop ---


@pytest.fixture
def bar(new_app):
    app = new_app
    app.session = Session(language="ko")
    app.go(Bar(app))
    return app


def click(app, action):
    pos = app.scene.buttons.rects()[[a for a, _ in app.scene.buttons.items].index(action)].center
    app.frame([down(pos), up(pos)], 0)


def test_time_runs_while_typing_stirring_and_waiting_and_talk_spans_mixing_and_serving(bar):
    scene = bar.scene
    click(bar, "add")
    assert scene.notice == "bar.added"  # the click shows a result even with F3 off
    bar.frame([down(scene.stir_rect.center)], 0)
    t0 = bar.sim.sim_ns
    for ch in "잔":
        bar.frame([text(ch)], 100 * MS)
    bar.frame([key(pygame.K_RETURN)], 100 * MS)  # send while stirring
    assert scene.encounter.talk is Talk.REQUEST_PENDING
    assert scene.encounter.drinks[-1].state is DrinkState.MIXING
    for _ in range(16):
        bar.frame([], 100 * MS)  # the placeholder reply arrives while still stirring
    assert scene.guest and scene.encounter.talk is Talk.AWAITING_PLAYER
    bar.frame([up((1200, 20))], 0)  # release far outside the tool
    assert bar.sim.sim_ns - t0 == 1_800 * MS
    assert scene.stirred_ns == 1_800 * MS and scene.router.captured is None
    click(bar, "serve")
    assert scene.encounter.drinks[-1].state is DrinkState.SERVED and scene.notice == "bar.served"
    bar.frame([text("또"), key(pygame.K_RETURN)], 0)  # talk continues after serving
    assert scene.encounter.talk is Talk.REQUEST_PENDING and scene.you == "또"


def test_draft_is_kept_while_a_reply_is_pending(bar):
    bar.frame([text("a"), key(pygame.K_RETURN), text("b"), key(pygame.K_RETURN)], 0)
    assert bar.scene.encounter.revision == 1 and bar.scene.field.text == "b"
    bar.frame([], NS_PER_S)  # frames are capped at 1 s each
    bar.frame([], NS_PER_S)
    bar.frame([key(pygame.K_RETURN)], 0)
    assert bar.scene.encounter.revision == 2 and bar.scene.field.text == ""


@pytest.mark.parametrize("kind", [pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED])
def test_unseen_window_pauses_time_until_resume(bar, kind):
    scene = bar.scene
    click(bar, "add")
    bar.frame([down(scene.stir_rect.center)], 0)
    bar.frame([E(kind)], 5 * NS_PER_S)
    t0 = bar.sim.sim_ns
    bar.frame([], 5 * NS_PER_S)
    assert scene.paused and bar.sim.sim_ns == t0 == 0
    assert scene.router.captured is None and scene.stir_from is None  # the stir ended
    bar.frame([key(pygame.K_RETURN)], 0)  # "Resume" has focus
    bar.frame([], 300 * MS)
    assert not scene.paused and bar.sim.sim_ns == 300 * MS


def test_escape_pauses_and_resumes_and_pause_menu_can_leave(bar):
    bar.frame([text("draft"), key(pygame.K_ESCAPE)], 0)
    assert bar.scene.paused
    bar.frame([key(pygame.K_ESCAPE)], 0)
    assert not bar.scene.paused and bar.scene.field.text == "draft"
    bar.frame([key(pygame.K_ESCAPE), key(pygame.K_DOWN), key(pygame.K_RETURN)], 0)
    assert isinstance(bar.scene, MainMenu) and bar.session is None


def test_window_drag_stall_adds_no_time(bar):
    bar.frame([E(pygame.WINDOWMOVED, x=10, y=10)], 4 * NS_PER_S)
    assert bar.sim.sim_ns == 0
    bar.frame([], 16 * MS)
    assert bar.sim.sim_ns == 16 * MS


def test_stirring_needs_an_ingredient_and_close_ends_the_encounter(bar):
    scene = bar.scene
    bar.frame([down(scene.stir_rect.center), up(scene.stir_rect.center)], 0)
    assert scene.notice == "bar.need_ingredient" and not scene.encounter.drinks
    encounter = scene.encounter
    click(bar, "close")
    assert encounter.closed and encounter.talk is Talk.CLOSED
