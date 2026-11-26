import os

import pygame

from bar_cadenza.ui.text_input import TextField, line_of, wrap_spans


def edit(text: str) -> pygame.event.Event:
    return pygame.event.Event(pygame.TEXTEDITING, text=text, start=len(text), length=0)


def commit(text: str) -> pygame.event.Event:
    return pygame.event.Event(pygame.TEXTINPUT, text=text)


def key(k: int, mod: int = 0) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=mod)


def batch(field: TextField, *events: pygame.event.Event) -> list[str]:
    """One frame's event batch; returns submitted messages."""
    sent = [m for e in events if (m := field.handle(e)) is not None]
    field.end_frame()
    return sent


def test_english_typing_editing_and_submit():
    f = TextField()
    batch(f, commit("helo"), key(pygame.K_LEFT), commit("l"))
    assert (f.text, f.cursor) == ("hello", 4)
    batch(f, key(pygame.K_HOME), key(pygame.K_DELETE), key(pygame.K_END), key(pygame.K_BACKSPACE))
    assert f.text == "ell"
    assert batch(f, key(pygame.K_RETURN)) == ["ell"]
    assert (f.text, f.cursor) == ("", 0)
    assert batch(f, commit("   "), key(pygame.K_RETURN)) == []  # blank never sends


SHIFT = pygame.KMOD_LSHIFT


def test_recorded_windows_korean_ime_log_sends_on_single_enter():
    """Frames 810-1084 of the user's real Windows Korean IME log (2026-11-26)."""
    f = TextField()
    sent = []
    sent += batch(f, edit("ㅎ"))
    sent += batch(f, edit("하"))
    sent += batch(f, edit(""), commit("하"), key(pygame.K_RETURN))  # frame 881
    sent += batch(f, key(pygame.K_RETURN))  # empty draft: nothing
    for e in ("ㅎ", "하", "핳"):
        sent += batch(f, edit(e))
    sent += batch(f, edit(""), commit("하"), edit("하"))  # frame 993: ㅎ moved to next syllable
    sent += batch(f, edit("한"))
    sent += batch(f, edit(""), commit("한"), key(pygame.K_RETURN))  # frame 1056
    assert sent == ["하", "하한"]
    assert (f.text, f.composition) == ("", "")


def test_enter_before_commit_waits_for_the_commit():
    f = TextField()
    assert batch(f, edit("한"), key(pygame.K_RETURN), edit(""), commit("한")) == ["한"]
    batch(f, edit("한"))
    assert batch(f, key(pygame.K_RETURN)) == []  # commit never came this batch: Enter dropped
    batch(f, commit("한"))
    assert f.text == "한"  # text kept; nothing sent twice or lost


def test_shift_enter_inserts_line_break_without_sending():
    f = TextField()
    assert batch(f, commit("a"), key(pygame.K_RETURN, SHIFT), commit("b")) == []
    assert f.text == "a\nb"
    assert batch(f, edit("한"), edit(""), commit("한"), key(pygame.K_RETURN, SHIFT)) == []
    assert batch(f, edit("둘"), key(pygame.K_RETURN, SHIFT), commit("둘")) == []
    assert f.text == "a\nb한\n둘\n"
    assert batch(f, key(pygame.K_RETURN)) == ["a\nb한\n둘"]


def test_ime_backspace_does_not_also_delete_committed_text():
    f = TextField()
    batch(f, commit("가"), edit("ㅎ"))
    batch(f, edit(""), key(pygame.K_BACKSPACE))  # IME deleted the jamo
    assert (f.text, f.composition) == ("가", "")
    batch(f, key(pygame.K_BACKSPACE))
    assert f.text == ""


def test_insert_sanitizes_and_bounds_length():
    f = TextField(max_chars=8)
    f.insert("a\r\nb\tc\x00d")
    assert f.text == "a\nb cd"
    f.insert("한국어English")
    assert f.text == "a\nb cd한국"


def test_wrap_english_words_and_korean_eojeol():
    def lines(text, width):
        return [text[a:b].rstrip() for a, b in wrap_spans(text, width, len)]

    assert lines("the quick brown fox", 10) == ["the quick", "brown fox"]
    assert lines("오늘 공연이 끝났어요", 6) == ["오늘 공연이", "끝났어요"]
    assert lines("가나다라마바사", 3) == ["가나다", "라마바", "사"]
    assert lines("Bar 카덴차에 welcome", 7) == ["Bar", "카덴차에", "welcome"]
    assert lines("a\nb", 10) == ["a", "b"]
    assert lines("", 10) == [""]


def test_line_of_caret():
    spans = wrap_spans("aa bb", 4, len)  # "aa " | "bb"
    assert [line_of(spans, i) for i in range(6)] == [0, 0, 0, 0, 1, 1]


def test_experiment_renders_both_languages_headless(monkeypatch):
    monkeypatch.setitem(os.environ, "SDL_VIDEODRIVER", "dummy")
    from bar_cadenza.ui.text_experiment import run

    assert run(max_seconds=0.3) == []
    assert not pygame.display.get_init()
