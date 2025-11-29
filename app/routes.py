from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from .models import GameState, Player, Action
from .store import create_game, get_game, apply_action

router = APIRouter(tags=["games"])


class CreateGameRequest(BaseModel):
    player_names: Optional[List[str]] = None


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
