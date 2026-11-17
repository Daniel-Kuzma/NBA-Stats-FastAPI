from test.utils import *
from database.core import get_db
from auth.service import get_current_user
from fastapi import status
import pytest
from sqlalchemy import select
from database.models import Users

app.dependency_overrides[get_db] = override_get_db

@pytest.mark.asyncio
async def test_login(test_data_users):
    request = {"username" : "jan123", "password" : "password"}
    respons = client.post("/token", data = request)
    respons_data = respons.json()
    assert "access_token" in respons_data
    assert respons_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_with_bad_username(test_data_users):
    request = {"username" : "jan123123", "password" : "password"}
    respons = client.post("/token", data = request)
    assert respons.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_login_with_bad_password(test_data_users):
    request = {"username" : "jan123", "password" : "password123"}
    respons = client.post("/token", data = request)
    assert respons.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_create_new_user(test_data_users):
    request = {"name" : "Adam",
               "last_name" : "Kowal",
               "username" : "kowal123",
               "password" : "password",
               "email" : "kowal@kowal.pl"}
    respons = client.post("/create_user", json = request)
    assert respons.status_code == status.HTTP_201_CREATED
    db = TestingSessionLocal()
    stmt = await db.execute(select(Users).where(Users.id == 3).limit(1))
    result = stmt.scalar()
    assert result.name == "Adam"
    assert result.last_name == "Kowal"
    assert result.username == "kowal123"
    assert bcrypt_context.verify("password", result.password) == True
    assert result.email == "kowal@kowal.pl"
    assert result.role == "user"
    assert result.user_status == True
