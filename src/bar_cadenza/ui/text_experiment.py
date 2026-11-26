"""T003 bilingual text and Korean IME experiment (not the game).

Run: uv run python -m bar_cadenza.ui.text_experiment [--seconds S]
Enter sends (including a syllable still being composed); Shift+Enter starts a new line.
Held keys repeat. Wheel scrolls the log.
Keyboard/IME events are printed to the console as evidence of the real event order.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pygame

from bar_cadenza.app.clock import NS_PER_S, SimClock
from bar_cadenza.app.window_experiment import ACCENT, BG, FG, LOGICAL_SIZE, indicator_x
from bar_cadenza.ui.text_input import TextField, line_of, wrap_spans

# ponytail: repo-relative paths; packaged resource lookup is decided in T005/T008.
ROOT = Path(__file__).resolve().parents[3]
FONT_PATH = ROOT / "assets/fonts/NanumGothic-Regular.ttf"
LOCALES_DIR = ROOT / "content/locales"
PANEL = (52, 21, 15)  # Burnt Coffee
LOG_RECT = pygame.Rect(40, 70, 1200, 460)
INPUT_RECT = pygame.Rect(40, 550, 1200, 112)
PAD = 12
MIXED_SAMPLE = (
    "Mixed wrap test — 손님이 Daiquiri를 주문했습니다. The violinist says the last encore "
    "still hums in her ears; 화이트 럼 60 ml, 라임 주스 25 ml, 심플 시럽 15 ml를 넣고 "
    "얼음과 함께 흔든 뒤 coupe 잔에 걸러 주세요. A very long unbroken run follows: "
    "가나다라마바사아자차카타파하가나다라마바사아자차카타파하가나다라마바사아자차카타파하"
    "가나다라마바사아자차카타파하가나다라마바사아자차카타파하가나다라마바사아자차카타파하."
)


def _log_event(frame: int, event: pygame.event.Event) -> None:
    if event.type == pygame.KEYDOWN:
        detail = f"key={pygame.key.name(event.key)!r} mod={event.mod}"
    elif event.type == pygame.TEXTEDITING:
        detail = f"text={event.text!r} start={event.start} length={event.length}"
    elif event.type == pygame.TEXTINPUT:
        detail = f"text={event.text!r}"
    else:
        return
    print(f"frame {frame:6d}  {pygame.event.event_name(event.type):12} {detail}", flush=True)


def run(max_seconds: float | None = None) -> list[str]:
    """Returns the messages the player sent."""
    if not FONT_PATH.is_file():
        sys.exit(f"Missing required font: {FONT_PATH}")
    if sys.stdout:  # piped Windows consoles use cp949; the event log must never crash the loop
        sys.stdout.reconfigure(errors="backslashreplace")
    os.environ.setdefault("SDL_IME_SHOW_UI", "1")  # native candidate list (e.g. Hanja) on Windows
    pygame.init()
    try:
        screen = pygame.display.set_mode(LOGICAL_SIZE, pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption("Bar Cadenza — T003 text/IME experiment")
        font = pygame.font.Font(FONT_PATH, 22)
        line_h = font.get_linesize()
        width = LOG_RECT.width - 2 * PAD

        def wrapped_surfaces(text: str, color=FG) -> list[pygame.Surface]:
            spans = wrap_spans(text, width, lambda s: font.size(s)[0])
            return [font.render(text[a:b], True, color) for a, b in spans]

        log_lines: list[pygame.Surface] = []
        for lang in ("en", "ko"):
            strings = json.loads((LOCALES_DIR / f"{lang}.json").read_text(encoding="utf-8"))
            for key, value in strings.items():
                log_lines += wrapped_surfaces(f"[{lang}] {key}: {value}")
        log_lines += wrapped_surfaces(MIXED_SAMPLE, ACCENT)
        scroll = max(len(log_lines) - LOG_RECT.height // line_h, 0)  # in lines, from top

        field, sent, sim, limiter = TextField(), [], SimClock(), pygame.time.Clock()
        pygame.key.start_text_input()
        pygame.key.set_repeat(500, 33)  # Windows default delay/rate: held keys repeat
        ime_rect = None
        start = last = time.perf_counter_ns()
        frame, running = 0, True
        while running:
            now = time.perf_counter_ns()
            sim.advance(now - last)
            last, frame = now, frame + 1
            visible = LOG_RECT.height // line_h
            for event in pygame.event.get():
                _log_event(frame, event)
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = field.composition != ""  # Esc cancels a composition, else quits
                elif event.type == pygame.MOUSEWHEEL:
                    scroll = max(0, min(scroll - event.y * 3, len(log_lines) - visible))
                elif (message := field.handle(event)) is not None:
                    sent.append(message)
                    log_lines += wrapped_surfaces(f"> {message}")
                    scroll = max(len(log_lines) - visible, 0)
            field.end_frame()
            if max_seconds is not None and now - start >= max_seconds * NS_PER_S:
                running = False

            screen.fill(BG)
            pygame.draw.rect(screen, ACCENT, (40 + indicator_x(sim.sim_ns, 1000), 20, 32, 32))
            screen.blit(font.render(f"sim {sim.sim_ns / NS_PER_S:7.2f} s", True, FG), (1120, 24))

            pygame.draw.rect(screen, PANEL, LOG_RECT)
            for i, surf in enumerate(log_lines[scroll : scroll + visible]):
                screen.blit(surf, (LOG_RECT.x + PAD, LOG_RECT.y + PAD + i * line_h))

            # Draft with the composition shown inline at the cursor.
            pygame.draw.rect(screen, PANEL, INPUT_RECT)
            pygame.draw.rect(screen, ACCENT, INPUT_RECT, 2)
            shown = field.text[: field.cursor] + field.composition + field.text[field.cursor :]
            spans = wrap_spans(shown, width, lambda s: font.size(s)[0])
            caret = field.cursor + len(field.composition)
            caret_line = line_of(spans, caret)
            first = max(0, caret_line - 2)
            for n, (a, b) in enumerate(spans[first : first + 3]):
                y = INPUT_RECT.y + PAD + n * line_h
                screen.blit(font.render(shown[a:b], True, FG), (INPUT_RECT.x + PAD, y))
            a = spans[caret_line][0]
            cx = INPUT_RECT.x + PAD + font.size(shown[a:caret])[0]
            cy = INPUT_RECT.y + PAD + (caret_line - first) * line_h
            pygame.draw.line(screen, FG, (cx, cy + 2), (cx, cy + line_h - 2), 2)
            rect = (cx, cy, 2, line_h)
            if rect != ime_rect:  # keep the IME candidate window at the caret
                pygame.key.set_text_input_rect(rect)
                ime_rect = rect

            status = (
                f"composing [{field.composition}]   {len(field.text)}/{field.max_chars}   "
                "Enter: send · Shift+Enter: new line · wheel: scroll · Esc: quit"
            )
            screen.blit(font.render(status, True, FG), (40, 680))
            pygame.display.flip()
            limiter.tick(60)
        return sent
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=None, help="auto-quit after S seconds")
    sent = run(parser.parse_args().seconds)
    print(f"sent={sent!r}")


if __name__ == "__main__":
    main()
