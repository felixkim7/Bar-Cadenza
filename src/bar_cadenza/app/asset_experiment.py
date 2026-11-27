"""T008 layered test scene (not the game).

Run: uv run python -m bar_cadenza.app.asset_experiment [--seconds S] [--verify-pointer]
Hover outlines the topmost interactive item under the mouse; click prints its ID. Missing
images appear as labelled placeholders, with the diagnostics listed on screen.
--verify-pointer (Windows) resizes the window to letterboxed sizes, moves the real cursor
onto each hit region and checks that SDL's window→logical mapping lands on that item.
"""

import argparse
import ctypes
import ctypes.wintypes
import sys
import time

import pygame

from bar_cadenza.app.assets import AssetStore, load_manifest
from bar_cadenza.app.clock import NS_PER_S
from bar_cadenza.app.main import FONT, LOGICAL_SIZE
from bar_cadenza.app.paths import resource_root
from bar_cadenza.ui.palette import BALSAMICO, CHAMPAGNE, WHISKEY_SOUR

SCENE = "t008_layer_test"


def logical_to_window(pos, window_size, logical_size=LOGICAL_SIZE) -> tuple[float, float]:
    """Where pygame-ce's SCALED mode draws a logical point: an integer scale (measured in
    T008 by screen capture — the picture stays 1× until the window is twice the size),
    centred, with bars on every side that has room."""
    scale = max(1, min(window_size[0] // logical_size[0], window_size[1] // logical_size[1]))
    ox = (window_size[0] - logical_size[0] * scale) / 2
    oy = (window_size[1] - logical_size[1] * scale) / 2
    return pos[0] * scale + ox, pos[1] * scale + oy


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _verify_pointer(store: AssetStore) -> list[str]:
    """Return failures; restores the window size and cursor position afterwards."""
    user32 = ctypes.windll.user32
    hwnd = pygame.display.get_wm_info()["window"]
    saved = _Point()
    user32.GetCursorPos(ctypes.byref(saved))
    outer = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(outer))
    failures, checks = [], 0
    for size in ((1500, 1000), (1840, 860)):  # letterbox, then pillarbox
        user32.SetWindowPos(hwnd, 0, 0, 0, *size, 0x0002 | 0x0004)  # NOMOVE|NOZORDER
        client = ctypes.wintypes.RECT()
        for _ in range(10):
            pygame.event.pump()
            time.sleep(0.02)
        user32.GetClientRect(hwnd, ctypes.byref(client))
        window_size = (client.right, client.bottom)
        for asset, rect in store.placed(SCENE):
            if not asset.hit:
                continue
            target = pygame.Rect(asset.hit).move(rect.topleft).center
            wx, wy = logical_to_window(target, window_size)
            point = _Point(round(wx), round(wy))
            user32.ClientToScreen(hwnd, ctypes.byref(point))
            user32.SetCursorPos(point.x, point.y)
            for _ in range(5):
                pygame.event.pump()
                time.sleep(0.01)
            got = pygame.mouse.get_pos()
            hit = store.hit_test(SCENE, got)
            checks += 1
            ok = abs(got[0] - target[0]) <= 1 and abs(got[1] - target[1]) <= 1
            ok = ok and hit is not None and hit[0].asset_id == asset.asset_id
            line = f"window {window_size} {asset.asset_id}: expected {target}, SDL gave {got}"
            print(("ok   " if ok else "FAIL ") + line, flush=True)
            if not ok:
                failures.append(line)
    w, h = outer.right - outer.left, outer.bottom - outer.top
    user32.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0002 | 0x0004)
    user32.SetCursorPos(saved.x, saved.y)
    print(f"pointer mapping: {checks - len(failures)}/{checks} ok", flush=True)
    return failures


def run(max_seconds: float | None = None, verify_pointer: bool = False) -> list[str]:
    """Returns pointer-mapping failures (empty when not verifying)."""
    root = resource_root()
    manifest = load_manifest(root / "assets/manifest.json")
    pygame.init()
    try:
        screen = pygame.display.set_mode(LOGICAL_SIZE, pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption("Bar Cadenza — T008 layered asset test")
        small = pygame.font.Font(root / FONT, 18)
        store = AssetStore(root / "assets", manifest, small)
        failures: list[str] = []
        start, running, limiter = time.perf_counter_ns(), True, pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    hit = store.hit_test(SCENE, event.pos)
                    print(f"click {event.pos} -> {hit[0].asset_id if hit else None}", flush=True)
            screen.fill(BALSAMICO)
            store.draw(screen, SCENE)
            pos = pygame.mouse.get_pos()
            if hit := store.hit_test(SCENE, pos):
                asset, rect = hit
                pygame.draw.rect(screen, WHISKEY_SOUR, rect, 3)
                label = small.render(asset.asset_id, True, CHAMPAGNE, BALSAMICO)
                screen.blit(label, (rect.x, max(rect.y - 24, 0)))
            info = f"window {pygame.display.get_window_size()}  logical mouse {pos}"
            lines = [info, *store.diagnostics]
            for i, line in enumerate(lines):
                screen.blit(small.render(line, True, CHAMPAGNE, BALSAMICO), (8, 8 + i * 24))
            pygame.display.flip()
            if verify_pointer and sys.platform == "win32":
                failures = _verify_pointer(store)
                verify_pointer = False
            if max_seconds is not None and time.perf_counter_ns() - start >= max_seconds * NS_PER_S:
                running = False
            limiter.tick(60)
        return failures
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seconds", type=float, default=None)
    parser.add_argument("--verify-pointer", action="store_true")
    args = parser.parse_args()
    sys.exit(1 if run(args.seconds, args.verify_pointer) else 0)


if __name__ == "__main__":
    main()
