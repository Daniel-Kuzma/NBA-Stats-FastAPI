from test.utils import *
from routes.admin import get_current_user, get_db
from fastapi import status
import pytest


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user 

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