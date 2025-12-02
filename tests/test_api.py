import copy
import pytest
from httpx import AsyncClient, ASGITransport

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.mark.asyncio
async def test_get_activities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/activities")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data


@pytest.mark.asyncio
async def test_signup_and_duplicate_rejection():
    email = "tester@example.com"
    activity = "Chess Club"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(f"/activities/{activity}/signup?email={email}")
        assert r.status_code == 200
        assert email in activities[activity]["participants"]

        # signing up again should fail
        r2 = await ac.post(f"/activities/{activity}/signup?email={email}")
        assert r2.status_code == 400


@pytest.mark.asyncio
async def test_unregister_existing_and_missing():
    activity = "Chess Club"
    # take an existing participant
    email = activities[activity]["participants"][0]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.delete(f"/activities/{activity}/participants?email={email}")
        assert r.status_code == 200
        assert email not in activities[activity]["participants"]

        # deleting again returns 404
        r2 = await ac.delete(f"/activities/{activity}/participants?email={email}")
        assert r2.status_code == 404


@pytest.mark.asyncio
async def test_activity_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/activities/NoSuchActivity/signup?email=a@b.com")
        assert r.status_code == 404
