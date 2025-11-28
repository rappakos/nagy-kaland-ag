from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import uuid4


class Player(BaseModel):
    id: str
    name: str


class Action(BaseModel):
    player_id: str
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    id: str
    type: str
    payload: Dict[str, Any]


class GameState(BaseModel):
    game_id: str
    players: List[Player] = []
    turn_index: int = 0
    logs: List[Event] = []
    meta: Dict[str, Any] = {}

    @classmethod
    def create(cls, players: Optional[List[Player]] = None):
        gid = str(uuid4())
        return cls(game_id=gid, players=players or [], turn_index=0, logs=[], meta={})
