from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
import httpx

router = APIRouter()

async def fetch_categories() -> list[dict]:
    url = f"{settings.coingecko_base_url}/coins/categories"
    async with httpx.AsyncClient(timeout=6.0) as client:
        response = await client.get(url)
        response.raise_for_status()
    return response.json()


@router.get("/coin-categories")
async def get_coin_categories(
    page_num: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    try:
        categories = await fetch_categories()
    except httpx.HTTPError:
        return {"error": "Failed to fetch coin categories"}
    start = (page_num - 1) * per_page
    return categories[start : start + per_page]


async def fetch_coin_list() -> list[dict]:
    url = f"{settings.coingecko_base_url}/coins/list"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch coins") from None


@router.get("/coins")
async def list_coins(
    page_num: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    coins = [coin for coin in await fetch_coin_list() if coin["id"] != "_"]
    start = (page_num - 1) * per_page
    page = coins[start : start + per_page]
    return [
        {"id": coin["id"], "name": coin["name"], "symbol": coin["symbol"]}
        for coin in page
    ]


async def notify_market_fetch(
    coin_id: str | None,
    category: str | None,
    page_num: int,
    count: int,
) -> None:
    if not settings.webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            await client.post(
                settings.webhook_url,
                json={
                    "event": "market_data_fetched",
                    "coin_id": coin_id,
                    "category": category,
                    "page_num": page_num,
                    "count": count,
                },
            )
    except httpx.HTTPError:
        return


async def fetch_markets(
    coin_id: str | None,
    category: str | None,
    page_num: int,
    per_page: int,
) -> list[dict]:
    params: dict = {
        "vs_currency": "cad",
        "page": page_num,
        "per_page": per_page,
    }
    if coin_id:
        params["ids"] = coin_id
    if category:
        params["category"] = category
    url = f"{settings.coingecko_base_url}/coins/markets"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        data = response.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch market data") from None
    await notify_market_fetch(coin_id, category, page_num, len(data))
    return data


@router.get("/markets")
async def market_data(
    coin_id: str | None = None,
    category: str | None = None,
    page_num: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    if not coin_id and not category:
        raise HTTPException(status_code=422, detail="coin_id or category is required")
    return await fetch_markets(coin_id, category, page_num, per_page)