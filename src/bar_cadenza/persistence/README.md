# persistence

SQLite saves and migrations. Follow docs/ARCHITECTURE.md and B013.

`saves.py` (T011):
- one file per game in the per-user saves folder;
- the schema version is held in `PRAGMA user_version`, with append-only migrations;
- each operation is one transaction;
- a save the game cannot use is reported (`SaveError`) and left unchanged.

Add new tables and columns by appending a migration; never edit a released one.
