from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from .models import GameState, Player, Action
from .store import create_game, get_game, apply_action
from .database import get_db
from .persistence import list_characters, get_character, save_character
from .models import Character

router = APIRouter(tags=["games"])


class CreateGameRequest(BaseModel):
    player_names: Optional[List[str]] = None


class SelectCharacterRequest(BaseModel):
    character_id: str


@router.post("/games")
async def create_game_endpoint(body: CreateGameRequest):
    game = create_game(player_names=body.player_names)
    return {"game_id": game.game_id, "players": [{"id": p.id, "name": p.name} for p in game.players]}


@router.get("/games/{game_id}")
async def get_game_endpoint(game_id: str):
    game = get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("/games/{game_id}/action")
async def post_action_endpoint(game_id: str, action: Action):
    game = apply_action(game_id, action)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/characters/{player_name}")
async def list_characters_endpoint(player_name: str, db: Session = Depends(get_db)):
    """List all characters for a player"""
    characters = list_characters(db, player_name)
    return {"player_name": player_name, "characters": characters}


@router.get("/characters/{player_name}/{character_id}")
async def get_character_endpoint(player_name: str, character_id: str, db: Session = Depends(get_db)):
    """Get detailed character information"""
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.post("/games/{game_id}/select-character/{player_id}")
async def select_character_endpoint(
    game_id: str, 
    player_id: str, 
    body: SelectCharacterRequest,
    db: Session = Depends(get_db)
):
    """
    Select/assign a character to a player in a game.
    This allows players to choose from their existing characters.
    """
    from .store import assign_character_to_game
    
    # Verify character exists
    character = get_character(db, body.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Assign character to game
    game = assign_character_to_game(game_id, player_id, body.character_id, character)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {"message": "Character assigned", "game_id": game_id, "player_id": player_id, "character": character}
