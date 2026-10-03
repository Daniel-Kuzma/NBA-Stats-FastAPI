from test.utils import *
from routes.admin import get_current_user, get_db
from fastapi import status
import pytest
from sqlalchemy import select
from models import Users
from routes.auth import bcrypt_context

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user 

@pytest.mark.asyncio
async def test_create_new_user(test_data_users):
    request = {"name" : "Adam",
               "last_name" : "Kowal",
               "username" : "kowal123",
               "password" : "password",
               "email" : "kowal@kowal.pl"}
    respons = client.post("/sing-in/create_user", json = request)
    assert respons.status_code == status.HTTP_201_CREATED
    db = TestingSessionLocal()
    stmt = await db.execute(select(Users).where(Users.id == 2).limit(1))
    result = stmt.scalar()
    assert result.name == "Adam"
    assert result.last_name == "Kowal"
    assert result.username == "kowal123"
    assert bcrypt_context.verify("password", result.password) == True
    assert result.email == "kowal@kowal.pl"
    assert result.role == "user"
    assert result.user_status == True

