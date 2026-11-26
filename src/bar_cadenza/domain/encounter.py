"""Independent encounter, drink, conversation and input-context states (T007). No pygame.

Each track has its own transition table instead of one combined enum, so a served drink can
coexist with a waiting conversation and a pending reply with stirring. Commands raise
InvalidTransition for a disallowed move; nothing is silently ignored.
"""

from dataclasses import dataclass, field
from enum import StrEnum


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


@dataclass
class Drink:
    drink_id: str
    state: DrinkState = DrinkState.EMPTY


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
