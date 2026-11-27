"""T008: manifest validation, layering, hit-testing, placeholders and pointer mapping.

Images here are tiny solid-colour fixtures written to tmp_path by the test, never assets.
"""

import json
import os

import pygame
import pytest

from bar_cadenza.app import asset_experiment
from bar_cadenza.app.asset_experiment import logical_to_window
from bar_cadenza.app.assets import AssetError, AssetStore, load_manifest
from bar_cadenza.app.paths import resource_root

ROOM, RED, BLUE, GREEN = (90, 90, 90), (200, 0, 0), (0, 0, 200), (0, 200, 0)


@pytest.fixture(autouse=True)
def display(monkeypatch):
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.font.init()
    yield pygame.display.set_mode((1280, 720))
    pygame.display.quit()


def asset(asset_id, file, layer, display, anchor=(0.5, 1.0), hit=None, **extra):
    return {
        "asset_id": asset_id, "file": file, "kind": "prop", "layer": layer,
        "display": display, "anchor": anchor, "hit": hit,
        "source": "test fixture", "license": "test fixture", **extra,
    }  # fmt: skip


def write(tmp_path, assets, scenes, images=()):
    for name, size, color in images:
        surface = pygame.Surface(size)
        surface.fill(color)
        pygame.image.save(surface, tmp_path / name)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"version": 1, "assets": assets, "scenes": scenes}))
    return path


@pytest.fixture
def bar_scene(tmp_path):
    assets = [
        asset("bg_room", "room.png", "room", (1280, 720), (0, 0)),
        asset("character_patron", "patron.png", "customer", (100, 200), hit=(0, 0, 100, 150)),
        asset("bg_counter", "counter.png", "counter", (400, 100)),
        asset("prop_jigger", "jigger.png", "props", (20, 40), hit=(0, 0, 20, 40)),
    ]
    scene = [  # deliberately front-to-back: layers, not list order, decide
        {"asset": "prop_jigger", "at": [640, 370]},
        {"asset": "bg_counter", "at": [640, 450]},
        {"asset": "character_patron", "at": [640, 400]},
        {"asset": "bg_room", "at": [0, 0]},
    ]
    images = [
        ("room.png", (1280, 720), ROOM),
        ("patron.png", (100, 200), RED),
        ("counter.png", (400, 100), BLUE),
        ("jigger.png", (20, 40), GREEN),
    ]
    path = write(tmp_path, assets, {"bar": scene}, images)
    return AssetStore(tmp_path, load_manifest(path), pygame.font.Font(None, 16))


def test_scene_layers_room_patron_counter_prop_back_to_front(bar_scene, display):
    bar_scene.draw(display, "bar")
    # patron 590..690 x 200..400; counter 440..840 x 350..450; jigger 630..650 x 330..370
    expected = {
        (100, 100): ROOM,
        (600, 250): RED,  # patron above the counter
        (600, 380): BLUE,  # counter hides the patron's lower body
        (640, 340): GREEN,  # prop in front of the patron
        (640, 360): GREEN,  # prop in front of the counter
    }
    assert {p: tuple(display.get_at(p))[:3] for p in expected} == expected
    assert bar_scene.diagnostics == []


def test_placement_layer_override_puts_a_prop_behind_the_counter(tmp_path, bar_scene, display):
    manifest = bar_scene.manifest.model_dump()
    manifest["scenes"]["bar"][0]["layer"] = "customer"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    store = AssetStore(tmp_path, load_manifest(path), bar_scene.font)
    store.draw(display, "bar")
    assert tuple(display.get_at((640, 360)))[:3] == BLUE
    # Same layer as the patron now, and listed first, so scene order puts it behind him too.
    assert tuple(display.get_at((640, 340)))[:3] == RED


def test_hit_test_returns_topmost_interactive_item(bar_scene):
    assert bar_scene.hit_test("bar", (640, 340))[0].asset_id == "prop_jigger"
    assert bar_scene.hit_test("bar", (600, 250))[0].asset_id == "character_patron"
    assert bar_scene.hit_test("bar", (600, 380)) is None  # patron hit stops above the counter
    assert bar_scene.hit_test("bar", (100, 100)) is None  # the room is inert


