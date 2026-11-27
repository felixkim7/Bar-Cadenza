"""Vertical list of buttons, usable with mouse or keyboard."""

from dataclasses import dataclass

import pygame

from bar_cadenza.ui.palette import BURNT_COFFEE, CHAMPAGNE, HONEY_GARLIC, WHISKEY_SOUR

_NEXT = {pygame.K_DOWN, pygame.K_TAB}
_ACTIVATE = {pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE}


@dataclass
class ButtonList:
    """items are (action, label). A click activates only if press and release land on the
    same button. Focus is shown by a thick border and a marker, not by color alone."""

    items: list[tuple[str, str]]
    center_x: int
    top: int
    width: int = 520
    height: int = 56
    gap: int = 14
    focus: int = 0
    _pressed: int | None = None

    def rects(self) -> list[pygame.Rect]:
        left = self.center_x - self.width // 2
        step = self.height + self.gap
        return [
            pygame.Rect(left, self.top + i * step, self.width, self.height)
            for i in range(len(self.items))
        ]

    def handle(self, event: pygame.event.Event) -> str | None:
        """Return the action activated by this event, if any."""
        n = len(self.items)
        if event.type == pygame.KEYDOWN:
            if event.key in _NEXT:
                self.focus = (self.focus + 1) % n
            elif event.key == pygame.K_UP:
                self.focus = (self.focus - 1) % n
            elif event.key in _ACTIVATE:
                return self.items[self.focus][0]
        elif event.type == pygame.MOUSEMOTION:
            if (hit := self._hit(event.pos)) is not None:
                self.focus = hit
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._pressed = self._hit(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pressed, self._pressed = self._pressed, None
            if pressed is not None and pressed == self._hit(event.pos):
                return self.items[pressed][0]
        return None

    def _hit(self, pos: tuple[int, int]) -> int | None:
        return next((i for i, r in enumerate(self.rects()) if r.collidepoint(pos)), None)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, active: bool = True) -> None:
        """`active` False hides the keyboard marker while keyboard focus is elsewhere; the
        button under the pointer still lights up, so it reads as clickable."""
        mouse = pygame.mouse.get_pos()
        for i, (rect, (_, label)) in enumerate(zip(self.rects(), self.items)):
            focused = active and i == self.focus
            lit = focused or rect.collidepoint(mouse)
            pygame.draw.rect(screen, BURNT_COFFEE, rect, border_radius=6)
            border = WHISKEY_SOUR if lit else HONEY_GARLIC
            pygame.draw.rect(screen, border, rect, 4 if lit else 2, border_radius=6)
            text = font.render(label, True, CHAMPAGNE)
            screen.blit(text, text.get_rect(center=rect.center))
            if focused:
                x, y = rect.x + 22, rect.centery
                pygame.draw.polygon(screen, WHISKEY_SOUR, [(x, y - 9), (x, y + 9), (x + 12, y)])
