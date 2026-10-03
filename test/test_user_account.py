from test.utils import *
from routes.admin import get_current_user, get_db
from fastapi import status
from models import Users, StatusTLog
import pytest
from sqlalchemy import select
from routes.auth import bcrypt_context

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user 

@pytest.mark.asyncio
async def test_change_user_status(test_data_users):
    respons = client.get("/account/user-information")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json() == {"name": "Jan",
                              "last_name": "Kowalski",
                              "username": "jan123",
                              "email": "jan@jan.pl",
                              "role": "admin",
                              "user_status": "active"}

@pytest.mark.asyncio
async def test_change_user_information(test_data_users):
    request = {"name" : "Jan",
               "last_name" : "Kowalski",
               "username" : "jan1234567", 
               "email" : "jan@jan.pl"}
    respons = client.put("/account/change-user-information", json = request)
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    stmt = await db.execute(select(Users).where(Users.id == 1).limit(1))
    result = stmt.scalar()
    assert result.username == "jan1234567"

@pytest.mark.asyncio
async def test_change_user_password(test_data_users):
    request = {"old_password" : "password",
               "new_password" : "password1"}
    respons = client.put("/account/change-password", json = request)
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    
    db = TestingSessionLocal()
    stmt = await db.execute(select(Users).where(Users.id == 1).limit(1))
    result = stmt.scalar()
    assert bcrypt_context.verify("password1", result.password) == True

@pytest.mark.asyncio
async def test_change_user_status_with_bad_password(test_data_users):
    request = {"old_password" : "password123",
               "new_password" : "password1"}
    respons = client.put("/account/change-password", json = request)
    assert respons.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_delete_user_account(test_data_users):
    request = {"password" : "password"}
    respons = client.request("DELETE", "/account/delete-user-account", json = request)
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    stmt = await db.execute(select(Users))
    result = stmt.scalars()
    assert result.all() == []

@pytest.mark.asyncio
async def test_delete_user_account_with_bad_password(test_data_users):
    request = {"password" : "password123"}
    respons = client.request("DELETE", "/account/delete-user-account", json = request)
    assert respons.status_code == status.HTTP_401_UNAUTHORIZED