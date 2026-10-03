from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from pydantic import BaseModel
from typing import Annotated
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from settings import settings
from models import Users
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from database import get_db

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

db_dependency = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter()

class Token(BaseModel):
    access_token : str
    token_type : str 

class LoginInRequest(BaseModel):
    username : str
    password : str

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

async def create_jwt_token(username : str, id : int, role : str, expired_time : timedelta):
    payload = {"username" : username, "id" : id, "role" : role}
    time_to_expired = datetime.now(timezone.utc) + timedelta(minutes = expired_time)
    payload.update({"exp" : time_to_expired})
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

async def get_current_user(token : Annotated[str, Depends(oauth2_scheme)]):
    try:
        user = jwt.decode(token, SECRET_KEY, ALGORITHM)
        username : str = user.get("username")
        id : str = user.get("id")
        role : str = user.get("role")
        if username is None or id is None or role is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not valid user")
        return {"username" : username, "id" : id, "role" : role}
    except InvalidTokenError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not valid user")

@router.post("/token", response_model = Token)
async def login(request : Annotated[OAuth2PasswordRequestForm, Depends()], db : db_dependency):
    login_user = await authenticate_user(request.username, request.password, db)
    if not login_user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Password or Username is incorrect")
    token = await create_jwt_token(login_user.username, login_user.id, login_user.role, 30)
    return {"access_token" : token, "token_type" : "bearer"}








    




