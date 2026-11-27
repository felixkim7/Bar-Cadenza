"""Shared fixture: the game App on a headless display (loading art needs a video mode)."""

import os

import pygame
import pytest

from bar_cadenza.app.assets import load_manifest
from bar_cadenza.app.main import LOGICAL_SIZE, MANIFEST, App, load_strings
from bar_cadenza.app.paths import resource_root


@pytest.fixture
def new_app(monkeypatch):
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode(LOGICAL_SIZE)
    root = resource_root()
    yield App(screen, load_strings(root), root, load_manifest(root / MANIFEST))
    pygame.display.quit()
