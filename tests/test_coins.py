import asyncio

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.routes.coins import fetch_markets
from app.core.config import settings
from app.main import app

client = TestClient(app)
auth = {"X-API-Key": settings.api_key}


def test_categories_second_page(monkeypatch):
    categories = [{"category_id": f"c{i}", "name": f"N{i}"} for i in range(25)]

    async def fake_fetch():
        return categories

    monkeypatch.setattr("app.api.routes.coins.fetch_categories", fake_fetch)
    response = client.get(
        "/coin-categories",
        params={"page_num": 2, "per_page": 10},
        headers=auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert body[0]["category_id"] == "c10"


def test_list_coins_second_page(monkeypatch):
    coins = [
        {"id": f"c{i}", "name": f"N{i}", "symbol": f"s{i}"} for i in range(25)
    ]

    async def fake_fetch():
        return coins

    monkeypatch.setattr("app.api.routes.coins.fetch_coin_list", fake_fetch)
    response = client.get("/coins", params={"page_num": 2, "per_page": 10}, headers=auth)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert body[0] == {"id": "c10", "name": "N10", "symbol": "s10"}
    assert set(body[0]) == {"id", "name", "symbol"}


def test_list_coins_skips_placeholder(monkeypatch):
    coins = [
        {"id": "_", "name": "placeholder", "symbol": "gib"},
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc"},
    ]

    async def fake_fetch():
        return coins

    monkeypatch.setattr("app.api.routes.coins.fetch_coin_list", fake_fetch)
    response = client.get("/coins", params={"page_num": 1, "per_page": 10}, headers=auth)
    assert response.status_code == 200
    body = response.json()
    assert "_" not in {coin["id"] for coin in body}
    assert body[0] == {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc"}


def test_markets_requires_a_filter():
    response = client.get("/markets", headers=auth)
    assert response.status_code == 422


def test_markets_passes_both_filters(monkeypatch):
    calls = []
    payload = [{"id": "bitcoin", "current_price": 1}]

    async def fake_fetch(coin_id, category, page_num, per_page):
        calls.append((coin_id, category, page_num, per_page))
        return payload

    monkeypatch.setattr("app.api.routes.coins.fetch_markets", fake_fetch)
    response = client.get(
        "/markets",
        params={
            "coin_id": "bitcoin",
            "category": "layer-1",
            "page_num": 2,
            "per_page": 10,
        },
        headers=auth,
    )
    assert response.status_code == 200
    assert response.json() == payload
    assert calls == [("bitcoin", "layer-1", 2, 10)]


def test_coins_rejects_a_wrong_api_key():
    response = client.get("/coins", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _fake_client(posts, *, fail=False):
    class FakeClient:
        def __init__(self, timeout=6.0):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params=None):
            if fail:
                raise httpx.ConnectError("down")
            return _FakeResponse([{"id": "bitcoin"}])

        async def post(self, url, json=None):
            posts.append((url, json))

    return FakeClient


def test_fetch_markets_notifies_webhook(monkeypatch):
    posts = []
    monkeypatch.setattr("app.api.routes.coins.httpx.AsyncClient", _fake_client(posts))
    monkeypatch.setattr(
        "app.api.routes.coins.settings.webhook_url", "https://example.test/hook"
    )
    data = asyncio.run(fetch_markets("bitcoin", "layer-1", 1, 10))
    assert data == [{"id": "bitcoin"}]
    assert posts == [
        (
            "https://example.test/hook",
            {
                "event": "market_data_fetched",
                "coin_id": "bitcoin",
                "category": "layer-1",
                "page_num": 1,
                "count": 1,
            },
        )
    ]


def test_fetch_markets_error_does_not_notify(monkeypatch):
    posts = []
    monkeypatch.setattr(
        "app.api.routes.coins.httpx.AsyncClient", _fake_client(posts, fail=True)
    )
    monkeypatch.setattr(
        "app.api.routes.coins.settings.webhook_url", "https://example.test/hook"
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(fetch_markets("bitcoin", None, 1, 10))
    assert exc.value.status_code == 502
    assert posts == []
