from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import uuid4


class Player(BaseModel):
    id: str
    name: str


class Character(BaseModel):
    """D&D style character sheet"""
    name: str
    class_type: str  # Warrior, Mage, Rogue, Cleric, etc.
    level: int = 1
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    hit_points: int = 10
    backstory: Optional[str] = None


class Action(BaseModel):
    player_id: str
    message: str


class Event(BaseModel):
    id: str
    type: str
    payload: Dict[str, Any]


class GameState(BaseModel):
    game_id: str
    players: List[Player] = []
    characters: Dict[str, Optional[Character]] = {}  # player_id -> Character
    turn_index: int = 0
    logs: List[Event] = []
    meta: Dict[str, Any] = {}

    @classmethod
    def create(cls, players: Optional[List[Player]] = None):
        gid = str(uuid4())
        # Initialize empty character slots for each player
        characters = {p.id: None for p in (players or [])}
        return cls(game_id=gid, players=players or [], characters=characters, turn_index=0, logs=[], meta={})
