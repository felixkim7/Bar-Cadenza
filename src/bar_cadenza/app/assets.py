"""Asset manifest, cached image loading and layered scene composition (T008).

assets/manifest.json gives every runtime image a stable ID, a display size in logical
pixels (1280×720 layout, B007), an anchor, a draw layer, an optional hit region and its
provenance. A scene places asset IDs at logical points. Each image is loaded and scaled once.
A missing or unreadable optional image becomes a labelled placeholder plus one diagnostic; a
missing required image raises AssetError naming the ID and path. Files must live under
assets/, so the supplied reference images in references/ can never be loaded as sprites.
"""

import logging
from collections import Counter
from functools import cached_property
from pathlib import Path, PurePosixPath
from typing import Literal

import pygame
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from bar_cadenza.ui.palette import BURNT_COFFEE, CHAMPAGNE, HONEY_GARLIC

log = logging.getLogger(__name__)

# Back to front (ASSET_SPEC "Layers"). Within a layer, scene order decides.
LAYERS = ("room", "midground", "customer", "counter", "props", "effects", "ui")
Layer = Literal["room", "midground", "customer", "counter", "props", "effects", "ui"]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class AssetError(Exception):
    """Bad manifest or missing required image; the message names the record and path."""


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Asset(_Record):
    asset_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")  # no localized words in IDs
    file: str  # relative to assets/, forward slashes
    kind: Literal["background", "character", "prop", "effect", "ui"]
    layer: Layer
    display: tuple[int, int]  # logical px; the image is scaled to this once
    anchor: tuple[float, float] = (0.5, 1.0)  # fraction of display placed on the scene point
    hit: tuple[int, int, int, int] | None = None  # x, y, w, h inside display; None = inert
    state: str | None = None  # expression / interaction state
    required: bool = False
    source: str = Field(min_length=1)
    license: str = Field(min_length=1)
    approval: Literal["pending", "approved", "rejected"] = "pending"

    @field_validator("file")
    @classmethod
    def _inside_assets(cls, value: str) -> str:
        path = PurePosixPath(value)
        if "\\" in value or path.is_absolute() or ".." in path.parts or ":" in value:
            raise ValueError("must be a relative path inside assets/ using forward slashes")
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError(f"must be one of {sorted(IMAGE_SUFFIXES)}")
        return value

    @model_validator(mode="after")
    def _geometry(self) -> "Asset":
        w, h = self.display
        if w <= 0 or h <= 0:
            raise ValueError("display size must be positive")
        if not all(0 <= a <= 1 for a in self.anchor):
            raise ValueError("anchor fractions must be within 0..1")
        if self.hit and not pygame.Rect(0, 0, w, h).contains(self.hit):
            raise ValueError("hit region must lie inside the display size")
        return self


class Placement(_Record):
    asset: str
    at: tuple[int, int]  # logical px where the asset's anchor lands
    layer: Layer | None = None  # override, e.g. a glass held behind the counter


class Manifest(_Record):
    version: Literal[1]
    assets: list[Asset]
    scenes: dict[str, list[Placement]]

    @model_validator(mode="after")
    def _references(self) -> "Manifest":
        counts = Counter(a.asset_id for a in self.assets)
        if dupes := sorted(i for i, n in counts.items() if n > 1):
            raise ValueError(f"duplicate asset_id {dupes}")
        for name, placements in self.scenes.items():
            for i, p in enumerate(placements):
                if p.asset not in counts:
                    raise ValueError(f"scene {name!r} item {i} uses unknown asset {p.asset!r}")
        return self

    @cached_property
    def by_id(self) -> dict[str, Asset]:
        return {a.asset_id: a for a in self.assets}


def load_manifest(path: Path) -> Manifest:
    try:
        return Manifest.model_validate_json(path.read_bytes())
    except OSError as exc:
        raise AssetError(f"Cannot read asset manifest {path}: {exc}") from exc
    except ValidationError as exc:
        raise AssetError(f"Invalid asset manifest {path}:\n{exc}") from exc


class AssetStore:
    """Loads each image once, converted for the display and scaled. Main thread only;
    needs a display mode (convert_alpha)."""

    def __init__(self, root: Path, manifest: Manifest, font: pygame.font.Font) -> None:
        self.root, self.manifest, self.font = root, manifest, font
        self.diagnostics: list[str] = []
        self._cache: dict[str, pygame.Surface] = {}

    def image(self, asset_id: str) -> pygame.Surface:
        if (surface := self._cache.get(asset_id)) is None:
            surface = self._cache[asset_id] = self._load(self.manifest.by_id[asset_id])
        return surface

    def placed(self, scene: str) -> list[tuple[Asset, pygame.Rect]]:
        """Back-to-front draw list with each item's logical rect."""
        items = []
        for p in self.manifest.scenes[scene]:
            asset = self.manifest.by_id[p.asset]
            (w, h), (ax, ay) = asset.display, asset.anchor
            rect = pygame.Rect(round(p.at[0] - ax * w), round(p.at[1] - ay * h), w, h)
            items.append((LAYERS.index(p.layer or asset.layer), asset, rect))
        items.sort(key=lambda item: item[0])  # stable: scene order within a layer
        return [(asset, rect) for _, asset, rect in items]

    def draw(self, screen: pygame.Surface, scene: str) -> None:
        for asset, rect in self.placed(scene):
            screen.blit(self.image(asset.asset_id), rect)

    def hit_test(self, scene: str, pos: tuple[int, int]) -> tuple[Asset, pygame.Rect] | None:
        """Topmost interactive item under a logical point, with its hit rect."""
        for asset, rect in reversed(self.placed(scene)):
            if asset.hit and (hit := pygame.Rect(asset.hit).move(rect.topleft)).collidepoint(pos):
                return asset, hit
        return None

    def _report(self, message: str) -> None:
        log.warning(message)
        self.diagnostics.append(message)

    def _load(self, asset: Asset) -> pygame.Surface:
        path = self.root / asset.file
        try:
            image = pygame.image.load(path).convert_alpha()
        except (OSError, pygame.error) as exc:
            reason = "file not found" if isinstance(exc, FileNotFoundError) else exc
            message = f"{asset.asset_id}: cannot load assets/{asset.file} ({reason})"
            if asset.required:
                raise AssetError(message) from exc
            self._report(f"placeholder shown — {message}")
            return self._placeholder(asset)
        (w, h), (dw, dh) = image.get_size(), asset.display
        if abs(w * dh - h * dw) > 0.01 * w * dh:
            self._report(f"{asset.asset_id}: {w}x{h} image is stretched to {dw}x{dh}")
        return image if (w, h) == (dw, dh) else pygame.transform.smoothscale(image, (dw, dh))

    def _placeholder(self, asset: Asset) -> pygame.Surface:
        """Code-drawn diagnostic box, never mistaken for art (D023)."""
        w, h = asset.display
        surface = pygame.Surface((w, h)).convert()  # opaque, so layering stays readable
        surface.fill(BURNT_COFFEE)
        for x in range(-h, w, 18):
            pygame.draw.line(surface, HONEY_GARLIC, (x, h), (x + h, 0), 2)
        pygame.draw.rect(surface, CHAMPAGNE, surface.get_rect(), 2)
        label = self.font.render(f"missing: {asset.asset_id}", True, CHAMPAGNE, BURNT_COFFEE)
        surface.blit(label, label.get_rect(center=(w // 2, h // 2)))
        return surface
