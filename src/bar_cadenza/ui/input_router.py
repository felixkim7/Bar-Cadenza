"""Routes each event to exactly one owner: modal > captured pointer action > keyboard focus.

The chat field keeps keyboard focus while the mouse works tools, so the player can type and
mix at once. While the field has focus every key goes to it, so text keys (letters, Space,
Enter) never trigger a control. Tab moves keyboard focus between the field and the buttons.
A pointer press on a hold control captures the pointer; the release ends the action wherever
it happens, and so does losing window focus (the release may never arrive).
"""

import pygame

from bar_cadenza.domain.encounter import InputContext
from bar_cadenza.ui.buttons import ButtonList
from bar_cadenza.ui.text_input import TextField

_POINTER = {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION}
_TEXT = {pygame.KEYDOWN, pygame.TEXTINPUT, pygame.TEXTEDITING}
_LOST = {pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED}

# ("send", text) | ("button" | "modal", action) | ("hold" | "release", control name)
Routed = tuple[str, str] | None


class InputRouter:
    def __init__(
        self,
        field: TextField,
        field_rect: pygame.Rect,
        buttons: ButtonList,
        holds: dict[str, pygame.Rect],
    ) -> None:
        self.field, self.field_rect, self.buttons, self.holds = field, field_rect, buttons, holds
        self.text_focus = True
        self.captured: str | None = None
        self.modal: ButtonList | None = None
        pygame.key.start_text_input()

    @property
    def context(self) -> InputContext:
        """Typing still works while HANDS_BUSY; the field keeps focus underneath."""
        if self.modal:
            return InputContext.MODAL
        if self.captured:
            return InputContext.HANDS_BUSY
        return InputContext.TEXT_ENTRY if self.text_focus else InputContext.GAMEPLAY

    def set_text_focus(self, on: bool) -> None:
        if not on and self.field.composition:  # keep the draft: commit the IME preview
            self.field.insert(self.field.composition)
            self.field.composition = ""
        self.text_focus = on
        (pygame.key.start_text_input if on else pygame.key.stop_text_input)()

    def release(self) -> Routed:
        name, self.captured = self.captured, None
        return ("release", name) if name else None

    def open_modal(self, buttons: ButtonList) -> Routed:
        self.modal = buttons
        return self.release()

    def close_modal(self) -> None:
        self.modal = None

    def handle(self, event: pygame.event.Event) -> Routed:
        t = event.type
        if t in _LOST:
            return self.release()
        if self.modal:
            if t in (pygame.TEXTINPUT, pygame.TEXTEDITING):
                self.field.handle(event)  # an IME commit during the modal is still draft text
            elif (action := self.modal.handle(event)) is not None:
                return ("modal", action)
            return None
        if self.captured and t in _POINTER:
            if t == pygame.MOUSEBUTTONUP and event.button == 1:
                return self.release()  # inside or outside the control
            return None
        if t == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, rect in self.holds.items():
                if rect.collidepoint(event.pos):
                    self.captured = name
                    return ("hold", name)
            if self.field_rect.collidepoint(event.pos):
                self.set_text_focus(True)
                return None
        if t == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.set_text_focus(not self.text_focus)
            return None
        if t in _TEXT and self.text_focus:
            message = self.field.handle(event)
            return ("send", message) if message is not None else None
        if t in (pygame.TEXTINPUT, pygame.TEXTEDITING):
            return None
        if (action := self.buttons.handle(event)) is not None:
            return ("button", action)
        return None
