# domain

Pure records and invariants. No pygame, network or file I/O. Follow docs/ARCHITECTURE.md.

- `encounter.py`:
  - the independent visit, drink, conversation and input-context states (T007);
  - orders, preparation events and drink observations (T010).
- `catalogue.py`: authored content contracts and cross-file validation (T010).
- `session.py`: the per-game session (T006).
