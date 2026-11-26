"""Free-typing text field with IME composition, plus line wrapping. No rendering here."""

from collections.abc import Callable
from dataclasses import dataclass

import pygame

MAX_CHARS = 500
_ENTER_KEYS = {pygame.K_RETURN, pygame.K_KP_ENTER}
_IME_OWNED_KEYS = {pygame.K_BACKSPACE, pygame.K_DELETE}
_NAV_KEYS = {pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END}


@dataclass
class TextField:
    """Committed text + cursor; `composition` is the uncommitted IME preview at the cursor.

    Enter sends at once and Shift+Enter inserts a line break, including the syllable being
    composed. Windows' Korean IME delivers the commit before the Enter key in the same batch;
    if Enter comes first, the action waits for the commit (dropped if it never comes that
    batch). Backspace/Delete are ignored for the whole batch in which the IME was active, so
    an IME Backspace never also deletes committed text. Call end_frame() after each batch.
    """

    text: str = ""
    cursor: int = 0
    composition: str = ""
    max_chars: int = MAX_CHARS
    _ime_active: bool = False
    _pending_enter: str | None = None

    def insert(self, s: str) -> None:
        s = "".join(
            c
            for c in s.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
            if c.isprintable() or c == "\n"
        )
        s = s[: max(self.max_chars - len(self.text), 0)]
        self.text = self.text[: self.cursor] + s + self.text[self.cursor :]
        self.cursor += len(s)

    def backspace(self) -> None:
        if self.cursor:
            self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
            self.cursor -= 1

    def delete(self) -> None:
        self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]

    def move_to(self, index: int) -> None:
        self.cursor = max(0, min(index, len(self.text)))

    def take(self) -> str | None:
        """Remove and return the draft for sending; None when there is nothing to send."""
        message = self.text.strip()
        if not message:
            return None
        self.text, self.cursor = "", 0
        return message

    def handle(self, event: pygame.event.Event) -> str | None:
        """Apply one event; return the message when the player submits."""
        if event.type == pygame.TEXTEDITING:
            if event.text or self.composition:
                self._ime_active = True
            self.composition = event.text
        elif event.type == pygame.TEXTINPUT:
            if self.composition:
                self._ime_active = True
                self.composition = ""
            self.insert(event.text)
            if self._pending_enter:
                return self._enter(self._pending_enter)
        elif event.type == pygame.KEYDOWN:
            return self._key(event)
        return None

    def end_frame(self) -> None:
        self._ime_active = bool(self.composition)
        self._pending_enter = None

    def _enter(self, action: str) -> str | None:
        self._pending_enter = None
        if action == "newline":
            self.insert("\n")
            return None
        return self.take()

    def _key(self, event: pygame.event.Event) -> str | None:
        key = event.key
        if key in _ENTER_KEYS:
            action = "newline" if event.mod & pygame.KMOD_SHIFT else "send"
            if self.composition:  # commit not delivered yet; act once it arrives
                self._pending_enter = action
                return None
            return self._enter(action)
        if (self._ime_active and key in _IME_OWNED_KEYS) or (self.composition and key in _NAV_KEYS):
            return None  # the IME consumed this key
        if key == pygame.K_BACKSPACE:
            self.backspace()
        elif key == pygame.K_DELETE:
            self.delete()
        elif key == pygame.K_LEFT:
            self.move_to(self.cursor - 1)
        elif key == pygame.K_RIGHT:
            self.move_to(self.cursor + 1)
        elif key == pygame.K_HOME:
            self.move_to(0)
        elif key == pygame.K_END:
            self.move_to(len(self.text))
        elif key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
            self.insert(pygame.scrap.get_text() or "")
        return None


def wrap_spans(text: str, max_width: int, measure: Callable[[str], int]) -> list[tuple[int, int]]:
    """Greedy wrap into (start, end) spans of `text`.

    Breaks after spaces (English words and Korean eojeol alike), hard-breaks runs wider than
    the line, honors '\\n', and lets trailing spaces hang. Every line keeps at least one char.
    """
    spans: list[tuple[int, int]] = []
    start, brk, i = 0, None, 0
    while i < len(text):
        ch = text[i]
        if ch == "\n":
            spans.append((start, i))
            start, brk = i + 1, None
        elif ch == " ":
            brk = i + 1
        elif i > start and measure(text[start : i + 1]) > max_width:
            end = brk if brk is not None else i
            spans.append((start, end))
            start, brk, i = end, None, end
            continue
        i += 1
    spans.append((start, len(text)))
    return spans


def line_of(spans: list[tuple[int, int]], index: int) -> int:
    """Line number holding text index `index` (a caret at a wrap point stays on the upper line)."""
    for n, (start, end) in enumerate(spans):
        if index <= end:
            return n
    return len(spans) - 1
