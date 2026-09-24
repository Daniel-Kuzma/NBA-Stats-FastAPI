from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database import LocalSession
from pydantic import BaseModel
from loader import add_players_game_logs, add_players_to_database, add_teams_game_logs, add_teams_to_database
from seeder import check_active_players, set_all_players_teams, upload_new_player_logs, upload_new_teams_logs
from starlette import status

async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter(
    prefix = "/admin",
    tags = ["admin"]
)

@router.get("/load_historical_data", status_code = status.HTTP_200_OK)
async def load_historical_data(db: db_dependency):
    await add_teams_to_database(db)
    await add_players_to_database(db)
    await add_teams_game_logs(db)
    await add_players_game_logs(db)
    await set_all_players_teams(db)
    await check_active_players(db)
    await upload_new_player_logs(db)
    await upload_new_teams_logs(db)