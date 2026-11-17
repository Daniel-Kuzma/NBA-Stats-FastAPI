from fastapi import Depends, HTTPException
from typing import Annotated
from database.core import db_dependency
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from core.settings import settings
from database.models import Users
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
import jwt
from jwt.exceptions import InvalidTokenError 
from .schemas import RequestUser
from sqlalchemy.ext.asyncio import AsyncSession

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

async def authenticate_user(user : str, password : str, db : db_dependency):
    stm = await db.execute(select(Users).where(Users.username == user))
    user_responds = stm.scalar()
    if user_responds is None:
        return False
    if bcrypt_context.verify(password, user_responds.password) == False:
        return False 
    if not user_responds.user_status:
        return False
    return user_responds

async def create_jwt_token(username : str, id : str, private_id : int, role : str, expired_time : timedelta):
    payload = {"username" : username, "id" : id, "private_id" : private_id, "role" : role}
    time_to_expired = datetime.now(timezone.utc) + timedelta(minutes = expired_time)
    payload.update({"exp" : time_to_expired})
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

async def get_current_user(token : Annotated[str, Depends(oauth2_scheme)]):
    try:
        user = jwt.decode(token, SECRET_KEY, ALGORITHM)
        username : str = user.get("username")
        id : str = user.get("id")
        role : str = user.get("role")
        private_id : int = user.get("private_id")
        if username is None or id is None or role is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not valid user")
        return {"username" : username, "id" : id, "role" : role, "private_id" : private_id}
    except InvalidTokenError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not valid user")

user_dependency = Annotated[dict, Depends(get_current_user)]

async def create_user_account(request_user : RequestUser, db : AsyncSession):
    try:
        new_user = Users(name = request_user.name,
                        last_name = request_user.last_name,
                        username = request_user.username,
                        password = bcrypt_context.hash(request_user.password),
                        email = request_user.email,
                        role = request_user.role)
        db.add(new_user)
        await db.commit()
        return {"message" : "Successfully created user account"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = f"Can not create user: {e}")