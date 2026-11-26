"""The game being played. Saving and loading arrive in T011."""

from dataclasses import dataclass
from typing import Literal

Language = Literal["ko", "en"]
LANGUAGES: tuple[Language, ...] = ("ko", "en")


@dataclass
class Session:
    language: Language  # chosen when the new game starts; fixed for the save (D004, B008)
    shift: int = 1

    def __post_init__(self) -> None:
        if self.language not in LANGUAGES:
            raise ValueError(f"unsupported language {self.language!r}")
