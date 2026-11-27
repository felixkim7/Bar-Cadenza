"""T010: content contracts, cross-file references, orders and preparation events."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from bar_cadenza.domain.catalogue import ContentError, build_catalogue
from bar_cadenza.domain.encounter import (
    Drink,
    DrinkState,
    InvalidOrder,
    InvalidTransition,
    Order,
    PreparationEvent,
)

EXAMPLES = Path(__file__).parents[1] / "content" / "examples"
FILES = ("ingredients.json", "glassware.json", "recipe.json", "character.json")
DAIQUIRI = "recipes[0] (daiquiri_house_example)"


def examples() -> dict[str, dict]:
    return {name: json.loads((EXAMPLES / name).read_text(encoding="utf-8")) for name in FILES}


def build(data: dict[str, dict], allow_examples=True):
    files = {name: json.dumps(d, ensure_ascii=False) for name, d in data.items()}
    return build_catalogue(files, allow_examples=allow_examples)


def problems(data: dict[str, dict]) -> list[str]:
    with pytest.raises(ContentError) as caught:
        build(data)
    return caught.value.problems


def recipe(data):
    return data["recipe.json"]["recipes"][0]


def test_example_content_loads_and_every_reference_resolves():
    c = build(examples())
    daiquiri = c.recipes["daiquiri_house_example"]
    categories = [c.ingredients[i.ingredient_id].category for i in daiquiri.ingredients]
    assert categories == ["spirit", "juice", "syrup"]
    assert c.glasses[daiquiri.glass_id].capacity_ul == 180_000
    assert c.characters["violinist_example"].preferences.dislikes == ("bitter",)


def test_example_only_files_are_refused_as_game_content():
    with pytest.raises(ContentError, match="ingredients.json: example_only"):
        build(examples(), allow_examples=False)


def ingredient(data):
    return data["ingredients.json"]["ingredients"][0]


def character(data):
    return data["character.json"]["characters"][0]


def garnish_lime(d):
    recipe(d).update(garnish_id="lime_juice", steps=[*recipe(d)["steps"], "garnish"])


BAD = {
    "negative quantity": (
        lambda d: recipe(d)["ingredients"][0].update(volume_ul=-5),
        f"recipe.json: {DAIQUIRI}.ingredients[0].volume_ul: Input should be greater than 0",
    ),
    "quantity as text": (
        lambda d: recipe(d)["ingredients"][0].update(volume_ul="60000"),
        f"{DAIQUIRI}.ingredients[0].volume_ul: Input should be a valid integer",
    ),
    "unknown ingredient": (
        lambda d: recipe(d)["ingredients"][0].update(ingredient_id="gin"),
        "recipe.json: recipe 'daiquiri_house_example': unknown ingredient 'gin'",
    ),
    "duplicate ID across files": (
        lambda d: d.update({"more.json": {"schema_version": 1, "ingredients": [ingredient(d)]}}),
        "more.json: duplicate ingredient_id 'white_rum', also in ingredients.json",
    ),
    "unsupported method": (
        lambda d: recipe(d).update(method="blend"),
        f"{DAIQUIRI}.method: Input should be 'shake', 'stir' or 'build'",
    ),
    "unsupported technique": (
        lambda d: recipe(d)["steps"].insert(0, "muddle"),
        f"{DAIQUIRI}.steps[0]: Input should be 'measure', 'add_ice'",
    ),
    "method without its step": (
        lambda d: recipe(d).update(method="stir"),
        "method 'stir' needs mixing steps ['stir'], got ['shake']",
    ),
    "unknown glass": (
        lambda d: recipe(d).update(glass_id="tumbler"),
        "recipe 'daiquiri_house_example': unknown glass 'tumbler'",
    ),
    "overfull glass": (
        lambda d: recipe(d)["ingredients"][0].update(volume_ul=150_000),
        "190 ml does not fit glass 'coupe' (180 ml)",
    ),
    "garnish of the wrong kind": (
        garnish_lime,
        "garnish_id: 'lime_juice' is a juice, not a garnish",
    ),
    "unknown variant base": (
        lambda d: recipe(d).update(variant_of="daiquiri_classic"),
        "variant_of: unknown recipe 'daiquiri_classic'",
    ),
    "ABV above 1": (
        lambda d: ingredient(d).update(abv_fraction=1.5),
        "ingredients[0] (white_rum).abv_fraction: Input should be less than or equal to 1",
    ),
    "flavor outside the vocabulary": (
        lambda d: ingredient(d).update(flavor_tags=["spirit"]),
        "ingredients[0] (white_rum).flavor_tags[0]: Input should be 'sweet'",
    ),
    "unknown field": (
        lambda d: recipe(d).update(required_techniques=["shake"]),
        f"{DAIQUIRI}.required_techniques: Extra inputs are not permitted",
    ),
    "missing Korean name": (
        lambda d: ingredient(d)["name"].pop("ko"),
        "ingredients[0] (white_rum).name.ko: Field required",
    ),
    "future schema": (
        lambda d: d["glassware.json"].update(schema_version=2),
        "glassware.json: schema_version: Input should be 1",
    ),
    "favorite spirit that is not a spirit": (
        lambda d: character(d)["preferences"].update(favorite_spirits=["lime_juice"]),
        "character 'violinist_example': favorite_spirits: 'lime_juice' is a juice, not a spirit",
    ),
    "minor": (
        lambda d: character(d).update(age_years=17),
        "characters[0] (violinist_example).age_years: Input should be greater than or equal to 18",
    ),
}


@pytest.mark.parametrize(("change", "expected"), BAD.values(), ids=BAD.keys())
def test_bad_content_is_reported_by_file_record_and_field(change, expected):
    data = examples()
    change(data)
    found = problems(data)
    assert any(expected in p for p in found), found


def test_invalid_json_names_the_file_and_all_problems_are_reported_together():
    data = examples()
    recipe(data)["ingredients"][0]["ingredient_id"] = "gin"
    files = {name: json.dumps(d, ensure_ascii=False) for name, d in data.items()}
    files["broken.json"] = '{"schema_version": 1,'
    with pytest.raises(ContentError) as caught:
        build_catalogue(files, allow_examples=True)
    found = caught.value.problems
    assert any(p.startswith("broken.json: Invalid JSON") for p in found), found
    assert any("unknown ingredient 'gin'" in p for p in found), found


def order(**fields) -> Order:
    return Order(order_id="o1", encounter_id="shift1-guest1", **fields)


def test_orders_reject_unknown_ids_and_unavailable_recipes():
    c = build(examples())
    syrup = [{"ingredient_id": "simple_syrup", "volume_ul": 7_500}]  # "less sweet"
    named = order(kind="named", recipe_id="daiquiri_house_example", adjustments=syrup)
    named.check(c, available={"daiquiri_house_example"})
    with pytest.raises(InvalidOrder, match="'daiquiri_house_example' is not available"):
        named.check(c, available=set())
    with pytest.raises(InvalidOrder, match="unknown recipe 'mojito'"):
        order(kind="named", recipe_id="mojito").check(c)
    order(kind="recommendation", revealed={"dislikes": ["bitter"]}).check(c)
    with pytest.raises(InvalidOrder, match="unknown ingredient 'gin'"):
        order(kind="recommendation", revealed={"avoid": ["gin"]}).check(c)


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"kind": "named"}, "named order needs recipe_id"),
        ({"kind": "recommendation", "recipe_id": "daiquiri_house_example"}, "needs recipe_id"),
        (
            {"kind": "recommendation", "adjustments": [{"ingredient_id": "x", "volume_ul": 0}]},
            "only a named order has adjustments",
        ),
        (
            {
                "kind": "named",
                "recipe_id": "r",
                "adjustments": [{"ingredient_id": "x", "volume_ul": -1}],
            },
            "greater than or equal to 0",
        ),
    ],
)
def test_order_shape_is_validated(fields, message):
    with pytest.raises(ValidationError, match=message):
        order(**fields)


POUR = {"event_id": "p1", "action": "measure", "start_ms": 1_000, "end_ms": 1_900}
POUR |= {"ingredient_id": "white_rum", "amount_ul": 30_000}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"start_ms": -1}, "greater than or equal to 0"),
        ({"end_ms": 500}, "end_ms is before start_ms"),
        ({"amount_ul": -1}, "greater than or equal to 0"),
        ({"amount_ul": None}, "a measure event needs amount_ul"),
        ({"ingredient_id": None}, "a measure event needs ingredient_id"),
        ({"action": "flambe"}, "Input should be 'measure'"),
        ({"intensity": 1.5}, "less than or equal to 1"),
    ],
)
def test_preparation_events_reject_negative_or_incomplete_observations(change, message):
    with pytest.raises(ValidationError, match=message):
        PreparationEvent(**(POUR | change))


def test_a_drink_appends_observations_and_sums_what_was_measured():
    drink = Drink("shift1-guest1-d1", DrinkState.ASSEMBLING)
    drink.record(PreparationEvent(**POUR))
    drink.record(PreparationEvent(**(POUR | {"event_id": "p2", "amount_ul": 31_500})))
    lime = {"event_id": "p3", "ingredient_id": "lime_juice", "amount_ul": 24_000}
    drink.record(PreparationEvent(**(POUR | lime)))
    drink.record(PreparationEvent(event_id="s1", action="shake", start_ms=5_000, end_ms=17_000))
    assert drink.additions == {"white_rum": 61_500, "lime_juice": 24_000}
    with pytest.raises(ValueError, match="already has event 'p1'"):
        drink.record(PreparationEvent(**POUR))  # a repeated event never counts twice
    drink.state = DrinkState.SERVED
    with pytest.raises(InvalidTransition, match="is served"):
        drink.record(PreparationEvent(**(POUR | {"event_id": "p4"})))


def test_domain_modules_import_without_pygame():
    code = (
        "import importlib, pkgutil, sys, bar_cadenza.domain as d\n"
        "for m in pkgutil.iter_modules(d.__path__):\n"
        "    importlib.import_module(f'bar_cadenza.domain.{m.name}')\n"
        "sys.exit('pygame' in sys.modules)\n"
    )
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0
