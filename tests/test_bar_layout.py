"""T009: the composed bar keeps tools clear of the panels, and its text fits in ko and en."""

import pygame
import pytest

from bar_cadenza.domain.session import Session
from bar_cadenza.scenes.shell import (
    FIELD_RECT,
    PAD,
    RECIPE_RECT,
    SCENE,
    TOOLS,
    TRANSCRIPT_RECT,
    Bar,
    _wrapped,
    recipe_lines,
)

FOCUS_MARKER = 40  # ButtonList draws its focus triangle inside this margin


def open_bar(app, lang):
    app.session = Session(language=lang)
    app.go(Bar(app))
    return app.scene


def test_panels_buttons_and_typing_never_cover_a_tool(new_app):
    bar = open_bar(new_app, "en")
    ui = [TRANSCRIPT_RECT, RECIPE_RECT, FIELD_RECT, *bar.buttons.rects()]
    tools = {
        asset.asset_id: (asset, pygame.Rect(asset.hit).move(rect.topleft))
        for asset, rect in new_app.assets.placed(SCENE)
        if asset.asset_id in TOOLS
    }
    assert tools.keys() == TOOLS.keys()
    for asset, hit in tools.values():
        assert asset.layer == "props" and hit.collidelist(ui) == -1, asset.asset_id
    assert bar.stir_rect == tools["prop_shaker_idle"][1]  # hold the shaker itself to mix


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_bar_text_fits_its_panels_in_both_languages(new_app, lang):
    app = new_app
    bar, small, t = open_bar(app, lang), app.small_font, app.t
    for (_, label), rect in zip(bar.buttons.items, bar.buttons.rects()):
        assert small.size(label)[0] <= rect.width - 2 * FOCUS_MARKER, label
    assert small.size(t("bar.chat_hint"))[0] <= FIELD_RECT.width - 2 * 12
    assert app.font.size(t("bar.transcript"))[0] <= TRANSCRIPT_RECT.width - 2 * PAD

    width = RECIPE_RECT.width - 2 * PAD
    rows = [(font, _wrapped(font, text, width)) for font, _, text in recipe_lines(app)]
    assert (
        sum(font.get_linesize() * len(lines) for font, lines in rows)
        <= RECIPE_RECT.height - 2 * PAD
    )
    assert all(font.size(line)[0] <= width for font, lines in rows for line in lines)

    longest = {"phase": "departing", "drink": "assembling", "talk": "response_available"}
    tags = [  # one-line labels on plates across the top or above a tool
        t("bar.state", **longest, input="text_entry"),
        f"{t('bar.prop_shaker')} · {t('bar.stir')} · {t('bar.stirred', seconds='999.9')}",
        t("bar.shift_time", time="99:59"),
        t("bar.need_ingredient"),
        t("bar.added"),
        t("bar.served"),
    ]
    assert all(small.size(text)[0] + 16 <= 1280 for text in tags)

    message = t("bar.you", text="오늘은 좀 긴 하루였어요, 그래도 여기 오니까 마음이 놓이네요. " * 3)
    lines = _wrapped(small, message, TRANSCRIPT_RECT.width - 2 * PAD)
    assert len(lines) > 1 and all(
        small.size(line)[0] <= TRANSCRIPT_RECT.width - 2 * PAD for line in lines
    )
