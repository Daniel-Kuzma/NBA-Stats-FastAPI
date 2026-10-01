from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database import LocalSession
from pydantic import BaseModel
from loader import add_players_game_logs, add_players_to_database, add_teams_game_logs, add_teams_to_database
from seeder import check_active_players, set_all_players_teams, upload_new_player_logs, upload_new_teams_logs
from starlette import status
from routes.auth import get_current_user
from sqlalchemy import select, update, delete
from models import Users, StatusTLog
from enum import Enum

async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter()

class UserRoleEnum(str, Enum):
    admin = "admin"
    user = "user"

@router.get("/load_historical_data", status_code = status.HTTP_200_OK)
async def load_historical_data(user: user_dependency, db: db_dependency):
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
        await add_teams_to_database(db)
        await add_players_to_database(db)
        await add_teams_game_logs(db)
        await add_players_game_logs(db)
        await set_all_players_teams(db)
        await check_active_players(db)
        await upload_new_player_logs(db)
        await upload_new_teams_logs(db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.put("/change-user-status/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
async def change_user_status(db : db_dependency, user : user_dependency, user_id : int, new_user_status : bool):
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
        stmt = await db.execute(select(Users).filter(Users.id == user_id).limit(1))
        result = stmt.scalars()
        if result is None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
        await db.execute(update(Users).where(Users.id == user_id).values(user_status = new_user_status))
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.put("/change-user-role/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
async def change_user_role(user : user_dependency, db : db_dependency, user_id : int, new_user_role : UserRoleEnum):
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
        stmt = await db.execute(select(Users).filter(Users.id == user_id).limit(1))
        result = stmt.scalars()
        if result is None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
        await db.execute(update(Users).where(Users.id == user_id).values(role = new_user_role))
        await db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.get("/all_user", status_code = status.HTTP_200_OK)
async def get_all_user(db : db_dependency, user : user_dependency):
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
        stmt = await db.execute(select(Users))
        result = stmt.scalars()
        return result.all()
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.delete("/delete-user{user_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_user(db : db_dependency, user : user_dependency, user_id : int):
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
        stmt = await db.execute(select(Users).filter(Users.id == user_id).limit(1))
        result = stmt.scalar()
        if result is None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
        await db.execute(delete(Users).where(Users.id == user_id))
        await db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.get("status-logs-from-data-base", status_code = status.HTTP_200_OK)
async def get_status_logs(user : user_dependency, db : db_dependency):
    if user.get("role") == "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
    stmt_logs = await db.execute(select(StatusTLog))
    result = stmt_logs.scalars()
    return result