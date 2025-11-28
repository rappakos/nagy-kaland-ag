from typing import Dict, Optional
from .models import GameState, Player, Event

# Very small in-memory store for MVP
_games: Dict[str, GameState] = {}


def create_game(player_names: Optional[list] = None) -> GameState:
    players = []
    if player_names:
        for i, name in enumerate(player_names):
            players.append(Player(id=str(i+1), name=name))
    game = GameState.create(players=players)
    _games[game.game_id] = game
    return game


def get_game(game_id: str) -> Optional[GameState]:
    return _games.get(game_id)


def apply_action(game_id: str, action) -> Optional[GameState]:
    game = _games.get(game_id)
    if not game:
        return None

    # Simple mechanics: append action as event and advance turn
    event = Event(id=str(len(game.logs)+1), type=action.type, payload={"player_id": action.player_id, **(action.payload or {})})
    game.logs.append(event)
    # advance turn
    if len(game.players) > 0:
        game.turn_index = (game.turn_index + 1) % len(game.players)
    return game
