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

    # Log the player message as an event
    event = Event(
        id=str(len(game.logs)+1),
        type="player_message",
        payload={"player_id": action.player_id, "message": action.message}
    )
    game.logs.append(event)
    
    # Hard-coded DM response for now (will be replaced by AI agent)
    dm_response = Event(
        id=str(len(game.logs)+1),
        type="dm_response",
        payload={"message": f"Reply to: {action.message}"}
    )
    game.logs.append(dm_response)
    
    # advance turn
    if len(game.players) > 0:
        game.turn_index = (game.turn_index + 1) % len(game.players)
    return game
