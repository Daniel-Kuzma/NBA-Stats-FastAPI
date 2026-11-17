from fastapi import HTTPException
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy import select, update, delete
from database.models import Users
from .schemas import UserChangeInformationRequest, PasswordRequest, DeleteUserRequest
from auth.service import bcrypt_context


async def get_user_information(db : AsyncSession, user):
    try:
        stmt = await db.execute(select(Users).where(Users.public_id == uuid.UUID(user.get("id"))).limit(1))
        result = stmt.scalar()
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

async def set_new_user_information(request_change_info : UserChangeInformationRequest, db : AsyncSession, user):
    try:
        await db.execute(update(Users).where(Users.public_id == uuid.UUID(user.get("id"))).values(
            name = request_change_info.name,
            last_name = request_change_info.last_name,
            username = request_change_info.username,
            email = request_change_info.email
        ))
        await db.commit()
        return {"message" : "Successfully changed user information"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

async def set_new_user_password(request_password : PasswordRequest, db : AsyncSession, user):
    stmt_password = await db.execute(select(Users.password).where(Users.public_id == uuid.UUID(user.get("id"))).limit(1))
    user_password = stmt_password.scalar()
    if not bcrypt_context.verify(request_password.old_password, user_password):    
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You pass bad password")
    try:        
        hash_new_password = bcrypt_context.hash(request_password.new_password)
        await db.execute(update(Users).where(Users.public_id == uuid.UUID(user.get("id"))).values(password = hash_new_password))
        await db.commit()
        return {"message" : "Successfully changed user password"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")    

async def delete_user(request_delete : DeleteUserRequest, db : AsyncSession, user):
    stmt_password = await db.execute(select(Users.password).where(Users.public_id == uuid.UUID(user.get("id"))).limit(1))
    user_password = stmt_password.scalar()
    if not bcrypt_context.verify(request_delete.password, user_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You pass bad password")
    try:
        await db.execute(delete(Users).where(Users.public_id == uuid.UUID(user.get("id"))))
        await db.commit()
        return {"message" : "Successfully deleted user account"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")