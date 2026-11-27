"""Shared fixture: the game App on a headless display (loading art needs a video mode)."""

import os

import pygame
import pytest

from bar_cadenza.app.assets import load_manifest
from bar_cadenza.app.main import LOGICAL_SIZE, MANIFEST, App, load_catalogue, load_strings
from bar_cadenza.app.paths import resource_root


@pytest.fixture
def new_app(monkeypatch, tmp_path):
    """Saves go to a temporary folder, never the player's own."""
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode(LOGICAL_SIZE)
    root = resource_root()
    manifest, catalogue = load_manifest(root / MANIFEST), load_catalogue(root)
    yield App(screen, load_strings(root), root, manifest, catalogue, tmp_path / "saves")
    pygame.display.quit()
