from fastapi import APIRouter, HTTPException, Path, Depends
from starlette import status
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from routes.auth import bcrypt_context
from models import Users

db_dependency = Annotated[AsyncSession, Depends(get_db)]

class RequestUser(BaseModel):
    name : str = Path(min_length = 3)
    last_name : str = Path(min_length = 1)
    username : str = Path(min_length = 3)
    password : str = Path(min_length = 8)
    email : str = Path(min_length = 3)

router = APIRouter()

@router.post("/create_user", status_code = status.HTTP_201_CREATED)
async def create_new_user(db : db_dependency, request : RequestUser):
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