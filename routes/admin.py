from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database import LocalSession
from pydantic import BaseModel
from loader import add_players_game_logs, add_players_to_database, add_teams_game_logs, add_teams_to_database
from seeder import check_active_players, set_all_players_teams, upload_new_player_logs, upload_new_teams_logs
from starlette import status
from routes.auth import get_current_user
from sqlalchemy import select, update 
from models import Users

async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter()

@router.get("/load_historical_data", status_code = status.HTTP_200_OK)
async def load_historical_data(user: user_dependency, db: db_dependency):
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this page")
    await add_teams_to_database(db)
    await add_players_to_database(db)
    await add_teams_game_logs(db)
    await add_players_game_logs(db)
    await set_all_players_teams(db)
    await check_active_players(db)
    await upload_new_player_logs(db)
    await upload_new_teams_logs(db)

@router.put("change-user-status/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
async def change_user_status(db : db_dependency, user : user_dependency, user_id : int, new_user_status : bool):
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this page")
    stmt = await db.execute(select(Users).filter(Users.id == user_id).limit(1))
    result = stmt.scalars()
    if result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
    await db.execute(update(Users).where(Users.id == user_id).values(user_status = new_user_status))
    await db.commit()
    # return {"user_id" : user_id, "username" : result.username, "is_active" : result.user_status}