"""Authored content contracts (T010, DATA_MODELS): ingredients, glasses, recipes, characters.

Content is JSON and read-only at runtime. Every file has a schema_version and any of the four
record lists, so a catalogue can be split across files. build_catalogue() validates each file
strictly (no unknown fields, no silent type coercion), then the rules that span files: unique
IDs and references that resolve. Problems are reported together, each naming the file, record
and field; a file that fails its own checks is left out of the cross-file checks until fixed.
No pygame and no file I/O here: callers pass the text.
"""

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

ID = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]  # stable ASCII snake_case
Text = Annotated[str, Field(min_length=1)]
Microliters = Annotated[int, Field(gt=0)]  # 1 ml = 1,000 µl

Category = Literal[
    "spirit", "liqueur", "wine", "bitters", "juice", "syrup", "mixer", "dairy", "egg", "garnish"
]
# Controlled vocabulary, so a guest's dislikes and a recipe's profile can be compared (T019).
Flavor = Literal[
    "sweet", "sour", "bitter", "dry", "citrus", "fruity", "herbal", "floral", "spicy", "smoky",
    "creamy", "nutty", "strong", "light", "refreshing",
]  # fmt: skip
Ice = Literal["none", "mixing_only", "cubes", "crushed"]


class Method(StrEnum):
    """Methods the game implements. Anything else is rejected, never converted (GAME_DESIGN)."""

    SHAKE = "shake"
    STIR = "stir"
    BUILD = "build"


class Technique(StrEnum):
    MEASURE = "measure"
    ADD_ICE = "add_ice"
    SHAKE = "shake"
    STIR = "stir"
    STRAIN = "strain"
    GARNISH = "garnish"
    SERVE = "serve"


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Localized(Record):
    en: Text
    ko: Text


class IngredientDefinition(Record):
    ingredient_id: ID
    name: Localized
    category: Category
    abv_fraction: float = Field(ge=0, le=1)
    flavor_tags: tuple[Flavor, ...] = ()
    asset_id: ID | None = None
    provenance: Text


class GlassDefinition(Record):
    glass_id: ID
    name: Localized
    capacity_ul: Microliters
    asset_id: ID | None = None
    provenance: Text


class RecipeIngredient(Record):
    ingredient_id: ID
    volume_ul: Microliters


class RecipeDefinition(Record):
    recipe_id: ID
    name: Localized
    ingredients: tuple[RecipeIngredient, ...] = Field(min_length=1)
    method: Method
    steps: tuple[Technique, ...] = Field(min_length=1)
    glass_id: ID
    ice: Ice
    garnish_id: ID | None = None
    flavor_tags: tuple[Flavor, ...] = ()
    unlock_level: int = Field(default=1, ge=1)  # thresholds are illustrative until O009
    variant_of: ID | None = None  # the house recipe this varies; None = it is the house version
    provenance: Text

    @model_validator(mode="after")
    def _consistent(self) -> "RecipeDefinition":
        ids = [item.ingredient_id for item in self.ingredients]
        if len(set(ids)) != len(ids):
            raise ValueError("lists an ingredient twice; combine the quantities")
        mixing = sorted(str(t) for t in {Technique.SHAKE, Technique.STIR} & set(self.steps))
        expected = [] if self.method is Method.BUILD else [str(self.method)]
        if mixing != expected:
            raise ValueError(f"method '{self.method}' needs mixing steps {expected}, got {mixing}")
        if (self.garnish_id is None) == (Technique.GARNISH in self.steps):
            raise ValueError("a garnish_id and a garnish step go together")
        return self


class Preferences(Record):
    """What a guest likes. On an Order it holds only what the player has learned (SCORING)."""

    likes: tuple[Flavor, ...] = ()
    dislikes: tuple[Flavor, ...] = ()
    favorite_spirits: tuple[ID, ...] = ()
    avoid: tuple[ID, ...] = ()  # ingredients the guest will not drink


class CharacterProfile(Record):
    character_id: ID
    name: Localized
    age_years: int = Field(ge=18)  # adults only (D009)
    appearance: Text
    personality: tuple[Text, ...] = Field(min_length=1)
    voice: Text
    stable_facts: tuple[Text, ...] = ()
    private_facts: tuple[Text, ...] = ()  # never shown in the journal or used to penalize
    initial_revealed_facts: tuple[Text, ...] = ()
    preferences: Preferences = Preferences()
    opening: Localized
    portrait_id: ID
    provenance: Text


class ContentFile(Record):
    schema_version: Literal[1]
    example_only: bool = False  # content/examples: never part of the game's catalogue
    ingredients: tuple[IngredientDefinition, ...] = ()
    glasses: tuple[GlassDefinition, ...] = ()
    recipes: tuple[RecipeDefinition, ...] = ()
    characters: tuple[CharacterProfile, ...] = ()


