from fastapi import APIRouter, Request, Depends
from core.limiter import limiter
from database.core import db_dependency, get_db
from auth.service import user_dependency
from .service import *
from .schemas import *
import uuid
from starlette import status

router = APIRouter()

@router.get("/load_historical_data", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("100/minute")
async def load_historical_data(user: user_dependency, db: db_dependency, request : Request):
    return await load_data(user, db)

@router.put("/change-user-status/{user_public_id}", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def change_user_status(db : db_dependency, user : user_dependency, user_public_id : uuid.UUID, new_user_status : bool, request : Request):
    return await set_new_user_status(user_public_id, new_user_status, db, user)

@router.put("/change-user-role/{user_public_id}", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def change_user_role(user : user_dependency, db : db_dependency, user_public_id : uuid.UUID, new_user_role : UserRoleEnum, request : Request):
    return await set_new_user_role(user_public_id, new_user_role, db, user)

@router.get("/all-users", response_model = list[AllUsersRespond], status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def get_all_user(db : db_dependency, user : user_dependency, request : Request):
    return await show_all_users(db, user)

@router.delete("/delete-user/{user_public_id}", response_model = SuccessMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def delete_user(db : db_dependency, user : user_dependency, user_public_id : uuid.UUID, request : Request):
    return await delete_user_account(user_public_id, db, user)

@router.get("/status-logs-about-data-load", response_model = list[DataLogsRespond], status_code = status.HTTP_200_OK)
@limiter.limit("300/minute")
async def get_status_logs(user : user_dependency, db : db_dependency, request : Request):
    return await get_all_status_logs(db, user)