"""Independent encounter, drink, conversation and input-context states (T007). No pygame.

Each track has its own transition table instead of one combined enum, so a served drink can
coexist with a waiting conversation and a pending reply with stirring. Commands raise
InvalidTransition for a disallowed move; nothing is silently ignored.

T010 adds the runtime records: a drink's observed preparation events and the guest's order.
"""

from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from bar_cadenza.domain.catalogue import ID, Catalogue, Preferences, Record, Technique, Text


class Phase(StrEnum):
    ARRIVING = "arriving"
    ORDERING = "ordering"
    VISITING = "visiting"
    DEPARTING = "departing"
    CLOSED = "closed"


class DrinkState(StrEnum):
    EMPTY = "empty"
    ASSEMBLING = "assembling"
    MIXING = "mixing"
    READY = "ready"
    SERVED = "served"
    DISCARDED = "discarded"


class Talk(StrEnum):
    IDLE = "idle"
    AWAITING_PLAYER = "awaiting_player"
    REQUEST_PENDING = "request_pending"
    RESPONSE_AVAILABLE = "response_available"
    CLOSED = "closed"


class InputContext(StrEnum):
    GAMEPLAY = "gameplay"
    TEXT_ENTRY = "text_entry"
    HANDS_BUSY = "hands_busy"
    MODAL = "modal"


P, D, T = Phase, DrinkState, Talk
PHASE_MOVES = {
    P.ARRIVING: {P.ORDERING, P.DEPARTING},
    P.ORDERING: {P.VISITING, P.DEPARTING},
    P.VISITING: {P.ORDERING, P.DEPARTING},  # a second order is allowed
    P.DEPARTING: {P.CLOSED},
    P.CLOSED: set(),
}
DRINK_MOVES = {
    D.EMPTY: {D.ASSEMBLING},
    D.ASSEMBLING: {D.MIXING, D.READY, D.DISCARDED},
    D.MIXING: {D.ASSEMBLING, D.READY, D.DISCARDED},
    D.READY: {D.ASSEMBLING, D.MIXING, D.SERVED, D.DISCARDED},
    D.SERVED: set(),
    D.DISCARDED: set(),
}
TALK_MOVES = {
    T.IDLE: {T.AWAITING_PLAYER, T.REQUEST_PENDING, T.CLOSED},
    T.AWAITING_PLAYER: {T.REQUEST_PENDING, T.CLOSED},
    T.REQUEST_PENDING: {T.RESPONSE_AVAILABLE, T.AWAITING_PLAYER, T.CLOSED},
    T.RESPONSE_AVAILABLE: {T.AWAITING_PLAYER, T.REQUEST_PENDING, T.CLOSED},
    T.CLOSED: set(),
}
TERMINAL_DRINK = {D.SERVED, D.DISCARDED}


class InvalidTransition(ValueError):
    pass


def _move[S: StrEnum](moves: dict[S, set[S]], current: S, target: S) -> S:
    if target not in moves[current]:
        raise InvalidTransition(f"{current} -> {target}")
    return target


class PreparationEvent(Record):
    """One observed action on a drink, in simulation ms. Observations only: recipe targets are
    never copied in as actuals (DATA_MODELS)."""

    event_id: Text
    action: Technique
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    ingredient_id: ID | None = None
    amount_ul: int | None = Field(default=None, ge=0)
    rotations: float | None = Field(default=None, ge=0)  # stirring
    intensity: float | None = Field(default=None, ge=0, le=1)  # shaking

    @model_validator(mode="after")
    def _valid(self) -> "PreparationEvent":
        if self.end_ms < self.start_ms:
            raise ValueError("end_ms is before start_ms")
        if self.action in (Technique.MEASURE, Technique.GARNISH) and self.ingredient_id is None:
            raise ValueError(f"a {self.action} event needs ingredient_id")
        if self.action is Technique.MEASURE and self.amount_ul is None:
            raise ValueError("a measure event needs amount_ul")
        return self


@dataclass
class Drink:
    """DATA_MODELS PreparedDrink: the drink's state plus its observed events, append only."""

    drink_id: str
    state: DrinkState = DrinkState.EMPTY
    events: list[PreparationEvent] = field(default_factory=list)

    def record(self, event: PreparationEvent) -> None:
        if self.state in TERMINAL_DRINK:
            raise InvalidTransition(f"drink {self.drink_id} is {self.state}")
        if any(e.event_id == event.event_id for e in self.events):
            raise ValueError(f"drink {self.drink_id} already has event {event.event_id!r}")
        self.events.append(event)

    @property
    def additions(self) -> dict[str, int]:
        """Measured µl per ingredient, summed from measure events."""
        totals: Counter[str] = Counter()
        for e in self.events:
            if e.action is Technique.MEASURE:
                totals[e.ingredient_id] += e.amount_ul
        return dict(totals)


