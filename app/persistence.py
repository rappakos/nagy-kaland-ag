"""
Persistence layer for storing and retrieving game data and characters
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from .database import DBGame, DBCharacter, DBGameCharacter
from .models import GameState, Character, Player, Event
from uuid import uuid4


def save_character(db: Session, character: Character, player_name: str) -> str:
    """
    Save or update a character to the database.
    Returns the character ID.
    """
    char_id = str(uuid4())
    db_char = DBCharacter(
        id=char_id,
        player_name=player_name,
        name=character.name,
        class_type=character.class_type,
        level=character.level,
        experience=character.experience,
        strength=character.strength,
        dexterity=character.dexterity,
        constitution=character.constitution,
        intelligence=character.intelligence,
        wisdom=character.wisdom,
        charisma=character.charisma,
        hit_points=character.hit_points,
        max_hit_points=character.max_hit_points,
        backstory=character.backstory
    )
    db.add(db_char)
    db.commit()
    db.refresh(db_char)
    return db_char.id


def update_character(db: Session, character_id: str, character: Character):
    """Update an existing character in the database"""
    db_char = db.query(DBCharacter).filter(DBCharacter.id == character_id).first()
    if db_char:
        db_char.name = character.name
        db_char.class_type = character.class_type
        db_char.level = character.level
        db_char.experience = character.experience
        db_char.strength = character.strength
        db_char.dexterity = character.dexterity
        db_char.constitution = character.constitution
        db_char.intelligence = character.intelligence
        db_char.wisdom = character.wisdom
        db_char.charisma = character.charisma
        db_char.hit_points = character.hit_points
        db_char.max_hit_points = character.max_hit_points
        db_char.backstory = character.backstory
        db.commit()


def get_character(db: Session, character_id: str) -> Optional[Character]:
    """Retrieve a character from the database by ID"""
    db_char = db.query(DBCharacter).filter(DBCharacter.id == character_id).first()
    if not db_char:
        return None
    
    return Character(
        name=db_char.name,
        class_type=db_char.class_type,
        level=db_char.level,
        experience=db_char.experience,
        strength=db_char.strength,
        dexterity=db_char.dexterity,
        constitution=db_char.constitution,
        intelligence=db_char.intelligence,
        wisdom=db_char.wisdom,
        charisma=db_char.charisma,
        hit_points=db_char.hit_points,
        max_hit_points=db_char.max_hit_points,
        backstory=db_char.backstory
    )


def list_characters(db: Session, player_name: str) -> List[Dict]:
    """List all characters for a player"""
    db_chars = db.query(DBCharacter).filter(DBCharacter.player_name == player_name).all()
    return [
        {
            "id": char.id,
            "name": char.name,
            "class_type": char.class_type,
            "level": char.level,
            "created_at": char.created_at.isoformat()
        }
        for char in db_chars
    ]


def save_game(db: Session, game_state: GameState, character_mappings: Dict[str, str]):
    """
    Save game state to database.
    character_mappings: dict of player_id -> character_id
    """
    # Save or update game
    db_game = db.query(DBGame).filter(DBGame.game_id == game_state.game_id).first()
    
    logs_json = [
        {
            "id": log.id,
            "type": log.type,
            "payload": log.payload
        }
        for log in game_state.logs
    ]
    
    if db_game:
        # Update existing
        db_game.turn_index = game_state.turn_index
        db_game.logs = logs_json
        db_game.meta = game_state.meta
    else:
        # Create new
        db_game = DBGame(
            game_id=game_state.game_id,
            turn_index=game_state.turn_index,
            logs=logs_json,
            meta=game_state.meta
        )
        db.add(db_game)
    
    db.commit()
    
    # Update character mappings
    # Remove old mappings
    db.query(DBGameCharacter).filter(DBGameCharacter.game_id == game_state.game_id).delete()
    
    # Add new mappings
    for player_id, char_id in character_mappings.items():
        if char_id:
            db_game_char = DBGameCharacter(
                game_id=game_state.game_id,
                character_id=char_id,
                player_id=player_id
            )
            db.add(db_game_char)
    
    db.commit()


def load_game(db: Session, game_id: str) -> Optional[tuple[GameState, Dict[str, str]]]:
    """
    Load game state from database.
    Returns (GameState, character_mappings) or None
    """
    db_game = db.query(DBGame).filter(DBGame.game_id == game_id).first()
    if not db_game:
        return None
    
    # Load game characters
    game_chars = db.query(DBGameCharacter).filter(DBGameCharacter.game_id == game_id).all()
    
    # Build character mappings and load characters
    character_mappings = {}
    characters = {}
    players = []
    
    for gc in game_chars:
        character_mappings[gc.player_id] = gc.character_id
        char = get_character(db, gc.character_id)
        characters[gc.player_id] = char
        players.append(Player(id=gc.player_id, name=gc.character.player_name))
    
    # Reconstruct events
    logs = [
        Event(id=log["id"], type=log["type"], payload=log["payload"])
        for log in db_game.logs
    ]
    
    game_state = GameState(
        game_id=db_game.game_id,
        players=players,
        characters=characters,
        turn_index=db_game.turn_index,
        logs=logs,
        meta=db_game.meta
    )
    
    return game_state, character_mappings
