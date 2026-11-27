"""Save files (T011): SQLite schema and migrations, metadata/language and a minimal snapshot.

Each new game is its own file in the per-user saves folder, so a damaged or newer-version
save is never overwritten by another game. Every operation is one transaction: a failure
rolls it back and raises SaveError, so nothing claims a save that did not happen. A save the
game cannot use is reported and left byte-for-byte unchanged. Only the explicit fields below
are stored; no objects, threads, futures or keys.
"""

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from bar_cadenza.domain.session import Session

SUFFIX = ".sqlite3"
CONTENT_VERSION = 1  # bump when authored content changes in a way old saves must know (T012+)
# MIGRATIONS[i] upgrades schema version i to i + 1; PRAGMA user_version holds the version.
# Never edit a released migration: append a new one.
MIGRATIONS: tuple[tuple[str, ...], ...] = (
    (
        """CREATE TABLE saves (
            save_id TEXT PRIMARY KEY,
            language TEXT NOT NULL CHECK (language IN ('ko', 'en')),
            content_version INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        ) STRICT""",
        """CREATE TABLE progress (
            save_id TEXT PRIMARY KEY REFERENCES saves (save_id),
            shift INTEGER NOT NULL CHECK (shift >= 1)
        ) STRICT""",
    ),
)
SCHEMA_VERSION = len(MIGRATIONS)
Reason = Literal["unreadable", "newer", "failed"]


class SaveError(Exception):
    """A save could not be read or written, and nothing was changed. `reason` selects the
    player message (locale key save.<reason>); the text names the file for the log."""

    def __init__(self, reason: Reason, path: Path, detail: object) -> None:
        super().__init__(f"{path}: {detail}")
        self.reason, self.path = reason, path


def latest_save(folder: Path) -> Path | None:
    """The most recently written save file, or None."""
    files = [p for p in folder.glob(f"*{SUFFIX}") if p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime_ns, default=None)


def create_save(folder: Path, session: Session) -> Path:
    """Write a new save file for `session` and return its path."""
    created = datetime.now(UTC)
    save_id = uuid.uuid4().hex
    path = folder / f"save-{created:%Y%m%dT%H%M%S}-{save_id[:8]}{SUFFIX}"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=False)  # never reuse an existing file
    except OSError as exc:
        raise SaveError("failed", path, exc) from exc
    try:
        with _transaction(path) as db:
            _upgrade(db, path)
            stamp = created.isoformat(timespec="seconds")
            row = (save_id, session.language, CONTENT_VERSION, stamp, stamp)
            db.execute("INSERT INTO saves VALUES (?, ?, ?, ?, ?)", row)
            db.execute("INSERT INTO progress VALUES (?, ?)", (save_id, session.shift))
    except (OSError, sqlite3.Error) as exc:
        with suppress(OSError):
            path.unlink()  # the half-made file is our own new one
        raise SaveError("failed", path, exc) from exc
    return path


def load_save(path: Path) -> Session:
    try:
        with _transaction(path) as db:
            _upgrade(db, path)
            rows = db.execute(
                "SELECT language, shift FROM saves JOIN progress USING (save_id)"
            ).fetchall()
            if len(rows) != 1:
                raise SaveError("unreadable", path, f"expected one save record, found {len(rows)}")
            language, shift = rows[0]
            return Session(language=language, shift=shift)
    except (OSError, sqlite3.Error, ValueError) as exc:  # ValueError: a value Session refuses
        raise SaveError("unreadable", path, exc) from exc


def write_save(path: Path, session: Session) -> None:
    """Store the snapshot; on any failure the file keeps its previous contents."""
    try:
        with _transaction(path) as db:
            _upgrade(db, path)
            now = datetime.now(UTC).isoformat(timespec="seconds")
            db.execute("UPDATE saves SET updated_at = ?", (now,))
            if db.execute("UPDATE progress SET shift = ?", (session.shift,)).rowcount != 1:
                raise SaveError("failed", path, "no progress record")
    except (OSError, sqlite3.Error) as exc:
        raise SaveError("failed", path, exc) from exc


@contextmanager
def _transaction(path: Path) -> Iterator[sqlite3.Connection]:
    """Open an existing file (never create one) as a single transaction: it commits when the
    block completes and rolls back on any error."""
    db = sqlite3.connect(f"{path.absolute().as_uri()}?mode=rw", uri=True, autocommit=True)
    try:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("BEGIN")
        yield db
        db.execute("COMMIT")
    finally:
        if db.in_transaction:
            db.execute("ROLLBACK")
        db.close()


def _upgrade(db: sqlite3.Connection, path: Path) -> None:
    """Check integrity and version, then apply any missing migrations in this transaction."""
    if (result := db.execute("PRAGMA quick_check").fetchone()[0]) != "ok":
        raise SaveError("unreadable", path, f"integrity check: {result}")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise SaveError("newer", path, f"schema {version} is newer than {SCHEMA_VERSION}")
    for statements in MIGRATIONS[version:]:
        for sql in statements:
            db.execute(sql)
    if version < SCHEMA_VERSION:
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
