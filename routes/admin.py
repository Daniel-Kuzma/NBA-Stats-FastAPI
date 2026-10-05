from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from pydantic import BaseModel
from loader import add_players_game_logs, add_players_to_database, add_teams_game_logs, add_teams_to_database
from seeder import check_active_players, set_all_players_teams, upload_new_player_logs, upload_new_teams_logs
from starlette import status
from routes.auth import get_current_user
from sqlalchemy import select, update, delete
from models import Users, StatusTLog
from enum import Enum
from database import get_db
from limiter import limiter
import uuid

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter()

class UserRoleEnum(str, Enum):
    admin = "admin"
    user = "user"

@router.get("/load_historical_data", status_code = status.HTTP_200_OK)
@limiter.limit("100/minute")
async def load_historical_data(user: user_dependency, db: db_dependency, request : Request):
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

@router.put("/change-user-status/{user_public_id}", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("300/minute")
async def change_user_status(db : db_dependency, user : user_dependency, user_public_id : uuid.UUID, new_user_status : bool, request : Request):
    
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
    stmt = await db.execute(select(Users).filter(Users.public_id == user_public_id).limit(1))
    result = stmt.scalar()
    if result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
    try:
        await db.execute(update(Users).where(Users.public_id == user_public_id).values(user_status = new_user_status))
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.put("/change-user-role/{user_public_id}", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("300/minute")
async def change_user_role(user : user_dependency, db : db_dependency, user_public_id : uuid.UUID, new_user_role : UserRoleEnum, request : Request):
    
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
    stmt = await db.execute(select(Users).filter(Users.public_id == user_public_id).limit(1))
    result = stmt.scalar()
    if result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
    try:
        await db.execute(update(Users).where(Users.public_id == user_public_id).values(role = new_user_role))
        await db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.get("/all-users", status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def get_all_user(db : db_dependency, user : user_dependency, request : Request):
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
    try:
        stmt = await db.execute(select(Users))
        result = stmt.scalars()
        return result.all()
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.delete("/delete-user/{user_public_id}", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("300/minute")
async def delete_user(db : db_dependency, user : user_dependency, user_public_id : uuid.UUID, request : Request):
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
    stmt = await db.execute(select(Users).filter(Users.public_id == user_public_id).limit(1))
    result = stmt.scalar()
    if result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")
    try:
        await db.execute(delete(Users).where(Users.public_id == user_public_id))
        await db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.get("/status-logs-from-data-base", status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def get_status_logs(user : user_dependency, db : db_dependency, request : Request):
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")
    try: 
        stmt_logs = await db.execute(select(StatusTLog))
        result = stmt_logs.scalars()
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpect error: {e}")