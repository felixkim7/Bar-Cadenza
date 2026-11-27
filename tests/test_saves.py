"""T011: save round trip, schema version, missing/damaged/newer saves and failed writes."""

import os
import sqlite3
import stat

import pytest

from bar_cadenza.domain.session import Session
from bar_cadenza.persistence import saves
from bar_cadenza.persistence.saves import (
    SCHEMA_VERSION,
    SaveError,
    create_save,
    latest_save,
    load_save,
    write_save,
)


def rows(path, sql):
    db = sqlite3.connect(path)
    try:
        return db.execute(sql).fetchall()
    finally:
        db.close()


@pytest.mark.parametrize("language", ["ko", "en"])
def test_a_save_round_trips_language_and_shift(tmp_path, language):
    path = create_save(tmp_path / "saves", Session(language, shift=1))
    assert load_save(path) == Session(language, shift=1)
    write_save(path, Session(language, shift=4))
    assert load_save(path) == Session(language, shift=4)
    assert rows(path, "PRAGMA user_version") == [(SCHEMA_VERSION,)]


def test_each_new_game_gets_its_own_file_and_continue_takes_the_newest(tmp_path):
    first = create_save(tmp_path, Session("ko"))
    second = create_save(tmp_path, Session("en"))
    assert first != second
    # Set the times (whole seconds; Windows keeps 100 ns units): two writes within one
    # clock tick can share a timestamp.
    os.utime(first, (1_000, 1_000))
    os.utime(second, (2_000, 2_000))
    assert latest_save(tmp_path) == second
    write_save(first, Session("ko", shift=2))  # writing makes it the newest again
    assert latest_save(tmp_path) == first


def test_missing_saves_are_reported_and_never_created(tmp_path):
    assert latest_save(tmp_path / "nowhere") is None
    with pytest.raises(SaveError) as caught:
        load_save(tmp_path / "gone.sqlite3")
    assert caught.value.reason == "unreadable"
    assert not (tmp_path / "gone.sqlite3").exists()


def damage_with_garbage(path):
    path.write_bytes(b"not a database" * 100)


def damage_by_truncating(path):
    path.write_bytes(path.read_bytes()[:1500])


def damage_by_emptying(path):
    path.write_bytes(b"")  # SQLite reads an empty file as an empty database: no save record


def damage_by_dropping_progress(path):
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE progress")
    db.close()


@pytest.mark.parametrize(
    "damage",
    [damage_with_garbage, damage_by_truncating, damage_by_emptying, damage_by_dropping_progress],
)
def test_a_damaged_save_is_reported_and_left_unchanged(tmp_path, damage):
    path = create_save(tmp_path, Session("ko", shift=3))
    damage(path)
    before = path.read_bytes()
    with pytest.raises(SaveError) as caught:
        load_save(path)
    assert caught.value.reason == "unreadable" and str(path) in str(caught.value)
    assert path.read_bytes() == before


def test_a_save_from_a_newer_version_is_refused_and_left_unchanged(tmp_path):
    path = create_save(tmp_path, Session("en", shift=2))
    with sqlite3.connect(path) as db:
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    db.close()
    before = path.read_bytes()
    for attempt in (lambda: load_save(path), lambda: write_save(path, Session("en", shift=3))):
        with pytest.raises(SaveError) as caught:
            attempt()
        assert caught.value.reason == "newer"
    assert path.read_bytes() == before


def test_an_older_save_is_migrated_on_load_and_keeps_its_data(tmp_path, monkeypatch):
    path = create_save(tmp_path, Session("ko", shift=3))
    later = (("ALTER TABLE progress ADD COLUMN xp INTEGER NOT NULL DEFAULT 0",),)
    monkeypatch.setattr(saves, "MIGRATIONS", saves.MIGRATIONS + later)
    monkeypatch.setattr(saves, "SCHEMA_VERSION", SCHEMA_VERSION + 1)
    assert load_save(path) == Session("ko", shift=3)
    assert rows(path, "PRAGMA user_version") == [(SCHEMA_VERSION + 1,)]
    assert rows(path, "SELECT shift, xp FROM progress") == [(3, 0)]


def test_a_refused_file_keeps_its_old_version(tmp_path):
    path = tmp_path / "old.sqlite3"
    sqlite3.connect(path).close()  # version 0: an empty, never-migrated file
    with pytest.raises(SaveError):
        load_save(path)  # no save record, so it is refused...
    assert rows(path, "PRAGMA user_version") == [(0,)]  # ...and the upgrade was rolled back


def test_a_failed_write_raises_and_changes_nothing(tmp_path):
    path = create_save(tmp_path, Session("ko", shift=2))
    stamp = rows(path, "SELECT updated_at FROM saves")
    with pytest.raises(SaveError) as caught:
        write_save(path, Session("ko", shift=0))  # refused by the schema after updated_at
    assert caught.value.reason == "failed"
    assert load_save(path) == Session("ko", shift=2)
    assert rows(path, "SELECT updated_at FROM saves") == stamp  # the whole write rolled back


def test_a_read_only_save_fails_to_write_without_losing_data(tmp_path):
    path = create_save(tmp_path, Session("en", shift=5))
    os.chmod(path, stat.S_IREAD)
    try:
        with pytest.raises(SaveError) as caught:
            write_save(path, Session("en", shift=6))
        assert caught.value.reason == "failed"
        assert load_save(path) == Session("en", shift=5)  # still readable
    finally:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


def test_a_save_folder_that_cannot_be_created_fails_cleanly(tmp_path):
    blocked = tmp_path / "file"
    blocked.write_text("in the way")
    with pytest.raises(SaveError) as caught:
        create_save(blocked, Session("ko"))
    assert caught.value.reason == "failed"


def test_only_the_listed_fields_are_stored(tmp_path, monkeypatch):
    secret = "sk-test-not-a-real-key-123"
    monkeypatch.setenv("BAR_CADENZA_API_KEY", secret)
    session = Session("ko", shift=7)
    session.api_key = secret  # stray runtime state must not leak into the file
    path = create_save(tmp_path, session)
    assert secret.encode() not in path.read_bytes()
    tables = rows(path, "SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name")
    columns = {t: [c[1] for c in rows(path, f"PRAGMA table_info({t})")] for (t,) in tables}
    assert columns == {
        "progress": ["save_id", "shift"],
        "saves": ["save_id", "language", "content_version", "created_at", "updated_at"],
    }