ID_FIELDS = {
    "ingredients": "ingredient_id",
    "glasses": "glass_id",
    "recipes": "recipe_id",
    "characters": "character_id",
}


@dataclass(frozen=True)
class Catalogue:
    ingredients: dict[str, IngredientDefinition]
    glasses: dict[str, GlassDefinition]
    recipes: dict[str, RecipeDefinition]
    characters: dict[str, CharacterProfile]


class ContentError(ValueError):
    """Bad authored content. `problems` lists every one, each naming file, record and field."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def build_catalogue(files: Mapping[str, str | bytes], *, allow_examples=False) -> Catalogue:
    """Validate and merge content files; `files` maps a file name to its JSON text."""
    problems: list[str] = []
    found: dict[str, dict[str, tuple[str, Any]]] = {kind: {} for kind in ID_FIELDS}
    for name, text in files.items():
        try:
            content = ContentFile.model_validate_json(text, strict=True)
        except ValidationError as exc:
            raw = _loads(text)
            problems += [f"{name}: {_where(raw, e['loc'])}{e['msg']}" for e in exc.errors()]
            continue
        if content.example_only and not allow_examples:
            problems.append(f"{name}: example_only content is not part of the catalogue")
            continue
        for kind, key in ID_FIELDS.items():
            for record in getattr(content, kind):
                rid = getattr(record, key)
                if rid in found[kind]:
                    first = found[kind][rid][0]
                    problems.append(f"{name}: duplicate {key} {rid!r}, also in {first}")
                else:
                    found[kind][rid] = (name, record)
    catalogue = Catalogue(**{k: {i: rec for i, (_, rec) in v.items()} for k, v in found.items()})
    problems += [f"{found[kind][rid][0]}: {msg}" for kind, rid, msg in _references(catalogue)]
    if problems:
        raise ContentError(problems)
    return catalogue


def _references(c: Catalogue) -> Iterator[tuple[str, str, str]]:
    """(kind, record id, message) for each reference that does not resolve."""

    def check(iid: str, category: str | None = None) -> str | None:
        item = c.ingredients.get(iid)
        if item is None:
            return f"unknown ingredient {iid!r}"
        if category and item.category != category:
            return f"{iid!r} is a {item.category}, not a {category}"
        return None

    for rid, recipe in c.recipes.items():
        where = f"recipe {rid!r}: "
        for item in recipe.ingredients:
            if problem := check(item.ingredient_id):
                yield "recipes", rid, where + problem
            elif c.ingredients[item.ingredient_id].category == "garnish":
                yield (
                    "recipes",
                    rid,
                    where + f"garnish {item.ingredient_id!r} belongs in garnish_id",
                )
        if recipe.garnish_id and (problem := check(recipe.garnish_id, "garnish")):
            yield "recipes", rid, where + f"garnish_id: {problem}"
        if (glass := c.glasses.get(recipe.glass_id)) is None:
            yield "recipes", rid, where + f"unknown glass {recipe.glass_id!r}"
        elif (total := sum(i.volume_ul for i in recipe.ingredients)) > glass.capacity_ul:
            yield (
                "recipes",
                rid,
                (
                    where + f"{total / 1000:g} ml does not fit glass {glass.glass_id!r} "
                    f"({glass.capacity_ul / 1000:g} ml)"
                ),
            )
        if recipe.variant_of is not None:
            if (base := c.recipes.get(recipe.variant_of)) is None:
                yield "recipes", rid, where + f"variant_of: unknown recipe {recipe.variant_of!r}"
            elif base.variant_of is not None:
                yield (
                    "recipes",
                    rid,
                    (
                        where + f"variant_of: {recipe.variant_of!r} is itself a variant; "
                        "point at the house recipe"
                    ),
                )
    for cid, character in c.characters.items():
        where, prefs = f"character {cid!r}: ", character.preferences
        for iid in prefs.favorite_spirits:
            if problem := check(iid, "spirit"):
                yield "characters", cid, where + f"favorite_spirits: {problem}"
        for iid in prefs.avoid:
            if problem := check(iid):
                yield "characters", cid, where + f"avoid: {problem}"


def _loads(text: str | bytes) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        return None


def _where(raw: Any, loc: tuple) -> str:
    """'recipes[0] (daiquiri).ingredients[1].volume_ul: ' from a pydantic error location."""
    if not loc:
        return ""
    path = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in loc).lstrip(".")
    if len(loc) > 1 and loc[0] in ID_FIELDS and isinstance(loc[1], int):
        try:
            rid = raw[loc[0]][loc[1]][ID_FIELDS[loc[0]]]
        except LookupError, TypeError:
            rid = None
        if isinstance(rid, str):
            head = f"{loc[0]}[{loc[1]}]"
            path = f"{head} ({rid}){path[len(head) :]}"
    return path + ": "
