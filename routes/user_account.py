from fastapi import APIRouter, Depends, HTTPException, Path, Request
from models import Users
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete 
from routes.auth import get_current_user
from starlette import status
from pydantic import BaseModel, Field
from routes.auth import bcrypt_context
from database import get_db
from limiter import limiter
import uuid

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class UserChangeInformationRequest(BaseModel):
    name : str
    last_name : str
    username : str
    email : str

class PasswordRequest(BaseModel):
    old_password : str
    new_password : str

class DeleteUserRequest(BaseModel):
    password : str = Field(description = "Pass password to confirm that you want to delete account")

router = APIRouter()

@router.get("/user-information", status_code = status.HTTP_200_OK)
@limiter.limit("100/minute")
async def show_user_information(db : db_dependency, user : user_dependency, request : Request):
    try:
        stmt = await db.execute(select(Users).where(Users.public_id == uuid.UUID(user.get("id"))).limit(1))
        result = stmt.scalar()
        return {
                "name": result.name,
                "last_name": result.last_name,
                "username": result.username,
                "email": result.email,
                "role": result.role,
                "user_status": "active" if result.user_status else "deactivate"}
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.put("/change-user-information", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def change_user_information(db: db_dependency, user : user_dependency, request_change_info : UserChangeInformationRequest, request : Request):
    try:
        await db.execute(update(Users).where(Users.public_id == uuid.UUID(user.get("id"))).values(
            name = request_change_info.name,
            last_name = request_change_info.last_name,
            username = request_change_info.username,
            email = request_change_info.email
        ))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.put("/change-password", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def change_user_password(db : db_dependency, user : user_dependency, request_password : PasswordRequest, request : Request):
    stmt_password = await db.execute(select(Users.password).where(Users.public_id == uuid.UUID(user.get("id"))).limit(1))
    user_password = stmt_password.scalar()
    if not bcrypt_context.verify(request_password.old_password, user_password):    
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You pass bad password")
    try:        
        hash_new_password = bcrypt_context.hash(request_password.new_password)
        await db.execute(update(Users).where(Users.public_id == uuid.UUID(user.get("id"))).values(password = hash_new_password))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

@router.delete("/delete-user-account", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_user_account(db : db_dependency, user : user_dependency, request_delete : DeleteUserRequest, request : Request):
    stmt_password = await db.execute(select(Users.password).where(Users.public_id == uuid.UUID(user.get("id"))).limit(1))
    user_password = stmt_password.scalar()
    if not bcrypt_context.verify(request_delete.password, user_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You pass bad password")
    try:
        await db.execute(delete(Users).where(Users.public_id == uuid.UUID(user.get("id"))))
        await db.commit()    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected problem: {e}")

