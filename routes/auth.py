from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from pydantic import BaseModel
from typing import Annotated
from passlib.context import CryptContext
# from jose import jwt, JWTError
from fastapi.security import OAuth2AuthorizationCodeBearer
from settings import settings
from database import LocalSession
from models import Users

# test1234
SECRET_KEY = settings.secret_key

bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter()
class RequestUser(BaseModel):
    name : str = Path(min_length = 3)
    last_name : str = Path(min_length = 1)
    username : str = Path(min_length = 3)
    password : str = Path(min_length = 8)
    email : str = Path(min_length = 3)

@router.post("/create_user", status_code = status.HTTP_201_CREATED)
async def create_new_user(db:db_dependency, request: RequestUser):
    try:
        new_user = Users(name = request.name,
                        last_name = request.last_name,
                        username = request.username,
                        password = bcrypt_context.hash(request.password),
                        email = request.email)
        db.add(new_user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = f"Can not create user: {e}")




