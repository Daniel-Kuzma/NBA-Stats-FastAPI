from fastapi import APIRouter, Depends, HTTPException, Path
from database import LocalSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from starlette import status
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from routes.auth import get_current_user
from models import UserFavoritePlayer, UserFavoriteTeam, Players


async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter()

@router.post("/add-favorite-player/{display_name}", status_code = status.HTTP_201_CREATED)
async def add_favorite_player(db : db_dependency, user : user_dependency, display_name : str):
    try:
        stmt_player_id = await db.execute(select(Players.player_id).where(Players.display_name == display_name).limit(1))
        result_player_id = stmt_player_id.scalar()
        if result_player_id is None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Player is not exists")
        
        stmt_check_user_favorite_players = await db.execute(select(UserFavoritePlayer).where(UserFavoritePlayer.player_id == result_player_id, UserFavoritePlayer.user_id == user.get("id")).limit(1))
        check = stmt_check_user_favorite_players.scalar()
        if check is not None:
            raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This player is added into your favorite players")

        new_favorite_player = UserFavoritePlayer(user_id = user.get("id"), player_id = result_player_id)
        db.add(new_favorite_player)
        await db.commit()

        return {"detail" : "Successfully added new favorite player"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = f"Unexpected error: {e}")


