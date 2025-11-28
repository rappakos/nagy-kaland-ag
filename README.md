nagy-kaland-ag — Agent backend (REST-only MVP)

Minimal FastAPI backend for a turn-based, text D&D-style game.

Quickstart

1. Create and activate a virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2. Run the app:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API (MVP)
- POST /games -> create game, returns {"game_id": "..."}
- GET /games/{game_id} -> get current game state
- POST /games/{game_id}/action -> submit player action

This project uses an in-memory store for MVP. Swap to persistent store later.
