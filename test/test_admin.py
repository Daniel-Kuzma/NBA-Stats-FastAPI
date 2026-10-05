from test.utils import *
from routes.admin import get_current_user, get_db
from fastapi import status
from models import Users, StatusTLog
import pytest
from sqlalchemy import select


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user 

@pytest.mark.asyncio
async def test_access_to_admin_page(test_data_users):
    app.dependency_overrides[get_current_user] = lambda : {"username": "jan123", "id": 1, "role": "user"}
    request_1 = {"new_user_status" : False}
    request_2 = {"new_user_role" : "user"}
    respons_1 = client.put("/admin/change-user-status/07c206d2-3449-451a-9cd7-86a10f6ec18f", params = request_1)
    respons_2 = client.put("/admin/change-user-role/07c206d2-3449-451a-9cd7-86a10f6ec18f", params = request_2)
    respons_3 = client.get("/admin/all-users")
    respons_4 = client.delete("/admin/delete-user/07c206d2-3449-451a-9cd7-86a10f6ec18f")
    respons_5 = client.get("/admin/status-logs-from-data-base")
    try: 
        assert respons_1.status_code == status.HTTP_401_UNAUTHORIZED
        assert respons_2.status_code == status.HTTP_401_UNAUTHORIZED
        assert respons_3.status_code == status.HTTP_401_UNAUTHORIZED
        assert respons_4.status_code == status.HTTP_401_UNAUTHORIZED
        assert respons_5.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        app.dependency_overrides[get_current_user] = override_get_current_user 

@pytest.mark.asyncio
async def test_change_user_status(test_data_users):
    request = {"new_user_status" : False}
    respons = client.put("/admin/change-user-status/07c206d2-3449-451a-9cd7-86a10f6ec18f", params = request)
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = await db.execute(select(Users).where(Users.public_id == uuid.UUID("07c206d2-3449-451a-9cd7-86a10f6ec18f")).limit(1))
    result = model.scalar()
    assert result.user_status == False

@pytest.mark.asyncio
async def test_change_user_status_with_noexist_user(test_data_users):
    request = {"new_user_status" : False}
    respons = client.put("/admin/change-user-status/aacb0872-ebd0-45a7-b86a-b15c9e3c2bb7", params = request)
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_change_user_role(test_data_users):
    request = {"new_user_role" : "user"}
    respons = client.put("/admin/change-user-role/07c206d2-3449-451a-9cd7-86a10f6ec18f", params = request)
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = await db.execute(select(Users.role).where(Users.public_id == uuid.UUID("07c206d2-3449-451a-9cd7-86a10f6ec18f")).limit(1))
    result = model.scalar()
    assert result == "user"

@pytest.mark.asyncio
async def test_change_user_role_with_noexist_user(test_data_users):
    request = {"new_user_role" : "user"}
    respons = client.put("/admin/change-user-role/aacb0872-ebd0-45a7-b86a-b15c9e3c2bb7", params = request)
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_get_all_users(test_data_users):
    respons = client.get("/admin/all-users")
    assert respons.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_user(test_data_users):
    respons = client.delete("/admin/delete-user/07c206d2-3449-451a-9cd7-86a10f6ec18f")
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = await db.execute(select(Users).where(Users.public_id == uuid.UUID("07c206d2-3449-451a-9cd7-86a10f6ec18f")).limit(1))
    result = model.one_or_none()
    assert result == None

@pytest.mark.asyncio
async def test_delete_user_with_noexist_user(test_data_users):
    respons = client.delete("/admin/delete-user/aacb0872-ebd0-45a7-b86a-b15c9e3c2bb7")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_get_status_logs(test_data_logs):
    respons = client.get("/admin/status-logs-from-data-base")
    assert respons.status_code == status.HTTP_200_OK
