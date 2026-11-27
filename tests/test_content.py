"""T012: the representative catalogue and offline guest load and resolve; new data files need
no code or screen changes. Counts here are fixtures, not final limits (D014, D015)."""

import json
import shutil

import pygame
import pytest

from bar_cadenza.app import main as app_main
from bar_cadenza.app.assets import load_manifest
from bar_cadenza.app.main import MANIFEST, StartupError, load_catalogue
from bar_cadenza.app.paths import resource_root
from bar_cadenza.domain.catalogue import Method
from bar_cadenza.domain.encounter import InvalidOrder, Order

ROOT = resource_root()
GUEST = "margot_hale"


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue(ROOT)


def available(catalogue, level: int) -> set[str]:
    """Recipes unlocked at `level` (illustrative levels, O009); stock arrives with T031."""
    return {rid for rid, r in catalogue.recipes.items() if r.unlock_level <= level}


def order(**fields) -> Order:
    return Order(order_id="o1", encounter_id=f"shift1-{GUEST}", **fields)


def test_the_fixture_set_covers_every_method_glass_and_a_house_variant(catalogue):
    recipes = catalogue.recipes.values()
    assert {r.method for r in recipes} == set(Method)
    assert {r.glass_id for r in recipes} == set(catalogue.glasses)
    assert {r.ice for r in recipes} >= {"mixing_only", "cubes"}
    variants = [r for r in recipes if r.variant_of]
    assert variants and all(catalogue.recipes[v.variant_of].variant_of is None for v in variants)
    assert all(r.provenance and "O004" in r.provenance for r in recipes)


def test_the_offline_guest_uses_existing_art_and_states_her_tastes(catalogue):
    guest = catalogue.characters[GUEST]
    assert guest.portrait_id in load_manifest(ROOT / MANIFEST).by_id
    assert guest.preferences.dislikes and guest.opening.ko and guest.opening.en


def test_a_named_order_resolves_and_respects_what_is_unlocked(catalogue):
    less_sweet = [{"ingredient_id": "honey_syrup", "volume_ul": 15_000}]
    order(kind="named", recipe_id="bees_knees", adjustments=less_sweet).check(
        catalogue, available(catalogue, 1)
    )
    negroni = order(kind="named", recipe_id="negroni")
    with pytest.raises(InvalidOrder, match="'negroni' is not available"):
        negroni.check(catalogue, available(catalogue, 1))
    negroni.check(catalogue, available(catalogue, 3))


def test_a_recommendation_for_the_guest_has_more_than_one_fitting_answer(catalogue):
    """Her opening line reveals her tastes; several unlocked drinks avoid what she dislikes."""
    wish = order(kind="recommendation", revealed=catalogue.characters[GUEST].preferences)
    wish.check(catalogue, available(catalogue, 1))
    dislikes, avoid = set(wish.revealed.dislikes), set(wish.revealed.avoid)
    fitting = {
        rid
        for rid, r in catalogue.recipes.items()
        if not dislikes & set(r.flavor_tags)
        and not avoid & {i.ingredient_id for i in r.ingredients}
    }
    assert len(fitting & available(catalogue, 1)) >= 2
    assert "negroni" not in fitting  # the bitter one


def copy_content(tmp_path):
    shutil.copytree(ROOT / "content", tmp_path / "content")


def test_a_new_content_file_is_picked_up_without_code_changes(tmp_path):
    copy_content(tmp_path)
    gimlet = {
        "recipe_id": "gimlet",
        "name": {"en": "Gimlet", "ko": "김렛"},
        "ingredients": [
            {"ingredient_id": "gin", "volume_ul": 60000},
            {"ingredient_id": "lime_juice", "volume_ul": 22500},
            {"ingredient_id": "simple_syrup", "volume_ul": 15000},
        ],
        "method": "shake",
        "steps": ["measure", "add_ice", "shake", "strain", "serve"],
        "glass_id": "coupe",
        "ice": "mixing_only",
        "provenance": "Test fixture.",
    }
    extra = tmp_path / "content/catalog/more_recipes.json"
    extra.write_text(json.dumps({"schema_version": 1, "recipes": [gimlet]}), encoding="utf-8")
    assert "gimlet" in load_catalogue(tmp_path).recipes


def test_bad_content_stops_startup_with_a_dialog_naming_the_file(tmp_path, monkeypatch):
    copy_content(tmp_path)  # includes the locales run() needs
    shutil.copytree(ROOT / "assets/fonts", tmp_path / "assets/fonts")
    shutil.copy(ROOT / MANIFEST, tmp_path / MANIFEST)
    broken = tmp_path / "content/catalog/broken.json"
    broken.write_text('{"schema_version": 1, "recipes": [{"recipe_id": "x"}]}', encoding="utf-8")
    with pytest.raises(StartupError, match=r"broken\.json: recipes\[0\] \(x\)\.name: Field"):
        load_catalogue(tmp_path)
    shown = []
    monkeypatch.setattr(app_main, "resource_root", lambda: tmp_path)
    monkeypatch.setattr(pygame.display, "message_box", lambda *a, **k: shown.append(a))
    assert app_main.run(max_seconds=0.1) == 1
    assert "content/catalog/broken.json" in shown[0][1]


def test_missing_content_stops_startup(tmp_path):
    with pytest.raises(StartupError, match="No recipes or guests"):
        load_catalogue(tmp_path)
