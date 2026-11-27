import json
import os
import shutil

import pygame
import pytest

from bar_cadenza.app import main as app_main
from bar_cadenza.app.main import App, StartupError, load_strings
from bar_cadenza.app.paths import resource_root
from bar_cadenza.domain.session import Session
from bar_cadenza.persistence.saves import load_save
from bar_cadenza.scenes.shell import Bar, LanguageSelect, MainMenu, PreShift, Results

E = pygame.event.Event


@pytest.fixture
def app(new_app):
    return new_app


def click(app: App, action: str) -> None:
    """Press and release the mouse on the scene's button for `action`, then draw a frame."""
    buttons = app.scene.buttons
    pos = buttons.rects()[[a for a, _ in buttons.items].index(action)].center
    app.frame(
        [E(pygame.MOUSEBUTTONDOWN, pos=pos, button=1), E(pygame.MOUSEBUTTONUP, pos=pos, button=1)],
        0,
    )


def key(app: App, *keys: int) -> None:
    app.frame([E(pygame.KEYDOWN, key=k, mod=0) for k in keys], 0)


@pytest.mark.parametrize("lang,title", [("ko", "영업 준비"), ("en", "Before opening")])
def test_full_shell_loop_in_each_language(app, lang, title):
    assert isinstance(app.scene, MainMenu)
    click(app, "new_game")
    assert isinstance(app.scene, LanguageSelect) and app.session is None
    click(app, lang)
    assert isinstance(app.scene, PreShift)
    assert app.session.language == lang and app.t("preshift.title") == title
    click(app, "open")
    assert isinstance(app.scene, Bar)
    app.frame([], 650_000_000)  # time keeps running in the bar
    assert app.sim.sim_ns - app.scene.opened_ns == 650_000_000
    click(app, "close")
    assert isinstance(app.scene, Results) and app.session.shift == 1
    click(app, "next")
    assert isinstance(app.scene, PreShift) and app.session.shift == 2
    click(app, "open")
    click(app, "close")
    click(app, "menu")
    assert isinstance(app.scene, MainMenu) and app.session is None


def test_new_game_requires_an_explicit_language_and_back_returns(app):
    click(app, "new_game")
    click(app, "back")
    assert isinstance(app.scene, MainMenu) and app.session is None


def test_continue_without_save_and_settings_show_notices(app):
    click(app, "continue")
    assert isinstance(app.scene, MainMenu) and app.scene.notice == "menu.no_save"
    click(app, "settings")
    assert app.scene.notice == "menu.settings_unavailable"


def test_keyboard_navigation_and_quit(app):
    key(app, pygame.K_DOWN, pygame.K_DOWN, pygame.K_DOWN, pygame.K_RETURN)  # 4th item: quit
    assert app.running is False


def test_window_close_quits_from_any_scene(app):
    click(app, "new_game")
    app.frame([E(pygame.QUIT)], 0)
    assert app.running is False


def test_click_needs_press_and_release_on_the_same_button(app):
    rects = app.scene.buttons.rects()
    app.frame(
        [
            E(pygame.MOUSEBUTTONDOWN, pos=rects[0].center, button=1),
            E(pygame.MOUSEBUTTONUP, pos=rects[3].center, button=1),
        ],
        0,
    )
    assert isinstance(app.scene, MainMenu) and app.running


def test_missing_or_mismatched_resources_are_reported_by_name(tmp_path):
    with pytest.raises(StartupError, match="NanumGothic-Regular.ttf"):
        load_strings(tmp_path)
    shutil.copytree(resource_root() / "assets/fonts", tmp_path / "assets/fonts")
    shutil.copytree(resource_root() / "content/locales", tmp_path / "content/locales")
    with pytest.raises(StartupError, match="ko.json"):
        (tmp_path / "content/locales/ko.json").unlink()
        load_strings(tmp_path)
    (tmp_path / "content/locales/ko.json").write_text(json.dumps({"only": "x"}), encoding="utf-8")
    with pytest.raises(StartupError, match="keys differ"):
        load_strings(tmp_path)


def test_run_reports_missing_resources_and_exits_1(tmp_path, monkeypatch):
    shown = []
    monkeypatch.setattr(app_main, "resource_root", lambda: tmp_path)
    monkeypatch.setattr(pygame.display, "message_box", lambda *a, **k: shown.append(a))
    assert app_main.run(max_seconds=0.1) == 1
    assert "NanumGothic" in shown[0][1]


def test_run_reports_a_bad_asset_manifest_by_name(tmp_path, monkeypatch):
    shown = []
    for folder in ("assets/fonts", "content/locales"):
        shutil.copytree(resource_root() / folder, tmp_path / folder)
    (tmp_path / "assets/manifest.json").write_text('{"version": 1, "assets": [{}]}')
    monkeypatch.setattr(app_main, "resource_root", lambda: tmp_path)
    monkeypatch.setattr(pygame.display, "message_box", lambda *a, **k: shown.append(a))
    assert app_main.run(max_seconds=0.1) == 1
    assert "manifest.json" in shown[0][1] and "assets.0.asset_id" in shown[0][1]


def test_run_headless_starts_and_exits_cleanly(monkeypatch):
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    assert app_main.run(max_seconds=0.3) == 0
    assert not pygame.display.get_init()


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_shift_boundaries_save_and_continue_restores_language_and_shift(app, lang):
    click(app, "new_game")
    click(app, lang)
    assert app.scene.notice == "save.done" and load_save(app.save_path) == Session(lang, 1)
    click(app, "open")
    click(app, "close")  # the shift is over: a reload starts shift 2
    assert app.scene.notice == "save.done" and load_save(app.save_path) == Session(lang, 2)
    click(app, "menu")
    click(app, "continue")
    assert isinstance(app.scene, PreShift) and app.session == Session(lang, 2)


def test_continue_reports_an_unreadable_save_and_leaves_it(app):
    app.saves.mkdir()
    damaged = app.saves / "save-damaged.sqlite3"
    damaged.write_bytes(b"not a database")
    click(app, "continue")
    assert isinstance(app.scene, MainMenu) and app.scene.notice == "save.unreadable"
    assert damaged.read_bytes() == b"not a database"


def test_a_failed_save_says_so_and_the_game_goes_on(app):
    app.saves.write_text("a file where the saves folder should be")
    click(app, "new_game")
    click(app, "ko")
    assert isinstance(app.scene, PreShift) and app.scene.notice == "save.failed"
    assert app.save_path is None and app.session == Session("ko", 1)


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_save_notices_fit_the_screen(app, lang):
    keys = ["save.done", "save.failed", "save.unreadable", "save.newer", "menu.no_save"]
    assert all(app.small_font.size(app.strings[lang][k])[0] <= 1280 - 32 for k in keys)