def test_images_load_once_and_are_scaled_to_display_size(tmp_path):
    path = write(
        tmp_path,
        [asset("prop_big", "big.png", "props", (50, 100)), asset("prop_odd", "odd.png", "props", (50, 50))],
        {},
        [("big.png", (100, 200), GREEN), ("odd.png", (100, 40), GREEN)],
    )  # fmt: skip
    store = AssetStore(tmp_path, load_manifest(path), pygame.font.Font(None, 16))
    assert store.image("prop_big") is store.image("prop_big")
    assert store.image("prop_big").get_size() == (50, 100)
    assert store.image("prop_odd").get_size() == (50, 50)
    assert store.diagnostics == ["prop_odd: 100x40 image is stretched to 50x50"]


def test_missing_or_corrupt_optional_image_shows_placeholder_with_one_diagnostic(tmp_path):
    (tmp_path / "broken.png").write_bytes(b"not a png")
    assets = [
        asset("prop_gone", "gone.png", "props", (80, 60)),
        asset("prop_broken", "broken.png", "props", (80, 60)),
    ]
    store = AssetStore(
        tmp_path, load_manifest(write(tmp_path, assets, {})), pygame.font.Font(None, 16)
    )
    for _ in range(2):
        gone, broken = store.image("prop_gone"), store.image("prop_broken")
    assert gone.get_size() == broken.get_size() == (80, 60)
    assert gone.get_at((1, 1)).a == 255  # visible border, not transparent
    assert len(store.diagnostics) == 2
    assert "prop_gone" in store.diagnostics[0] and "gone.png" in store.diagnostics[0]


def test_missing_required_image_is_an_error_naming_id_and_path(tmp_path):
    path = write(tmp_path, [asset("prop_key", "key.png", "props", (10, 10), required=True)], {})
    store = AssetStore(tmp_path, load_manifest(path), pygame.font.Font(None, 16))
    with pytest.raises(AssetError, match=r"prop_key: cannot load .*key\.png"):
        store.image("prop_key")


@pytest.mark.parametrize(
    "change,message",
    [
        (lambda m: m["assets"].append(dict(m["assets"][0])), "duplicate asset_id"),
        (
            lambda m: m["scenes"]["s"].append({"asset": "nope", "at": [0, 0]}),
            "unknown asset 'nope'",
        ),
        (lambda m: m["assets"][0].update(file="../references/art/x.png"), "inside assets/"),
        (lambda m: m["assets"][0].update(file="props\\a.png"), "inside assets/"),
        (lambda m: m["assets"][0].update(file="props/a.gif"), ".png"),
        (lambda m: m["assets"][0].update(hit=[0, 0, 11, 10]), "hit region"),
        (lambda m: m["assets"][0].update(layer="sky"), "assets.0.layer"),
        (lambda m: m["assets"][0].update(asset_id="손님"), "assets.0.asset_id"),
        (lambda m: m["assets"][0].update(license=""), "assets.0.license"),
    ],
)
def test_bad_manifest_is_rejected_with_the_file_and_record(tmp_path, change, message):
    manifest = {"version": 1, "assets": [asset("prop_a", "props/a.png", "props", (10, 10))]}
    manifest["scenes"] = {"s": [{"asset": "prop_a", "at": [0, 0]}]}
    change(manifest)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(AssetError, match="manifest.json") as err:
        load_manifest(path)
    assert message in str(err.value)


def test_shipped_manifest_is_valid_and_never_points_at_references():
    manifest = load_manifest(resource_root() / "assets/manifest.json")
    assert "t008_layer_test" in manifest.scenes
    assert all(not a.file.startswith("references") for a in manifest.assets)


def test_scaled_mode_mapping_fills_one_axis_and_centres_the_other():
    assert logical_to_window((0, 0), (1280, 720)) == (0, 0)
    assert logical_to_window((1280, 720), (2880, 1620)) == (2880, 1620)  # 2.25x, no bars
    # Measured by window capture in T009: 1478x944 shows the canvas at y 56..887,
    # 1818x804 at x 194..1623, and logical x 600 at window x 693.
    assert logical_to_window((0, 0), (1478, 944)) == (0, 56)
    assert logical_to_window((0, 0), (1818, 804)) == (194, 0)
    assert round(logical_to_window((600, 340), (1478, 944))[0]) == 693


def test_layer_test_window_runs_headless_with_placeholders():
    pygame.display.quit()
    assert asset_experiment.run(max_seconds=0.2) == []
    assert not pygame.display.get_init()
