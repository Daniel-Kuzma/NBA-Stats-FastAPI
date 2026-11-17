from fastapi import APIRouter, HTTPException, Depends, Request
from starlette import status
from core.limiter import limiter
from .service import authenticate_user, create_jwt_token, create_user_account
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from database.core import db_dependency
from .schemas import *

router = APIRouter()

@router.post("/token", response_model = Token)
@limiter.limit("5/minute")
async def login(request_token : Annotated[OAuth2PasswordRequestForm, Depends()], db : db_dependency, request : Request):
    login_user = await authenticate_user(request_token.username, request_token.password, db)
    if not login_user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Password or Username is incorrect")
    token = await create_jwt_token(login_user.username, str(login_user.public_id), login_user.id, login_user.role, 30)
    return {"access_token" : token, "token_type" : "bearer"}

@router.post("/create_user", response_model = SuccessMessageResponse, status_code = status.HTTP_201_CREATED)
@limiter.limit("2/minute")
async def create_new_user(db : db_dependency, request_user : RequestUser, request : Request):
    return await create_user_account(request_user, db)