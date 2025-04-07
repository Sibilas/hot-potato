import json
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient

from src.enroll.enroll import create_app
from src.database.database import db_manager

# Fixture to clear the enrollments table before and after each test.
@pytest.fixture(autouse=True)
def clear_db():
    db_manager.execute("DELETE FROM enrollments")
    yield
    db_manager.execute("DELETE FROM enrollments")

@pytest.fixture
async def client(aiohttp_client) -> TestClient:
    app = create_app()
    return await aiohttp_client(app)

@pytest.mark.asyncio
async def test_post_enroll_success(client):
    payload = {
        "queue": "chat.test",
        "target_url": "http://example.com/api",
        "subscription_args": {"durable": True}
    }
    resp = await client.post("/enroll", json=payload)
    assert resp.status == 201
    data = await resp.json()
    assert "id" in data
    assert data["queue"] == payload["queue"]
    assert data["target_url"] == payload["target_url"]
    assert data["subscription_args"] == payload["subscription_args"]

@pytest.mark.asyncio
async def test_post_enroll_invalid_json(client):
    # Sending a non-JSON payload with the proper header.
    resp = await client.post("/enroll", data="not a json", headers={"Content-Type": "application/json"})
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data

@pytest.mark.asyncio
async def test_post_enroll_missing_field(client):
    # Missing the required 'target_url' field.
    payload = {
        "queue": "chat.test",
        "subscription_args": {"durable": True}
    }
    resp = await client.post("/enroll", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "target_url" in data["error"]

@pytest.mark.asyncio
async def test_get_enrollments(client):
    # Create an enrollment first.
    payload = {
        "queue": "chat.test",
        "target_url": "http://example.com/api",
        "subscription_args": {"durable": True}
    }
    post_resp = await client.post("/enroll", json=payload)
    assert post_resp.status == 201

    # Retrieve enrollments.
    get_resp = await client.get("/enrollments")
    assert get_resp.status == 200
    enrollments = await get_resp.json()
    assert isinstance(enrollments, list)
    assert len(enrollments) == 1
    enrollment = enrollments[0]
    assert enrollment["queue"] == payload["queue"]
    assert enrollment["target_url"] == payload["target_url"]
    assert enrollment["subscription_args"] == payload["subscription_args"]

@pytest.mark.asyncio
async def test_delete_enrollment_success(client):
    # Create an enrollment.
    payload = {
        "queue": "chat.test",
        "target_url": "http://example.com/api",
        "subscription_args": {"durable": True}
    }
    post_resp = await client.post("/enroll", json=payload)
    data = await post_resp.json()
    enrollment_id = data["id"]

    # Delete the enrollment.
    del_resp = await client.delete(f"/enroll/{enrollment_id}")
    assert del_resp.status == 200
    del_data = await del_resp.json()
    assert "Enrollment" in del_data["message"]

    # Confirm deletion.
    get_resp = await client.get("/enrollments")
    enrollments = await get_resp.json()
    assert isinstance(enrollments, list)
    assert len(enrollments) == 0

@pytest.mark.asyncio
async def test_delete_nonexistent_enrollment(client):
    # Attempt to delete an enrollment that does not exist.
    enrollment_id = "nonexistent-id"
    del_resp = await client.delete(f"/enroll/{enrollment_id}")
    # Even if the enrollment does not exist, the endpoint returns 200.
    assert del_resp.status == 200
    del_data = await del_resp.json()
    assert "Enrollment" in del_data["message"]
