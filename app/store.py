from typing import Dict, Optional
from .models import GameState, Player, Event, Character
from .dm_agent import get_dm_agent
from .database import SessionLocal
from .persistence import save_game, load_game, save_character, update_character

# In-memory cache for active games (backed by database)
_games: Dict[str, GameState] = {}
_character_mappings: Dict[str, Dict[str, str]] = {}  # game_id -> {player_id -> character_id}


def create_game(player_names: Optional[list] = None) -> GameState:
    players = []
    if player_names:
        for i, name in enumerate(player_names):
            players.append(Player(id=str(i+1), name=name))
    game = GameState.create(players=players)
    _games[game.game_id] = game
    _character_mappings[game.game_id] = {}
    
    # Persist to database
    db = SessionLocal()
    try:
        save_game(db, game, {})
    finally:
        db.close()
    
    return game


def assign_character_to_game(game_id: str, player_id: str, character_id: str, character: Character) -> Optional[GameState]:
    """
    Assign an existing character to a player in a game.
    """
    game = get_game(game_id)
    if not game:
        return None
    
    # Assign character
    game.characters[player_id] = character
    
    # Update mappings
    if game_id not in _character_mappings:
        _character_mappings[game_id] = {}
    _character_mappings[game_id][player_id] = character_id
    
    # Persist to database
    db = SessionLocal()
    try:
        save_game(db, game, _character_mappings[game_id])
    finally:
        db.close()
    
    return game


def get_game(game_id: str) -> Optional[GameState]:
    # Check cache first
    if game_id in _games:
        return _games[game_id]
    
    # Try loading from database
    db = SessionLocal()
    try:
        result = load_game(db, game_id)
        if result:
            game_state, char_mappings = result
            _games[game_id] = game_state
            _character_mappings[game_id] = char_mappings
            return game_state
    finally:
        db.close()
    
    return None


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
    
    # Get DM response using LangChain agent
    dm_agent = get_dm_agent()
    
    # Prepare game state for agent
    game_state_dict = {
        "current_player_id": action.player_id,
        "characters": {
            pid: char.model_dump() if char else None 
            for pid, char in game.characters.items()
        },
        "history": [
            {
                "type": log.type,
                "payload": log.payload
            }
            for log in game.logs[:-1]  # Exclude the just-added player message
        ]
    }
    
    dm_result = dm_agent.get_response(action.message, game_state_dict)
    
    # If a character was created, save it
    if "character" in dm_result:
        char_data = dm_result["character"]
        new_char = Character(**char_data)
        game.characters[action.player_id] = new_char
        
        # Save to database
        db = SessionLocal()
        try:
            player_name = next((p.name for p in game.players if p.id == action.player_id), "Unknown")
            char_id = save_character(db, new_char, player_name)
            if game.game_id not in _character_mappings:
                _character_mappings[game.game_id] = {}
            _character_mappings[game.game_id][action.player_id] = char_id
        finally:
            db.close()
    
    # If experience was granted, update character
    if "experience" in dm_result:
        char = game.characters.get(action.player_id)
        if char:
            char.experience += dm_result["experience"]
    
    # If character leveled up, apply changes
    if "level_up" in dm_result and dm_result["level_up"]:
        char = game.characters.get(action.player_id)
        if char:
            # Check if they have enough XP to level up
            xp_needed = 100 * char.level
            if char.experience >= xp_needed:
                char.experience -= xp_needed
                char.level += 1
                char.max_hit_points += dm_result.get("hp_increase", 5)
                char.hit_points = char.max_hit_points  # Restore to full HP on level up
                
                # Increase chosen attribute
                attr = dm_result.get("attribute_increased")
                if attr and hasattr(char, attr):
                    current_val = getattr(char, attr)
                    setattr(char, attr, current_val + 1)
    
    # Update character in database if modified
    if game.characters.get(action.player_id):
        db = SessionLocal()
        try:
            char_id = _character_mappings.get(game.game_id, {}).get(action.player_id)
            if char_id:
                update_character(db, char_id, game.characters[action.player_id])
        finally:
            db.close()
    
    dm_response = Event(
        id=str(len(game.logs)+1),
        type="dm_response",
        payload={"message": dm_result["message"]}
    )
    game.logs.append(dm_response)
    
    # Persist game state to database
    db = SessionLocal()
    try:
        save_game(db, game, _character_mappings.get(game.game_id, {}))
    finally:
        db.close()
    
    # advance turn
    if len(game.players) > 0:
        game.turn_index = (game.turn_index + 1) % len(game.players)
    return game
