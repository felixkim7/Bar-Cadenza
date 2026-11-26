import pytest

from bar_cadenza.domain.encounter import DrinkState, Encounter, InvalidTransition, Phase, Talk

D = DrinkState


def test_conversation_continues_during_mixing_and_after_serving():
    enc = Encounter("e1")
    enc.move(Phase.ORDERING)
    enc.move_drink(D.ASSEMBLING)
    enc.move_drink(D.MIXING)
    rev = enc.send_player_turn()  # talking while stirring
    assert enc.talk is Talk.REQUEST_PENDING and enc.drinks[-1].state is D.MIXING
    enc.move_drink(D.READY)  # the drink moves on while the reply is pending
    assert enc.receive_reply(rev) and enc.talk is Talk.RESPONSE_AVAILABLE
    enc.read_reply()
    enc.move_drink(D.SERVED)
    enc.move(Phase.VISITING)
    rev = enc.send_player_turn()  # and after serving
    assert enc.receive_reply(rev) and enc.drinks[-1].state is D.SERVED


def test_one_turn_in_flight_and_stale_or_duplicate_replies_are_dropped():
    enc = Encounter("e1")
    first = enc.send_player_turn()
    assert not enc.can_send
    with pytest.raises(InvalidTransition):
        enc.send_player_turn()
    assert not enc.receive_reply(first - 1)  # older revision
    assert enc.receive_reply(first)
    assert not enc.receive_reply(first)  # duplicate
    assert enc.can_send  # may answer before reading (e.g. while busy)


def test_closing_ends_conversation_and_drops_late_replies():
    enc = Encounter("e1")
    rev = enc.send_player_turn()
    enc.move(Phase.DEPARTING)
    enc.move(Phase.CLOSED)
    assert enc.talk is Talk.CLOSED and not enc.can_send
    assert not enc.receive_reply(rev)
    for command in (enc.send_player_turn, lambda: enc.move_drink(D.ASSEMBLING)):
        with pytest.raises(InvalidTransition):
            command()


def test_drink_moves_are_validated_and_a_finished_glass_starts_a_new_drink():
    enc = Encounter("e1")
    with pytest.raises(InvalidTransition):
        enc.move_drink(D.SERVED)  # an empty glass cannot be served
    first = enc.move_drink(D.ASSEMBLING)
    enc.move_drink(D.READY)
    enc.move_drink(D.SERVED)
    second = enc.move_drink(D.ASSEMBLING)
    assert (first.drink_id, first.state) == ("e1-d1", D.SERVED)
    assert (second.drink_id, second.state) == ("e1-d2", D.ASSEMBLING)
    with pytest.raises(InvalidTransition):
        enc.move(Phase.CLOSED)  # must depart first
