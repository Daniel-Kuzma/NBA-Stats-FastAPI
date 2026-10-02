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
    respons_1 = client.put("/admin/change-user-status/1", params = request_1)
    respons_2 = client.put("/admin/change-user-role/1", params = request_2)
    respons_3 = client.get("/admin/all_user")
    respons_4 = client.delete("/admin/delete-user/1")
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
    respons = client.put("/admin/change-user-status/1", params = request)
    assert respons.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = await db.execute(select(Users).where(Users.id == 1).limit(1))
    result = model.scalar()
    assert result.user_status == False

@pytest.mark.asyncio
async def test_change_user_status_with_noexist_user(test_data_users):
    request = {"new_user_status" : False}
    respons = client.put("/admin/change-user-status/999", params = request)
    assert respons.status_code == status.HTTP_400_BAD_REQUEST




