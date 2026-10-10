"""Unit and Flask API integration tests."""

import pytest

from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "watchlist.sqlite"))
    app.config.update(TESTING=True)
    return app.test_client()


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Stock Trend Lab" in response.data


def test_health(client):
    assert client.get("/health").json["status"] == "ok"


def test_metrics(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"sit753_http_requests_total" in response.data


def test_prediction(client):
    response = client.post("/api/predict", json={"prices": [100, 105, 110, 115], "window": 2})
    assert response.status_code == 200
    assert response.json["forecast"] == 112.5
    assert response.json["trend"] == "down"


@pytest.mark.parametrize("payload", [
    {}, {"prices": []}, {"prices": [1, 2, 0]},
    {"prices": [1, 2, 3], "window": 4}, {"prices": [1, 2, 3], "window": True},
    {"prices": "123"},
])
def test_invalid_prediction(client, payload):
    assert client.post("/api/predict", json=payload).status_code == 400


def test_watchlist_create_read_remove(client):
    created = client.post("/api/watchlist", json={"symbol": "aapl"})
    assert created.status_code == 201
    assert created.json["symbol"] == "AAPL"
    assert client.post("/api/watchlist", json={"symbol": "AAPL"}).status_code == 200
    assert client.get("/api/watchlist").json["symbols"] == ["AAPL"]
    assert client.delete("/api/watchlist/AAPL").status_code == 200
    assert client.get("/api/watchlist").json["symbols"] == []
    assert client.delete("/api/watchlist/AAPL").status_code == 404


def test_watchlist_validation(client):
    assert client.post("/api/watchlist", json={"symbol": "../etc"}).status_code == 400
    assert client.post("/api/watchlist", json={"symbol": 12}).status_code == 400
