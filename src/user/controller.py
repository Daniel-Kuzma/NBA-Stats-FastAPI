from fastapi import APIRouter, Request
from starlette import status
from database.core import db_dependency
from auth.service import user_dependency
from core.limiter import limiter
from .service import *
from .schemas import *

router = APIRouter()

@router.get("/user-information", response_model = UserInformationResponse, status_code = status.HTTP_200_OK)
@limiter.limit("100/minute")
async def show_user_information(db : db_dependency, user : user_dependency, request : Request):
    return await get_user_information(db, user)

@router.put("/change-user-information", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def change_user_information(db: db_dependency, user : user_dependency, request_change_info : UserChangeInformationRequest, request : Request):
    return await set_new_user_information(request_change_info, db, user)

@router.put("/change-password", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def change_user_password(db : db_dependency, user : user_dependency, request_password : PasswordRequest, request : Request):
    return await set_new_user_password(request_password, db, user)

@router.delete("/delete-user-account", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def delete_user_account(db : db_dependency, user : user_dependency, request_delete : DeleteUserRequest, request : Request):
    return await delete_user(request_delete, db, user)