class InvalidOrder(ValueError):
    pass


class Adjustment(Record):
    """An explicit change the guest asked for: the new target volume (0 leaves it out)."""

    ingredient_id: ID
    volume_ul: int = Field(ge=0)


class Order(Record):
    """A named order uses a recipe plus explicit adjustments; a recommendation leaves the
    choice to the player (GAME_DESIGN)."""

    order_id: Text
    encounter_id: Text
    kind: Literal["named", "recommendation"]
    recipe_id: ID | None = None
    revealed: Preferences = Preferences()
    adjustments: tuple[Adjustment, ...] = ()

    @model_validator(mode="after")
    def _shape(self) -> "Order":
        if (self.kind == "named") != (self.recipe_id is not None):
            raise ValueError("a named order needs recipe_id and a recommendation has none")
        if self.adjustments and self.kind != "named":
            raise ValueError("only a named order has adjustments")
        ids = [a.ingredient_id for a in self.adjustments]
        if len(set(ids)) != len(ids):
            raise ValueError("adjusts an ingredient twice")
        return self

    def check(self, catalogue: Catalogue, available: Collection[str] | None = None) -> None:
        """Reject IDs the catalogue does not have, and a named recipe that is not `available`
        (locked or out of stock) when that set is given."""
        problems = []
        if self.recipe_id is not None:
            if self.recipe_id not in catalogue.recipes:
                problems.append(f"unknown recipe {self.recipe_id!r}")
            elif available is not None and self.recipe_id not in available:
                problems.append(f"recipe {self.recipe_id!r} is not available")
        mentioned = [a.ingredient_id for a in self.adjustments]
        mentioned += [*self.revealed.favorite_spirits, *self.revealed.avoid]
        problems += [
            f"unknown ingredient {i!r}" for i in mentioned if i not in catalogue.ingredients
        ]
        if problems:
            raise InvalidOrder(f"order {self.order_id}: " + "; ".join(problems))


@dataclass
class Encounter:
    """One visit. `revision` changes on every player turn and on close; a reply carrying an
    older revision is stale and is dropped (see ai.jobs.JobRunner.poll)."""

    encounter_id: str
    phase: Phase = Phase.ARRIVING
    talk: Talk = Talk.IDLE
    revision: int = 0
    drinks: list[Drink] = field(default_factory=list)

    @property
    def closed(self) -> bool:
        return self.phase is Phase.CLOSED

    def move(self, target: Phase) -> None:
        self.phase = _move(PHASE_MOVES, self.phase, target)
        if self.closed:
            self.talk = Talk.CLOSED
            self.revision += 1  # invalidates any late reply

    # Drink track: independent of the conversation.
    def move_drink(self, target: DrinkState) -> Drink:
        """Move the current drink; adding to a served/discarded glass starts a new one."""
        self._open()
        if not self.drinks or self.drinks[-1].state in TERMINAL_DRINK:
            self.drinks.append(Drink(f"{self.encounter_id}-d{len(self.drinks) + 1}"))
        drink = self.drinks[-1]
        drink.state = _move(DRINK_MOVES, drink.state, target)
        return drink

    # Conversation track: independent of the drinks.
    @property
    def can_send(self) -> bool:
        """One dialogue turn in flight at a time; the draft waits, it is not dropped."""
        return Talk.REQUEST_PENDING in TALK_MOVES[self.talk] and not self.closed

    def send_player_turn(self) -> int:
        self._open()
        self.talk = _move(TALK_MOVES, self.talk, Talk.REQUEST_PENDING)
        self.revision += 1
        return self.revision

    def receive_reply(self, revision: int) -> bool:
        """Apply a reply once; False for a stale, duplicate or post-close reply."""
        if revision != self.revision or self.talk is not Talk.REQUEST_PENDING:
            return False
        self.talk = Talk.RESPONSE_AVAILABLE
        return True

    def read_reply(self) -> None:
        self.talk = _move(TALK_MOVES, self.talk, Talk.AWAITING_PLAYER)

    def _open(self) -> None:
        if self.closed:
            raise InvalidTransition(f"encounter {self.encounter_id} is closed")
