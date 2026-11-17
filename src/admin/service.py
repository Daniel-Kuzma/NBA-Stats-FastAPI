from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.loader import *
from core.seeder import *
from database.models import Users, StatusTLog
from .schemas import UserRoleEnum
from sqlalchemy import delete, desc
from starlette import status


async def user_role_check(user):
    if user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have not access to this endpoint")

async def check_user_id(user_public_id, db : AsyncSession):
    stmt = await db.execute(select(Users).filter(Users.public_id == user_public_id).limit(1))
    result = stmt.scalar()
    if result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User with this id dose not exist")

async def load_data(user, db : AsyncSession):
    await user_role_check(user)
    try:
        await add_teams_to_database(db)
        await add_players_to_database(db)
        await add_teams_game_logs(db)
        await add_players_game_logs(db)
        await set_all_players_teams(db)
        await check_active_players(db)
        await upload_new_player_logs(db)
        await upload_new_teams_logs(db)
        return {"message" : "Successfully updated data"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")


async def set_new_user_status(user_public_id, new_user_status : bool, db : AsyncSession, user):
    await user_role_check(user)
    await check_user_id(user_public_id, db)
    try:
        await db.execute(update(Users).where(Users.public_id == user_public_id).values(user_status = new_user_status))
        await db.commit()
        return {"message" : "Successfully changed user status"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

async def set_new_user_role(user_public_id, new_user_role : UserRoleEnum, db : AsyncSession, user):
    await user_role_check(user)
    await check_user_id(user_public_id, db)
    try:
        await db.execute(update(Users).where(Users.public_id == user_public_id).values(role = new_user_role))
        await db.commit()
        return {"message" : "Successfully changed user role"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

async def show_all_users(db : AsyncSession, user):
    await user_role_check(user)
    try:
        stmt = await db.execute(select(Users))
        result = stmt.scalars().all()
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

async def delete_user_account(user_public_id, db : AsyncSession, user):
    await user_role_check(user)
    await check_user_id(user_public_id, db)
    try:
        await db.execute(delete(Users).where(Users.public_id == user_public_id))
        await db.commit()
        return {"message" : "Successfully deleted user"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

async def get_all_status_logs(db : AsyncSession, user):
    await user_role_check(user)
    try: 
        stmt_logs = await db.execute(select(StatusTLog).order_by(desc(StatusTLog.date)))
        result = stmt_logs.scalars().all()
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpect error: {e}")    
