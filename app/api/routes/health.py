from fastapi import APIRouter
from app.core.config import settings
import httpx

router = APIRouter()


async def coingeko_service_status():
    url = f"{settings.coingecko_base_url}/ping"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        return "reachable"
    except httpx.HTTPError:
        return "unreachable"
        


@router.get("/health")
async def health_check():
    return {
        "status" : "OK",
        "version" : settings.app_version,
        "coingecko_service_status": await coingeko_service_status(),
    }