import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_unknown_route_returns_json(client):
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "code" in data
